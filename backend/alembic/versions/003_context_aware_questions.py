"""Add context-aware columns to questions table

Revision ID: 003_context_aware_questions
Revises: 002_extend_schema
Create Date: 2026-05-31

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "003_context_aware_questions"
down_revision: Union[str, None] = "002_extend_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to the questions table
    op.add_column(
        "questions",
        sa.Column(
            "difficulty",
            sa.String(length=20),
            nullable=False,
            server_default="medium",
        ),
    )
    op.add_column(
        "questions",
        sa.Column(
            "category",
            sa.String(length=30),
            nullable=False,
            server_default="project_based",
        ),
    )
    op.add_column(
        "questions",
        sa.Column(
            "project_reference",
            sa.String(length=255),
            nullable=True,
        ),
    )


def downgrade() -> None:
    # Remove columns from the questions table
    op.drop_column("questions", "project_reference")
    op.drop_column("questions", "category")
    op.drop_column("questions", "difficulty")
