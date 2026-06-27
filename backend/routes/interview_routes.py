"""
Interview Routes — Handles question generation and mock interview chat.
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel


from backend.db.session import get_db
from backend.models.schemas import (
    GenerateQuestionsResponse,
    ChatRequest,
    ChatResponse,
    SessionSummaryResponse,
)
from backend.services.question_service import generate_questions
from backend.services.interview_service import (
    start_interview,
    process_interview_message,
    generate_final_summary_endpoint as generate_final_summary,
)
from backend.core.security import get_current_active_user
from backend.models.interview import InterviewSession
from backend.models.user import User, UserRole
from backend.core.logging import get_logger

logger = get_logger("backend.routes.interview")

# Create router with /interview prefix protected by authentication guard
router = APIRouter(
    prefix="/interview",
    tags=["Interview"],
    # Auth is applied per-endpoint to access current_user for ownership checks
)


def _validate_session_id(session_id: str) -> str:
    """Validate that session_id is a proper UUID format."""
    try:
        uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format. Must be a valid UUID.")
    return session_id


async def _verify_session_ownership(
    session_id: str,
    current_user: User,
    db: AsyncSession,
) -> None:
    """
    Verify that the session belongs to the current user.
    Admins and recruiters can access any session (for review purposes).
    Raises HTTP 403 if the user doesn't own the session.
    """
    # Admins and recruiters can view any session
    if current_user.role in (UserRole.ADMIN.value, UserRole.RECRUITER.value):
        return

    result = await db.execute(
        select(InterviewSession.user_id).where(InterviewSession.id == uuid.UUID(session_id))
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    if row != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this session.")


@router.post("/generate-questions/{session_id}", response_model=GenerateQuestionsResponse)
async def generate_interview_questions(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    session_id = _validate_session_id(session_id)
    await _verify_session_ownership(session_id, current_user, db)
    """
    Generate interview questions from the processed resume.
    Uses LangChain RetrievalQA + FAISS to create targeted questions.

    Args:
        session_id: The session ID from the resume upload step
        db: Async database session (injected)

    Returns:
        GenerateQuestionsResponse with list of questions
    """
    try:
        questions = await generate_questions(session_id, db)

        return GenerateQuestionsResponse(
            success=True,
            session_id=session_id,
            questions=questions,
            total_questions=len(questions),
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("generate_questions_failed", session_id=session_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to generate questions. Please try again or contact support."
        )


@router.post("/start/{session_id}", response_model=ChatResponse)
async def start_interview_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    session_id = _validate_session_id(session_id)
    await _verify_session_ownership(session_id, current_user, db)
    """
    Start the mock interview. Returns the first question.

    Args:
        session_id: The session ID (must have questions generated)
        db: Async database session (injected)

    Returns:
        ChatResponse with welcome message and first question
    """
    try:
        response = await start_interview(session_id, db)
        return response

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("start_interview_failed", session_id=session_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to start interview. Please try again or contact support."
        )


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Send a candidate's answer and receive feedback + next question.

    This is the main interview loop endpoint.
    Maintains conversation memory via LangChain ConversationBufferMemory.

    Args:
        request: ChatRequest with session_id and user's answer
        db: Async database session (injected)

    Returns:
        ChatResponse with feedback on the answer + next question
    """
    if not request.message.strip():
        raise HTTPException(
            status_code=400,
            detail="Answer cannot be empty. Please provide a response."
        )
    
    await _verify_session_ownership(request.session_id, current_user, db)

    try:
        response = await process_interview_message(
            request.session_id, request.message, db
        )
        return response

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("process_answer_failed", session_id=request.session_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to process answer. Please try again or contact support."
        )


@router.get("/summary/{session_id}")
async def get_interview_summary(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    session_id = _validate_session_id(session_id)
    await _verify_session_ownership(session_id, current_user, db)
    """
    Get the final interview summary with scores and overall feedback.

    Args:
        session_id: The session ID
        db: Async database session (injected)

    Returns:
        Complete interview summary with scoring breakdown
    """
    try:
        summary = await generate_final_summary(session_id, db)
        return summary

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("generate_summary_failed", session_id=session_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to generate summary. Please try again or contact support."
        )



# ── Voice Interview Session Save ──────────────────────────────────────────────
# Accepts results from the client-side voice interview and persists them.

from typing import List, Optional

class VoiceAnswerResult(BaseModel):
    question: str
    category: str
    answer: str
    score: float
    keywords_matched: List[str] = []
    feedback: Optional[str] = None

class VoiceSessionSaveRequest(BaseModel):
    results: List[VoiceAnswerResult]
    average_score: float
    total_questions: int
    answered_questions: int
    skipped_questions: int


@router.post("/voice-session")
async def save_voice_session(
    payload: VoiceSessionSaveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Save a completed voice interview session to the database.
    Called by the frontend after the voice interview finishes.
    This creates an InterviewSession with status='completed' and stores
    the Q&A breakdown so recruiters can review it.
    """
    from backend.models.interview import InterviewSession, SessionStatus
    from backend.models.question import Question
    from backend.models.answer import Answer

    # Create the session
    session = InterviewSession(
        candidate_name=current_user.name,
        user_id=current_user.id,
        resume_text="[Voice Interview — no resume]",
        skills_detected=["communication", "behavioral"],
        experience_years="N/A",
        status=SessionStatus.COMPLETED.value,
        current_question_index=payload.answered_questions,
        average_score=payload.average_score,
        recommendation=_voice_recommendation(payload.average_score),
        overall_feedback=f"Voice interview completed. {payload.answered_questions}/{payload.total_questions} questions answered.",
    )
    db.add(session)
    await db.flush()  # Get session.id

    # Save each Q&A as Question + Answer records
    for i, r in enumerate(payload.results):
        q = Question(
            session_id=session.id,
            question_number=i + 1,
            question_text=r.question,
            question_type="behavioral",
            category=r.category,
            difficulty="medium",
        )
        db.add(q)
        await db.flush()

        a = Answer(
            session_id=session.id,
            question_id=q.id,
            answer_text=r.answer,
            score=int(r.score),
            strengths=r.keywords_matched,
            improvements=[r.feedback] if r.feedback else [],
            model_answer_hint="",
        )
        db.add(a)

    await db.commit()

    logger.info("voice_session_saved", session_id=str(session.id), user_id=str(current_user.id), score=payload.average_score)

    return {
        "success": True,
        "session_id": str(session.id),
        "average_score": payload.average_score,
        "recommendation": session.recommendation,
    }


def _voice_recommendation(score: float) -> str:
    if score >= 8.0:
        return "Strong Hire"
    elif score >= 6.5:
        return "Hire"
    elif score >= 5.0:
        return "Maybe — needs improvement"
    else:
        return "No Hire"
