"""
Interview Routes - Handles question generation and mock interview chat.
"""

from fastapi import APIRouter, HTTPException

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
    generate_final_summary,
)

# Create router with /interview prefix
router = APIRouter(prefix="/interview", tags=["Interview"])


@router.post("/generate-questions/{session_id}", response_model=GenerateQuestionsResponse)
async def generate_interview_questions(session_id: str):
    """
    Generate interview questions from the processed resume.
    Uses LangChain RetrievalQA + FAISS to create targeted questions.
    
    Args:
        session_id: The session ID from the resume upload step
        
    Returns:
        GenerateQuestionsResponse with list of questions
    """
    try:
        questions = generate_questions(session_id)
        
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
async def start_interview_session(session_id: str):
    """
    Start the mock interview. Returns the first question.
    
    Args:
        session_id: The session ID (must have questions generated)
        
    Returns:
        ChatResponse with welcome message and first question
    """
    try:
        response = start_interview(session_id)
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start interview: {str(e)}"
        )


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a candidate's answer and receive feedback + next question.
    
    This is the main interview loop endpoint.
    Maintains conversation memory via LangChain ConversationBufferMemory.
    
    Args:
        request: ChatRequest with session_id and user's answer
        
    Returns:
        ChatResponse with feedback on the answer + next question
    """
    if not request.message.strip():
        raise HTTPException(
            status_code=400,
            detail="Answer cannot be empty. Please provide a response."
        )
    
    try:
        response = process_interview_message(request.session_id, request.message)
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process answer: {str(e)}"
        )


@router.get("/summary/{session_id}")
async def get_interview_summary(session_id: str):
    """
    Get the final interview summary with scores and overall feedback.
    
    Args:
        session_id: The session ID
        
    Returns:
        Complete interview summary with scoring breakdown
    """
    try:
        summary = generate_final_summary(session_id)
        return summary
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate summary: {str(e)}"
        )
