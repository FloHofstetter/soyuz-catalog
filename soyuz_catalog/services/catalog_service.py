"""Business logic for the Catalogs resource."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from soyuz_catalog.api.schemas import CreateCatalog, UpdateCatalog
from soyuz_catalog.db import commit_or_conflict
from soyuz_catalog.exceptions import ConflictError, InvalidRequestError, NotFoundError
from soyuz_catalog.models import (
    Catalog,
    Connection,
    Function,
    RegisteredModel,
    Schema,
    Table,
    Volume,
    _now_ms,
)
from soyuz_catalog.pagination import apply_keyset, build_next_token
from soyuz_catalog.services.permissions_service import wipe_permissions_for
from soyuz_catalog.storage import derive_managed_location, parse_storage_uri


def create_catalog(session: Session, payload: CreateCatalog) -> Catalog:
    """Insert a new catalog row.

    The unique-name constraint is enforced at the database level rather than
    by a pre-check ``SELECT``: a pre-check would race with concurrent inserts,
    and the ``IntegrityError`` translation is the only way to be correct under
    contention. ``properties`` defaults to an empty dict instead of ``None``
    because every read path in the service layer treats absent properties as
    "explicitly empty" — keeping the column non-nullable simplifies the
    PATCH-clears-properties code path (see ``update_catalog``).

    ``storage_root`` is optional but, when present, is scheme-validated
    via :func:`soyuz_catalog.storage.parse_storage_uri` before the row
    is built — same write-path gate as schemas, tables, and volumes.

    ``storage_location`` is derived at create time from ``storage_root``
    plus the pre-generated opaque ``id`` via
    :func:`soyuz_catalog.storage.derive_managed_location` (yields
    ``None`` when ``storage_root`` is absent). The id is generated here
    rather than left to the SQLAlchemy column default so that the
    derivation has something to key on before the row hits the
    database. ``update_catalog`` deliberately leaves ``storage_location``
    alone — the whole point of keying the managed path on ``id`` is
    that a rename does *not* recompute it.

    Args:
        session: Active SQLAlchemy session.
        payload: Validated create request.

    Returns:
        Catalog: The newly created catalog.

    Raises:
        ConflictError: If a catalog with the same name already exists.
        InvalidRequestError: On an unsupported ``storage_root`` scheme
            (via :func:`soyuz_catalog.storage.parse_storage_uri`) or
            on a mixed managed/foreign shape — ``type=FOREIGN``
            without ``connection_name``, ``type=FOREIGN`` with
            ``storage_root``, or ``type=MANAGED`` with
            ``connection_name``. See ``DIVERGENCES.md``.
        NotFoundError: On ``type=FOREIGN`` with a ``connection_name``
            that does not resolve to an existing connection.
    """
    catalog_type = payload.type or "MANAGED"
    connection_id: str | None = None
    if catalog_type == "FOREIGN":
        # Foreign catalogs (ADR-0013) bind to a
        # :class:`soyuz_catalog.models.Connection` instead of owning a
        # managed storage root. The two shapes are mutually exclusive:
        # any attempt to mix them surfaces as 400 instead of silently
        # persisting a half-valid row. Resolving ``connection_name``
        # here (rather than in a pydantic validator) lets the 404 for
        # a missing connection flow through the existing
        # NotFoundError → 404 handler.
        if payload.connection_name is None:
            raise InvalidRequestError(
                "Foreign catalog requires connection_name",
            )
        if payload.storage_root is not None:
            raise InvalidRequestError(
                "Foreign catalog cannot declare storage_root",
            )
        connection = session.scalar(
            select(Connection).where(Connection.name == payload.connection_name),
        )
        if connection is None:
            raise NotFoundError(
                f"Connection '{payload.connection_name}' does not exist",
            )
        connection_id = connection.id
    else:
        if payload.connection_name is not None:
            raise InvalidRequestError(
                "Managed catalog cannot declare connection_name",
            )
        if payload.storage_root is not None:
            parse_storage_uri(payload.storage_root)
    catalog_id = uuid.uuid4().hex
    catalog = Catalog(
        id=catalog_id,
        name=payload.name,
        comment=payload.comment,
        properties=payload.properties or {},
        storage_root=payload.storage_root if catalog_type == "MANAGED" else None,
        storage_location=(
            derive_managed_location(payload.storage_root, "catalogs", catalog_id)
            if catalog_type == "MANAGED"
            else None
        ),
        type=catalog_type,
        connection_id=connection_id,
        options=dict(payload.options or {}),
    )
    session.add(catalog)
    with commit_or_conflict(session, f"Catalog '{payload.name}' already exists"):
        pass
    session.refresh(catalog)
    return catalog


def get_catalog(session: Session, name: str) -> Catalog:
    """Fetch a catalog by name.

    The lookup is by the user-facing ``name`` column rather than the opaque
    ``id``, because every Unity Catalog REST endpoint addresses catalogs by
    name and we never want a database round-trip just to translate one to the
    other. The unique index on ``name`` makes this an O(log n) point lookup.

    Args:
        session: Active SQLAlchemy session.
        name: Catalog name.

    Returns:
        Catalog: The matching catalog row.

    Raises:
        NotFoundError: If no catalog with the given name exists.
    """
    catalog = session.scalar(select(Catalog).where(Catalog.name == name))
    if catalog is None:
        raise NotFoundError(f"Catalog '{name}' does not exist")
    return catalog


def list_catalogs(
    session: Session,
    max_results: int | None = None,
    page_token: str | None = None,
) -> tuple[list[Catalog], str | None]:
    """List catalogs with keyset pagination.

    Ordering is ``(created_at ASC, id ASC)`` — insertion order, with
    the UUID ``id`` as the tiebreaker so the sort is a stable total
    order. This is a deliberate divergence from the name-sorted
    behaviour an earlier draft used; see ``DIVERGENCES.md`` for the
    rationale.

    ``InvalidRequestError`` may propagate from
    :func:`soyuz_catalog.pagination.apply_keyset` when ``max_results``
    is outside ``[1, 1000]`` or ``page_token`` fails to decode.

    Args:
        session: Active SQLAlchemy session.
        max_results: Spec-defined page size hint. Defaults to 100,
            capped at 1000.
        page_token: Spec-defined opaque page token from a previous
            call, or ``None`` for the first page.

    Returns:
        tuple[list[Catalog], str | None]: One page of catalogs and the
            next page token (``None`` if the page is the last one).
    """
    stmt, limit = apply_keyset(select(Catalog), Catalog, page_token, max_results)
    rows = list(session.scalars(stmt))
    return build_next_token(rows, limit)


def update_catalog(
    session: Session,
    name: str,
    payload: UpdateCatalog,
    fields_set: set[str],
) -> Catalog:
    """Apply a PATCH to a catalog.

    Replace-style semantics: any field present in ``fields_set`` is written to
    the row, including ``properties={}`` which clears all properties (the UC
    OSS Java implementation treats this as a no-op — see DIVERGENCES.md).
    Fields absent from ``fields_set`` are left untouched.

    Args:
        session: Active SQLAlchemy session.
        name: Current catalog name (path parameter).
        payload: Validated update request.
        fields_set: Names of fields explicitly present in the request body.
            Used to distinguish "field not sent" from "field sent with a
            null/empty value".

    Returns:
        Catalog: The updated catalog row.

    Raises:
        ConflictError: If ``new_name`` collides with an existing catalog.
        InvalidRequestError: On ``connection_name`` PATCH against a
            managed catalog (rebinding is legal on foreign catalogs
            only) or on ``connection_name: null`` — unbinding a
            foreign catalog is not a recoverable state.
        NotFoundError: From :func:`get_catalog` when the target
            catalog does not exist, or on a ``connection_name``
            PATCH whose new value does not resolve to an existing
            connection.
    """
    catalog = get_catalog(session, name)

    if not fields_set:
        return catalog

    if "new_name" in fields_set and payload.new_name is not None:
        catalog.name = payload.new_name
    if "comment" in fields_set:
        catalog.comment = payload.comment
    if "properties" in fields_set:
        catalog.properties = payload.properties or {}
    if "connection_name" in fields_set:
        # PATCH rebinding a connection is legal on foreign catalogs
        # only (swapping out the target of a Lakehouse Federation
        # binding is a metadata-only edit that does not touch any
        # managed storage). On a managed catalog it has no defined
        # meaning and surfaces as 400 instead of silently writing a
        # half-valid row. ``connection_name: null`` is rejected
        # symmetrically — unbinding a foreign catalog would leave
        # it in a state that no other endpoint can recover.
        if catalog.type != "FOREIGN":
            raise InvalidRequestError(
                "Cannot set connection_name on a managed catalog",
            )
        if payload.connection_name is None:
            raise InvalidRequestError(
                "Foreign catalog requires connection_name",
            )
        connection = session.scalar(
            select(Connection).where(Connection.name == payload.connection_name),
        )
        if connection is None:
            raise NotFoundError(
                f"Connection '{payload.connection_name}' does not exist",
            )
        catalog.connection_id = connection.id
    if "options" in fields_set:
        catalog.options = dict(payload.options or {})

    catalog.updated_at = _now_ms()

    with commit_or_conflict(session, f"Catalog '{payload.new_name}' already exists"):
        pass
    session.refresh(catalog)
    return catalog


def delete_catalog(session: Session, name: str, force: bool = False) -> None:
    """Delete a catalog.

    If the catalog has child schemas and ``force`` is false, the delete is
    rejected with :class:`ConflictError` (HTTP 409, ``FAILED_PRECONDITION``).
    With ``force=true``, every child schema is deleted first and the catalog
    row is removed afterwards. The cascade is explicit in the service layer
    rather than a database ``ON DELETE CASCADE`` so that the two behaviours
    can be exercised from tests without relying on dialect-specific trigger
    semantics, matching how UC OSS Java's ``CatalogRepository.deleteCatalog``
    handles it.

    Args:
        session: Active SQLAlchemy session.
        name: Catalog name.
        force: When true, cascade-delete all child schemas (and anything
            under them). When false, refuse the delete if any schemas exist.

    Raises:
        ConflictError: If the catalog still has schemas and ``force`` is
            false.
    """
    catalog = get_catalog(session, name)
    child_count = session.scalar(
        select(func.count()).select_from(Schema).where(Schema.catalog_id == catalog.id),
    )
    if child_count and not force:
        raise ConflictError(
            f"Cannot delete catalog '{name}' because it still has schemas. "
            "Pass force=true to cascade.",
        )
    # Grants-cascade: collect the full descendant set before the
    # ORM ``session.delete`` cascade wipes the rows they reference,
    # then bulk-wipe every (type, id) pair in one transaction. The
    # ``permissions`` table has no FK into any resource table (see
    # :class:`soyuz_catalog.models.Permission` for why), so the
    # cascade is entirely service-owned.
    pairs: list[tuple[str, str]] = [("catalog", catalog.id)]
    schema_ids = list(
        session.scalars(select(Schema.id).where(Schema.catalog_id == catalog.id)),
    )
    pairs.extend(("schema", sid) for sid in schema_ids)
    table_ids: list[str] = []
    for model_cls, label in (
        (Table, "table"),
        (Volume, "volume"),
        (Function, "function"),
        (RegisteredModel, "registered_model"),
    ):
        ids = list(
            session.scalars(
                select(model_cls.id).where(model_cls.catalog_id == catalog.id),
            ),
        )
        if label == "table":
            table_ids = ids
        pairs.extend((label, rid) for rid in ids)
    wipe_permissions_for(session, pairs)
    # Declared-constraints cascade (ADR-0012): see
    # ``delete_schema`` — the subtree cascade must clean up constraint
    # rows the same way ``delete_table`` does.
    from soyuz_catalog.services.constraints_service import delete_constraints_for_tables

    delete_constraints_for_tables(session, table_ids)
    session.delete(catalog)
    session.commit()
