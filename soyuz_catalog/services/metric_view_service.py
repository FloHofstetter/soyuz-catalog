"""Business logic for the Metric Views resource (ADR-0014).

Over-the-spec addition: upstream UC OSS ``all.yaml`` defines no
semantic-layer surface, but Databricks ships metric views and
BI-adjacent clients expect somewhere to persist dimension/measure
definitions. soyuz stores and shape-validates the *definition* only;
compiling a metric view into SQL and executing it is the consumer's
job — the same metadata-only boundary connections (ADR-0013) draw
for federated query execution. ``expr`` strings are therefore opaque
payload here: a typo'd expression is the consumer compiler's error
to raise, not soyuz'.
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from soyuz_catalog.api.schemas import CreateMetricView, MetricViewSpec, UpdateMetricView
from soyuz_catalog.db import commit_or_conflict
from soyuz_catalog.exceptions import InvalidRequestError, NotFoundError
from soyuz_catalog.models import Catalog, MetricView, Schema, _now_ms
from soyuz_catalog.pagination import apply_keyset, build_next_token


def parse_full_name(full_name: str) -> tuple[str, str, str]:
    """Split a metric-view ``full_name`` into its three parts.

    Metric views are addressed by
    ``"{catalog_name}.{schema_name}.{metric_view_name}"`` with two dot
    separators, identical in shape to a table or function full name.
    Any other layout is surfaced as 400 ``INVALID_ARGUMENT`` so a
    client typo fails loudly instead of being routed to a surprising
    404.

    Args:
        full_name: The ``catalog.schema.metric_view`` path parameter.

    Returns:
        tuple[str, str, str]: ``(catalog_name, schema_name, name)``.

    Raises:
        InvalidRequestError: If ``full_name`` is not exactly three
            dot-separated non-empty parts.
    """
    parts = full_name.split(".")
    if len(parts) != 3 or not all(parts):
        raise InvalidRequestError(
            f"Metric view full_name '{full_name}' must be of the form "
            "'catalog_name.schema_name.metric_view_name'",
        )
    return parts[0], parts[1], parts[2]


def _get_schema_or_404(session: Session, catalog_name: str, schema_name: str) -> Schema:
    """Fetch the parent schema or raise ``NotFoundError``.

    Args:
        session: Active SQLAlchemy session.
        catalog_name: Name of the parent catalog.
        schema_name: Name of the parent schema, relative to its catalog.

    Returns:
        Schema: The matching schema row.

    Raises:
        NotFoundError: If either parent does not exist.
    """
    catalog = session.scalar(select(Catalog).where(Catalog.name == catalog_name))
    if catalog is None:
        raise NotFoundError(f"Catalog '{catalog_name}' does not exist")
    schema = session.scalar(
        select(Schema).where(
            Schema.catalog_id == catalog.id,
            Schema.name == schema_name,
        ),
    )
    if schema is None:
        raise NotFoundError(f"Schema '{catalog_name}.{schema_name}' does not exist")
    return schema


def _validate_spec(spec: MetricViewSpec) -> None:
    """Reject duplicate dimension/measure names across the combined set.

    The compiled view exposes dimensions and measures in one flat
    column namespace, so a dimension named ``revenue`` and a measure
    named ``revenue`` would collide in the consumer's ``SELECT`` list
    even though each list is individually well-formed. The check is
    semantic rather than structural, which is why it lives here as a
    400 ``INVALID_ARGUMENT`` instead of a pydantic 422 — same split
    every other service applies (see
    :class:`soyuz_catalog.exceptions.InvalidRequestError`).

    Args:
        spec: The validated spec payload.

    Raises:
        InvalidRequestError: If any name appears more than once across
            dimensions and measures combined.
    """
    seen: set[str] = set()
    for entry in [*spec.dimensions, *spec.measures]:
        if entry.name in seen:
            raise InvalidRequestError(
                f"Duplicate dimension/measure name '{entry.name}' in metric view "
                "spec; dimension and measure names share one flat namespace and "
                "must be unique",
            )
        seen.add(entry.name)


def _validate_source_table_name(source_table_full_name: str) -> None:
    """Reject source table references that are not three-part names.

    The reference itself is *not* resolved against the tables surface
    — see :func:`create_metric_view` — but a name that cannot ever
    resolve (wrong number of segments, empty segment) is a structural
    typo worth failing loudly on at write time.

    Args:
        source_table_full_name: The ``catalog.schema.table`` reference.

    Raises:
        InvalidRequestError: If the name is not exactly three
            dot-separated non-empty parts.
    """
    parts = source_table_full_name.split(".")
    if len(parts) != 3 or not all(parts):
        raise InvalidRequestError(
            f"source_table_full_name '{source_table_full_name}' must be of the "
            "form 'catalog_name.schema_name.table_name'",
        )


def create_metric_view(session: Session, payload: CreateMetricView) -> MetricView:
    """Insert a new metric view row under an existing schema.

    The parent schema is resolved by ``(catalog_name, schema_name)``
    to its opaque ``id``, with ``catalog_id`` denormalised onto the
    row — same shape as
    :func:`soyuz_catalog.services.function_service.create_function`.
    The ``source_table_full_name`` is shape-checked but deliberately
    *not* resolved: a metric view may be authored before its source
    table is registered, exactly like a SQL view body referencing a
    yet-to-be-created table. Duplicate detection relies on the
    ``(schema_id, name)`` unique constraint plus ``IntegrityError``
    translation rather than a pre-check ``SELECT``, which would race
    with concurrent inserts.

    Args:
        session: Active SQLAlchemy session.
        payload: Validated create request.

    Returns:
        MetricView: The newly created metric view row.

    Raises:
        ConflictError: If a metric view with the same name already
            exists under that schema. (``NotFoundError`` may propagate
            from :func:`_get_schema_or_404` and ``InvalidRequestError``
            from the spec / source-name validators.)
    """
    schema = _get_schema_or_404(session, payload.catalog_name, payload.schema_name)
    _validate_source_table_name(payload.source_table_full_name)
    _validate_spec(payload.spec)
    metric_view = MetricView(
        name=payload.name,
        schema_id=schema.id,
        catalog_id=schema.catalog_id,
        source_table_full_name=payload.source_table_full_name,
        spec=payload.spec.model_dump(exclude_none=True),
        comment=payload.comment,
        owner=payload.owner,
    )
    session.add(metric_view)
    with commit_or_conflict(
        session,
        f"Metric view '{payload.catalog_name}.{payload.schema_name}.{payload.name}' already exists",
    ):
        pass
    session.refresh(metric_view)
    return metric_view


def get_metric_view(session: Session, full_name: str) -> MetricView:
    """Fetch a metric view by its ``catalog.schema.name`` full name.

    The lookup walks catalog → schema → metric view because names are
    only unique per schema. A missing catalog, schema, or metric view
    all surface as 404 — the client's full_name address simply does
    not resolve to a real resource.

    Args:
        session: Active SQLAlchemy session.
        full_name: ``catalog.schema.metric_view`` path parameter.

    Returns:
        MetricView: The matching row.

    Raises:
        NotFoundError: If any of catalog, schema, or metric view is
            missing.
    """
    catalog_name, schema_name, name = parse_full_name(full_name)
    schema = _get_schema_or_404(session, catalog_name, schema_name)
    metric_view = session.scalar(
        select(MetricView).where(
            MetricView.schema_id == schema.id,
            MetricView.name == name,
        ),
    )
    if metric_view is None:
        raise NotFoundError(f"Metric view '{full_name}' does not exist")
    return metric_view


def list_metric_views(
    session: Session,
    catalog_name: str,
    schema_name: str,
    max_results: int | None = None,
    page_token: str | None = None,
) -> tuple[list[MetricView], str | None]:
    """List metric views under a schema with keyset pagination.

    The parent schema is resolved first so a bogus address surfaces
    as 404 rather than an empty page — same contract as
    :func:`soyuz_catalog.services.table_service.list_tables`.

    Args:
        session: Active SQLAlchemy session.
        catalog_name: Name of the parent catalog.
        schema_name: Name of the parent schema, relative to its catalog.
        max_results: Spec-defined page size hint.
        page_token: Opaque pagination cursor.

    Returns:
        tuple[list[MetricView], str | None]: One page of metric views
            plus the next page token (``None`` if last).

    Raises:
        NotFoundError: If the parent catalog or schema does not exist.
    """
    schema = _get_schema_or_404(session, catalog_name, schema_name)
    stmt, limit = apply_keyset(
        select(MetricView).where(MetricView.schema_id == schema.id),
        MetricView,
        page_token,
        max_results,
    )
    rows = list(session.scalars(stmt))
    return build_next_token(rows, limit)


def update_metric_view(
    session: Session,
    full_name: str,
    payload: UpdateMetricView,
    fields_set: set[str],
) -> MetricView:
    """Apply a PATCH to a metric view.

    Replace-style semantics driven by ``fields_set`` (from
    ``model_fields_set``): any field explicitly present is written
    through, and an empty body is a no-op. ``spec`` replaces the
    whole stored definition — a per-dimension merge would have no
    predictable semantics against an ordered list — and is re-run
    through the same duplicate-name gate as create. A rename collides
    on the ``(schema_id, name)`` unique constraint and surfaces as
    409.

    Args:
        session: Active SQLAlchemy session.
        full_name: Current ``catalog.schema.metric_view`` full name.
        payload: Validated update request.
        fields_set: Names of fields explicitly present in the request
            body.

    Returns:
        MetricView: The updated row.

    Raises:
        ConflictError: If ``new_name`` collides with an existing
            metric view under the same schema. (``NotFoundError`` may
            propagate from :func:`get_metric_view` and
            ``InvalidRequestError`` from the spec / source-name
            validators.)
    """
    metric_view = get_metric_view(session, full_name)

    if not fields_set:
        return metric_view

    if "new_name" in fields_set and payload.new_name is not None:
        metric_view.name = payload.new_name
    if "source_table_full_name" in fields_set and payload.source_table_full_name is not None:
        _validate_source_table_name(payload.source_table_full_name)
        metric_view.source_table_full_name = payload.source_table_full_name
    if "spec" in fields_set and payload.spec is not None:
        _validate_spec(payload.spec)
        metric_view.spec = payload.spec.model_dump(exclude_none=True)
    if "comment" in fields_set:
        metric_view.comment = payload.comment
    if "owner" in fields_set:
        metric_view.owner = payload.owner

    metric_view.updated_at = _now_ms()

    with commit_or_conflict(
        session,
        f"Metric view rename to '{payload.new_name}' collides with an existing "
        "metric view in the same schema",
    ):
        pass
    session.refresh(metric_view)
    return metric_view


def delete_metric_view(session: Session, full_name: str) -> None:
    """Delete a metric view.

    No ``force`` flag: metric views own no child resources, so there
    is nothing to gate — same single-step shape as ``delete_table``.
    The definition is the only state; dropping it cannot strand
    anything except consumers that referenced the view by name, and
    that breakage is visible at their next compile.

    Args:
        session: Active SQLAlchemy session.
        full_name: ``catalog.schema.metric_view`` path parameter.

    Raises:
        NotFoundError: Propagates from :func:`get_metric_view` when
            the full name does not resolve.
    """
    metric_view = get_metric_view(session, full_name)
    session.delete(metric_view)
    session.commit()


def delete_metric_views_for_schemas(session: Session, schema_ids: list[str]) -> None:
    """Bulk-delete every metric view under the given schemas.

    Cascade hook for ``delete_schema`` / ``delete_catalog`` with
    ``force=true`` — the parents' ORM cascades do not know about
    metric views (no back-populating relationship on
    :class:`soyuz_catalog.models.Schema`), so the parent services
    call this explicitly before removing the schema rows, the same
    pattern
    :func:`soyuz_catalog.services.constraints_service.delete_constraints_for_tables`
    uses. Deliberately does not commit: the caller owns the
    transaction so the cascade is atomic with the parent delete.

    Args:
        session: Active SQLAlchemy session.
        schema_ids: Opaque ``schemas.id`` values being cascaded.
    """
    if not schema_ids:
        return
    session.execute(delete(MetricView).where(MetricView.schema_id.in_(schema_ids)))
