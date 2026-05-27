"""Schemas table.

Revision ID: 002
Revises: 001
Create Date: 2026-04-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "schemas",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "catalog_id",
            sa.String(32),
            sa.ForeignKey("catalogs.id"),
            nullable=False,
        ),
        sa.Column("comment", sa.String(), nullable=True),
        sa.Column("properties", sa.JSON(), nullable=False),
        sa.Column("owner", sa.String(255), nullable=True),
        sa.Column("storage_root", sa.String(), nullable=True),
        sa.Column("storage_location", sa.String(), nullable=True),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("updated_at", sa.BigInteger(), nullable=False),
        sa.Column("updated_by", sa.String(255), nullable=True),
        sa.UniqueConstraint("catalog_id", "name", name="uq_schemas_catalog_id_name"),
    )
    op.create_index("ix_schemas_name", "schemas", ["name"])
    op.create_index("ix_schemas_catalog_id", "schemas", ["catalog_id"])


def downgrade() -> None:
    op.drop_index("ix_schemas_catalog_id", table_name="schemas")
    op.drop_index("ix_schemas_name", table_name="schemas")
    op.drop_table("schemas")
