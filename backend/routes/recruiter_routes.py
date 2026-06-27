"""
Recruiter Routes — Enhanced Candidate Listing API
Provides search, sort, filters, and pagination for the recruiter dashboard.

Register in main.py:
    from backend.routes.recruiter_routes import router as recruiter_router
    app.include_router(recruiter_router, prefix="/api/v1")
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, asc, or_, cast, String
from typing import Optional
import re as re_module

from backend.db.session import get_db
from backend.models.interview import InterviewSession
from backend.core.security import get_current_active_user, require_role
from backend.models.user import User, UserRole
from backend.core.logging import get_logger

logger = get_logger("backend.routes.recruiter")

router = APIRouter(
    prefix="/recruiter",
    tags=["Recruiter"],
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.RECRUITER))]
)


@router.get("/candidates")
async def get_candidates(
    db: AsyncSession = Depends(get_db),
    search: Optional[str] = Query(None, description="Search by candidate name or email"),
    sort_by: Optional[str] = Query("date", description="Sort field: score, date, name"),
    sort_order: Optional[str] = Query("desc", description="Sort direction: asc, desc"),
    status: Optional[str] = Query(None, description="Filter by status: completed, in_progress, pending, created, questions_generated"),
    min_score: Optional[float] = Query(None, ge=0, le=10, description="Minimum average score"),
    max_score: Optional[float] = Query(None, ge=0, le=10, description="Maximum average score"),
    skills: Optional[str] = Query(None, description="Comma-separated skills filter"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """
    Get paginated list of candidates with search, sort, and filter support.

    Returns:
        {candidates: [...], total_count, page, page_size, total_pages}

    Each candidate item contains:
        session_id, candidate_name, email, skills_detected, experience_years,
        average_score, status, recommendation, question_count, violations_count,
        created_at, pipeline_stage
    """
    try:
        # Base query
        query = select(InterviewSession)

        # ── Search filter (name or email pattern in resume_text) ──
        if search:
            search_term = f"%{search.strip()}%"
            query = query.where(
                or_(
                    InterviewSession.candidate_name.ilike(search_term),
                    InterviewSession.resume_text.ilike(search_term),
                )
            )

        # ── Status filter ──
        if status:
            status_map = {
                "completed": "completed",
                "in_progress": "in_progress",
                "pending": "created",
                "created": "created",
                "questions_generated": "questions_generated",
            }
            db_status = status_map.get(status.lower(), status.lower())
            query = query.where(InterviewSession.status == db_status)

        # ── Score range filter ──
        if min_score is not None:
            query = query.where(InterviewSession.average_score >= min_score)
        if max_score is not None:
            query = query.where(InterviewSession.average_score <= max_score)

        # ── Skills filter (comma-separated, match ANY) ──
        if skills:
            skills_list = [s.strip().lower() for s in skills.split(",") if s.strip()]
            if skills_list:
                skill_conditions = []
                for skill in skills_list:
                    skill_conditions.append(
                        cast(InterviewSession.skills_detected, String).ilike(f"%{skill}%")
                    )
                if skill_conditions:
                    query = query.where(or_(*skill_conditions))

        # ── Count total before pagination ──
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total_count = count_result.scalar() or 0

        # ── Sorting ──
        sort_column_map = {
            "score": InterviewSession.average_score,
            "date": InterviewSession.created_at,
            "name": InterviewSession.candidate_name,
        }
        sort_col = sort_column_map.get(sort_by, InterviewSession.created_at)

        if sort_order == "asc":
            query = query.order_by(asc(sort_col))
        else:
            query = query.order_by(desc(sort_col))

        # ── Pagination ──
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # ── Execute ──
        result = await db.execute(query)
        sessions = result.scalars().all()

        # ── Build response ──
        candidates = []
        for session in sessions:
            email = _extract_email(session.resume_text) if session.resume_text else None
            pipeline_stage = _determine_pipeline_stage(session)

            violations_count = 0
            try:
                violations_count = len(session.proctor_logs) if session.proctor_logs else 0
            except Exception:
                pass

            question_count = 0
            try:
                question_count = len(session.questions) if session.questions else 0
            except Exception:
                pass

            candidates.append({
                "session_id": str(session.id),
                "candidate_name": session.candidate_name or "Unknown",
                "email": email,
                "skills_detected": session.skills_detected or [],
                "experience_years": session.experience_years or "Not specified",
                "average_score": round(float(session.average_score), 2) if session.average_score else None,
                "status": session.status,
                "recommendation": session.recommendation,
                "question_count": question_count,
                "violations_count": violations_count,
                "created_at": session.created_at.isoformat() if session.created_at else None,
                "pipeline_stage": pipeline_stage,
            })

        total_pages = max(1, (total_count + page_size - 1) // page_size)

        return {
            "success": True,
            "candidates": candidates,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    except Exception as e:
        logger.error("recruiter_candidates_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch candidates: {str(e)}")


@router.get("/candidates/skills")
async def get_available_skills(
    db: AsyncSession = Depends(get_db),
):
    """
    Get all unique skills detected across sessions.
    Used to populate the skills filter multi-select dropdown.
    """
    try:
        query = select(InterviewSession.skills_detected).where(
            InterviewSession.skills_detected.isnot(None)
        )
        result = await db.execute(query)
        rows = result.scalars().all()

        all_skills = set()
        for skills_list in rows:
            if skills_list:
                for skill in skills_list:
                    if skill and skill.strip():
                        all_skills.add(skill.strip())

        sorted_skills = sorted(all_skills, key=str.lower)

        return {
            "success": True,
            "skills": sorted_skills,
        }

    except Exception as e:
        logger.error("recruiter_skills_list_error", error=str(e))
        return {"success": True, "skills": []}


@router.get("/candidates/{session_id}")
async def get_candidate_detail(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed information for a single candidate session.
    """
    try:
        import uuid as uuid_mod
        sid = uuid_mod.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    query = select(InterviewSession).where(InterviewSession.id == sid)
    result = await db.execute(query)
    session = result.scalars().first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    email = _extract_email(session.resume_text) if session.resume_text else None
    pipeline_stage = _determine_pipeline_stage(session)

    violations_count = len(session.proctor_logs) if session.proctor_logs else 0
    question_count = len(session.questions) if session.questions else 0

    return {
        "success": True,
        "candidate": {
            "session_id": str(session.id),
            "candidate_name": session.candidate_name or "Unknown",
            "email": email,
            "skills_detected": session.skills_detected or [],
            "experience_years": session.experience_years or "Not specified",
            "average_score": round(float(session.average_score), 2) if session.average_score else None,
            "status": session.status,
            "recommendation": session.recommendation,
            "overall_feedback": session.overall_feedback,
            "question_count": question_count,
            "violations_count": violations_count,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "pipeline_stage": pipeline_stage,
        }
    }


# ══════════════════════════════════════════════════════════════════════════════════
# Helper Functions
# ══════════════════════════════════════════════════════════════════════════════════

def _extract_email(text: str) -> Optional[str]:
    """Extract the first email address found in resume text."""
    if not text:
        return None
    match = re_module.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    return match.group(0) if match else None


def _determine_pipeline_stage(session: InterviewSession) -> str:
    """
    Determine pipeline stage from session status and scoring.

    Pipeline: screening → interview → evaluation → decision → hired/rejected
    """
    if session.status == "created":
        return "screening"
    elif session.status == "questions_generated":
        return "screening"
    elif session.status == "in_progress":
        return "interview"
    elif session.status == "completed":
        if session.average_score is None:
            return "evaluation"
        elif session.recommendation:
            rec_lower = (session.recommendation or "").lower()
            if "strong" in rec_lower and "hire" in rec_lower:
                return "hired"
            elif "not" in rec_lower or "reject" in rec_lower:
                return "rejected"
            else:
                return "decision"
        else:
            return "evaluation"
    return "screening"
