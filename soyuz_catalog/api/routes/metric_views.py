"""HTTP routes for the Metric Views resource.

Over-the-spec addition (ADR-0014). Upstream UC OSS ``all.yaml``
defines no semantic-layer surface, so the spec conformance subset
check in :mod:`tests.test_openapi_conformance` explicitly skips this
prefix — same posture as connections (ADR-0013), the other
catalog-hierarchy extension mounted under ``api_prefix``.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from soyuz_catalog.api.deps import get_db
from soyuz_catalog.api.schemas import (
    CreateMetricView,
    ListMetricViewsResponse,
    MetricViewInfo,
    MetricViewSpec,
    UpdateMetricView,
)
from soyuz_catalog.models import MetricView
from soyuz_catalog.services import audit_service, metric_view_service

router = APIRouter(prefix="/metric-views", tags=["metric-views"])


def _to_info(metric_view: MetricView) -> MetricViewInfo:
    """Assemble a :class:`MetricViewInfo` response from an ORM row.

    ``catalog_name``, ``schema_name``, and ``full_name`` are not
    columns on :class:`soyuz_catalog.models.MetricView` — they are
    computed from the live parent schema's (and the schema's parent
    catalog's) names so a rename of either parent propagates for
    free, the same trick the tables route uses.

    Args:
        metric_view: The metric view ORM row. Its ``schema``
            relationship must be loadable — the session that fetched
            it must still be active.

    Returns:
        MetricViewInfo: The wire-format response.
    """
    schema = metric_view.schema
    catalog_name = schema.catalog.name
    schema_name = schema.name
    return MetricViewInfo(
        name=metric_view.name,
        catalog_name=catalog_name,
        schema_name=schema_name,
        full_name=f"{catalog_name}.{schema_name}.{metric_view.name}",
        source_table_full_name=metric_view.source_table_full_name,
        spec=MetricViewSpec.model_validate(metric_view.spec),
        comment=metric_view.comment,
        owner=metric_view.owner,
        id=metric_view.id,
        created_at=metric_view.created_at,
        created_by=metric_view.created_by,
        updated_at=metric_view.updated_at,
        updated_by=metric_view.updated_by,
    )


@router.post(
    "",
    response_model=MetricViewInfo,
    response_model_exclude_none=True,
    summary="Create metric view",
)
def create_metric_view(
    payload: CreateMetricView,
    db: Session = Depends(get_db),
) -> MetricViewInfo:
    """Create a new metric view under an existing schema.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        MetricViewInfo: The created metric view.
    """
    metric_view = metric_view_service.create_metric_view(db, payload)
    audit_service.log_action(
        db,
        action="metric_view.created",
        target=f"{payload.catalog_name}.{payload.schema_name}.{payload.name}",
        detail={
            "metric_view_id": metric_view.id,
            "source_table_full_name": payload.source_table_full_name,
        },
    )
    return _to_info(metric_view)


@router.get(
    "",
    response_model=ListMetricViewsResponse,
    response_model_exclude_none=True,
    summary="List metric views",
)
def list_metric_views(
    catalog_name: str,
    schema_name: str,
    max_results: int | None = Query(default=None, ge=0, le=1000),
    page_token: str | None = None,
    db: Session = Depends(get_db),
) -> ListMetricViewsResponse:
    """List metric views under a schema with keyset pagination.

    Args:
        catalog_name: Required query parameter — name of the parent
            catalog.
        schema_name: Required query parameter — name of the parent
            schema, relative to its catalog.
        max_results: Page size hint, 1..1000. Defaults to 100 when
            omitted.
        page_token: Opaque cursor from a previous ``next_page_token``,
            or ``None`` for the first page.
        db: Database session dependency.

    Returns:
        ListMetricViewsResponse: One page of metric views under the
            schema plus the next page token (``None`` on the last
            page).
    """
    rows, next_token = metric_view_service.list_metric_views(
        db,
        catalog_name,
        schema_name,
        max_results,
        page_token,
    )
    return ListMetricViewsResponse(
        metric_views=[_to_info(r) for r in rows],
        next_page_token=next_token,
    )


@router.get(
    "/{full_name}",
    response_model=MetricViewInfo,
    response_model_exclude_none=True,
    summary="Get metric view by full name",
)
def get_metric_view(full_name: str, db: Session = Depends(get_db)) -> MetricViewInfo:
    """Fetch a single metric view by its three-part full name.

    Args:
        full_name: ``catalog.schema.metric_view`` path parameter.
        db: Database session dependency.

    Returns:
        MetricViewInfo: The requested metric view.
    """
    metric_view = metric_view_service.get_metric_view(db, full_name)
    return _to_info(metric_view)


@router.patch(
    "/{full_name}",
    response_model=MetricViewInfo,
    response_model_exclude_none=True,
    summary="Update metric view",
)
def update_metric_view(
    full_name: str,
    payload: UpdateMetricView,
    db: Session = Depends(get_db),
) -> MetricViewInfo:
    """Update an existing metric view.

    Args:
        full_name: Current ``catalog.schema.metric_view`` full name.
        payload: Patch body. Only fields explicitly present are
            applied; ``spec`` replaces the whole stored definition.
        db: Database session dependency.

    Returns:
        MetricViewInfo: The updated metric view.
    """
    metric_view = metric_view_service.update_metric_view(
        db,
        full_name,
        payload,
        set(payload.model_fields_set),
    )
    audit_service.log_action(
        db,
        action="metric_view.updated",
        target=full_name,
        detail={"changes": sorted(payload.model_fields_set)},
    )
    return _to_info(metric_view)


@router.delete("/{full_name}", summary="Delete metric view")
def delete_metric_view(full_name: str, db: Session = Depends(get_db)) -> dict[str, str]:
    """Delete a metric view.

    Args:
        full_name: ``catalog.schema.metric_view`` path parameter.
        db: Database session dependency.

    Returns:
        dict[str, str]: Empty success payload.
    """
    metric_view_service.delete_metric_view(db, full_name)
    audit_service.log_action(
        db,
        action="metric_view.deleted",
        target=full_name,
    )
    return {}
