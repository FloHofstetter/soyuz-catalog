"""Catalogs.storage_location.

Revision ID: 005
Revises: 004
Create Date: 2026-04-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: str | None = "004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("catalogs") as batch:
        batch.add_column(sa.Column("storage_location", sa.String(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("catalogs") as batch:
        batch.drop_column("storage_location")
