"""Business logic for the External Locations resource."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from soyuz_catalog.api.schemas import CreateExternalLocation, UpdateExternalLocation
from soyuz_catalog.db import commit_or_conflict
from soyuz_catalog.exceptions import NotFoundError
from soyuz_catalog.models import ExternalLocation, _now_ms
from soyuz_catalog.pagination import apply_keyset, build_next_token
from soyuz_catalog.services import credential_service
from soyuz_catalog.services.permissions_service import wipe_permissions_for
from soyuz_catalog.storage import parse_storage_uri


def create_external_location(
    session: Session,
    payload: CreateExternalLocation,
) -> ExternalLocation:
    """Insert a new external location bound to a credential.

    The client supplies ``credential_name``; we resolve it to a
    persistent ``credential_id`` via
    :func:`credential_service.get_credential` (which raises 404 if the
    name does not resolve) and store the **id** on the row. A later
    credential rename then propagates to every bound external location
    for free at read time — the service layer reconstructs
    ``credential_name`` from the live credential relationship on
    response assembly, same rename-invariance trick used for
    catalog→schema→table ``full_name``.

    ``url`` is scheme-validated via
    :func:`soyuz_catalog.storage.parse_storage_uri` before the row is
    built — same write-path gate as ``storage_location`` on catalogs,
    schemas, tables, and volumes. Unsupported schemes surface as 400
    ``INVALID_ARGUMENT``.

    Duplicate detection relies on the ``name`` unique index plus
    ``IntegrityError`` translation rather than a pre-check ``SELECT``,
    which would race with concurrent inserts.

    Args:
        session: Active SQLAlchemy session.
        payload: Validated create request.

    Returns:
        ExternalLocation: The newly created row.

    Raises:
        ConflictError: If an external location with the same name
            already exists. (``NotFoundError`` may also propagate from
            :func:`credential_service.get_credential` when
            ``credential_name`` does not resolve, and
            ``InvalidRequestError`` from
            :func:`soyuz_catalog.storage.parse_storage_uri` when
            ``url`` uses an unsupported scheme.)
    """
    parse_storage_uri(payload.url)
    credential = credential_service.get_credential(session, payload.credential_name)
    location = ExternalLocation(
        name=payload.name,
        url=payload.url,
        credential_id=credential.id,
        comment=payload.comment,
    )
    session.add(location)
    with commit_or_conflict(
        session,
        f"External location '{payload.name}' already exists",
    ):
        pass
    session.refresh(location)
    return location


def get_external_location(session: Session, name: str) -> ExternalLocation:
    """Fetch an external location by name.

    Args:
        session: Active SQLAlchemy session.
        name: External location name.

    Returns:
        ExternalLocation: The matching row.

    Raises:
        NotFoundError: If no external location with the given name exists.
    """
    location = session.scalar(
        select(ExternalLocation).where(ExternalLocation.name == name),
    )
    if location is None:
        raise NotFoundError(f"External location '{name}' does not exist")
    return location


def list_external_locations(
    session: Session,
    max_results: int | None = None,
    page_token: str | None = None,
) -> tuple[list[ExternalLocation], str | None]:
    """List external locations with keyset pagination.

    Ordering is ``(created_at ASC, id ASC)`` via
    :func:`soyuz_catalog.pagination.apply_keyset`.
    ``InvalidRequestError`` may propagate from ``apply_keyset`` on
    malformed pagination parameters.

    Args:
        session: Active SQLAlchemy session.
        max_results: Spec-defined page size hint.
        page_token: Opaque pagination cursor.

    Returns:
        tuple[list[ExternalLocation], str | None]: One page of rows
            plus the next page token (``None`` if last).
    """
    stmt, limit = apply_keyset(
        select(ExternalLocation),
        ExternalLocation,
        page_token,
        max_results,
    )
    rows = list(session.scalars(stmt))
    return build_next_token(rows, limit)


def update_external_location(
    session: Session,
    name: str,
    payload: UpdateExternalLocation,
    fields_set: set[str],
) -> ExternalLocation:
    """Apply a PATCH to an external location.

    Replace-style semantics driven by ``fields_set``: any field
    explicitly present in the request body — including ``comment:
    null`` — is written through to the row; an empty body is a no-op
    (regression pin against UC OSS's 500 on the same shape).

    ``url`` is scheme-validated on every update where the field is
    present, not just on create: a client may legitimately re-anchor
    an external location at a different storage URL, but only to a
    scheme soyuz recognises. A rebind to ``credential_name`` resolves
    the new name to a ``credential_id`` (404 if the name does not
    resolve) and writes that id onto the row — the stored binding is
    the id, never the name.

    A rename collides on the ``name`` unique index and surfaces as 409.

    Args:
        session: Active SQLAlchemy session.
        name: Current external location name (path parameter).
        payload: Validated update request.
        fields_set: Names of fields explicitly present in the request body.

    Returns:
        ExternalLocation: The updated row.

    Raises:
        ConflictError: If ``new_name`` collides with an existing row.
    """
    location = get_external_location(session, name)

    if not fields_set:
        return location

    if "new_name" in fields_set and payload.new_name is not None:
        location.name = payload.new_name
    if "url" in fields_set and payload.url is not None:
        parse_storage_uri(payload.url)
        location.url = payload.url
    if "credential_name" in fields_set and payload.credential_name is not None:
        credential = credential_service.get_credential(session, payload.credential_name)
        location.credential_id = credential.id
    if "comment" in fields_set:
        location.comment = payload.comment
    if "owner" in fields_set:
        location.owner = payload.owner

    location.updated_at = _now_ms()

    with commit_or_conflict(
        session,
        f"External location rename to '{payload.new_name}' collides with an existing row",
    ):
        pass
    session.refresh(location)
    return location


def delete_external_location(session: Session, name: str) -> None:
    """Delete an external location.

    External locations have no child resources of their own, so there
    is no ``force`` cascade parameter — the spec does not define one
    for this delete endpoint. ``NotFoundError`` may propagate from
    :func:`get_external_location`.

    Args:
        session: Active SQLAlchemy session.
        name: External location name.
    """
    location = get_external_location(session, name)
    wipe_permissions_for(session, [("external_location", location.id)])
    session.delete(location)
    session.commit()
