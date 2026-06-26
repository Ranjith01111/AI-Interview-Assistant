"""
Interview Routes — Handles question generation and mock interview chat.
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession

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

# Create router with /interview prefix protected by authentication guard
router = APIRouter(
    prefix="/interview",
    tags=["Interview"],
    dependencies=[Depends(get_current_active_user)]
)


def _validate_session_id(session_id: str) -> str:
    """Validate that session_id is a proper UUID format."""
    try:
        uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format. Must be a valid UUID.")
    return session_id


@router.post("/generate-questions/{session_id}", response_model=GenerateQuestionsResponse)
async def generate_interview_questions(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    session_id = _validate_session_id(session_id)
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
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate questions: {str(e)}"
        )


@router.post("/start/{session_id}", response_model=ChatResponse)
async def start_interview_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    session_id = _validate_session_id(session_id)
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
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start interview: {str(e)}"
        )


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
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

    try:
        response = await process_interview_message(
            request.session_id, request.message, db
        )
        return response

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process answer: {str(e)}"
        )


@router.get("/summary/{session_id}")
async def get_interview_summary(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    session_id = _validate_session_id(session_id)
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
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate summary: {str(e)}"
        )
