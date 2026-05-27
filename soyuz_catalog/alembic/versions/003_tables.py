"""Tables and columns.

Revision ID: 003
Revises: 002
Create Date: 2026-04-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tables",
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
        sa.Column("table_type", sa.String(32), nullable=False),
        sa.Column("data_source_format", sa.String(32), nullable=False),
        sa.Column("storage_location", sa.String(), nullable=True),
        sa.Column("comment", sa.String(), nullable=True),
        sa.Column("properties", sa.JSON(), nullable=False),
        sa.Column("owner", sa.String(255), nullable=True),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("updated_at", sa.BigInteger(), nullable=False),
        sa.Column("updated_by", sa.String(255), nullable=True),
        sa.UniqueConstraint("schema_id", "name", name="uq_tables_schema_id_name"),
    )
    op.create_index("ix_tables_name", "tables", ["name"])
    op.create_index("ix_tables_schema_id", "tables", ["schema_id"])
    op.create_index("ix_tables_catalog_id", "tables", ["catalog_id"])

    op.create_table(
        "table_columns",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "table_id",
            sa.String(32),
            sa.ForeignKey("tables.id"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("type_text", sa.String(), nullable=False),
        sa.Column("type_json", sa.String(), nullable=False),
        sa.Column("type_name", sa.String(32), nullable=False),
        sa.Column("type_precision", sa.Integer(), nullable=True),
        sa.Column("type_scale", sa.Integer(), nullable=True),
        sa.Column("type_interval_type", sa.String(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("comment", sa.String(), nullable=True),
        sa.Column("nullable", sa.Boolean(), nullable=False),
        sa.Column("partition_index", sa.Integer(), nullable=True),
        sa.UniqueConstraint(
            "table_id",
            "position",
            name="uq_table_columns_table_id_position",
        ),
    )
    op.create_index("ix_table_columns_table_id", "table_columns", ["table_id"])


def downgrade() -> None:
    op.drop_index("ix_table_columns_table_id", table_name="table_columns")
    op.drop_table("table_columns")
    op.drop_index("ix_tables_catalog_id", table_name="tables")
    op.drop_index("ix_tables_schema_id", table_name="tables")
    op.drop_index("ix_tables_name", table_name="tables")
    op.drop_table("tables")
