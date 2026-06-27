"""
Interview Agent v2 — Agentic AI-Powered Interview Conductor.

Drop-in replacement for backend/services/interview_agent.py that:
- Uses HybridEvaluator (deepseek-r1 + semantic + rule-based fallback)
- Uses InterviewConductor (llama3) for natural conversation
- Supports intelligent follow-up questions
- Maintains the same interface: process_answer() → ChatResponse
- Persists state to Redis, scores to PostgreSQL

Same external API, dramatically better intelligence.
"""

import uuid as uuid_mod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# ── Project imports ──────────────────────────────────────────────────────────
from backend.core.config import settings
from backend.core.logging import get_logger
from backend.models.interview import InterviewSession, SessionStatus
from backend.models.answer import Answer as AnswerORM
from backend.models.schemas import (
    ChatResponse,
    FeedbackDetail,
    AgentEvaluation,
)
from backend.services import session_service
from backend.nlp_engine.feedback_generator import generate_final_summary

# ── Agentic imports ──────────────────────────────────────────────────────────
from backend.agentic.hybrid_evaluator import evaluate_answer_agentic, get_hybrid_evaluator
from backend.agentic.interview_conductor import get_interview_conductor
from backend.agentic.agent_config import get_agentic_config

logger = get_logger("backend.services.interview_agent_v2")


# ══════════════════════════════════════════════════════════════════════════════
# AGENT STATE (Extended for follow-ups)
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class AgentStateV2:
    """
    Extended serializable state for the Agentic Interview Agent.

    Additions over v1:
    - awaiting_follow_up: bool flag for follow-up state
    - follow_up_count: tracks follow-ups per question
    - pending_follow_up: the follow-up question text
    - performance_trajectory: tracks score trend for adaptive behavior
    """
    session_id: str
    candidate_name: str = "Candidate"
    current_question_index: int = 0
    total_questions: int = 0
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    scores: List[Dict[str, Any]] = field(default_factory=list)

    # ── Follow-up state ──────────────────────────────────────────────────
    awaiting_follow_up: bool = False
    follow_up_count: int = 0            # Follow-ups asked for current question
    pending_follow_up: str = ""         # The follow-up question text
    pending_follow_up_context: Dict[str, Any] = field(default_factory=dict)

    # ── Performance tracking ─────────────────────────────────────────────
    performance_trajectory: List[float] = field(default_factory=list)


# ══════════════════════════════════════════════════════════════════════════════
# INTERVIEW AGENT V2
# ══════════════════════════════════════════════════════════════════════════════

class InterviewAgentV2:
    """
    Agentic AI-powered interview agent.

    Differences from v1:
    - Uses LLM (deepseek-r1) for deep answer evaluation
    - Uses LLM (llama3) for natural conversation flow
    - Supports follow-up questions when answers are weak/vague
    - Blends LLM + semantic + rule-based scoring
    - Falls back gracefully when Ollama is unavailable
    """

    def __init__(self, state: AgentStateV2):
        self.state = state
        self._config = get_agentic_config()
        self._conductor = get_interview_conductor()
        self._evaluator = get_hybrid_evaluator()

    # ── Factory Methods ──────────────────────────────────────────────────────

    @classmethod
    async def create_new(
        cls,
        session_id: str,
        candidate_name: str,
        total_questions: int,
    ) -> "InterviewAgentV2":
        """Create a brand-new agent for a new interview session."""
        state = AgentStateV2(
            session_id=session_id,
            candidate_name=candidate_name,
            total_questions=total_questions,
        )
        agent = cls(state)
        logger.info(
            "agent_v2_created",
            session_id=session_id,
            candidate=candidate_name,
            total_q=total_questions,
            mode="agentic",
        )
        return agent

    @classmethod
    async def restore(cls, session_id: str) -> Optional["InterviewAgentV2"]:
        """Restore an agent from Redis state."""
        raw = await session_service.get_agent_state(session_id)
        if raw is None:
            return None
        try:
            # Handle both v1 and v2 state formats
            if isinstance(raw, AgentStateV2):
                state = raw
            elif isinstance(raw, dict):
                state = AgentStateV2(**{
                    k: v for k, v in raw.items()
                    if k in AgentStateV2.__dataclass_fields__
                })
            else:
                # Try to adapt v1 AgentState
                state = AgentStateV2(
                    session_id=getattr(raw, "session_id", session_id),
                    candidate_name=getattr(raw, "candidate_name", "Candidate"),
                    current_question_index=getattr(raw, "current_question_index", 0),
                    total_questions=getattr(raw, "total_questions", 0),
                    conversation_history=getattr(raw, "conversation_history", []),
                    scores=getattr(raw, "scores", []),
                )
            agent = cls(state)
            logger.info("agent_v2_restored", session_id=session_id)
            return agent
        except Exception as e:
            logger.error("agent_v2_restore_failed", error=str(e))
            return None

    async def save(self) -> None:
        """Persist agent state to Redis."""
        await session_service.save_agent_state(self.state.session_id, self.state)

    # ── Core Interview Logic ─────────────────────────────────────────────────

    async def process_answer(
        self,
        user_message: str,
        questions_cache: List[Dict],
        db: AsyncSession,
    ) -> ChatResponse:
        """
        Process a candidate's answer with agentic evaluation.

        Flow:
        1. Check if this is a follow-up response or initial answer
        2. Evaluate answer (LLM + semantic + rule-based blending)
        3. Decide: ask follow-up OR move to next question
        4. Generate natural transition/response
        5. Persist everything

        Args:
            user_message: The candidate's answer text
            questions_cache: Cached question list from Redis
            db: Async SQLAlchemy session

        Returns:
            ChatResponse with feedback and next question/follow-up
        """
        s = self.state

        # ── Handle follow-up response ────────────────────────────────────
        if s.awaiting_follow_up:
            return await self._process_follow_up_answer(user_message, questions_cache, db)

        # ── Normal answer processing ─────────────────────────────────────
        current_idx = s.current_question_index

        # Guard: interview already complete
        if current_idx >= len(questions_cache):
            return self._build_complete_response()

        current_question = questions_cache[current_idx]
        question_text = current_question["question"]
        expected_keywords = current_question.get("expected_keywords", [])
        difficulty = current_question.get("difficulty", "medium")
        category = current_question.get("category", "technical")
        question_type = current_question.get("type", "technical")

        # ── Evaluate answer with hybrid system ───────────────────────────
        evaluation = await evaluate_answer_agentic(
            question_text=question_text,
            answer_text=user_message,
            expected_keywords=expected_keywords,
            difficulty=difficulty,
            category=category,
        )

        score = evaluation["score"]
        strengths = evaluation.get("strengths", [])
        gaps = evaluation.get("gaps", [])
        model_hint = evaluation.get("model_answer_hint", "")
        acknowledgment = evaluation.get("acknowledgment", "")
        feedback_text = evaluation.get("feedback", "")
        follow_up_question = evaluation.get("follow_up_question")
        eval_mode = evaluation.get("evaluation_mode", "unknown")

        # Track performance
        s.performance_trajectory.append(float(score))

        # ── Record in conversation history ───────────────────────────────
        s.conversation_history.append({
            "role": "candidate",
            "content": user_message,
            "question_index": current_idx,
            "is_follow_up": False,
        })

        # ── Store score ──────────────────────────────────────────────────
        score_entry = {
            "question_index": current_idx,
            "question": question_text,
            "answer": user_message,
            "score": score,
            "strengths": strengths,
            "gaps": gaps,
            "acknowledgment": acknowledgment,
            "evaluation_mode": eval_mode,
            "feedback": feedback_text,
        }
        s.scores.append(score_entry)

        # ── Persist to DB ────────────────────────────────────────────────
        await self._persist_answer_to_db(
            db=db,
            session_id=s.session_id,
            question_index=current_idx,
            answer_text=user_message,
            score=score,
            strengths=strengths,
            gaps=gaps,
            model_hint=model_hint,
        )

        # ── Save feedback to Redis ───────────────────────────────────────
        await session_service.add_answer_feedback(s.session_id, score_entry)

        # ── Decide: follow-up or next question? ──────────────────────────
        should_follow_up = self._should_ask_follow_up(
            score=score,
            follow_up_question=follow_up_question,
            answer_word_count=len(user_message.split()),
        )

        if should_follow_up and follow_up_question:
            # Ask follow-up
            return await self._ask_follow_up(
                follow_up_question=follow_up_question,
                current_idx=current_idx,
                score=score,
                acknowledgment=acknowledgment,
                feedback_text=feedback_text,
                strengths=strengths,
                gaps=gaps,
                model_hint=model_hint,
                questions_cache=questions_cache,
            )
        else:
            # Move to next question
            return await self._advance_to_next_question(
                current_idx=current_idx,
                score=score,
                acknowledgment=acknowledgment,
                feedback_text=feedback_text,
                strengths=strengths,
                gaps=gaps,
                model_hint=model_hint,
                questions_cache=questions_cache,
                db=db,
            )

    # ── Follow-up Handling ───────────────────────────────────────────────────

    def _should_ask_follow_up(
        self,
        score: float,
        follow_up_question: Optional[str],
        answer_word_count: int,
    ) -> bool:
        """
        Decide whether to ask a follow-up question.

        Conditions for follow-up:
        1. Follow-ups are enabled (max_follow_ups > 0)
        2. Haven't exceeded follow-up limit for this question
        3. Score is below threshold OR answer is too brief
        4. A follow-up question is available
        """
        if self._config.max_follow_ups <= 0:
            return False

        if self.state.follow_up_count >= self._config.max_follow_ups:
            return False

        if not follow_up_question:
            return False

        # Score below threshold
        if score < self._config.follow_up_threshold:
            return True

        # Answer too brief
        if answer_word_count < self._config.follow_up_min_answer_words:
            return True

        return False

    async def _ask_follow_up(
        self,
        follow_up_question: str,
        current_idx: int,
        score: float,
        acknowledgment: str,
        feedback_text: str,
        strengths: List[str],
        gaps: List[str],
        model_hint: str,
        questions_cache: List[Dict],
    ) -> ChatResponse:
        """Build a follow-up question response."""
        s = self.state

        # Set follow-up state
        s.awaiting_follow_up = True
        s.follow_up_count += 1
        s.pending_follow_up = follow_up_question
        s.pending_follow_up_context = {
            "question_index": current_idx,
            "original_score": score,
            "original_strengths": strengths,
            "original_gaps": gaps,
        }

        # Build message
        message = (
            f"{acknowledgment}\n\n"
            f"🔍 **Follow-up:** {follow_up_question}"
        )

        # Record in history
        s.conversation_history.append({
            "role": "interviewer",
            "content": follow_up_question,
            "question_index": current_idx,
            "is_follow_up": True,
            "follow_up_depth": s.follow_up_count,
        })

        await self.save()

        feedback = FeedbackDetail(
            score=int(score),
            strengths=strengths,
            improvements=gaps,
            model_answer_hint=model_hint,
        )

        return ChatResponse(
            success=True,
            session_id=s.session_id,
            message=message,
            feedback=feedback,
            is_interview_complete=False,
            current_question_number=current_idx + 1,
            total_questions=len(questions_cache),
            is_follow_up=True,
            follow_up_depth=s.follow_up_count,
        )

    async def _process_follow_up_answer(
        self,
        user_message: str,
        questions_cache: List[Dict],
        db: AsyncSession,
    ) -> ChatResponse:
        """
        Process a candidate's answer to a follow-up question.

        Evaluates the follow-up answer and then moves to the next question.
        May adjust the original score upward if the follow-up shows understanding.
        """
        s = self.state
        ctx = s.pending_follow_up_context
        current_idx = ctx.get("question_index", s.current_question_index)
        original_score = ctx.get("original_score", 5.0)

        current_question = questions_cache[current_idx] if current_idx < len(questions_cache) else {}
        question_text = current_question.get("question", "")
        expected_keywords = current_question.get("expected_keywords", [])

        # Evaluate the follow-up answer
        follow_up_eval = await evaluate_answer_agentic(
            question_text=s.pending_follow_up,
            answer_text=user_message,
            expected_keywords=expected_keywords,
            difficulty=current_question.get("difficulty", "medium"),
        )

        follow_up_score = follow_up_eval["score"]

        # Adjust score: blend original + follow-up (follow-up can only help, not hurt much)
        # If follow-up is better, give bonus. If worse, minimal penalty.
        if follow_up_score > original_score:
            adjusted_score = original_score + (follow_up_score - original_score) * 0.5
        else:
            adjusted_score = original_score - 0.5  # Small penalty for poor follow-up

        adjusted_score = max(0.0, min(10.0, adjusted_score))

        # Record follow-up in history
        s.conversation_history.append({
            "role": "candidate",
            "content": user_message,
            "question_index": current_idx,
            "is_follow_up": True,
            "follow_up_depth": s.follow_up_count,
        })

        # Update the score entry with adjusted score
        for score_entry in s.scores:
            if score_entry.get("question_index") == current_idx:
                score_entry["follow_up_answer"] = user_message
                score_entry["follow_up_score"] = follow_up_score
                score_entry["adjusted_score"] = int(round(adjusted_score))
                score_entry["score"] = int(round(adjusted_score))
                break

        # Clear follow-up state
        s.awaiting_follow_up = False
        s.follow_up_count = 0
        s.pending_follow_up = ""
        s.pending_follow_up_context = {}

        # Now advance to next question
        acknowledgment = follow_up_eval.get("acknowledgment", "Thanks for the clarification.")
        feedback_text = follow_up_eval.get("feedback", "")

        return await self._advance_to_next_question(
            current_idx=current_idx,
            score=adjusted_score,
            acknowledgment=acknowledgment,
            feedback_text=feedback_text,
            strengths=follow_up_eval.get("strengths", []),
            gaps=follow_up_eval.get("gaps", []),
            model_hint=follow_up_eval.get("model_answer_hint", ""),
            questions_cache=questions_cache,
            db=db,
        )

    # ── Advancing to Next Question ───────────────────────────────────────────

    async def _advance_to_next_question(
        self,
        current_idx: int,
        score: float,
        acknowledgment: str,
        feedback_text: str,
        strengths: List[str],
        gaps: List[str],
        model_hint: str,
        questions_cache: List[Dict],
        db: AsyncSession,
    ) -> ChatResponse:
        """Advance to the next question or complete the interview."""
        s = self.state

        # Move to next
        s.current_question_index = current_idx + 1
        s.follow_up_count = 0  # Reset for next question
        next_idx = s.current_question_index

        is_complete = next_idx >= len(questions_cache)

        if is_complete:
            # ── Interview Complete ───────────────────────────────────────
            # Generate closing message via conductor
            closing_msg = await self._conductor.generate_closing(
                candidate_name=s.candidate_name,
                total_questions=len(questions_cache),
                scores=s.scores,
            )

            message = (
                f"{acknowledgment}\n\n"
                f"---\n"
                f"🏁 **Interview Complete!**\n\n"
                f"{closing_msg}\n\n"
                f"Click 'View Summary' to see your detailed results and recommendations."
            )

            # Update DB status
            try:
                result_row = await db.execute(
                    select(InterviewSession).where(
                        InterviewSession.id == uuid_mod.UUID(s.session_id)
                    )
                )
                db_session = result_row.scalar_one_or_none()
                if db_session:
                    db_session.status = SessionStatus.COMPLETED.value
                    avg = sum(sc["score"] for sc in s.scores) / max(len(s.scores), 1)
                    db_session.average_score = avg
            except Exception as e:
                logger.error("failed_to_update_session_status", error=str(e))

        else:
            # ── Generate Transition to Next Question ─────────────────────
            next_q = questions_cache[next_idx]
            q_type_label = next_q.get("type", "technical").upper()

            # Generate natural transition
            transition = await self._conductor.generate_transition(
                prev_score=score,
                next_question=next_q["question"],
                question_number=next_idx + 1,
                total_questions=len(questions_cache),
                question_type=next_q.get("type", "technical"),
            )

            message = (
                f"{acknowledgment}\n\n"
                f"{transition}\n\n"
                f"---\n"
                f"**Question {next_idx + 1} of {len(questions_cache)}** [{q_type_label}]\n\n"
                f"❓ {next_q['question']}"
            )

            # Record interviewer turn
            s.conversation_history.append({
                "role": "interviewer",
                "content": next_q["question"],
                "question_index": next_idx,
                "is_follow_up": False,
            })

        # ── Save agent state ─────────────────────────────────────────────
        await self.save()

        # Build feedback detail
        feedback = FeedbackDetail(
            score=int(round(score)),
            strengths=strengths,
            improvements=gaps,
            model_answer_hint=model_hint,
        )

        return ChatResponse(
            success=True,
            session_id=s.session_id,
            message=message,
            feedback=feedback,
            is_interview_complete=is_complete,
            current_question_number=next_idx + (0 if is_complete else 1),
            total_questions=len(questions_cache),
            is_follow_up=False,
            follow_up_depth=0,
        )

    # ── Database Persistence ─────────────────────────────────────────────────

    async def _persist_answer_to_db(
        self,
        db: AsyncSession,
        session_id: str,
        question_index: int,
        answer_text: str,
        score: float,
        strengths: List[str],
        gaps: List[str],
        model_hint: str,
    ) -> None:
        """Persist the answer to PostgreSQL."""
        try:
            session_uuid = uuid_mod.UUID(session_id)
            from backend.models.question import Question as QuestionORM
            q_result = await db.execute(
                select(QuestionORM).where(
                    QuestionORM.session_id == session_uuid,
                    QuestionORM.question_number == (question_index + 1)
                )
            )
            db_question = q_result.scalar_one_or_none()
            if db_question:
                db_answer = AnswerORM(
                    session_id=session_uuid,
                    question_id=db_question.id,
                    answer_text=answer_text,
                    score=int(round(score)),
                    strengths=strengths,
                    improvements=gaps,
                    model_answer_hint=model_hint,
                )
                db.add(db_answer)
        except Exception as e:
            logger.error("failed_to_persist_answer", error=str(e))

    # ── Utility Methods ──────────────────────────────────────────────────────

    def _build_complete_response(self) -> ChatResponse:
        """Build a response for when interview is already complete."""
        return ChatResponse(
            success=True,
            session_id=self.state.session_id,
            message="🏁 Interview already complete. View your summary for detailed results.",
            feedback=None,
            is_interview_complete=True,
            current_question_number=self.state.total_questions,
            total_questions=self.state.total_questions,
        )

    async def generate_summary(self, db: AsyncSession) -> Dict:
        """Generate final interview summary from accumulated scores."""
        return generate_final_summary(
            scores=self.state.scores,
            candidate_name=self.state.candidate_name,
            total_questions=self.state.total_questions,
        )


# ══════════════════════════════════════════════════════════════════════════════
# FACTORY FUNCTION — Use this to decide between v1 and v2
# ══════════════════════════════════════════════════════════════════════════════

async def create_interview_agent(
    session_id: str,
    candidate_name: str,
    total_questions: int,
) -> InterviewAgentV2:
    """
    Factory function that creates the appropriate interview agent.

    Always returns InterviewAgentV2 which handles fallback internally
    (the hybrid evaluator falls back to rule-based when Ollama is down).
    """
    return await InterviewAgentV2.create_new(
        session_id=session_id,
        candidate_name=candidate_name,
        total_questions=total_questions,
    )


async def restore_interview_agent(session_id: str) -> Optional[InterviewAgentV2]:
    """Restore an interview agent from session state."""
    return await InterviewAgentV2.restore(session_id)
