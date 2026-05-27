"""Polymorphic governance resources: permissions, tags, audit log.

All three classes store an opaque ``securable_id`` (or ``target``) that
points at the underlying resource's primary key by convention but
carries **no** foreign key — the target table varies per row and a
partial FK per resource would not buy anything the service-level
cascade does not already buy. Append-only rows survive a parent delete
as unreachable orphans; the opaque id is unique per creation so a new
resource with the same name cannot inherit them.

See:
- :class:`Permission` — ADR-0005 (auth-proxy storage backend)
- :class:`Tag` — ADR-0010 (over-the-spec tag extension)
- :class:`AuditLog` — append-only mutation log
"""

from __future__ import annotations

from sqlalchemy import BigInteger, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from soyuz_catalog.models._base import Base, _new_id, _now_ms


class Permission(Base):
    """A single grant atom binding a principal to a privilege on a securable.

    soyuz-catalog persists permissions as a storage backend for an
    auth proxy that performs the actual enforcement; the catalog
    server itself never checks grants on any other endpoint. See
    ADR-0005 and ``DIVERGENCES.md`` for the full rationale and the
    list of privileges considered valid per securable type.

    Each row is one ``(securable_type, securable_id, principal,
    privilege)`` tuple. The composite unique constraint makes the
    grant identity explicit and lets ``PATCH`` operate idempotently:
    re-adding an existing grant is a no-op, and removing a
    non-existent grant is a no-op, without any pre-check ``SELECT``.

    ``securable_id`` is the opaque row id from whichever resource
    table the ``securable_type`` resolves to, never the user-facing
    ``full_name``. That keeps the binding rename-invariant: renaming
    the parent catalog of a table leaves every grant on the table
    attached, without a fan-out ``UPDATE``. There is deliberately **no
    foreign key** from ``securable_id`` into any resource table,
    because the column's target varies by row and nine partial FKs
    plus an unchecked metastore row would not buy anything the
    service-level cascade does not already buy.

    The ``metastore`` securable type resolves to the singleton
    :class:`soyuz_catalog.models.Metastore` row's ``id`` via
    :func:`soyuz_catalog.services.metastore_service.get_metastore_summary`;
    the user-facing ``full_name`` in the URL is expected to equal
    that id exactly.
    """

    __tablename__ = "permissions"
    __table_args__ = (
        UniqueConstraint(
            "securable_type",
            "securable_id",
            "principal",
            "privilege",
            name="uq_permissions_type_id_principal_privilege",
        ),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    securable_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    securable_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    principal: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    privilege: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False, default=_now_ms)


class Tag(Base):
    """A key/value tag bound to a securable.

    Tags are a Databricks-only, over-the-spec extension (ADR-0010);
    upstream Unity Catalog OSS and ``all.yaml`` have no tag
    concept at all. Each row is one ``(securable_type, securable_id,
    key)`` tuple with an optional free-form ``value``. The composite
    unique constraint makes the set-semantics explicit: re-setting an
    existing key updates the row in place, and removing a missing key
    is a no-op, without any pre-check ``SELECT``.

    ``securable_id`` is the opaque row id of the resource (catalog /
    schema / table / column in the MVP), never the user-facing
    ``full_name``. Keying on the opaque id keeps tags rename-invariant:
    renaming any parent in the chain leaves every tag attached, the
    same trick :class:`Permission` and
    :class:`soyuz_catalog.models.LineageEdge` use. There is
    deliberately **no foreign key** — the column's target varies by
    ``securable_type``. Tags are append-only history in the same sense
    as :class:`soyuz_catalog.models.LineageEdge`: when the underlying
    resource is deleted the rows stay behind as unreachable orphans
    (the opaque id is unique per creation, so a new resource with the
    same name cannot inherit them). This matches the lineage posture
    and keeps the delete paths simple.

    MVP scope is catalog / schema / table / column; volume / function /
    registered model are additive future extensions because the column
    is just a 32-char hex. Columns are addressed in the REST surface
    as 4-part ``catalog.schema.table.column`` names and resolved to the
    opaque :class:`soyuz_catalog.models.Column` id by
    :mod:`soyuz_catalog.services.tags_service`.
    """

    __tablename__ = "tags"
    __table_args__ = (
        UniqueConstraint(
            "securable_type",
            "securable_id",
            "key",
            name="uq_tags_type_id_key",
        ),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    securable_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    securable_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    key: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False, default=_now_ms)
    updated_at: Mapped[int] = mapped_column(BigInteger, nullable=False, default=_now_ms)


class AuditLog(Base):
    """One mutation event recorded by the audit-log middleware.

    A client that forwards ``X-Agent-Run-Id`` on every call (the
    intended pattern for agent-driven traffic) lets the
    ``log_action`` helper persist that header into ``agent_run_id``,
    which the client can then use to join soyuz mutations back into
    its own per-run views.

    Append-only.  No FK to other tables — actions on later-deleted
    securables stay queryable.

    Attributes:
        id: Auto-incremented primary key.
        action: Dotted action name (``table.created`` /
            ``schema.deleted`` / ``tag.updated`` / …).
        target: Dotted FQN of the affected securable.
        principal: ``X-Principal`` header value (the human or
            service the agent acts on behalf of).  ``None`` when
            absent.
        agent_run_id: ``X-Agent-Run-Id`` header value (UUID-shape).
            Lets clients filter audit rows by the agent run that
            produced them.  ``None`` for non-agent traffic.
        client_ip: Best-effort source IP for ops correlation.
        detail: JSON-as-Text payload carrying action-specific
            metadata (e.g. set-tag key/value, before/after owner).
        created_at: Epoch milliseconds when the row was inserted.
    """

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    target: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    principal: Mapped[str | None] = mapped_column(String(255), nullable=True)
    agent_run_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    client_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False, default=_now_ms, index=True)
