"""Semantic-layer resources: metric views (ADR-0014).

Over-the-spec extension: upstream UC OSS ``all.yaml`` defines no
semantic-layer surface at all, but Databricks ships metric views as
a first-class securable and BI-adjacent clients expect somewhere to
persist dimension/measure definitions. soyuz stores and validates
the *definition* only — compiling a metric view into SQL and
executing it is a query-engine concern that lives in the consumer,
the same boundary connections (ADR-0013) draw for federated query
execution.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import JSON, BigInteger, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from soyuz_catalog.models._base import Base, _new_id, _now_ms

if TYPE_CHECKING:
    from soyuz_catalog.models.catalog import Schema


class MetricView(Base):
    """A semantic-layer metric view definition under a schema.

    Metric views are an over-the-spec addition (ADR-0014). Each row
    stores a named bundle of dimensions and measures over one source
    table, addressed by the same three-part
    ``catalog.schema.metric_view`` full name tables use. soyuz
    persists and shape-validates the definition; it never parses the
    SQL expressions or executes the view — ``expr`` strings are
    opaque payload for the consumer's compiler.

    Structurally the row is a sibling of
    :class:`soyuz_catalog.models.Function`: uniqueness on
    ``(schema_id, name)``, denormalised ``catalog_id`` so list
    queries can filter on both parents without a join, and parent
    names reconstructed at response time from the live ``schema``
    relationship so a catalog or schema rename propagates for free.

    ``source_table_full_name`` is deliberately a *name*, not an
    opaque ``table_id``: the source table is a loose reference the
    consumer resolves at compile time, and a metric view may
    legitimately be authored before its source table is registered
    (the same way a SQL view body can reference a table that is
    created later). Renaming the source table therefore does *not*
    rewrite the stored reference — the consumer surfaces the broken
    reference at compile time, which is also where a typo'd source
    name would surface. See ADR-0014 for the trade-off discussion.

    ``spec`` is the validated JSON definition::

        {
          "dimensions": [{"name": ..., "expr": ..., "comment": ...}],
          "measures":   [{"name": ..., "expr": ..., "comment": ...}],
          "filter":     "optional opaque SQL predicate"
        }

    The pydantic layer guarantees at least one measure and the
    service layer guarantees dimension/measure names are unique
    across the combined set (the compiled view exposes them in one
    flat column namespace, so a dimension and a measure sharing a
    name would collide in the consumer's ``SELECT`` list).

    The foreign keys are declared without ``ondelete="CASCADE"`` —
    parent deletes cascade explicitly at the service layer
    (``delete_schema`` / ``delete_catalog`` with ``force=true``),
    same policy as every other child resource in this package.
    """

    __tablename__ = "metric_views"
    __table_args__ = (UniqueConstraint("schema_id", "name", name="uq_metric_views_schema_id_name"),)

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
    source_table_full_name: Mapped[str] = mapped_column(String(768), nullable=False)
    spec: Mapped[dict] = mapped_column(JSON, nullable=False)
    comment: Mapped[str | None] = mapped_column(String, nullable=True)
    owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False, default=_now_ms)
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[int] = mapped_column(BigInteger, nullable=False, default=_now_ms)
    updated_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    schema: Mapped[Schema] = relationship("Schema")
