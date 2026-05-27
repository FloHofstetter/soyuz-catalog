"""Connections and foreign catalogs (ADR-0013).

Revision ID: 014
Revises: 013
Create Date: 2026-04-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "014"
down_revision: str | None = "013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "connections",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("connection_type", sa.String(32), nullable=False),
        sa.Column("options", sa.JSON(), nullable=False),
        sa.Column("read_only", sa.Boolean(), nullable=False),
        sa.Column("comment", sa.String(), nullable=True),
        sa.Column("owner", sa.String(255), nullable=True),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("updated_at", sa.BigInteger(), nullable=False),
        sa.Column("updated_by", sa.String(255), nullable=True),
        sa.UniqueConstraint("name", name="uq_connections_name"),
    )
    op.create_index("ix_connections_name", "connections", ["name"])

    # Extend catalogs with the foreign-variant columns. Existing rows
    # become ``type="MANAGED"`` / ``options={}`` / ``connection_id=NULL``
    # via the ``server_default`` values below, which stay on the
    # columns forever — the ORM model also carries a Python-level
    # ``default`` so new inserts do not rely on either, and leaving
    # the server default in place is the simplest way to make the
    # NOT NULL column addition safe on a non-empty table. Same
    # rationale every other ``add_column`` + ``NOT NULL`` migration in
    # this tree would use if they had needed a default.
    with op.batch_alter_table("catalogs") as batch:
        batch.add_column(
            sa.Column(
                "type",
                sa.String(16),
                nullable=False,
                server_default="MANAGED",
            ),
        )
        batch.add_column(
            sa.Column(
                "connection_id",
                sa.String(32),
                sa.ForeignKey("connections.id", name="fk_catalogs_connection_id"),
                nullable=True,
            ),
        )
        batch.add_column(
            sa.Column(
                "options",
                sa.JSON(),
                nullable=False,
                server_default=sa.text("'{}'"),
            ),
        )

    op.create_index("ix_catalogs_connection_id", "catalogs", ["connection_id"])


def downgrade() -> None:
    op.drop_index("ix_catalogs_connection_id", table_name="catalogs")
    with op.batch_alter_table("catalogs") as batch:
        batch.drop_column("options")
        batch.drop_column("connection_id")
        batch.drop_column("type")
    op.drop_index("ix_connections_name", table_name="connections")
    op.drop_table("connections")
