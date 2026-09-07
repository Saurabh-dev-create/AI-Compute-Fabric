"""add workload spec to jobs

Revision ID: 4e8b7c1a6d32
Revises: 7c9f4a2d1e10
Create Date: 2026-09-07
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "4e8b7c1a6d32"
down_revision: Union[str, Sequence[str], None] = "7c9f4a2d1e10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "jobs",
        sa.Column(
            "workload_spec",
            postgresql.JSONB(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column(
        "jobs",
        "workload_spec",
    )
