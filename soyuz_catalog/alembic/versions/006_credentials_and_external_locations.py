"""Credentials and external locations.

Revision ID: 006
Revises: 005
Create Date: 2026-04-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "006"
down_revision: str | None = "005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "credentials",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("purpose", sa.String(32), nullable=False),
        sa.Column("comment", sa.String(), nullable=True),
        sa.Column("owner", sa.String(255), nullable=True),
        sa.Column("aws_iam_role_arn", sa.String(), nullable=True),
        sa.Column("aws_iam_role_external_id", sa.String(64), nullable=True),
        sa.Column("aws_iam_role_unity_catalog_iam_arn", sa.String(), nullable=True),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("updated_at", sa.BigInteger(), nullable=False),
        sa.Column("updated_by", sa.String(255), nullable=True),
        sa.UniqueConstraint("name", name="uq_credentials_name"),
    )
    op.create_index("ix_credentials_name", "credentials", ["name"])

    op.create_table(
        "external_locations",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column(
            "credential_id",
            sa.String(32),
            sa.ForeignKey("credentials.id"),
            nullable=False,
        ),
        sa.Column("comment", sa.String(), nullable=True),
        sa.Column("owner", sa.String(255), nullable=True),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("updated_at", sa.BigInteger(), nullable=False),
        sa.Column("updated_by", sa.String(255), nullable=True),
        sa.UniqueConstraint("name", name="uq_external_locations_name"),
    )
    op.create_index("ix_external_locations_name", "external_locations", ["name"])
    op.create_index(
        "ix_external_locations_credential_id",
        "external_locations",
        ["credential_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_external_locations_credential_id", table_name="external_locations")
    op.drop_index("ix_external_locations_name", table_name="external_locations")
    op.drop_table("external_locations")
    op.drop_index("ix_credentials_name", table_name="credentials")
    op.drop_table("credentials")
