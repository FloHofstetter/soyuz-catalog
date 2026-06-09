"""Business logic for the Tables resource."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from soyuz_catalog.api.schemas import ColumnInfo, CreateTable
from soyuz_catalog.db import commit_or_conflict
from soyuz_catalog.exceptions import InvalidRequestError, NotFoundError
from soyuz_catalog.models import Catalog, Column, Schema, Table, _now_ms
from soyuz_catalog.pagination import apply_keyset, build_next_token
from soyuz_catalog.services.permissions_service import wipe_permissions_for
from soyuz_catalog.storage import parse_storage_uri


def parse_full_name(full_name: str) -> tuple[str, str, str]:
    """Split a Unity Catalog table ``full_name`` into its three parts.

    The UC REST spec addresses tables by
    ``"{catalog_name}.{schema_name}.{table_name}"`` with two dot
    separators. Any other shape — missing dots, empty parts, extra dots —
    is a client bug and we surface it as 400 ``INVALID_ARGUMENT`` so the
    caller learns immediately rather than getting a confusing 404.

    Args:
        full_name: The ``catalog.schema.table`` path parameter.

    Returns:
        tuple[str, str, str]: ``(catalog_name, schema_name, table_name)``.

    Raises:
        InvalidRequestError: If ``full_name`` is not exactly three
            dot-separated non-empty parts.
    """
    parts = full_name.split(".")
    if len(parts) != 3 or not all(parts):
        raise InvalidRequestError(
            f"Table full_name '{full_name}' must be of the form "
            "'catalog_name.schema_name.table_name'",
        )
    return parts[0], parts[1], parts[2]


def _get_schema_or_404(session: Session, catalog_name: str, schema_name: str) -> Schema:
    """Fetch the parent schema or raise ``NotFoundError``.

    Resolves catalog → schema in two queries. Either miss is surfaced as
    404; we do not distinguish "no such catalog" from "no such schema
    inside that catalog" at the API layer because from the client's
    perspective the parent address is simply invalid.

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


def _resolve_column_positions(columns: list[ColumnInfo]) -> list[int]:
    """Resolve the ``position`` for every column of a create request.

    The UC spec marks ``ColumnInfo.position`` as optional, so a client may
    omit it entirely and rely on list order. Before this helper existed,
    omitted positions were inserted as ``NULL`` and explicit duplicates
    collided on ``UNIQUE(table_id, position)`` — both surfaced through the
    generic ``IntegrityError`` handler as a bogus 409 "already exists".
    Resolving and validating positions *before* the flush keeps that
    handler's 409 meaning exactly one thing: a duplicate table name.

    Mixed payloads (some columns with ``position``, some without) are
    rejected rather than back-filled because any gap-filling rule would
    silently reorder columns the client believed it had pinned.

    Args:
        columns: Validated column payloads, in request list order.

    Returns:
        list[int]: One position per column, parallel to ``columns``.

    Raises:
        InvalidRequestError: If positions mix explicit and omitted values,
            or if two columns carry the same explicit position.
    """
    explicit = [c.position for c in columns if c.position is not None]
    if not explicit:
        return list(range(len(columns)))
    if len(explicit) != len(columns):
        raise InvalidRequestError(
            "Either every column must specify 'position' or none may; "
            "got a mix of explicit and omitted positions",
        )
    if len(set(explicit)) != len(explicit):
        raise InvalidRequestError("Column 'position' values must be unique within a table")
    return explicit


def _column_from_payload(payload: ColumnInfo, position: int) -> Column:
    """Build a :class:`Column` ORM row from a :class:`ColumnInfo` payload.

    ``position`` is passed in pre-resolved by
    :func:`_resolve_column_positions` — verbatim from the payload when the
    client pinned it, auto-numbered from list order when the whole request
    omitted it. ``nullable`` defaults to ``True`` when the client omits it,
    matching the UC spec default for ``ColumnInfo.nullable``.

    Args:
        payload: Validated column info from the create request.
        position: Resolved ordinal position for this column.

    Returns:
        Column: The detached ORM row, ready to be appended to
            ``table.columns``.
    """
    return Column(
        name=payload.name,
        type_text=payload.type_text,
        type_json=payload.type_json,
        type_name=payload.type_name,
        type_precision=payload.type_precision,
        type_scale=payload.type_scale,
        type_interval_type=payload.type_interval_type,
        position=position,
        comment=payload.comment,
        nullable=payload.nullable if payload.nullable is not None else True,
        partition_index=payload.partition_index,
    )


def create_table(session: Session, payload: CreateTable) -> Table:
    """Insert a new table row with its columns under an existing schema.

    The parent schema is resolved by ``(catalog_name, schema_name)`` to
    its opaque ``id``, and ``catalog_id`` is denormalised onto the row
    from the resolved schema so list queries can filter on both parents
    without a join. Duplicate detection relies on the
    ``(schema_id, name)`` unique constraint plus ``IntegrityError``
    translation — same race-safety reasoning as
    :func:`soyuz_catalog.services.schema_service.create_schema`.

    ``storage_location`` is parsed by
    :func:`soyuz_catalog.storage.parse_storage_uri` before the row is
    built, so an unsupported scheme fails fast with
    ``400 INVALID_ARGUMENT`` instead of being accepted and silently
    breaking the first query — that laxness is the UC OSS Java
    behaviour we intentionally reject (see ``DIVERGENCES.md``).

    Column positions are resolved by :func:`_resolve_column_positions`
    before the flush: omitted everywhere means auto-numbered from list
    order, and invalid combinations fail with 400 instead of tripping
    the ``UNIQUE(table_id, position)`` constraint and masquerading as a
    duplicate-table 409.

    Args:
        session: Active SQLAlchemy session.
        payload: Validated create request.

    Returns:
        Table: The newly created table, with its columns attached.

    Raises:
        ConflictError: If a table with the same name already exists under
            that schema. (``NotFoundError`` may also propagate from
            :func:`_get_schema_or_404` when the parent catalog or schema
            does not exist, and ``InvalidRequestError`` from
            :func:`soyuz_catalog.storage.parse_storage_uri` when the
            ``storage_location`` scheme is unsupported or from
            :func:`_resolve_column_positions` when column positions are
            mixed or duplicated.)
    """
    schema = _get_schema_or_404(session, payload.catalog_name, payload.schema_name)
    parse_storage_uri(payload.storage_location)
    positions = _resolve_column_positions(payload.columns)
    table = Table(
        name=payload.name,
        schema_id=schema.id,
        catalog_id=schema.catalog_id,
        table_type=payload.table_type,
        data_source_format=payload.data_source_format,
        storage_location=payload.storage_location,
        comment=payload.comment,
        properties=payload.properties or {},
    )
    for col_payload, position in zip(payload.columns, positions, strict=True):
        table.columns.append(_column_from_payload(col_payload, position))
    session.add(table)
    with commit_or_conflict(
        session,
        f"Table '{payload.catalog_name}.{payload.schema_name}.{payload.name}' already exists",
    ):
        pass
    session.refresh(table)
    return table


def get_table(session: Session, full_name: str) -> Table:
    """Fetch a table by its ``catalog.schema.table`` full name.

    The lookup walks catalog → schema → table because table names are
    only unique per schema. A missing catalog, schema, or table all
    surface as 404 — the client's full_name address simply does not
    resolve to a real resource.

    Args:
        session: Active SQLAlchemy session.
        full_name: ``catalog_name.schema_name.table_name`` path parameter.

    Returns:
        Table: The matching table row.

    Raises:
        NotFoundError: If any of catalog, schema, or table is missing.
    """
    catalog_name, schema_name, table_name = parse_full_name(full_name)
    schema = _get_schema_or_404(session, catalog_name, schema_name)
    table = session.scalar(
        select(Table).where(
            Table.schema_id == schema.id,
            Table.name == table_name,
        ),
    )
    if table is None:
        raise NotFoundError(f"Table '{full_name}' does not exist")
    return table


def get_table_by_id(session: Session, table_id: str) -> Table:
    """Fetch a table by its opaque ``id`` rather than by full name.

    Used by endpoints that address a table by identity instead of by the
    catalog.schema.table path — primarily ``/temporary-table-credentials``,
    which is rename-safe by design and must not force clients to re-resolve
    the full name after every PATCH on a parent.

    Args:
        session: Active SQLAlchemy session.
        table_id: Opaque table identifier (the ``id`` column, not the
            ``full_name`` path).

    Returns:
        Table: The matching table row.

    Raises:
        NotFoundError: If no table with that id exists.
    """
    table = session.scalar(select(Table).where(Table.id == table_id))
    if table is None:
        raise NotFoundError(f"Table with id '{table_id}' does not exist")
    return table


def list_tables(
    session: Session,
    catalog_name: str,
    schema_name: str,
    max_results: int | None = None,
    page_token: str | None = None,
) -> tuple[list[Table], str | None]:
    """List tables under a schema with keyset pagination.

    Both ``catalog_name`` and ``schema_name`` are required by the UC
    spec — tables have no legitimate "list everything under this
    catalog" shape because a schema name is only meaningful inside
    its catalog. If the parent does not exist we surface 404 rather
    than an empty list so that typos in the query parameters are not
    silently masked. Ordering is ``(created_at ASC, id ASC)``.
    ``NotFoundError`` may propagate from :func:`_get_schema_or_404`,
    and ``InvalidRequestError`` from
    :func:`soyuz_catalog.pagination.apply_keyset` when
    ``max_results`` is out of range or ``page_token`` fails to
    decode.

    Args:
        session: Active SQLAlchemy session.
        catalog_name: Parent catalog name.
        schema_name: Parent schema name, relative to its catalog.
        max_results: Spec-defined page size hint. Defaults to 100,
            capped at 1000.
        page_token: Spec-defined opaque page token from a previous
            call, or ``None`` for the first page.

    Returns:
        tuple[list[Table], str | None]: One page of tables under the
            schema and the next page token (``None`` if last).
    """
    schema = _get_schema_or_404(session, catalog_name, schema_name)
    stmt, limit = apply_keyset(
        select(Table).where(Table.schema_id == schema.id),
        Table,
        page_token,
        max_results,
    )
    rows = list(session.scalars(stmt))
    return build_next_token(rows, limit)


def delete_table(session: Session, full_name: str, force: bool = False) -> None:
    """Delete a table and cascade through its columns.

    Columns are cascaded via the ORM relationship's ``cascade="all,
    delete-orphan"``, so ``session.delete(table)`` implicitly deletes the
    associated ``table_columns`` rows.

    ``force`` is accepted for spec and route-signature stability but is
    currently a no-op: tables have no child resources beyond columns,
    which always cascade unconditionally (a column has no independent
    existence).

    ``NotFoundError`` may propagate from :func:`get_table` when the table
    does not exist.

    Args:
        session: Active SQLAlchemy session.
        full_name: ``catalog_name.schema_name.table_name`` path parameter.
        force: Cascade flag — accepted but currently ignored.
    """
    del force
    table = get_table(session, full_name)
    wipe_permissions_for(session, [("table", table.id)])
    # ADR-0012: cascade declared constraints. Constraints on
    # *other* tables that reference this one as a FK parent stay and
    # render with the ``<deleted>`` sentinel on read — same append-only
    # history posture the lineage / tags orphans use.
    from soyuz_catalog.services.constraints_service import delete_constraints_for_table

    delete_constraints_for_table(session, table.id)
    session.delete(table)
    session.commit()


def rename_table(session: Session, full_name: str, new_name: str) -> Table:
    """Rename a table in place, preserving its opaque ``id``.

    The Delta REST Catalog API (ADR-0009) requires a
    POST ``/rename`` endpoint; the main UC REST spec has no rename
    for tables so this path is specific to the Delta surface. The
    implementation is deliberately tiny: look up by full_name,
    update the ``name`` column, bump ``updated_at``, and rely on
    the existing ``(schema_id, name)`` unique constraint to surface
    duplicate names as 409 ``ALREADY_EXISTS`` — no pre-check
    ``SELECT`` for a free race guard, consistent with every other
    write path in the project.

    The opaque ``id`` is untouched, so every downstream reference
    keyed on it — permissions, lineage edges, temporary-credential
    vending — stays valid automatically without a fan-out update.

    Args:
        session: Active SQLAlchemy session.
        full_name: Current ``catalog.schema.table`` full name.
        new_name: New leaf table name. Must be non-empty; the
            catalog and schema stay the same.

    Returns:
        Table: The updated table row, with the new ``name`` and the
            bumped ``updated_at``.

    Raises:
        InvalidRequestError: If ``new_name`` is empty.
        ConflictError: If a sibling table with ``new_name`` already
            exists under the same schema.
            ``NotFoundError`` may also propagate from
            :func:`get_table` when ``full_name`` does not resolve.
    """
    if not new_name:
        raise InvalidRequestError("new_name must be a non-empty string")

    table = get_table(session, full_name)
    table.name = new_name
    table.updated_at = _now_ms()
    with commit_or_conflict(
        session,
        f"Table '{new_name}' already exists under this schema",
    ):
        pass
    session.refresh(table)
    return table
