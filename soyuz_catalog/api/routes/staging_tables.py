"""HTTP routes for the Staging Tables resource."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from soyuz_catalog.api.deps import get_db
from soyuz_catalog.api.schemas import CreateStagingTable, StagingTableInfo
from soyuz_catalog.models import StagingTable
from soyuz_catalog.services import staging_table_service

router = APIRouter(tags=["tables"])


def _to_info(row: StagingTable) -> StagingTableInfo:
    """Assemble a :class:`StagingTableInfo` response from an ORM row.

    ``catalog_name`` / ``schema_name`` are reconstructed from the live
    parent chain so that a rename of either parent propagates to the
    allocation's wire representation the same way it does for every
    other child resource in this project.

    Args:
        row: The staging-table ORM row. Its ``schema`` relationship
            must be loadable.

    Returns:
        StagingTableInfo: The wire-format response.
    """
    schema = row.schema
    return StagingTableInfo(
        name=row.name,
        catalog_name=schema.catalog.name,
        schema_name=schema.name,
        id=row.id,
        staging_location=row.staging_location,
    )


@router.post(
    "/staging-tables",
    response_model=StagingTableInfo,
    response_model_exclude_none=True,
    summary="Allocate staging table",
)
def create_staging_table(
    payload: CreateStagingTable,
    db: Session = Depends(get_db),
) -> StagingTableInfo:
    """Allocate a new staging table.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        StagingTableInfo: The allocated row.
    """
    row = staging_table_service.create_staging_table(db, payload)
    return _to_info(row)
