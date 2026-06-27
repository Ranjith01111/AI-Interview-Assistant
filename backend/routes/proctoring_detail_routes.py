"""
Proctoring Detail Routes — Per-Session Risk Dashboard API

Provides a computed risk score, violation breakdown, and chronological timeline
for a specific interview session. Designed for the recruiter-facing risk dashboard.

Routes:
    GET /api/v1/recruiter/sessions/{session_id}/proctoring — Full proctoring risk detail
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.db.session import get_db
from backend.models.proctor_log import ProctorLog
from backend.models.interview import InterviewSession
from backend.models.user import User, UserRole
from backend.core.security import get_current_active_user, require_role
from backend.services.proctor_service import EVENT_RISK_SCORES

router = APIRouter(
    prefix="/recruiter",
    tags=["Proctoring Detail"],
)


# —— Response Schemas —————————————————————————————————————————————

class ViolationTypeSummary(BaseModel):
    type: str
    count: int
    risk_weight: float


class TimelineEvent(BaseModel):
    event_type: str
    timestamp: Optional[str]
    details: Optional[dict]


class ProctoringDetailResponse(BaseModel):
    risk_score: float
    risk_level: str  # "low" | "medium" | "high"
    total_violations: int
    violations_by_type: list[ViolationTypeSummary]
    timeline: list[TimelineEvent]
    auto_terminated: bool


# —— Risk Calculation ——————————————————————————————————————————————

# Maximum expected cumulative risk for normalization.
# This represents the denominator: if a session hits this raw sum, risk_score = 100.
# Tuned to ~10 moderate violations triggering "high" territory.
MAX_EXPECTED_RAW_RISK = 300.0


def calculate_risk_score(violation_counts: dict[str, int]) -> tuple[float, str]:
    """
    Calculate a normalized 0–100 risk score from violation counts.

    Formula: min(100, sum_of_all_violation_risk_scores / MAX_EXPECTED_RAW_RISK * 100)
    
    Risk levels:
        <25  → low
        25–75 → medium
        >75  → high
    """
    raw_sum = 0.0
    for event_type, count in violation_counts.items():
        weight = EVENT_RISK_SCORES.get(event_type, 10.0)  # Default 10 for unknown types
        raw_sum += weight * count

    score = min(100.0, (raw_sum / MAX_EXPECTED_RAW_RISK) * 100.0)
    score = round(score, 1)

    if score < 25:
        level = "low"
    elif score <= 75:
        level = "medium"
    else:
        level = "high"

    return score, level


# —— Endpoint ————————————————————————————————————————————————————

@router.get(
    "/sessions/{session_id}/proctoring",
    response_model=ProctoringDetailResponse,
)
async def get_session_proctoring_detail(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.RECRUITER)),
):
    """
    Retrieve full proctoring risk analysis for a specific interview session.

    Returns:
        - Computed risk score (0–100) and level (low/medium/high)
        - Total violation count
        - Violations grouped by type with risk weight
        - Chronological timeline of all proctoring events
        - Whether the session was auto-terminated due to violations

    Access: Admin, Recruiter only.
    """
    # Validate session_id
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session_id format. Must be a valid UUID.",
        )

    # Check session exists
    session_result = await db.execute(
        select(InterviewSession).where(InterviewSession.id == session_uuid)
    )
    session = session_result.scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview session not found.",
        )

    # Fetch all proctor logs for the session, ordered chronologically
    logs_result = await db.execute(
        select(ProctorLog)
        .where(ProctorLog.session_id == session_uuid)
        .order_by(ProctorLog.created_at.asc())
    )
    logs = logs_result.scalars().all()

    # Aggregate violations by type
    violation_counts: dict[str, int] = {}
    timeline: list[TimelineEvent] = []

    for log in logs:
        # Count by type
        violation_counts[log.event_type] = violation_counts.get(log.event_type, 0) + 1

        # Build timeline entry
        timeline.append(TimelineEvent(
            event_type=log.event_type,
            timestamp=log.created_at.isoformat() if log.created_at else None,
            details=log.details,
        ))

    # Calculate risk score
    risk_score, risk_level = calculate_risk_score(violation_counts)
    total_violations = len(logs)

    # Build violations_by_type with risk weights
    violations_by_type = [
        ViolationTypeSummary(
            type=event_type,
            count=count,
            risk_weight=EVENT_RISK_SCORES.get(event_type, 10.0),
        )
        for event_type, count in sorted(
            violation_counts.items(),
            key=lambda x: -x[1]  # Sort by count descending
        )
    ]

    # Determine auto-termination
    # Convention: if a SESSION_TERMINATED event exists in the logs, session was auto-ended
    auto_terminated = any(
        log.event_type in ("SESSION_TERMINATED", "AUTO_TERMINATED")
        for log in logs
    )

    return ProctoringDetailResponse(
        risk_score=risk_score,
        risk_level=risk_level,
        total_violations=total_violations,
        violations_by_type=violations_by_type,
        timeline=timeline,
        auto_terminated=auto_terminated,
    )
