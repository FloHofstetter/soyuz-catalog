"""Lakehouse-Federation connection (ADR-0013).

Over-the-spec extension: upstream UC OSS ``all.yaml`` defines no
connection surface at all, but Databricks ships Lakehouse Federation
and soyuz mirrors the wire shape so clients that expect it have
somewhere to write. soyuz persists metadata only — it never proxies
queries to the foreign engine.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import JSON, BigInteger, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from soyuz_catalog.models._base import Base, _new_id, _now_ms

if TYPE_CHECKING:
    from soyuz_catalog.models.catalog import Catalog


class Connection(Base):
    """A Lakehouse-Federation connection (metastore-level, flat namespace).

    Connections are an over-the-spec addition (ADR-0013): upstream
    UC OSS ``all.yaml`` defines no connection surface at all,
    but Databricks ships Lakehouse Federation and soyuz mirrors the
    wire shape so clients that expect it — and users who want to model
    federated catalogs in their own tooling — have somewhere to write.
    soyuz persists the metadata only; it **never** proxies queries to
    the foreign engine, and federated query execution is explicitly
    out of scope (same boundary as credential vending).

    Structurally a connection is a sibling of
    :class:`soyuz_catalog.models.Credential`: a flat metastore-level
    resource with a plain unique index on ``name`` and a one-to-many
    relationship to the foreign catalogs that bind to it. A foreign
    catalog stores ``connection_id`` on its row and reconstructs
    ``connection_name`` at response time so a connection rename
    propagates for free — same rename-invariance trick
    :class:`soyuz_catalog.models.ExternalLocation` uses for
    ``credential_name``.

    ``connection_type`` is stored as a plain string rather than a
    database ``Enum`` so adding a new connector kind (the upstream
    ecosystem is long and grows between Databricks releases) never
    requires a schema migration. The wire shape pins a ``Literal``
    of the common set so typos still surface as 422 at the pydantic
    layer; the DB column is free-form so an eventual
    soyuz-side-only extension needs nothing more than a new literal
    value. ``options`` is a free-form ``dict[str, str]`` passthrough
    — soyuz has no query side, so validating per-connector options
    would be speculative divergence. Sensitive options (passwords,
    tokens) are stored in plaintext, same posture as credentials; a
    future secrets-integration sprint can retrofit encryption
    additively without touching wire shapes.

    ``read_only`` is a metadata flag round-tripped through the wire
    for shape parity with Databricks clients. soyuz never enforces it
    because there is no query path to gate — the flag is purely
    descriptive until a query engine layers on top.

    The foreign key from :class:`soyuz_catalog.models.Catalog` to this
    row is declared without ``ondelete="CASCADE"``.
    ``delete_connection`` cascades explicitly at the service layer
    when ``force=true`` (calling ``delete_catalog`` per referencing
    foreign catalog so grants and child resources are wiped through
    the normal cascade) and refuses the delete with 409 otherwise —
    same policy as every other resource in this module.
    """

    __tablename__ = "connections"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    connection_type: Mapped[str] = mapped_column(String(32), nullable=False)
    options: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False, default=dict)
    read_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    comment: Mapped[str | None] = mapped_column(String, nullable=True)
    owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False, default=_now_ms)
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[int] = mapped_column(BigInteger, nullable=False, default=_now_ms)
    updated_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    foreign_catalogs: Mapped[list[Catalog]] = relationship(
        "Catalog",
        back_populates="connection",
    )
