"""
Question ORM Model

Stores each interview question generated for a session.
"""

from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base, TimestampMixin


class Question(TimestampMixin, Base):
    """
    questions table

    Each row is a single interview question tied to a session.
    """
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_number: Mapped[int] = mapped_column(Integer, nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="technical",
    )
    topic: Mapped[Optional[str]] = mapped_column(String(100), default="")
    difficulty: Mapped[Optional[str]] = mapped_column(String(20), default="medium")
    category: Mapped[Optional[str]] = mapped_column(String(30), default="project_based")
    project_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # ── Relationships ────────────────────────────────────────────────
    session = relationship("InterviewSession", back_populates="questions")
    answers = relationship(
        "Answer",
        back_populates="question",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<Question #{self.question_number} type={self.question_type} "
            f"session={str(self.session_id):.8}>"
        )
