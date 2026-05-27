"""Translation layer between the Delta REST Catalog API and soyuz state.

ADR-0009 adds a secondary REST surface defined in
``unitycatalog/api/delta.yaml``. Every endpoint in that surface
operates on the **existing** soyuz ``tables`` / ``staging_tables``
rows via the existing services — no new database schema, no
migration. This module is the thin adapter that translates between
Delta's native wire shapes (``DeltaColumn``, ``DeltaProtocol``,
``TableMetadata``) and soyuz' ``Column`` / ``Table`` ORM models.

Public entry points are one per Delta endpoint:

* :func:`build_config` — ``GET /v1/config`` response body.
* :func:`load_table_response` — ``GET .../tables/{table}`` and the
  response after a successful ``createTable`` / ``updateTable``.
* :func:`create_delta_table` — ``POST .../tables``.
* :func:`update_delta_table` — ``POST .../tables/{table}``.
* :func:`list_delta_tables` — ``GET .../tables``.
* :func:`rename_delta_table` — ``POST .../tables/{table}/rename``.
* :func:`delete_delta_table` — ``DELETE .../tables/{table}``.
* :func:`table_exists` — ``HEAD .../tables/{table}``.
* :func:`create_delta_staging_table` — ``POST .../staging-tables``.

The credential and ``reportMetrics`` endpoints are thin enough that
the route layer handles them directly without touching this module.

Design notes (see ADR-0009 for the full rationale):

* Column round-tripping: soyuz' :class:`Column.type_json` is already
  a JSON payload and is the source of truth for the Delta wire form.
  On create/update we store whatever the client sent as the
  ``type`` field verbatim inside ``type_json``; on load we parse
  it back out. ``type_text`` and ``type_name`` are derived for
  debugging/display only.
* ``etag`` is synthesised from ``Table.updated_at`` — any mutation
  bumps the timestamp and therefore invalidates a stale etag.
* ``DeltaProtocol`` is a fixed default on every response; soyuz
  does not track per-table protocol versions and the create/update
  paths accept-and-discard the client's protocol.
* ``set-protocol`` / ``set-domain-metadata`` / ``remove-domain-metadata``
  updates are accept-and-discard no-ops. ``add-commit`` /
  ``set-latest-backfilled-version`` /
  ``update-metadata-snapshot-version`` updates are rejected 501 per
  ADR-0006.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from soyuz_catalog.api import delta_schemas as ds
from soyuz_catalog.api.delta_schemas import (
    CatalogConfig,
    CreateStagingTableRequest,
    CreateTableRequest,
    DeltaColumn,
    DeltaListTablesResponse,
    LoadTableResponse,
    RenameTableRequest,
    StagingTableResponse,
    TableMetadata,
    UpdateTableRequest,
)
from soyuz_catalog.api.schemas import ColumnInfo, CreateTable
from soyuz_catalog.exceptions import (
    CommitCoordinatorUnsupportedError,
    ConflictError,
    InvalidRequestError,
)
from soyuz_catalog.models import Column, Table
from soyuz_catalog.services import constraints_service, staging_table_service, table_service

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from soyuz_catalog.models import StagingTable


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


# Fixed Delta protocol soyuz advertises on every load response and
# on every staging-table allocation. soyuz does not track per-table
# protocol versions; the baseline ``(1, 2)`` pair matches the
# minimum required for a Delta table that supports
# ``appendOnly``, ``invariants``, and ``checkConstraints``, which
# is what the UC OSS reference server publishes. See ADR-0009.
_DEFAULT_PROTOCOL = ds.DeltaProtocol(
    **{
        "min-reader-version": 1,
        "min-writer-version": 2,
        "reader-features": [],
        "writer-features": [],
    },
)


# The path list returned by ``/v1/config``. Ordering matches the
# upstream ``delta.yaml`` example block so a diff against upstream
# is easy to eyeball; no client is supposed to rely on order.
_CONFIG_ENDPOINTS: list[str] = [
    "POST /v1/catalogs/{catalog}/schemas/{schema}/staging-tables",
    "POST /v1/catalogs/{catalog}/schemas/{schema}/tables",
    "GET /v1/catalogs/{catalog}/schemas/{schema}/tables",
    "GET /v1/catalogs/{catalog}/schemas/{schema}/tables/{table}",
    "POST /v1/catalogs/{catalog}/schemas/{schema}/tables/{table}",
    "DELETE /v1/catalogs/{catalog}/schemas/{schema}/tables/{table}",
    "HEAD /v1/catalogs/{catalog}/schemas/{schema}/tables/{table}",
    "POST /v1/catalogs/{catalog}/schemas/{schema}/tables/{table}/rename",
    "GET /v1/catalogs/{catalog}/schemas/{schema}/tables/{table}/credentials",
    "POST /v1/catalogs/{catalog}/schemas/{schema}/tables/{table}/metrics",
    "GET /v1/staging-tables/{table_id}/credentials",
    "GET /v1/temporary-path-credentials",
]


# ---------------------------------------------------------------------------
# Column translation
# ---------------------------------------------------------------------------


def _delta_type_to_text_and_name(type_value: str | dict[str, object]) -> tuple[str, str]:
    """Derive ``type_text`` and ``type_name`` from a Delta ``type`` value.

    The Delta wire ``type`` field is either a primitive string
    (``"long"``, ``"decimal(10,2)"``) or a complex-type object whose
    own ``type`` field discriminates the variant (``array``, ``map``,
    ``struct``). soyuz stores the full value in ``Column.type_json``
    and keeps ``type_text`` / ``type_name`` as lightweight derived
    summaries for debugging and display — they are not authoritative.

    Args:
        type_value: The ``type`` field as it appeared in the
            incoming :class:`DeltaColumn`. Either a primitive
            string or a complex-type dict.

    Returns:
        tuple[str, str]: ``(type_text, type_name)``. For primitives
            both values equal the string (with ``type_name`` upper
            cased). For complex types ``type_text`` is the compact
            JSON form and ``type_name`` is the outer discriminator
            tag upper-cased (``STRUCT``, ``ARRAY``, ``MAP``).
    """
    if isinstance(type_value, str):
        return type_value, type_value.upper()
    outer = str(type_value.get("type", "STRUCT"))
    return json.dumps(type_value, sort_keys=True), outer.upper()


def _delta_column_to_orm(
    column: DeltaColumn,
    position: int,
    partition_index: int | None,
) -> Column:
    """Build an ORM :class:`Column` row from a :class:`DeltaColumn`.

    The full :class:`DeltaColumn` payload — ``type`` and
    ``metadata`` — is encoded as JSON and stored in ``type_json``
    so a subsequent :func:`_orm_column_to_delta` reads out exactly
    what the client sent. ``name``, ``nullable``, ``position``, and
    ``partition_index`` are lifted onto dedicated soyuz columns so
    list/filter queries still work without decoding JSON.

    Args:
        column: The :class:`DeltaColumn` from the request body.
        position: Index in the ``columns`` array, used for column
            ordering in response reconstruction.
        partition_index: ``None`` if the column is not a partition
            column; otherwise the index of its name in the
            ``partition-columns`` array.

    Returns:
        Column: A fresh, unattached ORM row ready to be attached
            to a :class:`Table` via the ``columns`` relationship.
    """
    type_text, type_name = _delta_type_to_text_and_name(column.type)
    payload = {"type": column.type, "metadata": column.metadata}
    return Column(
        name=column.name,
        type_text=type_text,
        type_json=json.dumps(payload, sort_keys=True),
        type_name=type_name,
        position=position,
        nullable=column.nullable,
        partition_index=partition_index,
    )


def _orm_column_to_delta(column: Column) -> DeltaColumn:
    """Rebuild a :class:`DeltaColumn` from a stored ORM row.

    Reads the JSON payload stored on ``type_json`` back out and
    returns a :class:`DeltaColumn` whose ``type`` and ``metadata``
    are byte-identical to what the client originally sent. Rows
    written through the main UC API (which uses soyuz'
    :class:`ColumnInfo`, not :class:`DeltaColumn`) have a
    ``type_json`` that is a bare type object; for those we wrap the
    value in the ``{"type": ..., "metadata": {}}`` envelope the
    Delta wire expects, so a table created through one surface and
    read through the other still produces a valid Delta response.

    Args:
        column: The ORM column row.

    Returns:
        DeltaColumn: The reconstructed Delta wire column.
    """
    raw = column.type_json or "null"
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = None

    if isinstance(parsed, dict) and "type" in parsed and "metadata" in parsed:
        delta_type = parsed["type"]
        metadata = parsed["metadata"] or {}
    else:
        # Main-UC-API path: ``type_json`` holds just the type
        # payload, or is entirely unparseable (fall back to the
        # lexical type_text so the response is at least valid).
        delta_type = parsed if parsed is not None else (column.type_text or "string")
        metadata = {}

    return ds.DeltaColumn(
        name=column.name,
        type=delta_type,
        nullable=column.nullable,
        metadata=metadata,
    )


# ---------------------------------------------------------------------------
# Etag / table-uuid helpers
# ---------------------------------------------------------------------------


def _compute_etag(table: Table) -> str:
    """Synthesise an etag for optimistic concurrency.

    The Delta REST API uses :class:`AssertEtag` to reject updates
    that race against a concurrent mutation. soyuz does not have a
    dedicated etag column; instead, every mutation bumps
    ``Table.updated_at`` and the stringified value is the etag.
    This is lossy only across a clock rewind, which would break
    every epoch-ms-keyed system in the project equally, so it is
    not a meaningful concern.

    Args:
        table: The table row.

    Returns:
        str: An etag value to return on the wire.
    """
    return str(table.updated_at)


def _build_metadata(table: Table) -> TableMetadata:
    """Construct the :class:`TableMetadata` block for a load response.

    Reads the full ORM state and produces the Delta wire shape:
    columns reconstructed from live rows, partition-columns derived
    from ``Column.partition_index``, fixed :class:`DeltaProtocol`,
    synthesised etag, and ``securable_type = "TABLE"`` (soyuz has no
    views). ``location`` defaults to the empty string when the
    table has no registered ``storage_location`` — the spec
    requires the field, and an empty string is the only sane
    fallback that does not surface as a silent ``None`` on the
    wire.

    Args:
        table: The table row (must have its ``columns`` relationship
            loadable on the active session).

    Returns:
        TableMetadata: The wire-format metadata block.
    """
    columns_sorted = sorted(table.columns, key=lambda c: c.position)
    delta_columns = [_orm_column_to_delta(c) for c in columns_sorted]
    partition_columns = [
        c.name
        for c in sorted(
            (c for c in table.columns if c.partition_index is not None),
            key=lambda c: c.partition_index or 0,
        )
    ]
    return ds.TableMetadata(
        **{
            "etag": _compute_etag(table),
            "data-source-format": table.data_source_format,
            "table-type": table.table_type,
            "table-uuid": table.id,
            "location": table.storage_location or "",
            "created-time": table.created_at,
            "updated-time": table.updated_at,
            "securable-type": "TABLE",
            "columns": delta_columns,
            "partition-columns": partition_columns,
            "protocol": _DEFAULT_PROTOCOL,
            "properties": dict(table.properties or {}),
        },
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_config() -> CatalogConfig:
    """Build the ``GET /v1/config`` response body.

    Returns the fixed list of Delta REST Catalog endpoints soyuz
    implements and the single supported protocol version ``1.0``.
    The ``catalog`` and ``protocol-versions`` query parameters
    accepted by the route are validated at the route layer but do
    not branch behaviour — soyuz has exactly one implementation.

    Returns:
        CatalogConfig: A fresh config response (cheap; no state).
    """
    return ds.CatalogConfig(
        **{
            "endpoints": list(_CONFIG_ENDPOINTS),
            "protocol-version": "1.0",
        },
    )


def _full_name(catalog: str, schema: str, table: str) -> str:
    """Assemble a three-part soyuz full_name from Delta path parts.

    The Delta REST API routes each segment as a separate path
    parameter (``/catalogs/{c}/schemas/{s}/tables/{t}``) whereas
    the main UC API uses a single dotted ``{full_name}``. This
    helper bridges the two so existing services that accept
    ``catalog.schema.table`` keep working unchanged.

    Args:
        catalog: Catalog segment.
        schema: Schema segment.
        table: Table segment.

    Returns:
        str: ``"catalog.schema.table"``.
    """
    return f"{catalog}.{schema}.{table}"


def load_table_response(
    session: Session,
    catalog: str,
    schema: str,
    table: str,
) -> LoadTableResponse:
    """Build a :class:`LoadTableResponse` for a single table.

    Looks up the table via the existing main-UC service layer and
    rebuilds the Delta wire shape through :func:`_build_metadata`.
    ``commits`` is always empty because soyuz is not a Delta
    commit coordinator (ADR-0006); ``uniform`` and
    ``latest_table_version`` are always omitted for the same
    reason.

    Args:
        session: Active SQLAlchemy session.
        catalog: Catalog path segment.
        schema: Schema path segment.
        table: Table path segment.

    ``NotFoundError`` may propagate from
    :func:`table_service.get_table` when any segment of the address
    does not resolve.

    Returns:
        LoadTableResponse: The full response body.
    """
    row = table_service.get_table(session, _full_name(catalog, schema, table))
    return LoadTableResponse(metadata=_build_metadata(row))


def _delta_create_to_soyuz_create(
    catalog: str,
    schema: str,
    payload: CreateTableRequest,
) -> CreateTable:
    """Translate a Delta ``CreateTableRequest`` to a soyuz ``CreateTable``.

    Builds the :class:`ColumnInfo` list from the Delta columns,
    pushing the full Delta payload (``type`` + ``metadata``) into
    ``type_json`` so the load path can reconstruct it verbatim, and
    attaches the ``partition-columns`` as ``partition_index``
    offsets on the matching :class:`ColumnInfo` rows. The Delta
    protocol and domain metadata are intentionally ignored — soyuz
    does not track them; see ADR-0009.

    Args:
        catalog: Catalog segment from the request path.
        schema: Schema segment from the request path.
        payload: The validated Delta create request.

    Returns:
        CreateTable: A soyuz create-table payload ready for
            :func:`table_service.create_table`.
    """
    partition_index_map = {name: i for i, name in enumerate(payload.partition_columns)}
    columns_out: list[ColumnInfo] = []
    for position, delta_col in enumerate(payload.columns):
        type_text, type_name = _delta_type_to_text_and_name(delta_col.type)
        envelope = {"type": delta_col.type, "metadata": delta_col.metadata}
        columns_out.append(
            ColumnInfo(
                name=delta_col.name,
                type_text=type_text,
                type_json=json.dumps(envelope, sort_keys=True),
                type_name=type_name,
                position=position,
                nullable=delta_col.nullable,
                partition_index=partition_index_map.get(delta_col.name),
            ),
        )
    return CreateTable(
        name=payload.name,
        catalog_name=catalog,
        schema_name=schema,
        table_type=payload.table_type,
        data_source_format=payload.data_source_format,
        storage_location=payload.location,
        comment=payload.comment,
        properties=payload.properties or {},
        columns=columns_out,
    )


def create_delta_table(
    session: Session,
    catalog: str,
    schema: str,
    payload: CreateTableRequest,
) -> LoadTableResponse:
    """Create a new table and return its load response.

    Translates the Delta create request into soyuz' own create
    shape and delegates to :func:`table_service.create_table`. On
    success, echoes back the full :class:`LoadTableResponse` with
    the freshly-synthesised etag and table-uuid so a client can
    immediately follow up with an ``assert-etag`` or
    ``assert-table-uuid`` update without a round-trip load.

    Args:
        session: Active SQLAlchemy session.
        catalog: Catalog segment.
        schema: Schema segment.
        payload: Validated Delta create body.

    Returns:
        LoadTableResponse: Full response matching a subsequent
            ``loadTable`` call byte-for-byte.
    """
    soyuz_payload = _delta_create_to_soyuz_create(catalog, schema, payload)
    row = table_service.create_table(session, soyuz_payload)
    return ds.LoadTableResponse(metadata=_build_metadata(row))


def list_delta_tables(
    session: Session,
    catalog: str,
    schema: str,
    max_results: int | None,
    page_token: str | None,
) -> DeltaListTablesResponse:
    """Return the Delta-shaped paginated list of tables under a schema.

    Reuses :func:`table_service.list_tables` for the actual query
    and ordering, then projects each ORM row down to the spec's
    :class:`TableIdentifierWithDataSourceFormat` (just ``name`` and
    ``data-source-format`` — parent names are implicit from the
    request path). The ``next-page-token`` is carried through
    unchanged.

    Args:
        session: Active SQLAlchemy session.
        catalog: Catalog segment.
        schema: Schema segment.
        max_results: ``maxResults`` query param; ``None`` uses the
            service-level default.
        page_token: Opaque keyset token from a previous call.

    Returns:
        DeltaListTablesResponse: One page of identifiers.
    """
    rows, next_token = table_service.list_tables(
        session,
        catalog,
        schema,
        max_results,
        page_token,
    )
    identifiers = [
        ds.TableIdentifierWithDataSourceFormat(
            **{"name": row.name, "data-source-format": row.data_source_format},
        )
        for row in rows
    ]
    return ds.DeltaListTablesResponse(
        **{"identifiers": identifiers, "next-page-token": next_token},
    )


def rename_delta_table(
    session: Session,
    catalog: str,
    schema: str,
    table: str,
    payload: RenameTableRequest,
) -> None:
    """Rename an existing table in place.

    Thin wrapper around :func:`table_service.rename_table`. The
    Delta REST API responds with 204 No Content on success, so this
    function returns ``None``. Opaque ids are preserved — every
    permissions, lineage, or credential reference keyed on the
    table's ``id`` stays valid automatically.

    Args:
        session: Active SQLAlchemy session.
        catalog: Catalog segment.
        schema: Schema segment.
        table: Current table segment.
        payload: Validated rename request body.
    """
    table_service.rename_table(
        session,
        _full_name(catalog, schema, table),
        payload.new_name,
    )


def delete_delta_table(
    session: Session,
    catalog: str,
    schema: str,
    table: str,
) -> None:
    """Delete a table via the main UC table service.

    Thin wrapper so the Delta route can call one function and get
    the existing cascade/permission-wipe behaviour for free.

    Args:
        session: Active SQLAlchemy session.
        catalog: Catalog segment.
        schema: Schema segment.
        table: Table segment.
    """
    table_service.delete_table(session, _full_name(catalog, schema, table))


def table_exists(
    session: Session,
    catalog: str,
    schema: str,
    table: str,
) -> bool:
    """Check whether a table exists without loading its columns.

    Uses :func:`table_service.get_table` and treats a
    :class:`NotFoundError` as ``False``. A cheaper existence-only
    query would be possible (``SELECT 1``), but the existing
    service path already walks the three-segment address and
    surfaces the same error contract, which keeps the Delta route
    aligned with every other endpoint's 404 behaviour.

    Args:
        session: Active SQLAlchemy session.
        catalog: Catalog segment.
        schema: Schema segment.
        table: Table segment.

    Returns:
        bool: ``True`` if the table resolves, ``False`` otherwise.
    """
    from soyuz_catalog.exceptions import NotFoundError

    try:
        table_service.get_table(session, _full_name(catalog, schema, table))
    except NotFoundError:
        return False
    return True


def _assert_requirements(
    table: Table,
    requirements: list[ds.AssertTableUUID | ds.AssertEtag],
) -> None:
    """Validate ``updateTable`` pre-conditions against the current row.

    Iterates the requirements in order and raises on the first
    mismatch. Implementing both requirement types is cheap — UUID
    is a string compare against ``Table.id``; etag is a string
    compare against ``_compute_etag(table)`` — so there is no
    reason to short-circuit either. A mismatch maps to 409
    ``ConflictError`` with a dedicated error code
    ``REQUIREMENT_NOT_MET`` so clients can tell a pre-condition
    failure apart from a duplicate-name collision.

    Args:
        table: The current table row.
        requirements: Parsed requirements from the update body.

    Raises:
        ConflictError: On the first failed requirement.
    """
    for req in requirements:
        if isinstance(req, ds.AssertTableUUID):
            if req.uuid != table.id:
                raise ConflictError(
                    f"assert-table-uuid failed: expected {req.uuid}, got {table.id}",
                )
        elif isinstance(req, ds.AssertEtag):
            actual = _compute_etag(table)
            if req.etag != actual:
                raise ConflictError(
                    f"assert-etag failed: expected {req.etag}, got {actual}",
                )


def _apply_set_columns(session: Session, table: Table, columns: list[DeltaColumn]) -> None:
    """Replace a table's column list in full.

    Drops every existing :class:`Column` row attached to the table
    and re-inserts fresh rows in the order of the incoming Delta
    columns. The ORM's ``cascade="all, delete-orphan"`` takes care
    of the delete side when we clear the collection. Partition
    membership is preserved for columns whose name also appears in
    the current table's partition set — Delta's ``set-columns``
    action carries only the columns, not partition info, so we
    re-derive partition indices from the pre-update state.

    Args:
        session: Active SQLAlchemy session.
        table: The target table.
        columns: New column list from the update request.
    """
    previous_partition_names = {
        c.name: c.partition_index for c in table.columns if c.partition_index is not None
    }
    table.columns.clear()
    # Flush so the DELETE of the old rows hits the database before
    # the INSERT of the new ones — otherwise the unique constraint
    # on ``(table_id, position)`` fires within the same flush
    # because SQLAlchemy batches the INSERTs before the DELETEs.
    session.flush()
    for position, delta_col in enumerate(columns):
        partition_index = previous_partition_names.get(delta_col.name)
        table.columns.append(_delta_column_to_orm(delta_col, position, partition_index))


def _apply_set_partition_columns(table: Table, names: list[str]) -> None:
    """Rewrite the ``partition_index`` field across the table's columns.

    Columns whose name appears in ``names`` receive the index of
    their name in the list; every other column has its
    ``partition_index`` cleared. This keeps the two representations
    (child-column field + derived partition array) in lock-step
    without adding a new column to the :class:`Table` row.

    Args:
        table: The target table.
        names: Partition column names from the update request.
    """
    index_map = {name: i for i, name in enumerate(names)}
    for col in table.columns:
        col.partition_index = index_map.get(col.name)


def update_delta_table(
    session: Session,
    catalog: str,
    schema: str,
    table: str,
    payload: UpdateTableRequest,
) -> LoadTableResponse:
    """Apply a batch of :class:`TableUpdate` entries to an existing table.

    Flow:

    1. Resolve the table by path segments.
    2. Validate every requirement against the current row — a
       failure short-circuits the whole batch with 409 before any
       mutation runs.
    3. Iterate the ``updates`` list in order, dispatching on the
       action discriminator. Implemented actions mutate the row;
       no-op actions (``set-protocol``,
       ``set-domain-metadata``, ``remove-domain-metadata``) are
       accepted and silently discarded; commit-coordinator actions
       (``add-commit``, ``set-latest-backfilled-version``,
       ``update-metadata-snapshot-version``) raise
       :class:`CommitCoordinatorUnsupportedError` which the app
       exception handler maps to 501 with a dedicated error code.
    4. Bump ``updated_at`` so the next etag read reflects the
       mutation.
    5. Commit and return the fresh load response.

    Args:
        session: Active SQLAlchemy session.
        catalog: Catalog segment.
        schema: Schema segment.
        table: Table segment.
        payload: The validated update request.

    Returns:
        LoadTableResponse: Post-update state (with bumped etag).

    Raises:
        CommitCoordinatorUnsupportedError: On any
            commit-coordinator action (``add-commit``,
            ``set-latest-backfilled-version``,
            ``update-metadata-snapshot-version``).
        InvalidRequestError: Discriminator sentinel for an unknown
            :class:`TableUpdate` variant. Pydantic normally rejects
            these at routing time, so this path is unreachable in
            practice.
            ``NotFoundError`` may propagate from
            :func:`table_service.get_table` if the address does
            not resolve; ``ConflictError`` may propagate from
            :func:`_assert_requirements` on a failed pre-condition.
    """
    from soyuz_catalog.models import _now_ms

    row = table_service.get_table(session, _full_name(catalog, schema, table))
    _assert_requirements(row, payload.requirements)

    for update in payload.updates:
        if isinstance(update, ds.SetPropertiesUpdate):
            merged = dict(row.properties or {})
            merged.update(update.updates)
            row.properties = merged
        elif isinstance(update, ds.RemovePropertiesUpdate):
            merged = dict(row.properties or {})
            for key in update.removals:
                merged.pop(key, None)
            row.properties = merged
        elif isinstance(update, ds.SetSchemaUpdate):
            _apply_set_columns(session, row, update.columns)
        elif isinstance(update, ds.SetTableCommentUpdate):
            row.comment = update.comment or None
        elif isinstance(update, ds.SetPartitionColumnsUpdate):
            _apply_set_partition_columns(row, update.partition_columns)
        elif isinstance(update, ds.AddConstraintUpdate):
            constraints_service.add_constraint(session, row, update.constraint)
        elif isinstance(update, ds.DropConstraintUpdate):
            constraints_service.drop_constraint(
                session,
                row,
                update.name,
                if_exists=update.if_exists,
            )
        elif isinstance(
            update,
            (ds.SetProtocolUpdate, ds.SetDomainMetadataUpdate, ds.RemoveDomainMetadataUpdate),
        ):
            # Accept-and-discard: soyuz does not track these but a
            # rejection would break Delta clients that always emit
            # them. See ADR-0009.
            continue
        elif isinstance(
            update,
            (
                ds.AddCommitUpdate,
                ds.SetLatestBackfilledVersionUpdate,
                ds.UpdateSnapshotVersionUpdate,
            ),
        ):
            raise CommitCoordinatorUnsupportedError(
                f"Delta REST update action '{update.action}' requires a commit "
                "coordinator, which soyuz-catalog does not implement (ADR-0006).",
            )
        else:  # pragma: no cover - discriminated union makes this unreachable
            raise InvalidRequestError(f"Unknown TableUpdate variant: {type(update).__name__}")

    row.updated_at = _now_ms()
    session.commit()
    session.refresh(row)
    return ds.LoadTableResponse(metadata=_build_metadata(row))


def create_delta_staging_table(
    session: Session,
    catalog: str,
    schema: str,
    payload: CreateStagingTableRequest,
) -> StagingTableResponse:
    """Allocate a staging table and return the Delta-shaped response.

    Reuses :func:`staging_table_service.create_staging_table` for
    the actual allocation (which is where ``staging_location`` is
    derived from the catalog / schema storage root), then wraps
    the result in the Delta wire shape with the fixed default
    protocol and empty credential / properties stubs. Empty
    credential lists match the existing soyuz stub posture for
    temporary credentials (see ``DIVERGENCES.md``).

    Args:
        session: Active SQLAlchemy session.
        catalog: Catalog segment.
        schema: Schema segment.
        payload: Validated staging-table create body.

    Returns:
        StagingTableResponse: Full Delta wire response.
    """
    from soyuz_catalog.api.schemas import CreateStagingTable

    staging_payload = CreateStagingTable(
        name=payload.name,
        catalog_name=catalog,
        schema_name=schema,
    )
    row: StagingTable = staging_table_service.create_staging_table(session, staging_payload)
    return ds.StagingTableResponse(
        **{
            "table-id": row.id,
            "table-type": "MANAGED",
            "location": row.staging_location,
            "storage-credentials": [],
            "required-protocol": _DEFAULT_PROTOCOL,
            "suggested-protocol": ds.SuggestedProtocol(),
            "required-properties": {},
            "suggested-properties": {},
        },
    )
