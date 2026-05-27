"""Functions, registered models, and model versions.

Revision ID: 007
Revises: 006
Create Date: 2026-04-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "007"
down_revision: str | None = "006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "functions",
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
        sa.Column("data_type", sa.String(64), nullable=False),
        sa.Column("full_data_type", sa.String(), nullable=False),
        sa.Column("input_params", sa.JSON(), nullable=False),
        sa.Column("return_params", sa.JSON(), nullable=False),
        sa.Column("routine_body", sa.String(16), nullable=False),
        sa.Column("routine_definition", sa.String(), nullable=True),
        sa.Column("routine_dependencies", sa.JSON(), nullable=True),
        sa.Column("parameter_style", sa.String(8), nullable=False),
        sa.Column("is_deterministic", sa.Boolean(), nullable=False),
        sa.Column("sql_data_access", sa.String(16), nullable=False),
        sa.Column("is_null_call", sa.Boolean(), nullable=False),
        sa.Column("security_type", sa.String(16), nullable=False),
        sa.Column("specific_name", sa.String(255), nullable=False),
        sa.Column("external_language", sa.String(64), nullable=True),
        sa.Column("comment", sa.String(), nullable=True),
        sa.Column("properties", sa.String(), nullable=True),
        sa.Column("owner", sa.String(255), nullable=True),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("updated_at", sa.BigInteger(), nullable=False),
        sa.Column("updated_by", sa.String(255), nullable=True),
        sa.UniqueConstraint("schema_id", "name", name="uq_functions_schema_id_name"),
    )
    op.create_index("ix_functions_name", "functions", ["name"])
    op.create_index("ix_functions_schema_id", "functions", ["schema_id"])
    op.create_index("ix_functions_catalog_id", "functions", ["catalog_id"])

    op.create_table(
        "registered_models",
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
        sa.Column("storage_location", sa.String(), nullable=True),
        sa.Column("comment", sa.String(), nullable=True),
        sa.Column("owner", sa.String(255), nullable=True),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("updated_at", sa.BigInteger(), nullable=False),
        sa.Column("updated_by", sa.String(255), nullable=True),
        sa.UniqueConstraint(
            "schema_id",
            "name",
            name="uq_registered_models_schema_id_name",
        ),
    )
    op.create_index("ix_registered_models_name", "registered_models", ["name"])
    op.create_index("ix_registered_models_schema_id", "registered_models", ["schema_id"])
    op.create_index("ix_registered_models_catalog_id", "registered_models", ["catalog_id"])

    op.create_table(
        "model_versions",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "registered_model_id",
            sa.String(32),
            sa.ForeignKey("registered_models.id"),
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("run_id", sa.String(255), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("storage_location", sa.String(), nullable=True),
        sa.Column("comment", sa.String(), nullable=True),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("updated_at", sa.BigInteger(), nullable=False),
        sa.Column("updated_by", sa.String(255), nullable=True),
        sa.UniqueConstraint(
            "registered_model_id",
            "version",
            name="uq_model_versions_registered_model_id_version",
        ),
    )
    op.create_index(
        "ix_model_versions_registered_model_id",
        "model_versions",
        ["registered_model_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_model_versions_registered_model_id",
        table_name="model_versions",
    )
    op.drop_table("model_versions")
    op.drop_index("ix_registered_models_catalog_id", table_name="registered_models")
    op.drop_index("ix_registered_models_schema_id", table_name="registered_models")
    op.drop_index("ix_registered_models_name", table_name="registered_models")
    op.drop_table("registered_models")
    op.drop_index("ix_functions_catalog_id", table_name="functions")
    op.drop_index("ix_functions_schema_id", table_name="functions")
    op.drop_index("ix_functions_name", table_name="functions")
    op.drop_table("functions")
