"""HTTP routes for the Metastore summary endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from soyuz_catalog.api.deps import get_db
from soyuz_catalog.api.schemas import GetMetastoreSummaryResponse
from soyuz_catalog.services import metastore_service

router = APIRouter(tags=["metastore"])


@router.get(
    "/metastore_summary",
    response_model=GetMetastoreSummaryResponse,
    response_model_exclude_none=True,
    summary="Get metastore summary",
)
def get_metastore_summary(
    db: Session = Depends(get_db),
) -> GetMetastoreSummaryResponse:
    """Return the metastore identity summary.

    The backing row is created lazily on the first call — see
    :func:`soyuz_catalog.services.metastore_service.get_metastore_summary`
    for the bootstrap rationale.

    Args:
        db: Database session dependency.

    Returns:
        GetMetastoreSummaryResponse: The singleton metastore identity.
    """
    row = metastore_service.get_metastore_summary(db)
    return GetMetastoreSummaryResponse(metastore_id=row.id)
