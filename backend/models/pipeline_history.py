"""
PipelineHistory ORM Model

Audit trail for candidate pipeline stage transitions.
Every time a recruiter moves a candidate between stages,
a row is inserted here for traceability.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, String, Text, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base, UUIDMixin


class PipelineStage:
    """Valid pipeline stage constants."""
    SCREENING = "screening"
    SHORTLISTED = "shortlisted"
    SELECTED = "selected"
    REJECTED = "rejected"
    ON_HOLD = "on_hold"

    ALL = [SCREENING, SHORTLISTED, SELECTED, REJECTED, ON_HOLD]

    # Display labels for frontend
    LABELS = {
        SCREENING: "Screening",
        SHORTLISTED: "Shortlisted",
        SELECTED: "Selected",
        REJECTED: "Rejected",
        ON_HOLD: "On Hold",
    }

    # Valid transitions (from_stage → allowed to_stages)
    # All transitions are allowed for flexibility, but this can be restricted
    TRANSITIONS = {
        SCREENING: [SHORTLISTED, REJECTED, ON_HOLD],
        SHORTLISTED: [SELECTED, REJECTED, ON_HOLD, SCREENING],
        SELECTED: [REJECTED, ON_HOLD],  # Can still reject after selection
        REJECTED: [SCREENING, ON_HOLD],  # Allow reconsideration
        ON_HOLD: [SCREENING, SHORTLISTED, REJECTED],
    }


class PipelineHistory(UUIDMixin, Base):
    """
    pipeline_history table

    Records every stage transition for audit and reporting.
    """
    __tablename__ = "pipeline_history"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    from_stage: Mapped[str] = mapped_column(String(30), nullable=False)
    to_stage: Mapped[str] = mapped_column(String(30), nullable=False)

    changed_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)

    # Denormalized for quick display without joins
    candidate_name: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )

    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # ── Relationships ────────────────────────────────────────────
    session = relationship("InterviewSession", backref="pipeline_history")
    changed_by_user = relationship(
        "User",
        foreign_keys=[changed_by],
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<PipelineHistory session={self.session_id!s:.8} "
            f"{self.from_stage}→{self.to_stage} "
            f"at={self.changed_at}>"
        )

    @classmethod
    def is_valid_transition(cls, from_stage: str, to_stage: str) -> bool:
        """Check if a stage transition is allowed."""
        if from_stage == to_stage:
            return False
        if to_stage not in PipelineStage.ALL:
            return False
        # Allow all transitions (flexible) — restrict via TRANSITIONS if needed
        return True
