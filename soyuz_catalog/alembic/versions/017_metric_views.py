"""Metric views (ADR-0014).

Revision ID: 017
Revises: 016
Create Date: 2026-06-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "017"
down_revision: str | None = "016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "metric_views",
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
        sa.Column("source_table_full_name", sa.String(768), nullable=False),
        sa.Column("spec", sa.JSON(), nullable=False),
        sa.Column("comment", sa.String(), nullable=True),
        sa.Column("owner", sa.String(255), nullable=True),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("updated_at", sa.BigInteger(), nullable=False),
        sa.Column("updated_by", sa.String(255), nullable=True),
        sa.UniqueConstraint("schema_id", "name", name="uq_metric_views_schema_id_name"),
    )
    op.create_index("ix_metric_views_name", "metric_views", ["name"])
    op.create_index("ix_metric_views_schema_id", "metric_views", ["schema_id"])
    op.create_index("ix_metric_views_catalog_id", "metric_views", ["catalog_id"])


def downgrade() -> None:
    op.drop_index("ix_metric_views_catalog_id", table_name="metric_views")
    op.drop_index("ix_metric_views_schema_id", table_name="metric_views")
    op.drop_index("ix_metric_views_name", table_name="metric_views")
    op.drop_table("metric_views")
