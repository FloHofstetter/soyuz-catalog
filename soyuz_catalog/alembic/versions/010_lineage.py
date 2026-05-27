"""Lineage runs and edges.

Revision ID: 010
Revises: 009
Create Date: 2026-04-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "010"
down_revision: str | None = "009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "lineage_runs",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("job_namespace", sa.String(255), nullable=False),
        sa.Column("job_name", sa.String(512), nullable=False),
        sa.Column("state", sa.String(16), nullable=False),
        sa.Column("started_at", sa.BigInteger(), nullable=False),
        sa.Column("ended_at", sa.BigInteger(), nullable=True),
    )
    op.create_index(
        "ix_lineage_runs_job_namespace_job_name",
        "lineage_runs",
        ["job_namespace", "job_name"],
    )

    op.create_table(
        "lineage_edges",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "run_id",
            sa.String(32),
            sa.ForeignKey("lineage_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_securable_id", sa.String(32), nullable=False),
        sa.Column("target_securable_id", sa.String(32), nullable=False),
        sa.Column("operation", sa.String(512), nullable=True),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.UniqueConstraint(
            "run_id",
            "source_securable_id",
            "target_securable_id",
            name="uq_lineage_edges_run_source_target",
        ),
    )
    op.create_index("ix_lineage_edges_run_id", "lineage_edges", ["run_id"])
    op.create_index(
        "ix_lineage_edges_source_securable_id",
        "lineage_edges",
        ["source_securable_id"],
    )
    op.create_index(
        "ix_lineage_edges_target_securable_id",
        "lineage_edges",
        ["target_securable_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_lineage_edges_target_securable_id", table_name="lineage_edges")
    op.drop_index("ix_lineage_edges_source_securable_id", table_name="lineage_edges")
    op.drop_index("ix_lineage_edges_run_id", table_name="lineage_edges")
    op.drop_table("lineage_edges")
    op.drop_index("ix_lineage_runs_job_namespace_job_name", table_name="lineage_runs")
    op.drop_table("lineage_runs")
