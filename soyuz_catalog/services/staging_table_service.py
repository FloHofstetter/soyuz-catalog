"""Business logic for the Staging Tables resource.

Staging tables are the experimental allocation half of the UC managed-
table creation protocol: a client POSTs the desired
``(catalog, schema, name)`` triple, the server returns an opaque id
plus a ``staging_location`` URL, and a later *promote* step (not
modelled in soyuz) turns the allocation into a real :class:`Table`.
soyuz implements the allocation half in isolation, because (a) the
upstream spec flags the feature as experimental, and (b) the promote
side would need the managed-table materialisation work that is
explicitly out of scope.

Two details worth calling out:

1. No per-schema uniqueness on ``(schema_id, name)``. Two POSTs for
   the same triple succeed with distinct ids and distinct
   ``staging_location`` URLs. This matches the upstream semantics
   ("a staging table is used to allocate storage") and lets a client
   retry safely without a 409.
2. The ``staging_location`` is derived from the parent schema's
   ``storage_location`` first, falling back to the catalog's
   ``storage_root``. Both being absent is a 400 — the spec is clear
   that a staging table's whole point is to hand back a URL, so
   refusing a request where we cannot produce one surfaces the
   configuration bug at allocation time instead of letting the
   client cache a ``None`` and crash later.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from soyuz_catalog.api.schemas import CreateStagingTable
from soyuz_catalog.exceptions import InvalidRequestError, NotFoundError
from soyuz_catalog.models import Catalog, Schema, StagingTable
from soyuz_catalog.storage import parse_storage_uri


def _get_schema_or_404(session: Session, catalog_name: str, schema_name: str) -> Schema:
    """Fetch the parent schema or raise ``NotFoundError``.

    Args:
        session: Active SQLAlchemy session.
        catalog_name: Name of the parent catalog.
        schema_name: Name of the parent schema, relative to its catalog.

    Returns:
        Schema: The matching schema row.

    Raises:
        NotFoundError: If either the catalog or the schema does not exist.
    """
    catalog = session.scalar(select(Catalog).where(Catalog.name == catalog_name))
    if catalog is None:
        raise NotFoundError(f"Catalog '{catalog_name}' does not exist")
    schema = session.scalar(
        select(Schema).where(
            Schema.catalog_id == catalog.id,
            Schema.name == schema_name,
        ),
    )
    if schema is None:
        raise NotFoundError(f"Schema '{catalog_name}.{schema_name}' does not exist")
    return schema


def _derive_staging_location(schema: Schema, name: str) -> str:
    """Derive the staging URL for a new allocation.

    Picks the parent schema's ``storage_location`` first — which is
    itself derived from the schema's own ``storage_root`` or the
    catalog's — and falls back to the catalog's bare ``storage_root``
    if the schema was created without one. A UUID-hex segment under
    ``__staging__/`` keeps two concurrent allocations under the same
    name from colliding on disk.

    The chosen root is re-validated through
    :func:`soyuz_catalog.storage.parse_storage_uri` even though the
    parent write paths already validated it, because (a) legacy rows
    may still have free-form values predating the write-path gate,
    and (b) a staging allocation that produced an unparseable URL
    would be a silent footgun.

    Args:
        schema: The parent schema row.
        name: The requested staging-table name, used as the last URL
            segment.

    Returns:
        str: The derived staging-location URL.

    Raises:
        InvalidRequestError: If neither the schema nor the catalog
            has a usable ``storage_location`` / ``storage_root``, or
            if the chosen root has an unsupported scheme.
    """
    root = schema.storage_location or schema.catalog.storage_root
    if root is None:
        raise InvalidRequestError(
            f"Cannot allocate staging table under schema "
            f"'{schema.catalog.name}.{schema.name}': neither the schema nor the "
            "parent catalog has a storage location configured",
        )
    parse_storage_uri(root)
    allocation = uuid.uuid4().hex
    return f"{root.rstrip('/')}/__staging__/{allocation}/{name}"


def get_staging_table_by_id(session: Session, staging_table_id: str) -> StagingTable:
    """Fetch a staging table by its opaque ``id``.

    Used by ``/temporary-table-credentials`` as a fallthrough after
    :func:`soyuz_catalog.services.table_service.get_table_by_id` misses.
    The upstream JVM ``UCSingleCatalog`` connector creates a staging
    table and then immediately vends credentials against that same id;
    this helper lets the credentials service resolve the row through
    the same code path as a real table without duplicating the query.

    Args:
        session: Active SQLAlchemy session.
        staging_table_id: Opaque staging-table id.

    Returns:
        StagingTable: The matching staging-table row.

    Raises:
        NotFoundError: If no staging table with that id exists.
    """
    row = session.scalar(select(StagingTable).where(StagingTable.id == staging_table_id))
    if row is None:
        raise NotFoundError(f"Staging table with id '{staging_table_id}' does not exist")
    return row


def create_staging_table(
    session: Session,
    payload: CreateStagingTable,
) -> StagingTable:
    """Allocate a new staging table under an existing schema.

    Args:
        session: Active SQLAlchemy session.
        payload: Validated create request.

    Returns:
        StagingTable: The newly created allocation row.

    Note:
        May propagate ``NotFoundError`` (if the parent catalog or
        schema does not exist) from :func:`_get_schema_or_404`, and
        ``InvalidRequestError`` (if the derived ``staging_location``
        cannot be computed) from :func:`_derive_staging_location`.
    """
    schema = _get_schema_or_404(session, payload.catalog_name, payload.schema_name)
    staging_location = _derive_staging_location(schema, payload.name)
    row = StagingTable(
        name=payload.name,
        schema_id=schema.id,
        catalog_id=schema.catalog_id,
        staging_location=staging_location,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row
