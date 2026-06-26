"""
Resume Service — Handles PDF parsing and structured data extraction.

STANDALONE VERSION: Uses local NLP engine instead of OpenAI/FAISS.
No external API calls. No embeddings. No vector store.
"""

import io
import uuid
from typing import Tuple

from pypdf import PdfReader
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.models.interview import InterviewSession, SessionStatus
from backend.services import session_service
from backend.nlp_engine.resume_parser import parse_resume_structured


def parse_pdf(file_bytes: bytes) -> str:
    """
    Extract raw text from PDF bytes using PyPDF.

    Args:
        file_bytes: The raw PDF file content as bytes

    Returns:
        Extracted text as a single string
    """
    reader = PdfReader(io.BytesIO(file_bytes))

    full_text = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            full_text.append(page_text)

    return "\n".join(full_text)


async def process_resume(
    file_bytes: bytes,
    db: AsyncSession,
    user_id: uuid.UUID = None,
) -> Tuple[str, dict]:
    """
    Process a resume PDF using local NLP — no external APIs.

    Steps:
    1. Parse PDF → extract raw text
    2. Run NLP parser → extract skills, experience, projects
    3. Persist to PostgreSQL
    4. Cache in Redis

    Args:
        file_bytes: Raw PDF file bytes
        db: Async SQLAlchemy session
        user_id: UUID of the authenticated user

    Returns:
        Tuple of (session_id, metadata_dict)
    """
    # Parse the PDF
    resume_text = parse_pdf(file_bytes)

    if not resume_text.strip():
        raise ValueError("Could not extract text from the PDF. Please ensure it's a text-based PDF.")

    # ── Run local NLP parser ─────────────────────────────────────
    parsed = parse_resume_structured(resume_text)

    candidate_name = parsed["candidate_name"]
    skills = parsed["skills"]
    experience_num = parsed["experience_years"]
    experience = f"{experience_num}+ years" if experience_num > 0 else "Not specified"

    # Generate a unique session ID for this interview
    session_id = str(uuid.uuid4())

    # ── Persist to PostgreSQL ────────────────────────────────────
    db_session = InterviewSession(
        id=uuid.UUID(session_id),
        candidate_name=candidate_name,
        user_id=user_id,
        resume_text=resume_text,
        skills_detected=skills,
        experience_years=experience,
        status=SessionStatus.CREATED.value,
    )
    db.add(db_session)
    await db.flush()

    # ── Cache in Redis ───────────────────────────────────────────
    await session_service.save_session_meta(
        session_id=session_id,
        candidate_name=candidate_name,
        skills=skills,
        experience=experience,
        resume_text=resume_text,
    )

    # Save parsed resume data (replaces FAISS vector store)
    await session_service.save_parsed_resume(session_id, parsed)

    await session_service.save_interview_state(session_id, {
        "current_question_index": 0,
        "total_questions": 0,
    })

    metadata = {
        "candidate_name": candidate_name,
        "skills_detected": skills,
        "experience_years": experience,
    }

    return session_id, metadata
