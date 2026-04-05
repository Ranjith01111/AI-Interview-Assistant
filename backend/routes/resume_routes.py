"""
Resume Router - Handles PDF upload and processing endpoints.
"""

from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse

try:
    from openai import AuthenticationError, RateLimitError
except ImportError:
    AuthenticationError = Exception
    RateLimitError = Exception

from backend.models.schemas import ResumeUploadResponse
from backend.services.resume_service import process_resume

# Create router with /resume prefix
router = APIRouter(prefix="/resume", tags=["Resume"])


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(file: UploadFile = File(...)):
    """
    Upload a PDF resume for processing.
    
    Steps:
    1. Validate file is a PDF
    2. Parse text from PDF
    3. Create embeddings and store in FAISS
    4. Return session ID for subsequent requests
    
    Args:
        file: The uploaded PDF file
        
    Returns:
        ResumeUploadResponse with session_id and detected metadata
    """
    # Validate file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported. Please upload a .pdf file."
        )
    
    # Check file size (max 10MB)
    file_bytes = await file.read()
    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum size is 10MB."
        )
    
    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty."
        )
    
    try:
        # Process the resume (parse + embed + store)
        session_id, metadata = process_resume(file_bytes)
        
        return ResumeUploadResponse(
            success=True,
            message=f"Resume processed successfully! Session created for {metadata['candidate_name']}.",
            session_id=session_id,
            candidate_name=metadata["candidate_name"],
            skills_detected=metadata["skills_detected"],
            experience_years=metadata["experience_years"],
        )
        
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RateLimitError as e:
        raise HTTPException(
            status_code=402,
            detail=(
                "OpenAI quota exceeded or rate limit hit. "
                "Please check your API key billing at https://platform.openai.com/account/billing "
                f"(Details: {str(e)})"
            )
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=401,
            detail=(
                "Invalid OpenAI API key. "
                "Please update OPENROUTER_API_KEY in your .env file. "
                f"(Details: {str(e)})"
            )
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process resume: {type(e).__name__}: {str(e)}"
        )
