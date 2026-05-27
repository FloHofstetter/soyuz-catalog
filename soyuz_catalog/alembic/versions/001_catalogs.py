"""Initial schema — catalogs table.

Revision ID: 001
Revises: None
Create Date: 2026-04-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "catalogs",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("comment", sa.String(), nullable=True),
        sa.Column("properties", sa.JSON(), nullable=False),
        sa.Column("owner", sa.String(255), nullable=True),
        sa.Column("storage_root", sa.String(), nullable=True),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("updated_at", sa.BigInteger(), nullable=False),
        sa.Column("updated_by", sa.String(255), nullable=True),
    )
    op.create_index("ix_catalogs_name", "catalogs", ["name"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_catalogs_name", table_name="catalogs")
    op.drop_table("catalogs")
