"""Business logic for the Lakehouse-Federation Connections resource.

Over-the-spec addition (ADR-0013). Connections are a
metastore-level flat namespace — the sibling of
:class:`soyuz_catalog.models.Credential` in structure and in
lifecycle. Foreign catalogs bind to a connection by opaque
``connection_id`` so a connection rename propagates without a
fan-out UPDATE. soyuz persists the metadata only and never proxies
queries to the external engine; federated execution is a
query-engine concern, explicitly out of scope.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from soyuz_catalog.api.schemas import CreateConnection, UpdateConnection
from soyuz_catalog.db import commit_or_conflict
from soyuz_catalog.exceptions import ConflictError, NotFoundError
from soyuz_catalog.models import Catalog, Connection, _now_ms
from soyuz_catalog.pagination import apply_keyset, build_next_token
from soyuz_catalog.services.permissions_service import wipe_permissions_for


def create_connection(session: Session, payload: CreateConnection) -> Connection:
    """Insert a new federation connection row.

    Duplicate detection relies on the ``name`` unique index plus
    ``IntegrityError`` translation rather than a pre-check ``SELECT``,
    which would race with concurrent inserts — same pattern as every
    other ``create_*`` in the service layer. ``options`` is stored
    verbatim: soyuz has no query side and therefore no per-connector
    option validation, so a ``host`` for ``POSTGRESQL`` and a
    ``sfUrl`` for ``SNOWFLAKE`` both flow through untouched.
    ``read_only`` defaults to ``False`` when the client omits it and
    is stored on the row for wire-shape parity only — soyuz never
    enforces it because there is no query path to gate.

    Args:
        session: Active SQLAlchemy session.
        payload: Validated create request.

    Returns:
        Connection: The newly created connection row.

    Raises:
        ConflictError: If a connection with the same name already exists.
    """
    connection = Connection(
        name=payload.name,
        connection_type=payload.connection_type,
        options=dict(payload.options),
        read_only=payload.read_only or False,
        comment=payload.comment,
        owner=payload.owner,
    )
    session.add(connection)
    with commit_or_conflict(session, f"Connection '{payload.name}' already exists"):
        pass
    session.refresh(connection)
    return connection


def get_connection(session: Session, name: str) -> Connection:
    """Fetch a connection by name.

    The user-facing identifier is ``name``; the opaque ``id`` is
    stored only so :class:`soyuz_catalog.models.Catalog` can bind to
    a rename-stable handle via ``connection_id``.

    Args:
        session: Active SQLAlchemy session.
        name: Connection name.

    Returns:
        Connection: The matching row.

    Raises:
        NotFoundError: If no connection with the given name exists.
    """
    connection = session.scalar(select(Connection).where(Connection.name == name))
    if connection is None:
        raise NotFoundError(f"Connection '{name}' does not exist")
    return connection


def list_connections(
    session: Session,
    max_results: int | None = None,
    page_token: str | None = None,
) -> tuple[list[Connection], str | None]:
    """List connections with keyset pagination.

    Ordering is ``(created_at ASC, id ASC)`` via
    :func:`soyuz_catalog.pagination.apply_keyset` — same total order
    as every other list endpoint.

    Args:
        session: Active SQLAlchemy session.
        max_results: Spec-defined page size hint.
        page_token: Opaque pagination cursor.

    Returns:
        tuple[list[Connection], str | None]: One page of connections
            plus the next page token (``None`` if last).
    """
    stmt, limit = apply_keyset(select(Connection), Connection, page_token, max_results)
    rows = list(session.scalars(stmt))
    return build_next_token(rows, limit)


def update_connection(
    session: Session,
    name: str,
    payload: UpdateConnection,
    fields_set: set[str],
) -> Connection:
    """Apply a PATCH to a connection.

    Replace-style semantics driven by ``fields_set`` (from
    ``model_fields_set``): any field explicitly present is written
    through, an empty body is a no-op (regression pin against the UC
    OSS Java 500-on-empty-PATCH behaviour). ``options`` PATCH fully
    replaces the stored dict (same shape as ``catalog.properties``)
    because a per-key merge would have no predictable semantics in a
    stringly-typed connector config. ``connection_type`` is **not**
    a PATCH field at all (``UpdateConnection`` does not expose it) —
    flipping a live connection from Postgres to Snowflake would
    orphan every bound foreign catalog's options dict, so the type
    is frozen at create time.

    A rename collides on the ``name`` unique index and surfaces as 409.

    Args:
        session: Active SQLAlchemy session.
        name: Current connection name (path parameter).
        payload: Validated update request.
        fields_set: Names of fields explicitly present in the request body.

    Returns:
        Connection: The updated row.

    Raises:
        ConflictError: If ``new_name`` collides with an existing connection.
    """
    connection = get_connection(session, name)

    if not fields_set:
        return connection

    if "new_name" in fields_set and payload.new_name is not None:
        connection.name = payload.new_name
    if "options" in fields_set:
        connection.options = dict(payload.options or {})
    if "read_only" in fields_set and payload.read_only is not None:
        connection.read_only = payload.read_only
    if "comment" in fields_set:
        connection.comment = payload.comment
    if "owner" in fields_set:
        connection.owner = payload.owner

    connection.updated_at = _now_ms()

    with commit_or_conflict(
        session,
        f"Connection rename to '{payload.new_name}' collides with an existing connection",
    ):
        pass
    session.refresh(connection)
    return connection


def delete_connection(session: Session, name: str, force: bool = False) -> None:
    """Delete a connection.

    If one or more foreign catalogs still reference the connection
    and ``force`` is false, the delete is rejected with 409 — same
    shape as "cannot delete credential with external locations"
    and "cannot delete catalog with schemas".
    With ``force=true``, the service deletes every referencing
    foreign catalog via :func:`soyuz_catalog.services.catalog_service.delete_catalog`
    (which cascades through schemas → tables/volumes/functions/models
    and wipes permissions along the way) and then removes the
    connection row. The per-catalog delegation is deliberate: a bulk
    ORM delete would bypass the grants-cascade the catalog service
    owns, and re-implementing it here would duplicate logic that
    already exists one module over.

    Args:
        session: Active SQLAlchemy session.
        name: Connection name.
        force: When true, cascade-delete every referencing foreign
            catalog. When false, refuse the delete if any foreign
            catalog still binds to this connection.

    Raises:
        ConflictError: If referencing foreign catalogs exist and
            ``force`` is false.
    """
    # Local import avoids a circular dependency: catalog_service
    # imports this module's helpers transitively through the
    # foreign-catalog validation gates, so the import has to live
    # inside the function.
    from soyuz_catalog.services import catalog_service

    connection = get_connection(session, name)
    ref_count = session.scalar(
        select(func.count()).select_from(Catalog).where(Catalog.connection_id == connection.id),
    )
    if ref_count and not force:
        raise ConflictError(
            f"Cannot delete connection '{name}' because {ref_count} foreign "
            "catalog(s) still reference it. Pass force=true to cascade.",
        )
    if ref_count:
        # Snapshot the catalog names before the cascade deletes the
        # rows. Each cascade commits inside ``delete_catalog``, which
        # flushes our own pending state — so we cannot hold onto ORM
        # instances across the loop.
        catalog_names = list(
            session.scalars(
                select(Catalog.name).where(Catalog.connection_id == connection.id),
            ),
        )
        for catalog_name in catalog_names:
            catalog_service.delete_catalog(session, catalog_name, force=True)
    wipe_permissions_for(session, [("connection", connection.id)])
    session.delete(connection)
    session.commit()


def get_connection_by_id(session: Session, connection_id: str) -> Connection:
    """Fetch a connection by opaque ``id``.

    Used by :mod:`soyuz_catalog.services.catalog_service` when
    reconstructing ``connection_name`` on response assembly fails
    through the ORM relationship (e.g. a detached instance after a
    cascade), and by future resolvers that address connections by
    their stable id rather than the renameable ``name``.

    Args:
        session: Active SQLAlchemy session.
        connection_id: Opaque UUID-hex id.

    Returns:
        Connection: The matching row.

    Raises:
        NotFoundError: If no connection with the given id exists.
    """
    connection = session.get(Connection, connection_id)
    if connection is None:
        raise NotFoundError(f"Connection with id '{connection_id}' does not exist")
    return connection
