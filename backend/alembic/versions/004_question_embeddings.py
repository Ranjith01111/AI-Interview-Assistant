"""Add question_embeddings table for Anti-Repetition Engine

Revision ID: 004_question_embeddings
Revises: 003_context_aware_questions
Create Date: 2026-06-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = "004_question_embeddings"
down_revision: Union[str, None] = "003_context_aware_questions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "question_embeddings",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column(
            "session_id",
            UUID(as_uuid=True),
            sa.ForeignKey("interview_sessions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "question_id",
            sa.Integer(),
            sa.ForeignKey("questions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("embedding_vector", sa.LargeBinary(), nullable=False),
        sa.Column(
            "embedding_model",
            sa.String(length=100),
            nullable=False,
            server_default="text-embedding-3-small",
        ),
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

    # Composite index for efficient session-level lookups
    op.create_index(
        "ix_question_embeddings_session_question",
        "question_embeddings",
        ["session_id", "question_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_question_embeddings_session_question", table_name="question_embeddings")
    op.drop_table("question_embeddings")
