"""Lineage column edges + value changes.

Extends the table-level :class:`LineageEdge` store with column-
and value-level resolution. Soyuz ingests two extra OpenLineage
facets and persists them alongside the table-level rows:

* ``columnLineage`` — OpenLineage 1.x standard facet.  One row
  per ``(target_column, input_field)`` pair captured per run.
  Spark, dbt-OpenLineage, and other emitters can populate it.
* ``valueChange`` — non-spec producer extension identified by
  its ``_producer`` URI on the facet payload. One row per
  ``(target_row_id, target_column, old_value, new_value)`` cell
  change. soyuz stores whatever the producer sent verbatim;
  producers handling PII are expected to redact upstream.

Revision ID: 016
Revises: 015
Create Date: 2026-04-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "016"
down_revision: str | None = "015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "lineage_column_edges",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "run_id",
            sa.String(32),
            sa.ForeignKey("lineage_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_securable_id", sa.String(32), nullable=False),
        sa.Column("source_column", sa.String(255), nullable=False),
        sa.Column("target_securable_id", sa.String(32), nullable=False),
        sa.Column("target_column", sa.String(255), nullable=False),
        sa.Column("transformation_type", sa.Text(), nullable=True),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.UniqueConstraint(
            "run_id",
            "source_securable_id",
            "source_column",
            "target_securable_id",
            "target_column",
            name="uq_lineage_column_edges_run_quad",
        ),
    )
    op.create_index(
        "ix_lineage_column_edges_target",
        "lineage_column_edges",
        ["target_securable_id", "target_column"],
    )
    op.create_index(
        "ix_lineage_column_edges_source",
        "lineage_column_edges",
        ["source_securable_id", "source_column"],
    )

    op.create_table(
        "lineage_value_changes",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "run_id",
            sa.String(32),
            sa.ForeignKey("lineage_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("target_securable_id", sa.String(32), nullable=False),
        sa.Column("target_row_id", sa.String(64), nullable=False),
        sa.Column("target_column", sa.String(255), nullable=False),
        sa.Column("old_value", sa.Text(), nullable=True),
        sa.Column("new_value", sa.Text(), nullable=True),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
    )
    op.create_index(
        "ix_lineage_value_changes_target",
        "lineage_value_changes",
        ["target_securable_id", "target_row_id"],
    )
    op.create_index(
        "ix_lineage_value_changes_run",
        "lineage_value_changes",
        ["run_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_lineage_value_changes_run", table_name="lineage_value_changes")
    op.drop_index("ix_lineage_value_changes_target", table_name="lineage_value_changes")
    op.drop_table("lineage_value_changes")
    op.drop_index("ix_lineage_column_edges_source", table_name="lineage_column_edges")
    op.drop_index("ix_lineage_column_edges_target", table_name="lineage_column_edges")
    op.drop_table("lineage_column_edges")
