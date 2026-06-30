"""
Analytics Routes
Provides aggregate metrics and historical summaries for the Analytics Dashboard.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from backend.db.session import get_db
from backend.models.interview import InterviewSession
from backend.models.answer import Answer as AnswerORM
from backend.models.proctor_log import ProctorLog as ProctorLogORM
from backend.core.security import get_current_active_user
from backend.models.user import User
from backend.models.question import Question as QuestionORM
from backend.core.logging import get_logger

logger = get_logger("backend.routes.analytics")

# Create router with /analytics prefix protected by authentication guard
router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
    dependencies=[Depends(get_current_active_user)]
)


@router.get("/overview")
async def get_analytics_overview(db: AsyncSession = Depends(get_db)):
    """
    Get high-level aggregated KPIs across all sessions.
    Returns safe defaults if tables are empty or missing columns.
    """
    try:
        # Total interviews count
        total_q = select(func.count(InterviewSession.id))
        total_res = await db.execute(total_q)
        total_interviews = total_res.scalar() or 0

        # Completed interviews count
        completed_q = select(func.count(InterviewSession.id)).where(
            InterviewSession.status == "completed"
        )
        completed_res = await db.execute(completed_q)
        completed_interviews = completed_res.scalar() or 0

        # Average score of completed interviews
        avg_score_q = select(func.avg(InterviewSession.average_score)).where(
            InterviewSession.status == "completed"
        )
        avg_score_res = await db.execute(avg_score_q)
        average_score = avg_score_res.scalar() or 0.0

        # Total proctor violations (may fail if table doesn't exist)
        total_violations = 0
        try:
            violations_q = select(func.count(ProctorLogORM.id))
            violations_res = await db.execute(violations_q)
            total_violations = violations_res.scalar() or 0
        except Exception:
            pass

        # Pass rate calculation (average_score >= 7.0 is considered a Pass)
        passed_count = 0
        if completed_interviews > 0:
            passed_q = select(func.count(InterviewSession.id)).where(
                InterviewSession.status == "completed",
                InterviewSession.average_score >= 7.0
            )
            passed_res = await db.execute(passed_q)
            passed_count = passed_res.scalar() or 0

        pass_rate = (
            round((passed_count / completed_interviews) * 100, 1)
            if completed_interviews > 0
            else 0.0
        )

        return {
            "success": True,
            "total_interviews": total_interviews,
            "completed_interviews": completed_interviews,
            "average_score": round(float(average_score), 2),
            "pass_rate": pass_rate,
            "total_violations": total_violations,
        }

    except Exception as e:
        logger.error("analytics_overview_error", error=str(e))
        return {
            "success": True,
            "total_interviews": 0,
            "completed_interviews": 0,
            "average_score": 0.0,
            "pass_rate": 0.0,
            "total_violations": 0,
        }


@router.get("/history")
async def get_interview_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get a list of past interview sessions.
    Candidates see only their own; recruiters/admins see all.
    Uses explicit subqueries to avoid async lazy-loading (MissingGreenlet).
    """
    try:
        query = (
            select(InterviewSession)
            .order_by(InterviewSession.created_at.desc())
        )

        # Candidates only see their own sessions
        if current_user.role == "candidate":
            query = query.where(InterviewSession.user_id == current_user.id)

        result = await db.execute(query)
        sessions = result.scalars().all()

        # Build session IDs list for batch subqueries
        session_ids = [s.id for s in sessions]
        sessions_data = []

        if session_ids:
            # Batch count questions per session
            q_count_q = (
                select(QuestionORM.session_id, func.count(QuestionORM.id).label("cnt"))
                .where(QuestionORM.session_id.in_(session_ids))
                .group_by(QuestionORM.session_id)
            )
            q_count_res = await db.execute(q_count_q)
            question_counts = {row.session_id: row.cnt for row in q_count_res.all()}

            # Batch count proctor violations per session
            v_count_q = (
                select(ProctorLogORM.session_id, func.count(ProctorLogORM.id).label("cnt"))
                .where(ProctorLogORM.session_id.in_(session_ids))
                .group_by(ProctorLogORM.session_id)
            )
            v_count_res = await db.execute(v_count_q)
            violation_counts = {row.session_id: row.cnt for row in v_count_res.all()}
        else:
            question_counts = {}
            violation_counts = {}

        for session in sessions:
            sessions_data.append({
                "session_id": str(session.id),
                "candidate_name": session.candidate_name,
                "skills_detected": session.skills_detected or [],
                "experience_years": session.experience_years,
                "status": session.status,
                "average_score": session.average_score,
                "recommendation": session.recommendation,
                "created_at": session.created_at.isoformat() if session.created_at else None,
                "question_count": question_counts.get(session.id, 0),
                "violations_count": violation_counts.get(session.id, 0),
            })

        return {
            "success": True,
            "sessions": sessions_data,
        }

    except Exception as e:
        logger.error("analytics_history_error", error=str(e))
        return {
            "success": True,
            "sessions": [],
        }


@router.get("/skills")
async def get_skills_distribution(db: AsyncSession = Depends(get_db)):
    """
    Analyze skill frequencies and candidate average score per skill.
    """
    try:
        query = select(
            InterviewSession.skills_detected,
            InterviewSession.average_score
        ).where(
            InterviewSession.status == "completed"
        )

        result = await db.execute(query)
        rows = result.all()

        skill_stats = {}
        for skills_list, avg_score in rows:
            if not skills_list:
                continue
            for skill in skills_list:
                if skill not in skill_stats:
                    skill_stats[skill] = {"count": 0, "total_score": 0.0, "scored_count": 0}
                skill_stats[skill]["count"] += 1
                if avg_score is not None:
                    skill_stats[skill]["total_score"] += avg_score
                    skill_stats[skill]["scored_count"] += 1

        skills_data = []
        for skill, stats in skill_stats.items():
            avg = stats["total_score"] / stats["scored_count"] if stats["scored_count"] > 0 else 0.0
            skills_data.append({
                "skill": skill,
                "candidate_count": stats["count"],
                "average_score": round(avg, 2)
            })

        skills_data.sort(key=lambda x: x["candidate_count"], reverse=True)

        return {
            "success": True,
            "skills": skills_data
        }

    except Exception as e:
        logger.error("analytics_skills_error", error=str(e))
        return {"success": True, "skills": []}


@router.get("/strengths-weaknesses")
async def get_strengths_weaknesses(db: AsyncSession = Depends(get_db)):
    """
    Get top candidate strengths and areas for improvement.
    """
    try:
        query = select(AnswerORM.strengths, AnswerORM.improvements)
        result = await db.execute(query)
        rows = result.all()

        strengths_freq = {}
        improvements_freq = {}

        for strengths, improvements in rows:
            if strengths:
                for s in strengths:
                    s_clean = s.strip()
                    if s_clean:
                        strengths_freq[s_clean] = strengths_freq.get(s_clean, 0) + 1
            if improvements:
                for imp in improvements:
                    imp_clean = imp.strip()
                    if imp_clean:
                        improvements_freq[imp_clean] = improvements_freq.get(imp_clean, 0) + 1

        top_strengths = sorted(
            [{"text": k, "count": v} for k, v in strengths_freq.items()],
            key=lambda x: x["count"],
            reverse=True
        )[:10]

        top_weaknesses = sorted(
            [{"text": k, "count": v} for k, v in improvements_freq.items()],
            key=lambda x: x["count"],
            reverse=True
        )[:10]

        return {
            "success": True,
            "strengths": top_strengths,
            "weaknesses": top_weaknesses
        }

    except Exception as e:
        logger.error("analytics_strengths_error", error=str(e))
        return {"success": True, "strengths": [], "weaknesses": []}


@router.get("/proctor-violations")
async def get_proctor_violations_analytics(db: AsyncSession = Depends(get_db)):
    """
    Get proctor violations data.
    """
    try:
        # Counts by event type
        type_q = select(
            ProctorLogORM.event_type,
            func.count(ProctorLogORM.id)
        ).group_by(ProctorLogORM.event_type)
        type_res = await db.execute(type_q)
        by_type = [{"event_type": row[0], "count": row[1]} for row in type_res.all()]

        return {
            "success": True,
            "by_type": by_type,
            "high_risk_candidates": [],
            "recent_logs": []
        }

    except Exception as e:
        logger.error("analytics_proctor_error", error=str(e))
        return {
            "success": True,
            "by_type": [],
            "high_risk_candidates": [],
            "recent_logs": []
        }


@router.get("/performance-trend")
async def get_performance_trend(db: AsyncSession = Depends(get_db)):
    """
    Get candidate scores trended over time.
    """
    try:
        query = select(
            InterviewSession.created_at,
            InterviewSession.average_score
        ).where(
            InterviewSession.status == "completed"
        ).order_by(
            InterviewSession.created_at.asc()
        )

        result = await db.execute(query)
        rows = result.all()

        trend_stats = {}
        for created_at, score in rows:
            if created_at is None or score is None:
                continue
            date_str = created_at.strftime("%Y-%m-%d")
            if date_str not in trend_stats:
                trend_stats[date_str] = {"total_score": 0.0, "count": 0}
            trend_stats[date_str]["total_score"] += score
            trend_stats[date_str]["count"] += 1

        trend_data = []
        for date_str, stats in sorted(trend_stats.items()):
            trend_data.append({
                "date": date_str,
                "average_score": round(stats["total_score"] / stats["count"], 2),
                "count": stats["count"]
            })

        return {
            "success": True,
            "trend": trend_data
        }

    except Exception as e:
        logger.error("analytics_trend_error", error=str(e))
        return {"success": True, "trend": []}


@router.get("/candidate/{session_id}")
async def get_candidate_detail(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get detailed analytics for a specific candidate session.
    Returns per-question scores, strengths, weaknesses, violations,
    recommendation, and total score.
    """
    try:
        # Validate UUID
        try:
            session_uuid = uuid.UUID(session_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid session ID format")

        # Get the session
        session_q = select(InterviewSession).where(InterviewSession.id == session_uuid)
        session_res = await db.execute(session_q)
        session = session_res.scalar_one_or_none()

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Candidates can only view their own sessions
        if current_user.role == "candidate" and session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Get answers joined with questions for this session
        answers_q = (
            select(AnswerORM, QuestionORM)
            .join(QuestionORM, AnswerORM.question_id == QuestionORM.id)
            .where(AnswerORM.session_id == session_uuid)
            .order_by(QuestionORM.question_number.asc())
        )
        answers_res = await db.execute(answers_q)
        answer_rows = answers_res.all()

        # Build per-question scores
        per_question_scores = []
        all_strengths = {}
        all_weaknesses = {}
        total_score = 0
        scored_count = 0

        for answer, question in answer_rows:
            score = answer.score or 0
            total_score += score
            scored_count += 1

            per_question_scores.append({
                "question_number": question.question_number,
                "question_text": question.question_text[:120],
                "topic": question.topic or question.question_type,
                "category": question.category or "general",
                "difficulty": question.difficulty or "medium",
                "score": score,
            })

            # Aggregate strengths
            if answer.strengths:
                for s in answer.strengths:
                    s_clean = s.strip() if isinstance(s, str) else str(s)
                    if s_clean:
                        all_strengths[s_clean] = all_strengths.get(s_clean, 0) + 1

            # Aggregate weaknesses
            if answer.improvements:
                for w in answer.improvements:
                    w_clean = w.strip() if isinstance(w, str) else str(w)
                    if w_clean:
                        all_weaknesses[w_clean] = all_weaknesses.get(w_clean, 0) + 1

        # Get proctor violations for this session
        violations_q = select(ProctorLogORM).where(
            ProctorLogORM.session_id == session_uuid
        )
        violations_res = await db.execute(violations_q)
        violations = violations_res.scalars().all()

        violations_by_type = {}
        for v in violations:
            event_type = v.event_type or "Unknown"
            violations_by_type[event_type] = violations_by_type.get(event_type, 0) + 1

        # Sort strengths/weaknesses by frequency
        sorted_strengths = sorted(
            [{"text": k, "count": v} for k, v in all_strengths.items()],
            key=lambda x: x["count"], reverse=True
        )[:10]

        sorted_weaknesses = sorted(
            [{"text": k, "count": v} for k, v in all_weaknesses.items()],
            key=lambda x: x["count"], reverse=True
        )[:10]

        avg_score = round(total_score / scored_count, 2) if scored_count > 0 else 0.0

        return {
            "success": True,
            "session_id": session_id,
            "candidate_name": session.candidate_name,
            "skills_detected": session.skills_detected or [],
            "status": session.status,
            "average_score": avg_score,
            "total_score": total_score,
            "question_count": scored_count,
            "recommendation": session.recommendation,
            "per_question_scores": per_question_scores,
            "strengths": sorted_strengths,
            "weaknesses": sorted_weaknesses,
            "violations_count": len(violations),
            "violations_by_type": [
                {"event_type": k, "count": v}
                for k, v in sorted(violations_by_type.items(), key=lambda x: x[1], reverse=True)
            ],
            "created_at": session.created_at.isoformat() if session.created_at else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("analytics_candidate_detail_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to load candidate details")
