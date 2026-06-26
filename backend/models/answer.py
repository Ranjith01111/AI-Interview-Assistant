"""
Answer ORM Model

Stores each candidate answer along with the AI's scoring and feedback.
"""

from typing import Optional

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base, TimestampMixin


class Answer(TimestampMixin, Base):
    """
    answers table

    One row per answered question — captures the candidate's response
    and the AI evaluator's feedback (score, strengths, improvements).
    """
    __tablename__ = "answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
    )

    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[int] = mapped_column(Integer, default=0)
    strengths: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    improvements: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    model_answer_hint: Mapped[Optional[str]] = mapped_column(Text, default="")

    # ── Relationships ────────────────────────────────────────────────
    session = relationship("InterviewSession", back_populates="answers")
    question = relationship("Question", back_populates="answers")

    def __repr__(self) -> str:
        return (
            f"<Answer question_id={self.question_id} "
            f"score={self.score} session={str(self.session_id):.8}>"
        )
