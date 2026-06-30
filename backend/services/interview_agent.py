"""
Interview Agent — Timer-Based Continuous Questioning

FLOW:
  • Questions asked continuously within the session timer
  • If answer is good (score ≥ 5.0) → move to next question immediately
  • If answer is insufficient (score < 5.0) → prompt up to 3 times:
      Prompt 1: "I'd like you to elaborate more on that..."
      Prompt 2: "Almost there, but I need more detail about..."
      Prompt 3: "One last chance — can you expand on..."
  • After 3 insufficient attempts → move to next question anyway
  • Cumulative score = all questions attempted within time
  • No fixed question limit — keeps going until timer ends

No LangChain, no OpenAI, no external API calls.
"""

import uuid as uuid_mod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
from backend.nlp_engine.answer_evaluator import evaluate_answer
from backend.nlp_engine.feedback_generator import generate_final_summary

logger = get_logger("backend.services.interview_agent")

# Threshold: score at or above this means "good answer, move on"
GOOD_ANSWER_THRESHOLD = 5.0

# Maximum number of re-prompts before force-moving to next question
MAX_REPROMPTS = 3

# Re-prompt messages (progressively more insistent)
REPROMPT_MESSAGES = [
    "I'd like you to elaborate more on that. Can you provide more specific details or examples about {topic}?",
    "Almost there, but I need a bit more depth in your answer. Could you explain further?",
    "One last chance — try to expand on the key concepts. What else can you add to your answer?",
]


@dataclass
class AgentState:
    """Serializable state for the Interview Agent — persisted to Redis."""
    session_id: str
    candidate_name: str = "Candidate"
    current_question_index: int = 0
    total_questions: int = 0  # Total available questions (pool size)
    questions_attempted: int = 0  # How many questions the candidate has seen
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    scores: List[Dict[str, Any]] = field(default_factory=list)
    # Re-prompt tracking for current question
    current_reprompt_count: int = 0  # 0 = first answer, 1-3 = re-prompts
    current_best_score: float = 0.0  # Best score across attempts for this question
    current_attempts: List[str] = field(default_factory=list)  # All answers for current Q


class InterviewAgent:
    """
    Timer-based interview agent — continuously asks questions,
    re-prompts up to 3 times if answer is insufficient,
    then moves on.
    """

    def __init__(self, state: AgentState):
        self.state = state

    # ── Factory methods ──────────────────────────────────────────

    @classmethod
    async def create_new(
        cls,
        session_id: str,
        candidate_name: str,
        total_questions: int,
    ) -> "InterviewAgent":
        """Create a brand-new agent for a new interview session."""
        state = AgentState(
            session_id=session_id,
            candidate_name=candidate_name,
            total_questions=total_questions,
        )
        agent = cls(state)
        logger.info("agent_created", session_id=session_id, candidate=candidate_name, total_q=total_questions)
        return agent

    @classmethod
    async def restore(cls, session_id: str) -> Optional["InterviewAgent"]:
        """Restore an agent from Redis state."""
        raw = await session_service.get_agent_state(session_id)
        if raw is None:
            return None
        try:
            agent = cls(raw)
            logger.info("agent_restored", session_id=session_id)
            return agent
        except Exception as e:
            logger.error("agent_restore_failed", error=str(e))
            return None

    async def save(self) -> None:
        """Persist agent state to Redis."""
        await session_service.save_agent_state(self.state.session_id, self.state)

    # ── Core interview logic ─────────────────────────────────────

    async def process_answer(
        self,
        user_message: str,
        questions_cache: List[Dict],
        db: AsyncSession,
    ) -> ChatResponse:
        """
        Process a candidate's answer:
        1. Evaluate with local NLP
        2. If good answer (≥5.0) → persist score, move to next question
        3. If bad answer (<5.0) and reprompts < 3 → ask for more
        4. If bad answer and reprompts = 3 → persist best score, move on
        """
        s = self.state
        current_idx = s.current_question_index

        # All questions exhausted from pool
        if current_idx >= len(questions_cache):
            return self._build_complete_response()

        current_question = questions_cache[current_idx]
        question_text = current_question["question"]
        expected_keywords = current_question.get("expected_keywords", [])
        topic = current_question.get("topic", "this topic")

        # ── Evaluate answer locally ──────────────────────────────
        evaluation = evaluate_answer(
            question_text=question_text,
            answer_text=user_message,
            expected_keywords=expected_keywords,
        )

        score = evaluation["score"]
        strengths = evaluation["strengths"]
        gaps = evaluation["gaps"]
        model_hint = evaluation["model_answer_hint"]
        acknowledgment = evaluation["acknowledgment"]

        # Track attempt
        s.current_attempts.append(user_message)

        # Update best score for this question
        if score > s.current_best_score:
            s.current_best_score = score

        # Record in conversation history
        s.conversation_history.append({
            "role": "candidate",
            "content": user_message,
            "question_index": current_idx,
            "attempt": s.current_reprompt_count + 1,
        })

        # ── DECISION: Move on or re-prompt? ──────────────────────
        answer_is_good = score >= GOOD_ANSWER_THRESHOLD
        max_reprompts_reached = s.current_reprompt_count >= MAX_REPROMPTS
        time_expired = "[Time expired" in user_message

        if answer_is_good or max_reprompts_reached or time_expired:
            if time_expired:
                acknowledgment = "⏱️ **Time expired for this question.**"
            
            # ═══ MOVE TO NEXT QUESTION ═══
            return await self._finalize_and_advance(
                current_idx=current_idx,
                current_question=current_question,
                questions_cache=questions_cache,
                user_message=user_message,
                score=s.current_best_score,  # Use best score across attempts
                strengths=strengths,
                gaps=gaps,
                model_hint=model_hint,
                acknowledgment=acknowledgment,
                evaluation=evaluation,
                db=db,
            )
        else:
            # ═══ RE-PROMPT: Ask for more detail ═══
            return await self._reprompt(
                current_idx=current_idx,
                current_question=current_question,
                questions_cache=questions_cache,
                score=score,
                strengths=strengths,
                gaps=gaps,
                model_hint=model_hint,
                topic=topic,
                db=db,
            )

    async def _reprompt(
        self,
        current_idx: int,
        current_question: Dict,
        questions_cache: List[Dict],
        score: float,
        strengths: List[str],
        gaps: List[str],
        model_hint: str,
        topic: str,
        db: AsyncSession,
    ) -> ChatResponse:
        """Ask the candidate for a better answer (up to 3 times)."""
        s = self.state

        # Increment reprompt count
        s.current_reprompt_count += 1
        prompt_idx = s.current_reprompt_count - 1  # 0-indexed

        # Build the re-prompt message
        hint = ", ".join(gaps[:2]) if gaps else topic
        reprompt_template = REPROMPT_MESSAGES[min(prompt_idx, len(REPROMPT_MESSAGES) - 1)]
        reprompt_text = reprompt_template.format(topic=topic, hint=hint)

        # Build response message with partial feedback
        attempt_label = f"(Attempt {s.current_reprompt_count}/{MAX_REPROMPTS + 1})"
        message = (
            f"**Score: {score:.1f}/10** {attempt_label}\n\n"
            f"{reprompt_text}"
        )

        # Record interviewer re-prompt
        s.conversation_history.append({
            "role": "interviewer",
            "content": reprompt_text,
            "question_index": current_idx,
            "is_reprompt": True,
            "reprompt_number": s.current_reprompt_count,
        })

        # Save state
        await self.save()

        # Build feedback (partial — encouraging more)
        feedback = FeedbackDetail(
            score=score,
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
            current_question_number=s.questions_attempted + 1,
            total_questions=len(questions_cache),
            is_follow_up=True,
            follow_up_depth=s.current_reprompt_count,
        )

    async def _finalize_and_advance(
        self,
        current_idx: int,
        current_question: Dict,
        questions_cache: List[Dict],
        user_message: str,
        score: float,
        strengths: List[str],
        gaps: List[str],
        model_hint: str,
        acknowledgment: str,
        evaluation: Dict,
        db: AsyncSession,
    ) -> ChatResponse:
        """Finalize current question score and advance to next question."""
        s = self.state

        question_text = current_question["question"]

        # ── Store final score for this question ──────────────────
        score_entry = {
            "question_index": current_idx,
            "question": question_text,
            "answer": user_message,
            "best_answer": user_message,  # Last attempt (or best)
            "score": score,
            "attempts": len(s.current_attempts),
            "strengths": strengths,
            "gaps": gaps,
            "acknowledgment": acknowledgment,
        }
        s.scores.append(score_entry)
        s.questions_attempted += 1

        # ── Persist answer to DB ─────────────────────────────────
        try:
            session_uuid = uuid_mod.UUID(s.session_id)
            from backend.models.question import Question as QuestionORM
            q_result = await db.execute(
                select(QuestionORM).where(
                    QuestionORM.session_id == session_uuid,
                    QuestionORM.question_number == (current_idx + 1)
                )
            )
            db_question = q_result.scalar_one_or_none()
            if db_question:
                # Combine all attempts for the answer text
                combined_answer = " | ".join(s.current_attempts) if len(s.current_attempts) > 1 else user_message
                db_answer = AnswerORM(
                    session_id=session_uuid,
                    question_id=db_question.id,
                    answer_text=combined_answer,
                    score=int(score),
                    strengths=strengths,
                    improvements=gaps,
                    model_answer_hint=model_hint,
                )
                db.add(db_answer)
        except Exception as e:
            logger.error("failed_to_persist_answer", error=str(e))

        # Save feedback to Redis
        await session_service.add_answer_feedback(s.session_id, score_entry)

        # ── Reset re-prompt state for next question ──────────────
        s.current_reprompt_count = 0
        s.current_best_score = 0.0
        s.current_attempts = []

        # ── Advance to next question ─────────────────────────────
        s.current_question_index = current_idx + 1
        next_idx = s.current_question_index

        # ── Build response ───────────────────────────────────────
        is_complete = next_idx >= len(questions_cache)

        if is_complete:
            # All questions from pool exhausted
            message = self._build_completion_message(acknowledgment, len(questions_cache))
            # Update DB status
            await self._mark_session_complete(db)
        else:
            # Build next question message
            next_q = questions_cache[next_idx]
            q_type_label = next_q.get("type", "technical").upper()

            # Determine move-on context
            if len(s.scores) > 0 and s.scores[-1]["attempts"] > 1:
                transition = f"{acknowledgment}\n\nLet's move to the next question."
            else:
                transition = f"{acknowledgment}"

            message = (
                f"{transition}\n\n"
                f"---\n"
                f"**Question {s.questions_attempted + 1}** [{q_type_label}]\n\n"
                f"❓ {next_q['question']}"
            )

            # Record interviewer turn
            s.conversation_history.append({
                "role": "interviewer",
                "content": next_q["question"],
                "question_index": next_idx,
            })

        # ── Save agent state ─────────────────────────────────────
        await self.save()

        # Build feedback detail
        feedback = FeedbackDetail(
            score=score,
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
            current_question_number=s.questions_attempted,
            total_questions=len(questions_cache),
            is_follow_up=False,
            follow_up_depth=0,
        )

    def _build_completion_message(self, acknowledgment: str, total_pool: int) -> str:
        """Build the interview-complete message with cumulative stats."""
        s = self.state
        total_answered = s.questions_attempted
        avg_score = sum(sc["score"] for sc in s.scores) / max(len(s.scores), 1)
        total_attempts = sum(sc.get("attempts", 1) for sc in s.scores)

        return (
            f"{acknowledgment}\n\n"
            f"---\n"
            f"🏁 **Interview Complete!**\n\n"
            f"📊 **Your Performance:**\n"
            f"• Questions answered: **{total_answered}**\n"
            f"• Average score: **{avg_score:.1f}/10**\n"
            f"• Total attempts: **{total_attempts}** (across all questions)\n\n"
            f"Click 'View Summary' to see your detailed results and recommendations."
        )

    async def _mark_session_complete(self, db: AsyncSession) -> None:
        """Update the DB session status to completed."""
        s = self.state
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
                # Recommendation based on cumulative performance
                if avg >= 8.0:
                    db_session.recommendation = "Strong Hire"
                elif avg >= 6.5:
                    db_session.recommendation = "Hire"
                elif avg >= 5.0:
                    db_session.recommendation = "Maybe — needs improvement"
                else:
                    db_session.recommendation = "No Hire"
                db_session.overall_feedback = (
                    f"Interview completed. {s.questions_attempted} questions answered "
                    f"with average score {avg:.1f}/10."
                )
        except Exception as e:
            logger.error("failed_to_update_session_status", error=str(e))

    def _build_complete_response(self) -> ChatResponse:
        """Build a response for when interview is already complete."""
        return ChatResponse(
            success=True,
            session_id=self.state.session_id,
            message="🏁 Interview already complete. View your summary for detailed results.",
            feedback=None,
            is_interview_complete=True,
            current_question_number=self.state.questions_attempted,
            total_questions=self.state.total_questions,
        )

    async def generate_summary(self, db: AsyncSession) -> Dict:
        """Generate final interview summary from accumulated scores."""
        return generate_final_summary(
            scores=self.state.scores,
            candidate_name=self.state.candidate_name,
            total_questions=self.state.questions_attempted,
        )
