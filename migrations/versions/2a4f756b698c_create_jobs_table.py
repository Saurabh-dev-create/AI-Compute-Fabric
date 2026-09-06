"""create jobs table

Revision ID: 2a4f756b698c
Revises:
Create Date: 2026-09-06 19:51:06.178063

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2a4f756b698c"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("job_type", sa.Text(), nullable=False),
        sa.Column("gpu_type", sa.Text(), nullable=True),
        sa.Column("min_vram_gb", sa.Float(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("gpu_id", sa.Text(), nullable=True),
        sa.Column("node_id", sa.Text(), nullable=True),
        sa.Column("allocated_vram_gb", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("jobs")
