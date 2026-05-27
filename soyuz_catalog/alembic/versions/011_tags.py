"""Tags table.

Revision ID: 011
Revises: 010
Create Date: 2026-04-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "011"
down_revision: str | None = "010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tags",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("securable_type", sa.String(32), nullable=False),
        sa.Column("securable_id", sa.String(32), nullable=False),
        sa.Column("key", sa.String(255), nullable=False),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.Column("updated_at", sa.BigInteger(), nullable=False),
        sa.UniqueConstraint(
            "securable_type",
            "securable_id",
            "key",
            name="uq_tags_type_id_key",
        ),
    )
    op.create_index("ix_tags_securable_type", "tags", ["securable_type"])
    op.create_index("ix_tags_securable_id", "tags", ["securable_id"])


def downgrade() -> None:
    op.drop_index("ix_tags_securable_id", table_name="tags")
    op.drop_index("ix_tags_securable_type", table_name="tags")
    op.drop_table("tags")
