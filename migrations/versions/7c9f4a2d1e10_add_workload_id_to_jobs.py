"""add workload id to jobs

Revision ID: 7c9f4a2d1e10
Revises: 2a4f756b698c
Create Date: 2026-09-07
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7c9f4a2d1e10"
down_revision: Union[str, Sequence[str], None] = "2a4f756b698c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "jobs",
        sa.Column(
            "workload_id",
            sa.Text(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column(
        "jobs",
        "workload_id",
    )
