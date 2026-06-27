"""
Interview Agent — STANDALONE VERSION (No LLM)

Simplified agent that:
  • Maintains conversation state in Redis
  • Evaluates answers using local NLP keyword matching
  • NEVER asks follow-up questions (moves to next question immediately)
  • Generates final summary from accumulated scores

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


@dataclass
class AgentState:
    """Serializable state for the Interview Agent — persisted to Redis."""
    session_id: str
    candidate_name: str = "Candidate"
    current_question_index: int = 0
    total_questions: int = 0
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    scores: List[Dict[str, Any]] = field(default_factory=list)


class InterviewAgent:
    """
    Simplified interview agent — evaluates answers locally,
    moves to next question, tracks scores.
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
        2. Persist score to DB
        3. Move to next question (NEVER follow-up)
        4. Return response with feedback + next question

        Args:
            user_message: The candidate's answer text
            questions_cache: Cached question list from Redis
            db: Async SQLAlchemy session

        Returns:
            ChatResponse with feedback and next question
        """
        s = self.state
        current_idx = s.current_question_index

        # Get current question data
        if current_idx >= len(questions_cache):
            return self._build_complete_response()

        current_question = questions_cache[current_idx]
        question_text = current_question["question"]
        expected_keywords = current_question.get("expected_keywords", [])

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

        # ── Record in conversation history ───────────────────────
        s.conversation_history.append({
            "role": "candidate",
            "content": user_message,
            "question_index": current_idx,
        })

        # ── Store score ──────────────────────────────────────────
        score_entry = {
            "question_index": current_idx,
            "question": question_text,
            "answer": user_message,
            "score": score,
            "strengths": strengths,
            "gaps": gaps,
            "acknowledgment": acknowledgment,
        }
        s.scores.append(score_entry)

        # ── Persist answer to DB ─────────────────────────────────
        try:
            session_uuid = uuid_mod.UUID(s.session_id)
            # Find the actual question row ID from the DB
            from backend.models.question import Question as QuestionORM
            q_result = await db.execute(
                select(QuestionORM).where(
                    QuestionORM.session_id == session_uuid,
                    QuestionORM.question_number == (current_idx + 1)
                )
            )
            db_question = q_result.scalar_one_or_none()
            if db_question:
                db_answer = AnswerORM(
                    session_id=session_uuid,
                    question_id=db_question.id,
                    answer_text=user_message,
                    score=score,
                    strengths=strengths,
                    improvements=gaps,
                    model_answer_hint=model_hint,
                )
                db.add(db_answer)
        except Exception as e:
            logger.error("failed_to_persist_answer", error=str(e))

        # ── Save feedback to Redis ───────────────────────────────
        await session_service.add_answer_feedback(s.session_id, score_entry)

        # ── Move to next question (NO follow-ups) ────────────────
        s.current_question_index = current_idx + 1
        next_idx = s.current_question_index

        # ── Build response ───────────────────────────────────────
        is_complete = next_idx >= len(questions_cache)

        if is_complete:
            # Interview finished
            message = (
                f"{acknowledgment}\n\n"
                f"---\n"
                f"🏁 **Interview Complete!**\n\n"
                f"You've answered all {len(questions_cache)} questions. "
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
                    # Save recommendation based on score
                    if avg >= 8.0:
                        db_session.recommendation = "Strong Hire"
                    elif avg >= 6.5:
                        db_session.recommendation = "Hire"
                    elif avg >= 5.0:
                        db_session.recommendation = "Maybe — needs improvement"
                    else:
                        db_session.recommendation = "No Hire"
                    db_session.overall_feedback = f"Interview completed. {len(s.scores)} questions answered with average score {avg:.1f}/10."
            except Exception as e:
                logger.error("failed_to_update_session_status", error=str(e))
        else:
            # Build next question message
            next_q = questions_cache[next_idx]
            q_type_label = next_q.get("type", "technical").upper()
            message = (
                f"{acknowledgment}\n\n"
                f"---\n"
                f"**Question {next_idx + 1} of {len(questions_cache)}** [{q_type_label}]\n\n"
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
            current_question_number=next_idx + (0 if is_complete else 1),
            total_questions=len(questions_cache),
            is_follow_up=False,
            follow_up_depth=0,
        )

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
