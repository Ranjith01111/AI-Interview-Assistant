"""
AuditLog ORM Model

Immutable record of every security-relevant event in the system.
Used for compliance, debugging, and intrusion detection.
"""

import uuid
from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base, TimestampMixin


class AuditLog(TimestampMixin, Base):
    """
    audit_logs table

    Each row represents a single auditable event (login, registration,
    token refresh, failed auth attempt, admin action, etc.).

    Columns:
        id          — Auto-increment integer PK
        user_id     — FK to users.id (nullable for pre-auth events)
        action      — Event type: LOGIN, REGISTER, TOKEN_REFRESH, LOGOUT,
                      LOGIN_FAILED, ACCOUNT_DEACTIVATED, etc.
        resource    — The API path that triggered the event
        ip_address  — Client IP extracted from the request
        user_agent  — Client User-Agent header
        details     — JSON blob for additional context
        status      — "success" or "failure"
    """
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    resource: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
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
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="success",
    )

    # ── Relationships ────────────────────────────────────────────────
    user = relationship("User", back_populates="audit_logs")

    def __repr__(self) -> str:
        return (
            f"<AuditLog id={self.id} action={self.action!r} "
            f"user_id={self.user_id!s:.8 if self.user_id else 'anon'} "
            f"status={self.status}>"
        )
