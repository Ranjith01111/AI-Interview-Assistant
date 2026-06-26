"""
AI Proctoring Routes
Handles frame image snapshot submissions, real-time proctor evaluations,
and session integrity reports for recruiters.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uuid

from backend.models.proctor_log import ProctorLog
from backend.models.interview import InterviewSession
from backend.core.security import get_current_active_user, require_role
from backend.models.user import User, UserRole

from backend.db.session import get_db
from backend.services.proctor_service import proctor_service

# Proctor router has NO auth guard — the embedded iframe cannot carry JWT tokens.
# All proctoring data is scoped by session_id, which provides sufficient isolation.
router = APIRouter(
    prefix="/proctor",
    tags=["Proctoring"],
)



class FrameAnalysisRequest(BaseModel):
    session_id: str
    image_data: str  # Base64-encoded JPEG image string


class ViolationDetail(BaseModel):
    event_type: str
    confidence: float
    details: Dict[str, Any]


class FrameAnalysisResponse(BaseModel):
    success: bool
    violations: List[ViolationDetail]
    face_count: int
    gaze: Dict[str, Any]
    head_pose: Dict[str, Any]
    objects: List[Dict[str, Any]]
    mock_mode: bool


@router.post("/analyze-frame", response_model=FrameAnalysisResponse)
async def analyze_webcam_frame(
    payload: FrameAnalysisRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Submit a webcam frame for integrity checks (face count, gaze direction, head pose, objects).
    Logs triggered violations directly to the database.
    """
    # Extract client IP and user agent headers for auditing logs
    client_ip = request.client.host if request.client else None
    
    # Try forward headers for deployment behind proxies
    x_forwarded = request.headers.get("x-forwarded-for")
    if x_forwarded:
        client_ip = x_forwarded.split(",")[0].strip()
        
    user_agent = request.headers.get("user-agent")

    result = await proctor_service.analyze_frame(
        base64_image=payload.image_data,
        session_id=payload.session_id,
        db=db,
        client_ip=client_ip,
        user_agent=user_agent
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Failed to process proctor frame analysis")
        )

    return FrameAnalysisResponse(
        success=True,
        violations=result["violations"],
        face_count=result["face_count"],
        gaze=result["gaze"],
        head_pose=result["head_pose"],
        objects=result["objects"],
        mock_mode=result["mock_mode"]
    )


class ProctorEventRequest(BaseModel):
    session_id: str
    event_type: str
    details: Optional[Dict[str, Any]] = None


class ProctorEventResponse(BaseModel):
    success: bool
    error: Optional[str] = None


@router.post("/log-event", response_model=ProctorEventResponse)
async def log_proctor_event(
    payload: ProctorEventRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Log client-side browser proctor events (tab switch, window minimize, focus loss, copy/paste).
    """
    client_ip = request.client.host if request.client else None
    x_forwarded = request.headers.get("x-forwarded-for")
    if x_forwarded:
        client_ip = x_forwarded.split(",")[0].strip()
        
    user_agent = request.headers.get("user-agent")

    result = await proctor_service.log_browser_event(
        session_id=payload.session_id,
        event_type=payload.event_type,
        details=payload.details,
        db=db,
        client_ip=client_ip,
        user_agent=user_agent
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Failed to log browser event")
        )

    return ProctorEventResponse(success=True)


# ── Session Integrity Report (Recruiter / Admin only) ─────────────────

@router.get("/session-report/{session_id}")
async def get_session_proctor_report(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieve a full proctor integrity report for a specific interview session.
    Shows all violation logs grouped by type, with timeline and risk level.

    Access: recruiter/admin see any session; candidates see only their own.
    """
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session_id format.")

    session_res = await db.execute(
        select(InterviewSession).where(InterviewSession.id == session_uuid)
    )
    session = session_res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found.")

    # Candidates can only view their own session reports
    if current_user.role == UserRole.CANDIDATE.value:
        if session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied.")

    logs_res = await db.execute(
        select(ProctorLog)
        .where(ProctorLog.session_id == session_uuid)
        .order_by(ProctorLog.created_at.asc())
    )
    logs = logs_res.scalars().all()

    type_counts: Dict[str, int] = {}
    timeline = []
    for log in logs:
        type_counts[log.event_type] = type_counts.get(log.event_type, 0) + 1
        timeline.append({
            "id": str(log.id),
            "event_type": log.event_type,
            "timestamp": log.created_at.isoformat() if log.created_at else None,
            "details": log.details or {},
            "client_ip": log.client_ip,
        })

    total_violations = len(logs)
    risk_level = "low" if total_violations == 0 else "medium" if total_violations <= 5 else "high"

    return {
        "success": True,
        "session_id": session_id,
        "candidate_name": session.candidate_name,
        "total_violations": total_violations,
        "risk_level": risk_level,
        "violations_by_type": [
            {"event_type": k, "count": v}
            for k, v in sorted(type_counts.items(), key=lambda x: -x[1])
        ],
        "timeline": timeline,
    }
