"""
Export Routes — CSV and HTML/PDF report downloads for Recruiters.

Endpoints:
  GET /api/v1/export/candidates/csv     — CSV download of candidate listing
  GET /api/v1/export/session/{id}/pdf   — Single candidate HTML report
  GET /api/v1/export/candidates/pdf     — All-candidates summary HTML report

All endpoints require RECRUITER or ADMIN role.
"""

import csv
import io
import uuid
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.db.session import get_db
from backend.models.interview import InterviewSession
from backend.models.answer import Answer as AnswerORM
from backend.models.question import Question as QuestionORM
from backend.models.proctor_log import ProctorLog as ProctorLogORM
from backend.models.user import User, UserRole
from backend.core.security import get_current_active_user, require_role
from backend.core.logging import get_logger

# Import report templates
from backend.routes.report_templates import (
    render_single_candidate_report,
    render_candidates_summary_report,
)

logger = get_logger("backend.routes.export")

router = APIRouter(
    prefix="/export",
    tags=["Export"],
    dependencies=[Depends(require_role(UserRole.RECRUITER, UserRole.ADMIN))],
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Helper: Build filtered query for interview sessions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _apply_session_filters(
    query,
    status_filter: Optional[str] = None,
    min_score: Optional[float] = None,
    max_score: Optional[float] = None,
    skills: Optional[str] = None,
    pipeline_stage: Optional[str] = None,
):
    """
    Apply optional filters to an InterviewSession query.

    Args:
        status_filter: Filter by session status (e.g., "completed", "in_progress")
        min_score: Minimum average score threshold
        max_score: Maximum average score threshold
        skills: Comma-separated skill names to filter (matches any)
        pipeline_stage: Filter by recommendation / pipeline stage value
    """
    if status_filter:
        query = query.where(InterviewSession.status == status_filter)

    if min_score is not None:
        query = query.where(InterviewSession.average_score >= min_score)

    if max_score is not None:
        query = query.where(InterviewSession.average_score <= max_score)

    if pipeline_stage:
        query = query.where(InterviewSession.recommendation == pipeline_stage)

    # Skills filtering: check if any of the requested skills appear in the JSON array
    # Note: For PostgreSQL JSONB, we can use array overlap. For simpler approach,
    # we do a text-based filter on the JSON column (works with both PG and SQLite).
    if skills:
        skill_list = [s.strip().lower() for s in skills.split(",") if s.strip()]
        if skill_list:
            # Use PostgreSQL JSONB contains or fallback to text cast
            # This approach works with both PostgreSQL JSON arrays
            for skill in skill_list:
                query = query.where(
                    func.lower(func.cast(InterviewSession.skills_detected, String)).contains(skill)
                )

    return query


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GET /api/v1/export/candidates/csv
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.get("/candidates/csv")
async def export_candidates_csv(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by session status"),
    min_score: Optional[float] = Query(None, description="Minimum average score"),
    max_score: Optional[float] = Query(None, description="Maximum average score"),
    skills: Optional[str] = Query(None, description="Comma-separated skills to filter"),
    pipeline_stage: Optional[str] = Query(None, description="Filter by recommendation/pipeline stage"),
):
    """
    Export candidates listing as a CSV file download.

    Columns: Name, Email, Score, Status, Pipeline Stage, Skills,
             Experience, Date, Recommendation, Violations Count
    """
    try:
        query = select(InterviewSession).order_by(InterviewSession.created_at.desc())
        query = _apply_session_filters(query, status_filter, min_score, max_score, skills, pipeline_stage)

        result = await db.execute(query)
        sessions = result.scalars().all()

        # Fetch associated user emails in bulk
        user_ids = [s.user_id for s in sessions if s.user_id]
        user_email_map = {}
        if user_ids:
            from backend.models.user import User as UserModel
            users_q = select(UserModel.id, UserModel.email).where(UserModel.id.in_(user_ids))
            users_result = await db.execute(users_q)
            for uid, email in users_result.all():
                user_email_map[uid] = email

        # Generate CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Header row
        writer.writerow([
            "Name",
            "Email",
            "Score",
            "Status",
            "Pipeline Stage",
            "Skills",
            "Experience",
            "Date",
            "Recommendation",
            "Violations Count",
        ])

        # Data rows
        for session in sessions:
            email = user_email_map.get(session.user_id, "—")
            skills_str = ", ".join(session.skills_detected) if session.skills_detected else ""
            date_str = session.created_at.strftime("%Y-%m-%d %H:%M") if session.created_at else ""
            violations_count = len(session.proctor_logs) if session.proctor_logs else 0
            score_str = f"{session.average_score:.1f}" if session.average_score is not None else "N/A"

            writer.writerow([
                session.candidate_name,
                email,
                score_str,
                session.status,
                session.recommendation or "—",
                skills_str,
                session.experience_years or "—",
                date_str,
                session.recommendation or "—",
                violations_count,
            ])

        # Return as streaming CSV response
        output.seek(0)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"candidates_export_{timestamp}.csv"

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Cache-Control": "no-cache",
            },
        )

    except Exception as e:
        logger.error("export_csv_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate CSV export: {str(e)}",
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GET /api/v1/export/session/{session_id}/pdf
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.get("/session/{session_id}/pdf")
async def export_session_pdf(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Export a single candidate's interview session as an HTML report download.

    Content includes: candidate name, date, overall score, per-question breakdown
    (question, answer excerpt, score, feedback), recommendation, and proctoring
    violations summary.

    Returns styled HTML with @media print CSS for clean printable output.
    """
    try:
        # Fetch session with related data (eager loaded via selectin)
        query = select(InterviewSession).where(InterviewSession.id == session_id)
        result = await db.execute(query)
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found",
            )

        # Build question+answer data
        questions_data = []
        if session.questions:
            for question in sorted(session.questions, key=lambda q: q.question_number):
                # Find the matching answer for this question
                answer = None
                if session.answers:
                    answer = next(
                        (a for a in session.answers if a.question_id == question.id),
                        None,
                    )

                questions_data.append({
                    "question_text": question.question_text,
                    "question_type": question.question_type,
                    "topic": question.topic,
                    "answer_text": answer.answer_text if answer else "No answer provided",
                    "score": answer.score if answer else None,
                    "strengths": answer.strengths if answer else [],
                    "improvements": answer.improvements if answer else [],
                })

        # Build violations data
        violations_data = []
        if session.proctor_logs:
            for log in session.proctor_logs:
                violations_data.append({
                    "event_type": log.event_type,
                    "timestamp": log.created_at.strftime("%H:%M:%S") if log.created_at else "",
                    "details": getattr(log, "details", ""),
                })

        # Assemble session data for template
        session_data = {
            "candidate_name": session.candidate_name,
            "created_at": session.created_at,
            "status": session.status,
            "average_score": session.average_score,
            "recommendation": session.recommendation,
            "overall_feedback": session.overall_feedback,
            "skills_detected": session.skills_detected or [],
            "experience_years": session.experience_years,
            "questions": questions_data,
            "violations": violations_data,
        }

        # Render HTML report
        html_content = render_single_candidate_report(session_data)

        # Return as downloadable HTML file
        safe_name = session.candidate_name.replace(" ", "_").lower()
        timestamp = datetime.now().strftime("%Y%m%d")
        filename = f"interview_report_{safe_name}_{timestamp}.html"

        return StreamingResponse(
            iter([html_content]),
            media_type="text/html",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Cache-Control": "no-cache",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("export_session_pdf_error", error=str(e), session_id=str(session_id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}",
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GET /api/v1/export/candidates/pdf
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.get("/candidates/pdf")
async def export_candidates_pdf(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by session status"),
    min_score: Optional[float] = Query(None, description="Minimum average score"),
    max_score: Optional[float] = Query(None, description="Maximum average score"),
    skills: Optional[str] = Query(None, description="Comma-separated skills to filter"),
    pipeline_stage: Optional[str] = Query(None, description="Filter by recommendation/pipeline stage"),
):
    """
    Export a summary table of all candidates as an HTML report download.

    Content: Table with Name, Score, Status, Recommendation, Date.
    Supports same filters as the CSV export.

    Returns styled HTML with @media print CSS optimized for printing/sharing.
    """
    try:
        query = select(InterviewSession).order_by(InterviewSession.created_at.desc())
        query = _apply_session_filters(query, status_filter, min_score, max_score, skills, pipeline_stage)

        result = await db.execute(query)
        sessions = result.scalars().all()

        # Build session data for template
        sessions_data = []
        for session in sessions:
            sessions_data.append({
                "candidate_name": session.candidate_name,
                "average_score": session.average_score,
                "status": session.status,
                "recommendation": session.recommendation,
                "created_at": session.created_at,
            })

        # Capture active filters for display
        filters_applied = {
            "status": status_filter,
            "min_score": min_score,
            "max_score": max_score,
            "skills": skills,
            "pipeline_stage": pipeline_stage,
        }

        # Render HTML report
        html_content = render_candidates_summary_report(sessions_data, filters_applied)

        # Return as downloadable HTML file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"candidates_summary_{timestamp}.html"

        return StreamingResponse(
            iter([html_content]),
            media_type="text/html",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Cache-Control": "no-cache",
            },
        )

    except Exception as e:
        logger.error("export_candidates_pdf_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate summary report: {str(e)}",
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Import String for cast (used in skills filter)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
from sqlalchemy import String
