"""
Question Embedding ORM Model

Stores the vector embedding for each generated interview question.
Used by the Anti-Repetition Engine to detect and prevent semantically
duplicate questions via FAISS cosine-similarity search.

Each embedding is a 1536-dimensional float32 vector produced by
OpenAI's text-embedding-3-small model, serialized as raw bytes.
"""

from typing import Optional

from sqlalchemy import ForeignKey, Integer, LargeBinary, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base, TimestampMixin


class QuestionEmbedding(TimestampMixin, Base):
    """
    question_embeddings table

    Each row stores the vector embedding of a single interview question,
    enabling similarity searches to prevent duplicate question generation.
    """
    __tablename__ = "question_embeddings"

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
        index=True,
    )

    question_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Raw question string — kept for debugging and audit",
    )

    embedding_vector: Mapped[bytes] = mapped_column(
        LargeBinary,
        nullable=False,
        comment="Serialized numpy float32 array (1536 dims)",
    )

    embedding_model: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="text-embedding-3-small",
        comment="Model used to produce the embedding",
    )

    # ── Relationships ────────────────────────────────────────────────
    session = relationship("InterviewSession", backref="question_embeddings")
    question = relationship("Question", backref="embedding")

    def __repr__(self) -> str:
        return (
            f"<QuestionEmbedding id={self.id} "
            f"question_id={self.question_id} "
            f"model={self.embedding_model}>"
        )
