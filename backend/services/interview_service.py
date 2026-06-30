"""
Interview Service — STANDALONE VERSION (No LLM)

Manages the mock interview conversation using the local NLP agent.
No LangChain, no OpenAI, no external API calls.
"""

import uuid as uuid_mod
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.logging import get_logger
from backend.models.interview import InterviewSession, SessionStatus
from backend.models.schemas import ChatResponse, FeedbackDetail
from backend.services import session_service
from backend.services.interview_agent import InterviewAgent
from backend.nlp_engine.feedback_generator import generate_final_summary

logger = get_logger("backend.services.interview_service")


async def process_interview_message(
    session_id: str,
    user_message: str,
    db: AsyncSession,
) -> ChatResponse:
    """
    Process a candidate's answer and return the next question + feedback.

    Args:
        session_id: The unique session ID
        user_message: The candidate's answer text
        db: Async SQLAlchemy session

    Returns:
        ChatResponse with feedback and next question (or completion message)
    """
    # Restore agent
    agent = await InterviewAgent.restore(session_id)
    if agent is None:
        raise ValueError(f"No active interview agent for session {session_id}.")

    # Get cached questions
    questions_cache = await session_service.get_questions_cache(session_id)
    if not questions_cache:
        raise ValueError("No questions found. Please generate questions first.")

    # Delegate to the agent (uses local NLP evaluator)
    response = await agent.process_answer(user_message, questions_cache, db)

    # Sync interview state
    await session_service.save_interview_state(session_id, {
        "current_question_index": agent.state.current_question_index,
        "total_questions": agent.state.total_questions,
    })

    return response


async def start_interview(
    session_id: str,
    db: AsyncSession,
) -> ChatResponse:
    """
    Start the interview by creating a new agent and asking the first question.

    Args:
        session_id: The unique session ID
        db: Async SQLAlchemy session

    Returns:
        ChatResponse with the first question
    """
    session_uuid = uuid_mod.UUID(session_id)

    # Get session meta from Redis
    session_meta = await session_service.get_session_meta(session_id)
    if session_meta is None:
        raise ValueError(f"Session {session_id} not found.")

    # Get cached questions
    questions_cache = await session_service.get_questions_cache(session_id)
    if not questions_cache:
        raise ValueError("No questions generated. Please generate questions first.")

    candidate_name = session_meta.get("candidate_name", "Candidate")

    # Create the Interview Agent
    agent = await InterviewAgent.create_new(
        session_id=session_id,
        candidate_name=candidate_name,
        total_questions=len(questions_cache),
    )

    # Record the first question in agent conversation history
    first_question = questions_cache[0]
    agent.state.conversation_history.append({
        "role": "interviewer",
        "content": first_question["question"],
        "question_index": 0,
    })

    # Save agent to Redis
    await agent.save()

    # Reset interview state
    await session_service.save_interview_state(session_id, {
        "current_question_index": 0,
        "total_questions": len(questions_cache),
    })
    await session_service.clear_feedback(session_id)

    # Update DB status
    result_row = await db.execute(
        select(InterviewSession).where(InterviewSession.id == session_uuid)
    )
    db_session_row = result_row.scalar_one_or_none()
    if db_session_row:
        db_session_row.status = SessionStatus.IN_PROGRESS.value
        db_session_row.current_question_index = 0
    await db.flush()

    tech_count = sum(1 for q in questions_cache if q.get("type") == "technical")
    hr_count = sum(1 for q in questions_cache if q.get("type") == "hr")

    intro_message = (
        f"👋 Hello **{candidate_name}**! Welcome to your mock interview.\n\n"
        f"💡 **Tip:** Answer as specifically as possible with concrete examples.\n\n"
        f"Ready? Let's begin!\n\n"
        f"❓ {first_question['question']}"
    )

    return ChatResponse(
        success=True,
        session_id=session_id,
        message=intro_message,
        feedback=None,
        is_interview_complete=False,
        current_question_number=1,
        total_questions=len(questions_cache),
    )


async def generate_final_summary_endpoint(
    session_id: str,
    db: AsyncSession,
) -> dict:
    """
    Generate a comprehensive final interview summary.

    Args:
        session_id: The unique session ID
        db: Async SQLAlchemy session

    Returns:
        Dict with complete summary data
    """
    session_uuid = uuid_mod.UUID(session_id)

    # Try agent-powered summary
    agent = await InterviewAgent.restore(session_id)
    if agent is not None:
        logger.info("generating_agent_summary", session_id=session_id)
        summary_data = await agent.generate_summary(db)
    else:
        # Fallback — build from stored feedback
        logger.info("agent_not_found_building_from_feedback", session_id=session_id)
        all_feedback = await session_service.get_all_feedback(session_id)
        session_meta = await session_service.get_session_meta(session_id)
        candidate_name = session_meta.get("candidate_name", "Candidate") if session_meta else "Candidate"

        summary_data = generate_final_summary(
            scores=all_feedback,
            candidate_name=candidate_name,
            total_questions=len(all_feedback),
        )

    # ── Persist summary to database ──────────────────────────────────────
    try:
        result_row = await db.execute(
            select(InterviewSession).where(InterviewSession.id == session_uuid)
        )
        db_session = result_row.scalar_one_or_none()
        if db_session:
            # Save recommendation and overall feedback
            if summary_data.get("recommendation"):
                db_session.recommendation = summary_data["recommendation"]
            if summary_data.get("overall_feedback"):
                db_session.overall_feedback = summary_data["overall_feedback"]
            # Also save average_score if present and not already set
            if summary_data.get("average_score") is not None and db_session.average_score is None:
                db_session.average_score = summary_data["average_score"]
            # Ensure status is completed
            if db_session.status != SessionStatus.COMPLETED.value:
                db_session.status = SessionStatus.COMPLETED.value
            await db.commit()
            logger.info("summary_persisted_to_db", session_id=session_id)
    except Exception as e:
        logger.error("failed_to_persist_summary", session_id=session_id, error=str(e))

    # Add success flag
    summary_data["success"] = True
    summary_data["session_id"] = session_id

    return summary_data
