"""Add proctoring enhancements

Revision ID: 006_proctor_enhancements
Revises: 005_coding_assessment
Create Date: 2026-06-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


# revision identifiers, used by Alembic.
revision: str = "006_proctor_enhancements"
down_revision: Union[str, None] = "005_coding_assessment"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Identity verification fields on interview_sessions
    op.add_column(
        "interview_sessions",
        sa.Column("reference_photo_path", sa.String(length=500), nullable=True)
    )
    op.add_column(
        "interview_sessions",
        sa.Column("face_embedding", JSON(), nullable=True)
    )

    # Proctor log enrichment
    op.add_column(
        "proctor_logs",
        sa.Column("snapshot_path", sa.String(length=500), nullable=True)
    )
    op.add_column(
        "proctor_logs",
        sa.Column("risk_score", sa.Float(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("proctor_logs", "risk_score")
    op.drop_column("proctor_logs", "snapshot_path")
    op.drop_column("interview_sessions", "face_embedding")
    op.drop_column("interview_sessions", "reference_photo_path")
