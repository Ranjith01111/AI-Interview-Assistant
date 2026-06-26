"""Add coding_challenges and coding_submissions tables

Revision ID: 005_coding_assessment
Revises: 004_question_embeddings
Create Date: 2026-06-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON


# revision identifiers, used by Alembic.
revision: str = "005_coding_assessment"
down_revision: Union[str, None] = "004_question_embeddings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create coding_challenges table
    op.create_table(
        "coding_challenges",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("difficulty", sa.String(length=50), nullable=False, server_default="Medium"),
        sa.Column("template_code", JSON(), nullable=False, server_default="{}"),
        sa.Column("test_cases", JSON(), nullable=False, server_default="[]"),
        sa.Column("time_limit", sa.Float(), nullable=False, server_default="2.0"),
        sa.Column("memory_limit", sa.Integer(), nullable=False, server_default="128"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # Create coding_submissions table
    op.create_table(
        "coding_submissions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "session_id",
            UUID(as_uuid=True),
            sa.ForeignKey("interview_sessions.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "challenge_id",
            UUID(as_uuid=True),
            sa.ForeignKey("coding_challenges.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("language", sa.String(length=50), nullable=False),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="Pending"),
        sa.Column("score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("results", JSON(), nullable=False, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("coding_submissions")
    op.drop_table("coding_challenges")
