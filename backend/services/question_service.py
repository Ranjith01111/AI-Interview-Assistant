"""
Question Generation Service — STANDALONE VERSION

Uses local NLP question bank + generator instead of LLM API calls.
No OpenRouter, no LangChain, no external API.
"""

import uuid as uuid_mod
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.logging import get_logger
from backend.models.interview import InterviewSession, SessionStatus
from backend.models.question import Question as QuestionORM
from backend.models.schemas import InterviewQuestion, QuestionType, QuestionCategory, DifficultyLevel
from backend.services import session_service
from backend.nlp_engine.question_generator import generate_questions_for_candidate

logger = get_logger("backend.services.question_service")


async def generate_questions(
    session_id: str,
    db: AsyncSession,
) -> List[InterviewQuestion]:
    """
    Generate interview questions using the local NLP engine.

    Pipeline:
      1. Retrieve session metadata from Redis
      2. Run local question generator (template-based)
      3. Persist questions to PostgreSQL
      4. Cache in Redis for the interview loop

    Args:
        session_id: The unique session ID (must have a processed resume)
        db: Async SQLAlchemy session

    Returns:
        List of InterviewQuestion objects

    Raises:
        ValueError: If the session is not found
    """
    logger.info("generating_questions", session_id=session_id)

    # ── Step 1: Retrieve session data from Redis ─────────────────
    session_meta = await session_service.get_session_meta(session_id)
    if session_meta is None:
        raise ValueError(f"Session {session_id} not found. Please upload a resume first.")

    skills = session_meta.get("skills", [])
    experience = session_meta.get("experience", "Not specified")

    # Get parsed resume for experience level
    parsed_resume = await session_service.get_parsed_resume(session_id)
    experience_level = "mid"
    if parsed_resume:
        experience_level = parsed_resume.get("experience_level", "mid")

    # ── Step 2: Generate questions locally ────────────────────────
    raw_questions = generate_questions_for_candidate(
        skills=skills,
        experience_years=experience,
        experience_level=experience_level,
        num_questions=10,
    )

    logger.info(
        "questions_generated",
        session_id=session_id,
        total=len(raw_questions),
    )

    # ── Step 3: Convert to InterviewQuestion schema ──────────────
    questions: List[InterviewQuestion] = []
    for idx, q in enumerate(raw_questions, start=1):
        # Map category string to enum
        category_map = {
            "technical": QuestionCategory.GENERAL,
            "system_design": QuestionCategory.ARCHITECTURE,
            "behavioral": QuestionCategory.GENERAL,
        }
        category = category_map.get(q["category"], QuestionCategory.GENERAL)

        # Map difficulty
        diff_map = {
            "easy": DifficultyLevel.EASY,
            "medium": DifficultyLevel.MEDIUM,
            "hard": DifficultyLevel.HARD,
        }
        difficulty = diff_map.get(q["difficulty"], DifficultyLevel.MEDIUM)

        # Map type
        q_type = QuestionType.HR if q["type"] == "hr" else QuestionType.TECHNICAL

        questions.append(InterviewQuestion(
            id=idx,
            question=q["question"],
            type=q_type,
            topic=q["topic"],
            category=category,
            difficulty=difficulty,
            project_reference=q.get("project_reference") or "",
        ))

    # ── Step 4: Persist to PostgreSQL ────────────────────────────
    session_uuid = uuid_mod.UUID(session_id)

    for q in questions:
        db_question = QuestionORM(
            session_id=session_uuid,
            question_number=q.id,
            question_text=q.question,
            question_type=q.type.value,
            topic=q.topic,
            difficulty=q.difficulty.value,
            category=q.category.value,
            project_reference=q.project_reference,
        )
        db.add(db_question)

    # Update session status
    result_row = await db.execute(
        select(InterviewSession).where(InterviewSession.id == session_uuid)
    )
    db_session = result_row.scalar_one_or_none()
    if db_session:
        db_session.status = SessionStatus.QUESTIONS_GENERATED.value

    await db.flush()

    # ── Step 5: Cache in Redis ───────────────────────────────────
    questions_cache = [
        {
            "id": idx + 1,
            "question": q["question"],
            "type": q["type"],
            "topic": q["topic"],
            "category": q["category"],
            "difficulty": q["difficulty"],
            "expected_keywords": q.get("expected_keywords", []),
            "model_answer_hint": q.get("model_answer_hint", ""),
            "project_reference": q.get("project_reference"),
        }
        for idx, q in enumerate(raw_questions)
    ]
    await session_service.save_questions_cache(session_id, questions_cache)
    await session_service.save_interview_state(session_id, {
        "current_question_index": 0,
        "total_questions": len(questions),
    })

    return questions
