"""
ProctorLog ORM Model

Stores activity events logged during interview sessions for proctoring/integrity checks.
"""

import uuid
from typing import Optional

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base, TimestampMixin, UUIDMixin


class ProctorLog(UUIDMixin, TimestampMixin, Base):
    """
    proctor_logs table

    Captures client-side activity events (tab switching, focus loss, voice warnings, etc.).

    Columns:
        id           — UUID primary key (from UUIDMixin)
        session_id   — Foreign key to interview_sessions.id
        event_type   — Type of event (e.g., TAB_SWITCH, FACE_NOT_DETECTED)
        client_ip    — Client IP address
        user_agent   — Client User-Agent
        details      — Dynamic JSON for event context
        created_at   — Row creation time (from TimestampMixin)
        updated_at   — Last update time (from TimestampMixin)
    """
    __tablename__ = "proctor_logs"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    client_ip: Mapped[Optional[str]] = mapped_column(
        String(45),  # supports IPv6
        nullable=True,
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    details: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        default=None,
    )
    snapshot_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    risk_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    # ── Relationships ────────────────────────────────────────────────
    session = relationship("InterviewSession", back_populates="proctor_logs")

    def __repr__(self) -> str:
        return (
            f"<ProctorLog id={self.id!s:.8} "
            f"session_id={self.session_id!s:.8} event_type={self.event_type!r}>"
        )
