"""Delta Sharing: shares, share objects, recipients, grants (ADR-0015).

Revision ID: 018
Revises: 017
Create Date: 2026-06-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "018"
down_revision: str | None = "017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "shares",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("comment", sa.String(), nullable=True),
        sa.Column("owner", sa.String(255), nullable=True),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("updated_at", sa.BigInteger(), nullable=False),
        sa.Column("updated_by", sa.String(255), nullable=True),
        sa.UniqueConstraint("name", name="uq_shares_name"),
    )
    op.create_index("ix_shares_name", "shares", ["name"])

    op.create_table(
        "share_objects",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "share_id",
            sa.String(32),
            sa.ForeignKey("shares.id"),
            nullable=False,
        ),
        sa.Column("table_full_name", sa.String(768), nullable=False),
        sa.Column("shared_as", sa.String(512), nullable=True),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.UniqueConstraint("share_id", "table_full_name", name="uq_share_objects_share_id_table"),
    )
    op.create_index("ix_share_objects_share_id", "share_objects", ["share_id"])

    op.create_table(
        "recipients",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("comment", sa.String(), nullable=True),
        sa.Column("owner", sa.String(255), nullable=True),
        sa.Column("bearer_token_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("updated_at", sa.BigInteger(), nullable=False),
        sa.Column("updated_by", sa.String(255), nullable=True),
        sa.UniqueConstraint("name", name="uq_recipients_name"),
        sa.UniqueConstraint("bearer_token_hash", name="uq_recipients_bearer_token_hash"),
    )
    op.create_index("ix_recipients_name", "recipients", ["name"])
    op.create_index("ix_recipients_bearer_token_hash", "recipients", ["bearer_token_hash"])

    op.create_table(
        "share_grants",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "share_id",
            sa.String(32),
            sa.ForeignKey("shares.id"),
            nullable=False,
        ),
        sa.Column(
            "recipient_id",
            sa.String(32),
            sa.ForeignKey("recipients.id"),
            nullable=False,
        ),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.UniqueConstraint("share_id", "recipient_id", name="uq_share_grants_share_recipient"),
    )
    op.create_index("ix_share_grants_share_id", "share_grants", ["share_id"])
    op.create_index("ix_share_grants_recipient_id", "share_grants", ["recipient_id"])


def downgrade() -> None:
    op.drop_index("ix_share_grants_recipient_id", table_name="share_grants")
    op.drop_index("ix_share_grants_share_id", table_name="share_grants")
    op.drop_table("share_grants")
    op.drop_index("ix_recipients_bearer_token_hash", table_name="recipients")
    op.drop_index("ix_recipients_name", table_name="recipients")
    op.drop_table("recipients")
    op.drop_index("ix_share_objects_share_id", table_name="share_objects")
    op.drop_table("share_objects")
    op.drop_index("ix_shares_name", table_name="shares")
    op.drop_table("shares")
