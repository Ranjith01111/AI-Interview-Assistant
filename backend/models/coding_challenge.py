"""
CodingChallenge ORM Model
"""

import uuid
from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base, TimestampMixin, UUIDMixin


class CodingChallenge(UUIDMixin, TimestampMixin, Base):
    """
    coding_challenges table

    Stores coding problem descriptions, starter code templates,
    test cases, and resource limits.
    """
    __tablename__ = "coding_challenges"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(50), default="Medium", nullable=False)
    
    # JSON mapping: { "python": "...", "javascript": "...", ... }
    template_code: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    
    # JSON list of test cases: [ { "input": "...", "expected_output": "...", "is_hidden": false }, ... ]
    # For SQL: [ { "schema_sql": "...", "seed_sql": "...", "expected_output": "..." } ]
    test_cases: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    
    # limits
    time_limit: Mapped[float] = mapped_column(default=2.0, nullable=False)  # in seconds
    memory_limit: Mapped[int] = mapped_column(default=128, nullable=False)  # in MB

    # ── Relationships ────────────────────────────────────────────────
    submissions = relationship(
        "CodingSubmission",
        back_populates="challenge",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<CodingChallenge id={self.id!s:.8} title={self.title!r} difficulty={self.difficulty}>"
