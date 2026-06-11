"""HTTP routes for the Delta Sharing Shares management resource.

Over-the-spec addition (ADR-0015). Upstream UC OSS ``all.yaml``
defines no sharing surface, so the spec conformance subset check in
:mod:`tests.test_openapi_conformance` explicitly skips this prefix —
same posture as connections (ADR-0013) and metric views (ADR-0014).

These management routes carry no authentication (the project-wide
auth-proxy posture, ADR-0005). The recipient-facing *protocol*
routes under ``/delta-sharing/`` are the deliberate exception — see
:mod:`soyuz_catalog.api.routes.delta_sharing`.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from soyuz_catalog.api.deps import get_db
from soyuz_catalog.api.schemas import (
    AddShareObject,
    CreateShare,
    ListSharesResponse,
    ShareInfo,
    ShareObjectInfo,
    UpdateShare,
)
from soyuz_catalog.models import Share
from soyuz_catalog.services import audit_service, sharing_service

router = APIRouter(prefix="/shares", tags=["shares"])


def _to_info(share: Share, db: Session) -> ShareInfo:
    """Assemble a :class:`ShareInfo` response from an ORM row.

    ``objects`` is always inlined — a share object is one table
    reference, so even a large share stays a small payload, and the
    protocol surface (not this one) is what recipients poll.

    Args:
        share: The share ORM row.
        db: Active SQLAlchemy session, used to fetch the object rows.

    Returns:
        ShareInfo: The wire-format response.
    """
    objects = sharing_service.list_share_objects(db, share.id)
    return ShareInfo(
        name=share.name,
        id=share.id,
        comment=share.comment,
        owner=share.owner,
        objects=[
            ShareObjectInfo(
                table_full_name=o.table_full_name,
                shared_as=o.shared_as,
                added_at=o.created_at,
            )
            for o in objects
        ],
        created_at=share.created_at,
        created_by=share.created_by,
        updated_at=share.updated_at,
        updated_by=share.updated_by,
    )


@router.post(
    "",
    response_model=ShareInfo,
    response_model_exclude_none=True,
    summary="Create share",
)
def create_share(payload: CreateShare, db: Session = Depends(get_db)) -> ShareInfo:
    """Create a new, empty share.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        ShareInfo: The created share.
    """
    share = sharing_service.create_share(db, payload)
    audit_service.log_action(
        db,
        action="share.created",
        target=payload.name,
        detail={"share_id": share.id},
    )
    return _to_info(share, db)


@router.get(
    "",
    response_model=ListSharesResponse,
    response_model_exclude_none=True,
    summary="List shares",
)
def list_shares(
    max_results: int | None = Query(default=None, ge=0, le=1000),
    page_token: str | None = None,
    db: Session = Depends(get_db),
) -> ListSharesResponse:
    """List shares with keyset pagination.

    Args:
        max_results: Page size hint, 1..1000.
        page_token: Opaque cursor from a previous ``next_page_token``.
        db: Database session dependency.

    Returns:
        ListSharesResponse: One page of shares plus the next page
            token (``None`` on the last page).
    """
    rows, next_token = sharing_service.list_shares(
        db,
        max_results=max_results,
        page_token=page_token,
    )
    return ListSharesResponse(
        shares=[_to_info(r, db) for r in rows],
        next_page_token=next_token,
    )


@router.get(
    "/{name}",
    response_model=ShareInfo,
    response_model_exclude_none=True,
    summary="Get share by name",
)
def get_share(name: str, db: Session = Depends(get_db)) -> ShareInfo:
    """Fetch a single share, objects inlined.

    Args:
        name: Share name.
        db: Database session dependency.

    Returns:
        ShareInfo: The requested share.
    """
    share = sharing_service.get_share(db, name)
    return _to_info(share, db)


@router.patch(
    "/{name}",
    response_model=ShareInfo,
    response_model_exclude_none=True,
    summary="Update share",
)
def update_share(
    name: str,
    payload: UpdateShare,
    db: Session = Depends(get_db),
) -> ShareInfo:
    """Update an existing share's name, comment, or owner.

    Args:
        name: Current share name.
        payload: Patch body. Only fields explicitly present are
            applied; object membership has its own endpoints.
        db: Database session dependency.

    Returns:
        ShareInfo: The updated share.
    """
    share = sharing_service.update_share(db, name, payload, set(payload.model_fields_set))
    audit_service.log_action(
        db,
        action="share.updated",
        target=name,
        detail={"changes": sorted(payload.model_fields_set)},
    )
    return _to_info(share, db)


@router.delete("/{name}", summary="Delete share")
def delete_share(name: str, db: Session = Depends(get_db)) -> dict[str, str]:
    """Delete a share together with its objects and grants.

    Args:
        name: Share name.
        db: Database session dependency.

    Returns:
        dict[str, str]: Empty success payload.
    """
    sharing_service.delete_share(db, name)
    audit_service.log_action(db, action="share.deleted", target=name)
    return {}


@router.post(
    "/{name}/objects",
    response_model=ShareInfo,
    response_model_exclude_none=True,
    summary="Add table to share",
)
def add_share_object(
    name: str,
    payload: AddShareObject,
    db: Session = Depends(get_db),
) -> ShareInfo:
    """Place an existing table inside a share.

    Args:
        name: Share name.
        payload: The table reference and optional ``shared_as`` alias.
        db: Database session dependency.

    Returns:
        ShareInfo: The share with its post-add object list.
    """
    sharing_service.add_share_object(db, name, payload)
    audit_service.log_action(
        db,
        action="share.object_added",
        target=name,
        detail={
            "table_full_name": payload.table_full_name,
            "shared_as": payload.shared_as,
        },
    )
    return _to_info(sharing_service.get_share(db, name), db)


@router.delete(
    "/{name}/objects",
    response_model=ShareInfo,
    response_model_exclude_none=True,
    summary="Remove table from share",
)
def remove_share_object(
    name: str,
    table_full_name: str,
    db: Session = Depends(get_db),
) -> ShareInfo:
    """Remove a table from a share.

    Args:
        name: Share name.
        table_full_name: Required query parameter — the stored
            three-part name of the table to remove (not the
            ``shared_as`` alias).
        db: Database session dependency.

    Returns:
        ShareInfo: The share with its post-remove object list.
    """
    sharing_service.remove_share_object(db, name, table_full_name)
    audit_service.log_action(
        db,
        action="share.object_removed",
        target=name,
        detail={"table_full_name": table_full_name},
    )
    return _to_info(sharing_service.get_share(db, name), db)


@router.put("/{name}/recipients/{recipient_name}", summary="Grant share to recipient")
def grant_share(
    name: str,
    recipient_name: str,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Make a share visible to a recipient (idempotent).

    Args:
        name: Share name.
        recipient_name: Recipient name.
        db: Database session dependency.

    Returns:
        dict[str, str]: Empty success payload.
    """
    sharing_service.grant_share(db, name, recipient_name)
    audit_service.log_action(
        db,
        action="share.granted",
        target=name,
        detail={"recipient": recipient_name},
    )
    return {}


@router.delete("/{name}/recipients/{recipient_name}", summary="Revoke share from recipient")
def revoke_share(
    name: str,
    recipient_name: str,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Remove a recipient's visibility of a share.

    Args:
        name: Share name.
        recipient_name: Recipient name.
        db: Database session dependency.

    Returns:
        dict[str, str]: Empty success payload.
    """
    sharing_service.revoke_share(db, name, recipient_name)
    audit_service.log_action(
        db,
        action="share.revoked",
        target=name,
        detail={"recipient": recipient_name},
    )
    return {}
