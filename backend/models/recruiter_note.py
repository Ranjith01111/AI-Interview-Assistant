"""
RecruiterNote ORM Model

Stores text notes/comments that recruiters attach to interview sessions.
Supports private (author-only) and shared (visible to all recruiters/admins) visibility.
"""

import uuid
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base, TimestampMixin, UUIDMixin


class RecruiterNote(UUIDMixin, TimestampMixin, Base):
    """
    recruiter_notes table

    Captures recruiter commentary on candidate interview sessions.

    Columns:
        id           — UUID primary key (from UUIDMixin)
        session_id   — Foreign key to interview_sessions.id
        recruiter_id — Foreign key to users.id (the note author)
        content      — Free-text note body
        is_private   — If True, only the author can see the note
        created_at   — Row creation time (from TimestampMixin)
        updated_at   — Last update time (from TimestampMixin)
    """
    __tablename__ = "recruiter_notes"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    recruiter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    is_private: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # —— Relationships ————————————————————————————————————————
    session = relationship("InterviewSession", backref="recruiter_notes")
    recruiter = relationship("User", backref="recruiter_notes")

    def __repr__(self) -> str:
        return (
            f"<RecruiterNote id={self.id!s:.8} "
            f"session_id={self.session_id!s:.8} "
            f"recruiter_id={self.recruiter_id!s:.8} "
            f"private={self.is_private}>"
        )
