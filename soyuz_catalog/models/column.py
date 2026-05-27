"""Table-level detail rows: columns and declared constraints.

Both classes are sub-resources of :class:`soyuz_catalog.models.Table`:
:class:`Column` is the in-spec per-column metadata row; declared
:class:`TableConstraint` rows (ADR-0012) are an over-the-spec extension
that mirrors Databricks' surface. Both use opaque ``table_id`` foreign
keys with no ``ON DELETE CASCADE`` so the service layer can keep its
cascade policy unified.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from soyuz_catalog.models._base import Base, _new_id, _now_ms

if TYPE_CHECKING:
    from soyuz_catalog.models.catalog import Table


class Column(Base):
    """A column belonging to a :class:`soyuz_catalog.models.Table`.

    Columns live in their own table rather than as a JSON blob on ``tables``
    because the UC REST spec treats each column as an addressable entity
    with its own precision/scale/nullable/position metadata, and later
    sprints will likely want per-column queries (partition index lookups,
    type evolution, comment edits). A separate row per column keeps those
    future operations index-friendly.

    The physical table name is ``table_columns`` rather than ``columns`` to
    avoid clashing with the reserved word on some SQL backends and with the
    ``information_schema.columns`` view on PostgreSQL.

    ``nullable`` defaults to ``True`` to match the UC OpenAPI spec's default
    for ``ColumnInfo.nullable``; ``position`` is taken verbatim from the
    request payload rather than being auto-numbered so that a client can
    round-trip a column list without the server silently renumbering it.
    """

    __tablename__ = "table_columns"
    __table_args__ = (
        UniqueConstraint("table_id", "position", name="uq_table_columns_table_id_position"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    table_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("tables.id"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type_text: Mapped[str] = mapped_column(String, nullable=False)
    type_json: Mapped[str] = mapped_column(String, nullable=False)
    type_name: Mapped[str] = mapped_column(String(32), nullable=False)
    type_precision: Mapped[int | None] = mapped_column(Integer, nullable=True)
    type_scale: Mapped[int | None] = mapped_column(Integer, nullable=True)
    type_interval_type: Mapped[str | None] = mapped_column(String, nullable=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(String, nullable=True)
    nullable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    partition_index: Mapped[int | None] = mapped_column(Integer, nullable=True)

    table: Mapped[Table] = relationship("Table", back_populates="columns")


class TableConstraint(Base):
    """A declared constraint on a :class:`soyuz_catalog.models.Table` (ADR-0012).

    Databricks-supported, UC OSS missing: ``PRIMARY KEY``, ``FOREIGN
    KEY``, ``CHECK``, and named ``NOT NULL`` constraints declared on
    tables. The feature is **metadata-only** — soyuz has no query
    engine and therefore does not enforce the declarations at write
    time; the value is interoperability with Spark / dbt / downstream
    catalog UIs that read declared constraints to display schema
    documentation or pick join strategies.

    Storage is a flat polymorphic-JSON table keyed on the opaque
    ``table_id`` of the parent. Same trick as
    :class:`soyuz_catalog.models.Permission` /
    :class:`soyuz_catalog.models.Tag` /
    :class:`soyuz_catalog.models.LineageEdge`: because the FK stores
    the opaque id and never the user-facing full name, renaming the
    parent (or any of *its* parents) leaves every declared constraint
    attached for free. The same applies to foreign keys, which store
    a second opaque id in ``definition`` pointing at the *referenced*
    table — rename either side and the declaration still round-trips.

    ``constraint_type`` is one of ``PRIMARY_KEY``, ``FOREIGN_KEY``,
    ``CHECK``, ``NOT_NULL``. The ``definition`` JSON shape varies by
    type (see :mod:`soyuz_catalog.services.constraints_service`):

    * ``PRIMARY_KEY``: ``{"child_columns": ["c0", "c1"]}``
    * ``FOREIGN_KEY``: ``{"child_columns": [...], "parent_table_id":
      "<opaque>", "parent_columns": [...]}``
    * ``CHECK``: ``{"child_columns": [...], "sql_text": "c0 > 0"}``
    * ``NOT_NULL``: ``{"child_column": "c0"}``

    The existing :class:`Column` ``nullable`` flag stays untouched
    and authoritative for the column's nullability; a named
    ``NOT_NULL`` constraint is a separate declared row that carries
    a user-chosen ``name``. Flipping ``Column.nullable`` as a side
    effect of adding / dropping the named constraint would reintroduce
    the silent-side-effects class that the "no table PATCH"
    invariant (Tables resource has no update endpoint in the UC spec)
    was designed to prevent.

    Unique constraint ``(table_id, name)`` — constraint names are
    unique per table but may be reused across tables. The table's
    ``id`` is the opaque 32-char hex, so a DROP-and-recreate of the
    parent yields a fresh namespace automatically.
    """

    __tablename__ = "table_constraints"
    __table_args__ = (
        UniqueConstraint(
            "table_id",
            "name",
            name="uq_table_constraints_table_id_name",
        ),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    table_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    constraint_type: Mapped[str] = mapped_column(String(16), nullable=False)
    definition: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False, default=_now_ms)
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
