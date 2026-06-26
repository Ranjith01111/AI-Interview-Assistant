"""
CodingSubmission ORM Model
"""

import uuid
from typing import Optional
from sqlalchemy import String, Text, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base, TimestampMixin, UUIDMixin


class CodingSubmission(UUIDMixin, TimestampMixin, Base):
    """
    coding_submissions table

    Stores candidate submissions, code, run logs, test case passing stats.
    """
    __tablename__ = "coding_submissions"

    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    challenge_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("coding_challenges.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    language: Mapped[str] = mapped_column(String(50), nullable=False)
    code: Mapped[str] = mapped_column(Text, nullable=False)
    
    status: Mapped[str] = mapped_column(String(50), default="Pending", nullable=False)
    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 0 to 100
    
    # JSON detailing test case execution details
    results: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # ── Relationships ────────────────────────────────────────────────
    challenge = relationship("CodingChallenge", back_populates="submissions")
    session = relationship("InterviewSession", lazy="select")

    def __repr__(self) -> str:
        return f"<CodingSubmission id={self.id!s:.8} challenge_id={self.challenge_id!s:.8} status={self.status} score={self.score}>"
