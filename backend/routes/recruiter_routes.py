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
from sqlalchemy.orm import joinedload
from pydantic import BaseModel
from typing import Optional
import re as re_module

from backend.db.session import get_db
from backend.models.interview import InterviewSession
from backend.models.user import User, UserRole
from backend.core.security import get_current_active_user, require_role
from backend.core.logging import get_logger

logger = get_logger("backend.routes.recruiter")

router = APIRouter(
    prefix="/recruiter",
    tags=["Recruiter"],
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.RECRUITER))]
)


from datetime import datetime, timedelta

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
    date_range: Optional[str] = Query(None, description="Date filter: today, week, month, all"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """
    Get paginated list of candidates with their nested interview sessions.
    The response groups multiple sessions for the same candidate.
    """
    try:
        query = select(InterviewSession).outerjoin(
            User, InterviewSession.user_id == User.id
        ).options(joinedload(InterviewSession.user))

        if search:
            search_term = f"%{search.strip()}%"
            query = query.where(
                or_(
                    InterviewSession.candidate_name.ilike(search_term),
                    User.email.ilike(search_term),
                    User.name.ilike(search_term),
                )
            )

        if date_range and date_range != "all":
            now = datetime.utcnow()
            if date_range == "today":
                query = query.where(InterviewSession.created_at >= now - timedelta(days=1))
            elif date_range == "week":
                query = query.where(InterviewSession.created_at >= now - timedelta(days=7))
            elif date_range == "month":
                query = query.where(InterviewSession.created_at >= now - timedelta(days=30))

        if status:
            status_map = {
                "completed": "completed",
                "in_progress": "in_progress",
                "pending": "created",
                "created": "created",
                "questions_generated": "questions_generated",
            }
            status_lower = status.lower()

            if status_lower == "decision":
                query = query.where(InterviewSession.status == "completed")
                query = query.where(InterviewSession.recommendation.isnot(None))
                query = query.where(InterviewSession.recommendation.in_([
                    "Strong Hire", "Hire", "Maybe", "Maybe — needs improvement", "No Hire", "Decision"
                ]))
            elif status_lower == "strong_hire":
                query = query.where(InterviewSession.status == "completed")
                query = query.where(InterviewSession.recommendation == "Strong Hire")
            elif status_lower == "hire":
                query = query.where(InterviewSession.status == "completed")
                query = query.where(InterviewSession.recommendation == "Hire")
            elif status_lower == "maybe":
                query = query.where(InterviewSession.status == "completed")
                query = query.where(InterviewSession.recommendation.in_(["Maybe", "Maybe — needs improvement"]))
            elif status_lower == "no_hire":
                query = query.where(InterviewSession.status == "completed")
                query = query.where(InterviewSession.recommendation == "No Hire")
            elif status_lower == "evaluation":
                query = query.where(InterviewSession.status == "completed")
                query = query.where(
                    or_(
                        InterviewSession.recommendation.is_(None),
                        InterviewSession.recommendation == "Evaluation",
                        InterviewSession.average_score.is_(None)
                    )
                )
            else:
                db_status = status_map.get(status_lower, status_lower)
                query = query.where(InterviewSession.status == db_status)

        if min_score is not None:
            query = query.where(InterviewSession.average_score >= min_score)
        if max_score is not None:
            query = query.where(InterviewSession.average_score <= max_score)

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

        query = query.order_by(desc(InterviewSession.created_at))

        result = await db.execute(query)
        sessions = result.unique().scalars().all()

        grouped = {}
        for session in sessions:
            email = None
            if session.user:
                email = session.user.email
            if not email:
                email = _extract_email(session.resume_text) if session.resume_text else None
            
            key = email.lower() if email else (session.candidate_name or "Unknown").lower()
            
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

            avg_score = None
            if session.average_score is not None:
                avg_score = round(float(session.average_score), 2)

            session_data = {
                "session_id": str(session.id),
                "skills_detected": session.skills_detected or [],
                "experience_years": session.experience_years or "Not specified",
                "average_score": avg_score,
                "status": session.status,
                "recommendation": session.recommendation,
                "question_count": question_count,
                "violations_count": violations_count,
                "created_at": session.created_at.isoformat() if session.created_at else None,
                "pipeline_stage": pipeline_stage,
            }

            if key not in grouped:
                grouped[key] = {
                    "candidate_name": session.candidate_name or "Unknown",
                    "email": email,
                    "sessions": [],
                    "total_sessions": 0,
                    "latest_date": session.created_at,
                    "highest_score": avg_score or 0.0,
                    "total_violations": 0
                }
            
            grouped[key]["sessions"].append(session_data)
            grouped[key]["total_sessions"] += 1
            if session.created_at and (not grouped[key]["latest_date"] or session.created_at > grouped[key]["latest_date"]):
                grouped[key]["latest_date"] = session.created_at
            if avg_score and avg_score > grouped[key]["highest_score"]:
                grouped[key]["highest_score"] = avg_score
            grouped[key]["total_violations"] += violations_count
            
        candidate_list = list(grouped.values())

        if sort_by == "score":
            candidate_list.sort(key=lambda x: x["highest_score"], reverse=(sort_order == "desc"))
        elif sort_by == "name":
            candidate_list.sort(key=lambda x: (x["candidate_name"] or "").lower(), reverse=(sort_order == "desc"))
        else:
            # default to date
            candidate_list.sort(key=lambda x: x["latest_date"] or datetime.min, reverse=(sort_order == "desc"))

        for c in candidate_list:
            c["latest_date"] = c["latest_date"].isoformat() if c["latest_date"] else None

        total_count = len(candidate_list)
        total_pages = max(1, (total_count + page_size - 1) // page_size)
        offset = (page - 1) * page_size
        paginated_candidates = candidate_list[offset:offset + page_size]

        return {
            "success": True,
            "candidates": paginated_candidates,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    except Exception as e:
        logger.error("recruiter_candidates_error", error=str(e))
        import traceback
        logger.error("recruiter_candidates_traceback", tb=traceback.format_exc())
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

    query = select(InterviewSession).where(
        InterviewSession.id == sid
    ).options(joinedload(InterviewSession.user))
    result = await db.execute(query)
    session = result.unique().scalars().first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get email from User relationship
    email = None
    if session.user:
        email = session.user.email
    if not email:
        email = _extract_email(session.resume_text) if session.resume_text else None

    pipeline_stage = _determine_pipeline_stage(session)

    violations_count = len(session.proctor_logs) if session.proctor_logs else 0
    question_count = len(session.questions) if session.questions else 0

    # FIX: Proper None check for 0.0 scores
    avg_score = None
    if session.average_score is not None:
        avg_score = round(float(session.average_score), 2)

    return {
        "success": True,
        "candidate": {
            "session_id": str(session.id),
            "candidate_name": session.candidate_name or "Unknown",
            "email": email,
            "skills_detected": session.skills_detected or [],
            "experience_years": session.experience_years or "Not specified",
            "average_score": avg_score,
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
    """Extract the first email address found in resume text (fallback only)."""
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


# ── Update candidate decision/recommendation ──────────────────────────────────

class UpdateDecisionRequest(BaseModel):
    recommendation: str


@router.put("/candidates/{session_id}/decision")
async def update_candidate_decision(
    session_id: str,
    request: UpdateDecisionRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Update the recommendation/decision for a candidate session.
    Recruiters can change: Strong Hire, Hire, Maybe, No Hire, Evaluation, Decision.
    """
    try:
        import uuid as uuid_mod
        sid = uuid_mod.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    result = await db.execute(
        select(InterviewSession).where(InterviewSession.id == sid)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Validate recommendation value
    valid_decisions = ["Strong Hire", "Hire", "Maybe", "Maybe — needs improvement", "No Hire", "Evaluation", "Decision"]
    if request.recommendation not in valid_decisions:
        raise HTTPException(status_code=400, detail=f"Invalid decision. Must be one of: {valid_decisions}")

    session.recommendation = request.recommendation
    await db.commit()

    logger.info("decision_updated", session_id=session_id, new_decision=request.recommendation)

    return {
        "success": True,
        "session_id": session_id,
        "recommendation": request.recommendation,
    }
