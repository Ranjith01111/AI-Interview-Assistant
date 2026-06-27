"""
Coding Assessment Routes — Endpoints for challenges, run execution, and submissions.
"""

import uuid
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.future import select as sa_select
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.session import get_db
from backend.models.coding_challenge import CodingChallenge
from backend.models.coding_submission import CodingSubmission
from backend.services.sandbox_service import sandbox_service
from backend.core.security import get_current_active_user
from backend.models.interview import InterviewSession
from backend.models.user import User, UserRole
from backend.core.logging import get_logger

logger = get_logger("backend.routes.coding_routes")

# Create protected router
router = APIRouter(
    prefix="/coding",
    tags=["Coding Assessment"],
    dependencies=[Depends(get_current_active_user)]
)


async def _verify_coding_session_ownership(
    session_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> None:
    """Verify user owns the interview session linked to this coding submission."""
    if current_user.role in (UserRole.ADMIN.value, UserRole.RECRUITER.value):
        return
    result = await db.execute(
        sa_select(InterviewSession.user_id).where(InterviewSession.id == session_id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    if row != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this session.")


# ── Pydantic Request/Response Schemas ─────────────────────────────────

class ChallengeRunRequest(BaseModel):
    challenge_id: uuid.UUID
    language: str
    code: str

class ChallengeSubmitRequest(BaseModel):
    session_id: uuid.UUID
    challenge_id: uuid.UUID
    language: str
    code: str

class ChallengeResponse(BaseModel):
    id: uuid.UUID
    title: str
    difficulty: str
    description: str
    time_limit: float
    memory_limit: int
    template_code: dict

# ── Route Handlers ───────────────────────────────────────────────────

@router.get("/challenges", response_model=List[ChallengeResponse])
async def get_challenges(db: AsyncSession = Depends(get_db)):
    """Retrieve all available coding challenges."""
    try:
        result = await db.execute(select(CodingChallenge))
        challenges = result.scalars().all()
        return [
            ChallengeResponse(
                id=c.id,
                title=c.title,
                difficulty=c.difficulty,
                description=c.description,
                time_limit=c.time_limit,
                memory_limit=c.memory_limit,
                template_code=c.template_code
            )
            for c in challenges
        ]
    except Exception as e:
        logger.error("get_challenges_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch challenges: {str(e)}"
        )


@router.post("/reseed")
async def reseed_challenges(db: AsyncSession = Depends(get_db)):
    """Force re-seed coding challenges. Useful if table is empty."""
    from sqlalchemy import delete
    from backend.models.coding_submission import CodingSubmission
    from backend.seed_challenges import seed_default_challenges, CHALLENGES
    from backend.models.coding_challenge import CodingChallenge as CC
    from sqlalchemy import select, func

    # Check current count
    count_result = await db.execute(select(func.count(CC.id)))
    current = count_result.scalar() or 0

    if current == 0:
        # Table empty — seed fresh
        added = await seed_default_challenges(db)
        return {"success": True, "action": "seeded", "added": added}
    else:
        return {"success": True, "action": "already_exists", "count": current}


@router.post("/deduplicate")
async def deduplicate_challenges(db: AsyncSession = Depends(get_db)):
    """Remove duplicate challenges, keeping only the first inserted per title."""
    from sqlalchemy import text

    try:
        # Find duplicate titles
        result = await db.execute(text("""
            SELECT title, COUNT(*) as cnt 
            FROM coding_challenges 
            GROUP BY title 
            HAVING COUNT(*) > 1
        """))
        duplicates = result.fetchall()

        removed = 0
        for row in duplicates:
            title = row[0]
            # Keep the first one (oldest), delete the rest
            ids_result = await db.execute(text(
                "SELECT id FROM coding_challenges WHERE title = :t ORDER BY id"
            ), {"t": title})
            all_ids = [str(r[0]) for r in ids_result.fetchall()]
            if len(all_ids) > 1:
                ids_to_delete = all_ids[1:]  # Keep first, delete rest
                for del_id in ids_to_delete:
                    await db.execute(text("DELETE FROM coding_challenges WHERE id = :id"), {"id": del_id})
                    removed += 1

        await db.commit()
        return {"success": True, "duplicates_removed": removed}
    except Exception as e:
        logger.error("deduplicate_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Deduplication failed: {str(e)}")


@router.get("/challenges/{challenge_id}", response_model=ChallengeResponse)
async def get_challenge_detail(challenge_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Retrieve details for a specific coding challenge."""
    result = await db.execute(select(CodingChallenge).where(CodingChallenge.id == challenge_id))
    challenge = result.scalar_one_or_none()
    if not challenge:
        raise HTTPException(status_code=404, detail="Coding challenge not found.")
    
    return ChallengeResponse(
        id=challenge.id,
        title=challenge.title,
        difficulty=challenge.difficulty,
        description=challenge.description,
        time_limit=challenge.time_limit,
        memory_limit=challenge.memory_limit,
        template_code=challenge.template_code
    )


@router.post("/run")
async def run_code(request: ChallengeRunRequest, db: AsyncSession = Depends(get_db)):
    """
    Run code against visible (sample) test cases.
    Does not persist submission in the database.
    """
    result = await db.execute(select(CodingChallenge).where(CodingChallenge.id == request.challenge_id))
    challenge = result.scalar_one_or_none()
    if not challenge:
        raise HTTPException(status_code=404, detail="Coding challenge not found.")

    try:
        # Filter out hidden test cases
        visible_test_cases = [tc for tc in (challenge.test_cases or []) if not tc.get("is_hidden", False)]
        if not visible_test_cases:
            visible_test_cases = (challenge.test_cases or [])[:1]

        if not visible_test_cases:
            return {"status": "No Test Cases", "score": 0, "results": [], "sandbox_type": "N/A"}

        logger.info("running_sandbox_test", challenge_id=str(challenge.id), language=request.language)

        # Execute in sandbox
        run_results = await sandbox_service.execute(
            language=request.language,
            code=request.code,
            test_cases=visible_test_cases,
            time_limit=challenge.time_limit,
            memory_limit=challenge.memory_limit
        )

        return run_results
    except Exception as e:
        logger.error("code_run_failed", error=str(e))
        import traceback
        tb = traceback.format_exc()
        logger.error("code_run_traceback", tb=tb)
        return {
            "status": "System Error",
            "score": 0,
            "results": [],
            "error": str(e) or tb.split('\n')[-2] if tb else "Unknown error",
            "sandbox_type": "Error"
        }


@router.post("/submit")
async def submit_code(
    request: ChallengeSubmitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Evaluate code against all test cases (hidden & visible).
    Saves submission status and score in the database.
    """
    result = await db.execute(select(CodingChallenge).where(CodingChallenge.id == request.challenge_id))
    challenge = result.scalar_one_or_none()
    if not challenge:
        raise HTTPException(status_code=404, detail="Coding challenge not found.")

    await _verify_coding_session_ownership(request.session_id, current_user, db)

    try:
        test_cases = challenge.test_cases or []
        if not test_cases:
            return {"status": "No Test Cases", "score": 0, "results": []}

        logger.info("submitting_code_evaluation", challenge_id=str(challenge.id), session_id=str(request.session_id))

        # Execute in sandbox
        run_results = await sandbox_service.execute(
            language=request.language,
            code=request.code,
            test_cases=test_cases,
            time_limit=challenge.time_limit,
            memory_limit=challenge.memory_limit
        )

        # Save to PostgreSQL
        submission = CodingSubmission(
            session_id=request.session_id,
            challenge_id=request.challenge_id,
            language=request.language,
            code=request.code,
            status=run_results.get("status", "Error"),
            score=run_results.get("score", 0),
            results=run_results
        )
        db.add(submission)

        return {
            "submission_id": str(submission.id) if hasattr(submission, 'id') else "pending",
            "status": run_results.get("status", "Error"),
            "score": run_results.get("score", 0),
            "results": run_results
        }
    except Exception as e:
        logger.error("code_submit_failed", error=str(e))
        return {
            "status": "System Error",
            "score": 0,
            "results": [],
            "error": str(e)
        }


@router.get("/submissions/{session_id}")
async def get_submissions(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get all submissions registered for a given interview session."""
    await _verify_coding_session_ownership(session_id, current_user, db)
    result = await db.execute(
        select(CodingSubmission)
        .where(CodingSubmission.session_id == session_id)
        .order_by(CodingSubmission.created_at.desc())
    )
    submissions = result.scalars().all()
    
    return [
        {
            "id": s.id,
            "challenge_id": s.challenge_id,
            "language": s.language,
            "status": s.status,
            "score": s.score,
            "code": s.code,
            "created_at": s.created_at,
            "results": s.results
        }
        for s in submissions
    ]
