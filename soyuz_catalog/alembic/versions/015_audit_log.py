"""Audit log table.

Adds the ``audit_log`` table. Mutation routes call
:func:`soyuz_catalog.services.audit_service.log_action` to insert
one row per successful mutation; the ``agent_run_id`` column is
populated from the ``X-Agent-Run-Id`` header so agent-driven
clients can cross-reference UC mutations back to their own
per-run views.

Revision ID: 015
Revises: 014
Create Date: 2026-04-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "015"
down_revision: str | None = "014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("target", sa.String(length=512), nullable=False),
        sa.Column("principal", sa.String(length=255), nullable=True),
        sa.Column("agent_run_id", sa.String(length=36), nullable=True),
        sa.Column("client_ip", sa.String(length=64), nullable=True),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_log_action", "audit_log", ["action"])
    op.create_index("ix_audit_log_target", "audit_log", ["target"])
    op.create_index("ix_audit_log_agent_run_id", "audit_log", ["agent_run_id"])
    op.create_index("ix_audit_log_created_at", "audit_log", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_audit_log_created_at", table_name="audit_log")
    op.drop_index("ix_audit_log_agent_run_id", table_name="audit_log")
    op.drop_index("ix_audit_log_target", table_name="audit_log")
    op.drop_index("ix_audit_log_action", table_name="audit_log")
    op.drop_table("audit_log")
