"""Three-level UC namespace + schema-scoped routines.

Holds the spec-canonical resource hierarchy:

* :class:`Catalog` — top-level namespace; binds to
  :class:`soyuz_catalog.models.Connection` for federated catalogs.
* :class:`Schema` — middle layer, per-catalog uniqueness.
* :class:`Table`, :class:`Volume`, :class:`Function` — innermost
  layer, per-schema uniqueness; addressed by 3-part ``full_name``.

The hierarchy uses string forward references for ``relationship()`` so
:class:`Catalog.connection` can point into
:mod:`soyuz_catalog.models.federation` without an import cycle.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from soyuz_catalog.models._base import Base, _new_id, _now_ms

if TYPE_CHECKING:
    from soyuz_catalog.models.column import Column
    from soyuz_catalog.models.federation import Connection


class Catalog(Base):
    """A Unity Catalog top-level catalog (namespace for schemas).

    Catalogs are the outermost layer of the UC three-level namespace
    (catalog → schema → table). The user-facing identifier is ``name``, which
    is unique and indexed because every REST endpoint addresses catalogs by
    name; ``id`` is an opaque UUID kept around so future endpoints (rename
    semantics, references from other resources) have a stable handle that
    survives a rename.

    ``properties`` is a non-nullable JSON column defaulting to ``{}`` rather
    than ``NULL``. The service layer treats absent properties as "explicitly
    empty", which keeps the PATCH-clears-properties bug fix (see
    ``DIVERGENCES.md``) symmetric: ``{}`` and "no properties" are the same
    state, not two.

    ``created_at`` / ``updated_at`` are stored as epoch milliseconds (int)
    rather than ``DateTime`` because the UC OpenAPI spec defines them as
    ``int64`` epoch milliseconds and we round-trip them verbatim through the
    JSON wire format with no timezone trickery.

    ``storage_location`` is the server-derived managed path under
    ``storage_root`` (example:
    ``s3://bucket/root/__unitystorage/catalogs/{id}``). It is computed
    once on ``create_catalog`` from ``storage_root`` plus the opaque
    ``id`` and never recomputed — a rename leaves it intact so that any
    child resource whose physical layout depends on it stays valid. If
    ``storage_root`` is ``None`` the derivation yields ``None`` as well.

    ``type`` (``MANAGED`` / ``FOREIGN``), ``connection_id``, and
    ``options`` back the Lakehouse-Federation variant (ADR-0013).
    A foreign catalog stores ``connection_id`` and leaves
    ``storage_root`` / ``storage_location`` ``None``; a managed catalog
    is the inverse. The column is modelled as a plain string rather
    than a database ``Enum`` so adding a third type upstream (or
    downstream) never needs a schema migration — same reasoning as
    :class:`soyuz_catalog.models.Credential` ``purpose``.
    ``connection_name`` is **not** a column: it is reconstructed at
    response time from the live :class:`Connection` row so a
    connection rename propagates without a fan-out UPDATE, the same
    rename-invariance trick :class:`soyuz_catalog.models.ExternalLocation`
    uses for ``credential_name``.
    """

    __tablename__ = "catalogs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    comment: Mapped[str | None] = mapped_column(String, nullable=True)
    properties: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False, default=dict)
    owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    storage_root: Mapped[str | None] = mapped_column(String, nullable=True)
    storage_location: Mapped[str | None] = mapped_column(String, nullable=True)
    type: Mapped[str] = mapped_column(String(16), nullable=False, default="MANAGED")
    connection_id: Mapped[str | None] = mapped_column(
        String(32),
        ForeignKey("connections.id"),
        nullable=True,
        index=True,
    )
    options: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False, default=_now_ms)
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[int] = mapped_column(BigInteger, nullable=False, default=_now_ms)
    updated_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    schemas: Mapped[list[Schema]] = relationship(
        "Schema",
        back_populates="catalog",
        cascade="all, delete-orphan",
        passive_deletes=False,
    )
    connection: Mapped[Connection | None] = relationship(
        "Connection",
        back_populates="foreign_catalogs",
    )

    @property
    def connection_name(self) -> str | None:
        """Reconstruct the bound connection's current name, if any.

        Returns ``None`` for managed catalogs (no connection binding)
        and for foreign catalogs whose relationship has been detached
        from the session. Reading off ``self.connection.name`` rather
        than a stored column is the rename-invariance trick — the
        wire field follows a connection rename for free.

        Returns:
            str | None: The live connection name, or ``None`` for
                managed catalogs.
        """
        return self.connection.name if self.connection is not None else None


class Schema(Base):
    """A Unity Catalog schema (middle layer of the three-level namespace).

    Schemas live inside a single catalog (the ``catalog_id`` foreign key) and
    carry their own ``name``, which is only unique *within* that catalog — two
    catalogs may each have a ``default`` schema. The user-facing identifier on
    every REST endpoint is the ``full_name`` ``"{catalog.name}.{schema.name}"``,
    but that string is *never* stored: it is reconstructed at response time
    from the live catalog name so that a catalog rename propagates to every
    schema under it without a fan-out UPDATE. This mirrors UC OSS
    ``SchemaRepository.convertFromDAO`` behaviour.

    The foreign key to ``catalogs.id`` is deliberately declared without
    ``ondelete="CASCADE"``. The service layer cascades explicitly when a
    ``DELETE /catalogs/{name}?force=true`` request arrives, which keeps the
    two soyuz behaviours (reject without ``force``, cascade with ``force``)
    on the Python side where they are easy to test — matching how UC OSS
    Java's ``CatalogRepository.deleteCatalog`` handles it.

    ``properties``, timestamps, and the system-field conventions match
    :class:`Catalog`; see that class for the rationale.
    """

    __tablename__ = "schemas"
    __table_args__ = (UniqueConstraint("catalog_id", "name", name="uq_schemas_catalog_id_name"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    catalog_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("catalogs.id"),
        nullable=False,
        index=True,
    )
    comment: Mapped[str | None] = mapped_column(String, nullable=True)
    properties: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False, default=dict)
    owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    storage_root: Mapped[str | None] = mapped_column(String, nullable=True)
    storage_location: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False, default=_now_ms)
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[int] = mapped_column(BigInteger, nullable=False, default=_now_ms)
    updated_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    catalog: Mapped[Catalog] = relationship("Catalog", back_populates="schemas")
    tables: Mapped[list[Table]] = relationship(
        "Table",
        back_populates="schema",
        cascade="all, delete-orphan",
        passive_deletes=False,
    )
    volumes: Mapped[list[Volume]] = relationship(
        "Volume",
        back_populates="schema",
        cascade="all, delete-orphan",
        passive_deletes=False,
    )


class Table(Base):
    """A Unity Catalog table (innermost layer of the three-level namespace).

    Tables live inside a single schema (the ``schema_id`` foreign key) and
    carry their own ``name``, which is only unique *within* that schema —
    two schemas may each own an ``events`` table. The user-facing identifier
    on every REST endpoint is the ``full_name``
    ``"{catalog.name}.{schema.name}.{table.name}"``; it is *never* stored
    but reconstructed at response time from the live parent names, so a
    rename propagates for free without a fan-out UPDATE (same strategy as
    :class:`Schema`).

    Both ``schema_id`` and ``catalog_id`` are stored as foreign keys even
    though ``catalog_id`` is derivable via ``schema.catalog_id``. The
    denormalisation pays for itself twice: (1) the list endpoint filters on
    both parents and would otherwise need a join on every call, and (2)
    future bulk operations (e.g. "drop every table in this catalog") are a
    single ``WHERE catalog_id = ?`` instead of a correlated subquery. The
    service layer is the sole writer and keeps the two columns consistent.

    Neither foreign key declares ``ondelete="CASCADE"``. Parent-delete
    cascading is handled explicitly by the service layer so the "reject
    without ``force``, cascade with ``force=true``" behaviour stays on the
    Python side where it is easy to test — same reasoning as :class:`Schema`.

    ``table_type`` and ``data_source_format`` are stored as plain strings
    validated by the Pydantic layer against the UC enum values, rather than
    SQL enums, because UC OSS occasionally extends these sets between minor
    versions and we do not want a database migration for a new enum member.
    """

    __tablename__ = "tables"
    __table_args__ = (UniqueConstraint("schema_id", "name", name="uq_tables_schema_id_name"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    schema_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("schemas.id"),
        nullable=False,
        index=True,
    )
    catalog_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("catalogs.id"),
        nullable=False,
        index=True,
    )
    table_type: Mapped[str] = mapped_column(String(32), nullable=False)
    data_source_format: Mapped[str] = mapped_column(String(32), nullable=False)
    storage_location: Mapped[str | None] = mapped_column(String, nullable=True)
    comment: Mapped[str | None] = mapped_column(String, nullable=True)
    properties: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False, default=dict)
    owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False, default=_now_ms)
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[int] = mapped_column(BigInteger, nullable=False, default=_now_ms)
    updated_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    columns: Mapped[list[Column]] = relationship(
        "Column",
        back_populates="table",
        cascade="all, delete-orphan",
        order_by="Column.position",
    )
    schema: Mapped[Schema] = relationship("Schema", back_populates="tables")


class Volume(Base):
    """A Unity Catalog volume (file-based asset under a schema).

    Volumes live alongside tables in the third level of the UC namespace
    (``catalog.schema.volume``). They wrap a free-form ``storage_location``
    with a ``volume_type`` of ``MANAGED`` or ``EXTERNAL`` — soyuz does not
    interpret the location string at this layer because credential vending
    is explicitly out of scope.

    The shape mirrors :class:`Table` deliberately: per-schema uniqueness on
    ``(schema_id, name)``, denormalised ``catalog_id`` so the list endpoint
    can filter on both parents without a join, ``full_name`` reconstructed
    at response time so a parent rename propagates without a fan-out
    UPDATE, and explicit service-layer cascade rather than a database
    ``ON DELETE CASCADE``.

    Unlike :class:`Catalog` and :class:`Schema`, a volume has **no
    ``properties``** column: the UC OpenAPI ``VolumeInfo`` does not define
    one, and adding one would silently extend the spec.
    """

    __tablename__ = "volumes"
    __table_args__ = (UniqueConstraint("schema_id", "name", name="uq_volumes_schema_id_name"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    schema_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("schemas.id"),
        nullable=False,
        index=True,
    )
    catalog_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("catalogs.id"),
        nullable=False,
        index=True,
    )
    volume_type: Mapped[str] = mapped_column(String(16), nullable=False)
    storage_location: Mapped[str | None] = mapped_column(String, nullable=True)
    comment: Mapped[str | None] = mapped_column(String, nullable=True)
    owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False, default=_now_ms)
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[int] = mapped_column(BigInteger, nullable=False, default=_now_ms)
    updated_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    schema: Mapped[Schema] = relationship("Schema", back_populates="volumes")


class Function(Base):
    """A Unity Catalog function (SQL/EXTERNAL routine, third-level namespace).

    Functions live alongside tables and volumes in the third level of the
    UC namespace (``catalog.schema.function``) and mirror :class:`Table`'s
    shape almost field-for-field on the bookkeeping columns: per-schema
    uniqueness on ``(schema_id, name)``, denormalised ``catalog_id`` so
    the list endpoint can filter on both parents without a join, and
    ``full_name`` reconstructed at response time from the live parent
    names so a rename of either parent propagates without a fan-out
    UPDATE.

    The function-specific payload is stored in three chunks:

    * **Scalar metadata** — ``data_type``, ``full_data_type``,
      ``routine_body`` (SQL/EXTERNAL), ``routine_definition`` (body
      string), ``parameter_style``, ``is_deterministic``,
      ``sql_data_access``, ``is_null_call``, ``security_type``,
      ``specific_name``, and optional ``external_language`` — are
      mirrored 1:1 from the UC OpenAPI ``FunctionInfo`` schema.
    * **Parameter lists** — ``input_params`` and ``return_params`` — are
      stored as ``JSON`` objects of the shape
      ``{"parameters": [...]}`` rather than as separate child rows. UC
      REST treats parameters as a read-only read-at-once blob (there is
      no ``/functions/{name}/parameters`` sub-resource and no PATCH
      route at all), so paying for a second table and the join it
      implies would be overhead for no benefit. UC OSS Java makes the
      same call.
    * **Routine dependencies** — optional ``JSON`` column holding a
      ``DependencyList`` object; stored as-is and round-tripped
      verbatim, soyuz performs no dependency validation.

    ``properties`` is a free-form string in the upstream spec (the docs
    say *"JSON-serialized key-value pair map, encoded (escaped) as a
    string"*), so it is stored as ``Text`` and passed through
    unchanged. This is the rare case where soyuz does **not** reject
    unknown keys: the field's contract is "server-opaque blob", and
    structurally validating it would silently extend the spec.

    Like :class:`Table`, functions have **no ``UpdateFunction`` route**
    in the UC REST spec and soyuz returns 405 on ``PATCH /functions/
    {full_name}``. The service module accordingly exposes only create /
    get / list / delete — see ``DIVERGENCES.md`` for the shared
    rationale with tables.
    """

    __tablename__ = "functions"
    __table_args__ = (UniqueConstraint("schema_id", "name", name="uq_functions_schema_id_name"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    schema_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("schemas.id"),
        nullable=False,
        index=True,
    )
    catalog_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("catalogs.id"),
        nullable=False,
        index=True,
    )
    data_type: Mapped[str] = mapped_column(String(64), nullable=False)
    full_data_type: Mapped[str] = mapped_column(String, nullable=False)
    input_params: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    return_params: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    routine_body: Mapped[str] = mapped_column(String(16), nullable=False)
    routine_definition: Mapped[str | None] = mapped_column(String, nullable=True)
    routine_dependencies: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    parameter_style: Mapped[str] = mapped_column(String(8), nullable=False)
    is_deterministic: Mapped[bool] = mapped_column(Boolean, nullable=False)
    sql_data_access: Mapped[str] = mapped_column(String(16), nullable=False)
    is_null_call: Mapped[bool] = mapped_column(Boolean, nullable=False)
    security_type: Mapped[str] = mapped_column(String(16), nullable=False)
    specific_name: Mapped[str] = mapped_column(String(255), nullable=False)
    external_language: Mapped[str | None] = mapped_column(String(64), nullable=True)
    comment: Mapped[str | None] = mapped_column(String, nullable=True)
    properties: Mapped[str | None] = mapped_column(String, nullable=True)
    owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False, default=_now_ms)
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[int] = mapped_column(BigInteger, nullable=False, default=_now_ms)
    updated_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    schema: Mapped[Schema] = relationship("Schema")
