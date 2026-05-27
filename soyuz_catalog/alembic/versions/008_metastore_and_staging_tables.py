"""Metastore singleton and staging tables.

Revision ID: 008
Revises: 007
Create Date: 2026-04-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "008"
down_revision: str | None = "007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "metastore",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
    )

    op.create_table(
        "staging_tables",
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
        sa.Column("staging_location", sa.String(), nullable=False),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
    )
    op.create_index("ix_staging_tables_name", "staging_tables", ["name"])
    op.create_index("ix_staging_tables_schema_id", "staging_tables", ["schema_id"])
    op.create_index("ix_staging_tables_catalog_id", "staging_tables", ["catalog_id"])


def downgrade() -> None:
    op.drop_index("ix_staging_tables_catalog_id", table_name="staging_tables")
    op.drop_index("ix_staging_tables_schema_id", table_name="staging_tables")
    op.drop_index("ix_staging_tables_name", table_name="staging_tables")
    op.drop_table("staging_tables")
    op.drop_table("metastore")
