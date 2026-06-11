"""Delta Sharing resources: shares, share objects, recipients, grants (ADR-0015).

Over-the-spec extension: upstream UC OSS ``all.yaml`` defines no
sharing surface, but the open `Delta Sharing protocol
<https://github.com/delta-io/delta-sharing/blob/main/PROTOCOL.md>`_ is
the de-facto standard for cross-organisation table sharing and
Databricks ships shares / recipients as first-class UC securables.
soyuz persists the sharing metadata (which tables are exposed under
which share, and which recipient tokens may read them) and serves the
read-only protocol surface itself for ``file://``-backed tables.

The four classes split the same way the protocol does: a
:class:`Share` is a named, flat container; :class:`ShareObject` rows
place tables inside it; a :class:`Recipient` is a bearer-token
identity; and a :class:`ShareGrant` row makes one share visible to one
recipient. Grants and objects are weak composition — they exist only
as part of their share/recipient and are cascaded by the service layer
without a ``force`` gate, the same way table columns ride along with
their table.
"""

from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from soyuz_catalog.models._base import Base, _new_id, _now_ms


class Share(Base):
    """A named, flat container of shared tables.

    Shares are metastore-level resources with a plain unique index on
    ``name`` — structurally a sibling of
    :class:`soyuz_catalog.models.Connection`. The Delta Sharing
    protocol addresses shares by name on every endpoint, so the
    opaque ``id`` exists only for the wire-shape ``id`` field and the
    keyset-pagination cursor; nothing binds to it.

    A share owns its :class:`ShareObject` and :class:`ShareGrant`
    rows as weak composition: ``delete_share`` removes both row sets
    in the same transaction with no ``force`` gate, because an object
    or grant has no meaning outside its share — same reasoning as
    table columns riding along with their table.
    """

    __tablename__ = "shares"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    comment: Mapped[str | None] = mapped_column(String, nullable=True)
    owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False, default=_now_ms)
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[int] = mapped_column(BigInteger, nullable=False, default=_now_ms)
    updated_by: Mapped[str | None] = mapped_column(String(255), nullable=True)


class ShareObject(Base):
    """One table placed inside a share.

    ``table_full_name`` stores the three-part UC name — deliberately
    a *name*, not the opaque ``table_id`` every other soyuz binding
    uses. The Delta Sharing ecosystem is name-keyed end to end: the
    management wire adds and removes tables by full name, the
    protocol addresses them as ``share.schema.table``, and the
    reference server's static config also binds by name. Renaming a
    shared table therefore drops it out of the share (protocol reads
    surface 404) until it is re-added — a documented divergence from
    the rename-invariance rule, see ADR-0015's Alternatives.

    ``shared_as`` optionally re-homes the table inside the share's
    namespace as a two-part ``schema.table`` alias; when absent, the
    protocol placement is derived from the stored full name's schema
    and table segments. The effective placement must be unique within
    the share (enforced at the service layer — two objects must never
    answer to the same protocol address).

    ``created_at`` is the wire-level ``added_at``: a share object is
    immutable after creation (remove + re-add is the only edit), so
    the row never carries an ``updated_at``.
    """

    __tablename__ = "share_objects"
    __table_args__ = (
        UniqueConstraint("share_id", "table_full_name", name="uq_share_objects_share_id_table"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    share_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("shares.id"),
        nullable=False,
        index=True,
    )
    table_full_name: Mapped[str] = mapped_column(String(768), nullable=False)
    shared_as: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False, default=_now_ms)


class Recipient(Base):
    """A bearer-token identity that shares can be granted to.

    The bearer token is the *only* credential on the protocol surface
    (per the Delta Sharing spec's bearer-token profile), so soyuz
    never stores it: ``bearer_token_hash`` holds the SHA-256 hex
    digest and the plaintext is returned exactly once — in the
    create response and in each rotate-token response. A leaked
    database therefore does not leak usable tokens, the same
    threat-model line pre-signed URLs draw.

    This is deliberately narrower than Databricks' recipient model:
    no activation-link flow, no expiration windows, no IP access
    lists. All three are additive future fields; the MVP is the
    bearer-token profile the open protocol actually requires.
    """

    __tablename__ = "recipients"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    comment: Mapped[str | None] = mapped_column(String, nullable=True)
    owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bearer_token_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False, default=_now_ms)
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[int] = mapped_column(BigInteger, nullable=False, default=_now_ms)
    updated_by: Mapped[str | None] = mapped_column(String(255), nullable=True)


class ShareGrant(Base):
    """One share made visible to one recipient.

    The composite unique constraint makes the grant identity explicit
    and lets ``PUT`` operate idempotently — re-granting an existing
    pair is a no-op, same semantics as
    :class:`soyuz_catalog.models.Permission` rows. Both foreign keys
    are declared without ``ondelete="CASCADE"``; ``delete_share`` and
    ``delete_recipient`` cascade explicitly at the service layer,
    the project-wide policy.
    """

    __tablename__ = "share_grants"
    __table_args__ = (
        UniqueConstraint("share_id", "recipient_id", name="uq_share_grants_share_recipient"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    share_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("shares.id"),
        nullable=False,
        index=True,
    )
    recipient_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("recipients.id"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False, default=_now_ms)
