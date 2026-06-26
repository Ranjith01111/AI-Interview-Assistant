"""
Analytics ORM Model

Stores metric entries and analytical insights linked to interview sessions.
"""

import uuid
from typing import Optional

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base, TimestampMixin, UUIDMixin


class Analytics(UUIDMixin, TimestampMixin, Base):
    """
    analytics table

    Captures numeric metrics and metadata details for session analysis.

    Columns:
        id           — UUID primary key (from UUIDMixin)
        session_id   — Foreign key to interview_sessions.id
        metric_name  — Category or label (e.g., pace_score, answer_relevance)
        metric_value — Numeric value associated with the metric
        details      — JSON context/details for deeper introspection
        created_at   — Row creation time (from TimestampMixin)
        updated_at   — Last update time (from TimestampMixin)
    """
    __tablename__ = "analytics"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    metric_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    metric_value: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    details: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        default=None,
    )

    # ── Relationships ────────────────────────────────────────────────
    session = relationship("InterviewSession", back_populates="analytics")

    def __repr__(self) -> str:
        return (
            f"<Analytics id={self.id!s:.8} "
            f"session_id={self.session_id!s:.8} metric_name={self.metric_name!r}>"
        )
