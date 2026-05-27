"""HTTP routes for the Permissions (grants) resource.

Both endpoints are thin translations of their
:mod:`soyuz_catalog.services.permissions_service` counterparts. The
only work done at this layer is FastAPI-native: path-parameter typing
via the :data:`soyuz_catalog.api.schemas.SecurableType` ``Literal`` so
an unknown type is a 422 at routing time before any service code
runs, and the ``response_model_exclude_none`` flag on the response
model so an empty-grants response stays byte-identical to a real
empty state.

Grants are a storage-only resource in soyuz — the catalog server
never consults them on any other endpoint. See ADR-0005 for the
proxy-offload rationale.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from soyuz_catalog.api.deps import get_db
from soyuz_catalog.api.schemas import (
    PermissionsList,
    SecurableType,
    UpdatePermissions,
)
from soyuz_catalog.services import permissions_service

router = APIRouter(prefix="/permissions", tags=["permissions"])


@router.get(
    "/{securable_type}/{full_name}",
    response_model=PermissionsList,
    response_model_exclude_none=True,
    summary="Get permissions for securable",
)
def get_permissions(
    securable_type: SecurableType,
    full_name: str,
    principal: str | None = None,
    db: Session = Depends(get_db),
) -> PermissionsList:
    """Return the permission assignments on a securable.

    Args:
        securable_type: One of the nine UC ``SecurableType`` values.
            Typed as a ``Literal`` so unknown values surface as 422.
        full_name: Spec-shaped dotted address — 1 segment for
            catalog / credential / external location, 2 for schema,
            3 for table / volume / function / registered model, or
            the live metastore id for metastore.
        principal: Optional filter. When set, only that principal's
            grants appear in the response.
        db: Database session dependency.

    Returns:
        PermissionsList: The current grant state of the securable.
    """
    return permissions_service.get_permissions(db, securable_type, full_name, principal)


@router.patch(
    "/{securable_type}/{full_name}",
    response_model=PermissionsList,
    response_model_exclude_none=True,
    summary="Update permissions for securable",
)
def update_permissions(
    securable_type: SecurableType,
    full_name: str,
    payload: UpdatePermissions,
    db: Session = Depends(get_db),
) -> PermissionsList:
    """Apply a batch of add/remove changes to a securable's grants.

    Unlike the other PATCH routes in this project, the update shape
    is additive, not replace-style. The service layer validates
    every ``add`` against the per-type allow-set before any write
    and rolls back the whole batch if any single entry is invalid.

    Args:
        securable_type: One of the nine UC ``SecurableType`` values.
        full_name: Spec-shaped dotted address.
        payload: The ``UpdatePermissions`` body containing the
            ordered list of changes.
        db: Database session dependency.

    Returns:
        PermissionsList: The full post-change grant state.
    """
    return permissions_service.update_permissions(
        db,
        securable_type,
        full_name,
        payload.changes,
    )
