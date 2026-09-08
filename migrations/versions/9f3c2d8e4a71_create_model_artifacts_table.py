"""create model artifacts table

Revision ID: 9f3c2d8e4a71
Revises: 4e8b7c1a6d32
Create Date: 2026-09-08
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9f3c2d8e4a71"
down_revision: Union[str, Sequence[str], None] = "4e8b7c1a6d32"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "model_artifacts",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column(
            "job_id",
            sa.Text(),
            sa.ForeignKey("jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("artifact_type", sa.Text(), nullable=False),
        sa.Column("storage_uri", sa.Text(), nullable=False),
        sa.Column("base_model", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_model_artifacts_job_id",
        "model_artifacts",
        ["job_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_model_artifacts_job_id",
        table_name="model_artifacts",
    )
    op.drop_table("model_artifacts")
