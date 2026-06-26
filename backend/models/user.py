"""
User ORM Model

Represents an authenticated user of the AI Interview Assistant platform.
Supports role-based access control with Admin, Interviewer, and Candidate roles.
"""

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base, TimestampMixin, UUIDMixin


class UserRole(str, enum.Enum):
    """Available roles for access control."""
    ADMIN = "admin"
    RECRUITER = "recruiter"      # Can create/manage interviews, view candidate reports
    INTERVIEWER = "interviewer"  # Legacy — use RECRUITER for new accounts
    CANDIDATE = "candidate"


class User(UUIDMixin, TimestampMixin, Base):
    """
    users table

    Stores user credentials and profile information.
    Passwords are stored as bcrypt hashes — never in plaintext.

    Columns:
        id           — UUID primary key (from UUIDMixin)
        name         — Display name
        email        — Unique email address (login identifier)
        password_hash— bcrypt-hashed password
        role         — One of: admin, recruiter, interviewer, candidate
        is_active    — Soft-delete flag (False = deactivated)
        last_login_at— Timestamp of most recent successful login
        created_at   — Row creation time (from TimestampMixin)
        updated_at   — Last update time (from TimestampMixin)
    """
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    email: Mapped[str] = mapped_column(
        String(320),
        unique=True,
        index=True,
        nullable=False,
    )
    password_hash: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(20),
        default=UserRole.CANDIDATE.value,
        nullable=False,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    # ── Relationships ────────────────────────────────────────────────
    resumes = relationship(
        "Resume",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    interview_sessions = relationship(
        "InterviewSession",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    audit_logs = relationship(
        "AuditLog",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<User id={self.id!s:.8} "
            f"email={self.email!r} role={self.role}>"
        )
