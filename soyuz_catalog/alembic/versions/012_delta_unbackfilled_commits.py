"""Delta unbackfilled commits table.

Revision ID: 012
Revises: 011
Create Date: 2026-04-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "012"
down_revision: str | None = "011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "delta_unbackfilled_commits",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("table_id", sa.String(32), nullable=False),
        sa.Column("commit_version", sa.BigInteger(), nullable=False),
        sa.Column("commit_timestamp", sa.BigInteger(), nullable=False),
        sa.Column("file_name", sa.String(512), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("file_modification_timestamp", sa.BigInteger(), nullable=False),
        sa.Column("is_backfilled_latest_commit", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.UniqueConstraint(
            "table_id",
            "commit_version",
            name="uq_delta_unbackfilled_commits_table_id_version",
        ),
    )
    op.create_index(
        "ix_delta_unbackfilled_commits_table_id",
        "delta_unbackfilled_commits",
        ["table_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_delta_unbackfilled_commits_table_id",
        table_name="delta_unbackfilled_commits",
    )
    op.drop_table("delta_unbackfilled_commits")
