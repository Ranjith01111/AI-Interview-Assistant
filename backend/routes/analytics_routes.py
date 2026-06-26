"""
Analytics Routes
Provides aggregate metrics and historical summaries for the Analytics Dashboard.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List, Dict, Any, Optional
from datetime import datetime

from backend.db.session import get_db
from backend.models.interview import InterviewSession
from backend.models.answer import Answer as AnswerORM
from backend.models.proctor_log import ProctorLog as ProctorLogORM
from backend.core.security import get_current_active_user
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
async def get_interview_history(db: AsyncSession = Depends(get_db)):
    """
    Get a list of past interview sessions.
    """
    try:
        # Simple query without join first
        query = (
            select(InterviewSession)
            .order_by(InterviewSession.created_at.desc())
        )

        result = await db.execute(query)
        sessions = result.scalars().all()
        sessions_data = []

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
                "question_count": len(session.questions) if session.questions else 0,
                "violations_count": len(session.proctor_logs) if session.proctor_logs else 0,
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
