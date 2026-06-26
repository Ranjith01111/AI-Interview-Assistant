"""
Resume ORM Model

Represents a resume uploaded by a user.
"""

import uuid
from typing import Optional

from sqlalchemy import ForeignKey, String, Text, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base, TimestampMixin, UUIDMixin


class Resume(UUIDMixin, TimestampMixin, Base):
    """
    resumes table

    Stores uploaded candidate resumes associated with users.

    Columns:
        id           — UUID primary key (from UUIDMixin)
        user_id      — Foreign key to users.id
        file_name    — Name of the uploaded file
        content      — Extracted text content of the resume
        created_at   — Row creation time (from TimestampMixin)
        updated_at   — Last update time (from TimestampMixin)
    """
    __tablename__ = "resumes"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    content: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    file_path: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
    )
    file_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    size_bytes: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # ── Relationships ────────────────────────────────────────────────
    user = relationship("User", back_populates="resumes")

    def __repr__(self) -> str:
        return (
            f"<Resume id={self.id!s:.8} "
            f"user_id={self.user_id!s:.8} file_name={self.file_name!r}>"
        )
