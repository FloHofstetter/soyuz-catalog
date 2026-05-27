"""Volumes.

Revision ID: 004
Revises: 003
Create Date: 2026-04-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: str | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "volumes",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "schema_id",
            sa.String(32),
            sa.ForeignKey("schemas.id"),
            nullable=False,
        ),
        sa.Column(
            "catalog_id",
            sa.String(32),
            sa.ForeignKey("catalogs.id"),
            nullable=False,
        ),
        sa.Column("volume_type", sa.String(16), nullable=False),
        sa.Column("storage_location", sa.String(), nullable=True),
        sa.Column("comment", sa.String(), nullable=True),
        sa.Column("owner", sa.String(255), nullable=True),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("updated_at", sa.BigInteger(), nullable=False),
        sa.Column("updated_by", sa.String(255), nullable=True),
        sa.UniqueConstraint("schema_id", "name", name="uq_volumes_schema_id_name"),
    )
    op.create_index("ix_volumes_name", "volumes", ["name"])
    op.create_index("ix_volumes_schema_id", "volumes", ["schema_id"])
    op.create_index("ix_volumes_catalog_id", "volumes", ["catalog_id"])


def downgrade() -> None:
    op.drop_index("ix_volumes_catalog_id", table_name="volumes")
    op.drop_index("ix_volumes_schema_id", table_name="volumes")
    op.drop_index("ix_volumes_name", table_name="volumes")
    op.drop_table("volumes")
