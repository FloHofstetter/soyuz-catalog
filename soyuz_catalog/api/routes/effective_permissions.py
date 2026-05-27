"""HTTP route for the Effective Permissions resource.

One read-only endpoint at ``/effective-permissions/{securable_type}/{full_name}``
that returns the **inherited** grant set for a securable — the union of
every privilege granted to each principal on the leaf itself or any of
its ancestors in the ownership chain (``table → schema → catalog →
metastore``). This is a soyuz-specific over-the-spec extension: upstream
``all.yaml`` defines only the direct-grant form under ``/permissions``,
leaving chain-walking to clients. soyuz moves the computation
server-side so every client gets the same answer and the inheritance
rule is a single documented contract — see ``DIVERGENCES.md`` under
"Permissions: effective computation" and ADR-0005 for the broader
grants-as-storage-backend rationale.

The endpoint is mounted under the standard UC ``api_prefix`` (not at
the root like lineage or tags) because effective permissions is a
sibling operation to the existing permissions surface: a client
looking at ``/api/2.1/unity-catalog/permissions/...`` should find
``/api/2.1/unity-catalog/effective-permissions/...`` next to it. The
conformance-test skip lives in ``tests/test_openapi_conformance.py``
next to the Delta REST Catalog prefix skip.

There is deliberately **no PATCH**: the effective set is a view over
the underlying ``permissions`` table, not stored state. Writes go
through the existing ``PATCH /permissions/{type}/{name}`` route.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from soyuz_catalog.api.deps import get_db
from soyuz_catalog.api.schemas import PermissionsList, SecurableType
from soyuz_catalog.services import permissions_service

router = APIRouter(prefix="/effective-permissions", tags=["effective-permissions"])


@router.get(
    "/{securable_type}/{full_name}",
    response_model=PermissionsList,
    response_model_exclude_none=True,
    summary="Get effective permissions",
)
def get_effective_permissions(
    securable_type: SecurableType,
    full_name: str,
    principal: str | None = None,
    db: Session = Depends(get_db),
) -> PermissionsList:
    """Return the effective (inherited) grant set for a securable.

    The response shape is identical to ``GET /permissions/{type}/{name}``
    so clients can swap endpoints without changing their grant-display
    code. The difference is purely semantic: this endpoint unions
    grants across the full ownership chain, while the direct endpoint
    returns only grants bound to the leaf row.

    Args:
        securable_type: One of the nine UC ``SecurableType`` values.
            Typed as a ``Literal`` so unknown values surface as 422.
        full_name: Spec-shaped dotted address — 1 segment for
            catalog / credential / external location, 2 for schema,
            3 for table / volume / function / registered model, or
            the live metastore id for metastore.
        principal: Optional filter. When set, only that principal's
            inherited grant set appears in the response.
        db: Database session dependency.

    Returns:
        PermissionsList: The effective grant state, unioned across
            the leaf and all of its ancestors.
    """
    return permissions_service.get_effective_permissions(
        db,
        securable_type,
        full_name,
        principal,
    )
