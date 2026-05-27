"""Permissions.

Revision ID: 009
Revises: 008
Create Date: 2026-04-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "009"
down_revision: str | None = "008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "permissions",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("securable_type", sa.String(32), nullable=False),
        sa.Column("securable_id", sa.String(32), nullable=False),
        sa.Column("principal", sa.String(512), nullable=False),
        sa.Column("privilege", sa.String(64), nullable=False),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.UniqueConstraint(
            "securable_type",
            "securable_id",
            "principal",
            "privilege",
            name="uq_permissions_type_id_principal_privilege",
        ),
    )
    op.create_index("ix_permissions_securable_type", "permissions", ["securable_type"])
    op.create_index("ix_permissions_securable_id", "permissions", ["securable_id"])
    op.create_index("ix_permissions_principal", "permissions", ["principal"])


def downgrade() -> None:
    op.drop_index("ix_permissions_principal", table_name="permissions")
    op.drop_index("ix_permissions_securable_id", table_name="permissions")
    op.drop_index("ix_permissions_securable_type", table_name="permissions")
    op.drop_table("permissions")
