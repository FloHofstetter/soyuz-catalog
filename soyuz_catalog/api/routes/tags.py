"""HTTP routes for the Tags resource.

Two endpoints, registered as a genuine over-the-spec extension —
upstream Unity Catalog OSS has no tags at all, and ``all.yaml`` does not
define a tags API:

* ``GET /tags/{securable_type}/{full_name}`` — return the current tag set
  of a catalog / schema / table / column.
* ``PATCH /tags/{securable_type}/{full_name}`` — apply an additive batch
  of set/remove operations and return the post-change state.

These routes are deliberately *not* nested under the Unity Catalog
``/api/2.1/unity-catalog`` prefix because they do not exist in
``all.yaml``. Registering them at the root keeps the spec-conformance
test honest — see the explicit skip list in
``tests/test_openapi_conformance.py``. See ADR-0010 for the full
rationale and ``DIVERGENCES.md`` for the wire-format notes.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from soyuz_catalog.api.deps import get_db
from soyuz_catalog.api.schemas import TagList, TagSecurableType, UpdateTags
from soyuz_catalog.services import audit_service, tags_service

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get(
    "/{securable_type}/{full_name}",
    response_model=TagList,
    summary="Get tags for securable",
)
def get_tags(
    securable_type: TagSecurableType,
    full_name: str,
    db: Session = Depends(get_db),
) -> TagList:
    """Return the current tag set of a securable.

    The response shape is identical to the ``PATCH`` response so clients
    can reuse the same deserialiser. Tags are sorted by key, and an empty
    result returns ``{"tags": []}`` rather than 404 — the absence of tags
    is a valid state, not an error.

    Args:
        securable_type: One of ``catalog``, ``schema``, ``table``, ``column``.
            Narrower than the full UC ``SecurableType`` enum (MVP scope —
            see ADR-0010).
        full_name: Dotted address of the securable. 1 segment for catalog,
            2 for schema, 3 for table, 4 for column.
        db: Database session dependency.

    Returns:
        TagList: The current tag set, sorted by key.
    """
    return tags_service.list_tags(db, securable_type, full_name)


@router.patch(
    "/{securable_type}/{full_name}",
    response_model=TagList,
    summary="Update tags for securable",
)
def update_tags(
    securable_type: TagSecurableType,
    full_name: str,
    payload: UpdateTags,
    db: Session = Depends(get_db),
) -> TagList:
    """Apply an additive batch of set/remove changes to a securable's tags.

    The shape is not replace-style: the client submits set/remove
    operations and the service applies them transactionally. Overlapping
    operations within a single batch resolve as *set wins*
    (``remove key`` followed by ``set key`` ends with the key present) to
    keep multi-writer workflows safe. See
    :func:`soyuz_catalog.services.tags_service.update_tags` for the full
    semantics and ``DIVERGENCES.md`` for the over-the-spec notes.

    Args:
        securable_type: One of ``catalog``, ``schema``, ``table``, ``column``.
        full_name: Dotted address of the securable.
        payload: The batch of changes to apply.
        db: Database session dependency.

    Returns:
        TagList: The full post-change tag set, sorted by key.
    """
    result = tags_service.update_tags(db, securable_type, full_name, payload.changes)
    audit_service.log_action(
        db,
        action="tag.updated",
        target=f"{securable_type}:{full_name}",
        detail={"changes": [c.model_dump() for c in payload.changes]},
    )
    return result
