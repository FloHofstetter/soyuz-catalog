"""HTTP routes for lineage ingestion and traversal.

Three endpoints, registered as a genuine over-the-spec extension —
upstream Unity Catalog OSS has no lineage at all (see ADR-0008):

* ``POST /lineage/v1/events`` — OpenLineage event sink. Accepts any
  ``RunEvent``-shaped body and upserts the run + edge rows that
  :mod:`soyuz_catalog.services.lineage_service` derives from it.
* ``GET /lineage/upstream/{full_name}`` — walk backward from a table
  to the tables that fed it, bounded by ``?depth=N``.
* ``GET /lineage/downstream/{full_name}`` — mirror: walk forward to
  the tables that consume this one.

These routes are deliberately *not* nested under the Unity Catalog
``/api/2.1/unity-catalog`` prefix because they do not exist in
``all.yaml``. Registering them at the root keeps the OpenLineage
endpoint URL shape matching the OpenLineage ecosystem's conventions
and keeps the spec-conformance test honest — see the explicit skip
list in ``tests/test_openapi_conformance.py``.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from soyuz_catalog.api.deps import get_db
from soyuz_catalog.api.schemas import (
    LineageGraphResponse,
    LineageIngestResponse,
    OpenLineageEvent,
)
from soyuz_catalog.services import lineage_service

router = APIRouter(prefix="/lineage", tags=["lineage"])


@router.post(
    "/v1/events",
    response_model=LineageIngestResponse,
    status_code=201,
    summary="Ingest OpenLineage event",
)
def ingest_lineage_event(
    event: OpenLineageEvent,
    db: Session = Depends(get_db),
) -> LineageIngestResponse:
    """Ingest one OpenLineage ``RunEvent``.

    The body is validated permissively — OpenLineage facets evolve
    independently of soyuz and the endpoint must not crash producers
    when a new field ships. The service layer extracts the small set
    of fields soyuz actually stores (run id, job name, event time,
    input + output dataset names) and leaves everything else on the
    wire.

    Dataset names that do not resolve to a soyuz table are silently
    dropped and counted in the response — OpenLineage producers
    routinely emit events for tables outside UC and a 400 would make
    soyuz unusable as a drop-in sink.

    Args:
        event: The OpenLineage ``RunEvent`` body.
        db: Database session dependency.

    Returns:
        LineageIngestResponse: ``run_id``, current ``state``, number
            of edges actually inserted on this call, and number of
            dataset references that did not resolve.
    """
    return lineage_service.ingest_event(db, event)


@router.get(
    "/upstream/{full_name}",
    response_model=LineageGraphResponse,
    summary="Traverse upstream lineage",
)
def get_upstream(
    full_name: str,
    depth: int = 3,
    db: Session = Depends(get_db),
) -> LineageGraphResponse:
    """Walk the lineage graph backward from a table.

    Returns every securable that fed ``full_name`` up to ``depth``
    hops away, together with the edges traversed. The root table
    appears as a depth-0 node even when it has no recorded lineage
    so clients can render "no upstream lineage" as a single-node
    graph rather than an error.

    Args:
        full_name: ``catalog.schema.table`` dotted address.
        depth: Maximum number of hops. Must be in
            ``[0, lineage_service.MAX_DEPTH]``; requests beyond the
            cap return 400.
        db: Database session dependency.

    Returns:
        LineageGraphResponse: The reachable subgraph.
    """
    return lineage_service.traverse(db, full_name, "upstream", depth)


@router.get(
    "/downstream/{full_name}",
    response_model=LineageGraphResponse,
    summary="Traverse downstream lineage",
)
def get_downstream(
    full_name: str,
    depth: int = 3,
    db: Session = Depends(get_db),
) -> LineageGraphResponse:
    """Walk the lineage graph forward from a table.

    Mirror of :func:`get_upstream`: returns every securable that the
    table feeds, up to ``depth`` hops. Same cap and same single-node
    shape for tables with no recorded downstream lineage.

    Args:
        full_name: ``catalog.schema.table`` dotted address.
        depth: Maximum number of hops.
        db: Database session dependency.

    Returns:
        LineageGraphResponse: The reachable subgraph.
    """
    return lineage_service.traverse(db, full_name, "downstream", depth)
