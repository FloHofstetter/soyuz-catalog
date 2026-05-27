"""Table constraints (ADR-0012).

Revision ID: 013
Revises: 012
Create Date: 2026-04-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "013"
down_revision: str | None = "012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "table_constraints",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("table_id", sa.String(32), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("constraint_type", sa.String(16), nullable=False),
        sa.Column("definition", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.UniqueConstraint(
            "table_id",
            "name",
            name="uq_table_constraints_table_id_name",
        ),
    )
    op.create_index(
        "ix_table_constraints_table_id",
        "table_constraints",
        ["table_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_table_constraints_table_id", table_name="table_constraints")
    op.drop_table("table_constraints")
