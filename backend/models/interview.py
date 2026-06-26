"""
InterviewSession ORM Model

Represents a single interview session — from resume upload through
question generation, the live interview, and final scoring.
"""

import uuid
from typing import List, Optional

from sqlalchemy import Column, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base, TimestampMixin, UUIDMixin

import enum


class SessionStatus(str, enum.Enum):
    """Lifecycle states for an interview session."""
    CREATED = "created"
    QUESTIONS_GENERATED = "questions_generated"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class InterviewSession(UUIDMixin, TimestampMixin, Base):
    """
    interview_sessions table

    Stores metadata about each interview: candidate info,
    detected skills, status, and final scoring.
    """
    __tablename__ = "interview_sessions"

    candidate_name: Mapped[str] = mapped_column(String(255), default="Candidate")
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    resume_text: Mapped[str] = mapped_column(Text, nullable=False)
    skills_detected: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    experience_years: Mapped[str] = mapped_column(String(50), default="Not specified")

    status: Mapped[str] = mapped_column(
        String(30),
        default=SessionStatus.CREATED.value,
        nullable=False,
        index=True,
    )
    current_question_index: Mapped[int] = mapped_column(Integer, default=0)

    # Identity verification (reference photo + face embedding captured at start)
    reference_photo_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    face_embedding: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=None)

    # Final scoring (populated when status = COMPLETED)
    average_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    recommendation: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    overall_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Relationships ────────────────────────────────────────────────
    user = relationship("User", back_populates="interview_sessions")
    questions = relationship(
        "Question",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    answers = relationship(
        "Answer",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    coding_submissions = relationship(
        "CodingSubmission",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    proctor_logs = relationship(
        "ProctorLog",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    analytics = relationship(
        "Analytics",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<InterviewSession id={self.id!s:.8} "
            f"candidate={self.candidate_name!r} status={self.status}>"
        )
