"""Recipient-facing Delta Sharing protocol routes (ADR-0015).

Implements the read-only half of the open `Delta Sharing protocol
<https://github.com/delta-io/delta-sharing/blob/main/PROTOCOL.md>`_
for ``file://``-backed tables, mounted at the root under
``/delta-sharing/`` — like ``/lineage/``, the path is part of an
external wire contract (recipients put the base URL in their profile
file), so it is deliberately not nested under the UC API prefix and
the spec-conformance subset check skips it.

This surface is the **one authenticated corner of soyuz**: every
route except the pre-signed file download requires a recipient
bearer token, because the token *is* the protocol's identity
mechanism — it cannot be delegated to the front proxy the way
ADR-0005 delegates UC auth. Errors use the protocol's own
``{"errorCode", "message"}`` envelope via
:class:`soyuz_catalog.exceptions.SharingProtocolError`.

Query parameters are camelCase (``maxResults`` / ``pageToken``) per
the protocol; the FastAPI ``alias=`` declarations keep the Python
identifiers house-style.
"""

from __future__ import annotations

import time

from fastapi import APIRouter, Depends, Header, Query, Request, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from soyuz_catalog.api.deps import get_db
from soyuz_catalog.api.sharing_schemas import (
    GetProtocolShareResponse,
    ListProtocolSchemasResponse,
    ListProtocolSharesResponse,
    ListProtocolTablesResponse,
    ProtocolSchema,
    ProtocolShare,
    ProtocolTable,
    QueryTableRequest,
)
from soyuz_catalog.exceptions import SharingProtocolError
from soyuz_catalog.models import Recipient
from soyuz_catalog.services import delta_sharing_service as protocol
from soyuz_catalog.settings import get_settings
from soyuz_catalog.storage.signed_urls import sign_file_handle, verify_file_handle

router = APIRouter(prefix="/delta-sharing", tags=["delta-sharing"])

NDJSON_MEDIA_TYPE = "application/x-ndjson; charset=utf-8"
DELTA_TABLE_VERSION_HEADER = "Delta-Table-Version"


def get_recipient(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> Recipient:
    """FastAPI dependency: authenticate the protocol bearer token.

    Args:
        authorization: Raw ``Authorization`` header.
        db: Database session dependency.

    Returns:
        Recipient: The authenticated recipient row.
    """
    return protocol.authenticate_recipient(db, authorization)


@router.get(
    "/shares",
    response_model=ListProtocolSharesResponse,
    response_model_exclude_none=True,
    summary="List shares (Delta Sharing protocol)",
)
def list_shares(
    max_results: int | None = Query(default=None, alias="maxResults"),
    page_token: str | None = Query(default=None, alias="pageToken"),
    recipient: Recipient = Depends(get_recipient),
    db: Session = Depends(get_db),
) -> ListProtocolSharesResponse:
    """List the shares granted to the calling recipient.

    Args:
        max_results: Protocol ``maxResults`` page-size hint.
        page_token: Protocol ``pageToken`` cursor.
        recipient: Authenticated recipient (dependency).
        db: Database session dependency.

    Returns:
        ListProtocolSharesResponse: ``items`` plus ``nextPageToken``
            when more pages exist.
    """
    shares = protocol.list_recipient_shares(db, recipient)
    page, next_token = protocol.paginate_items(shares, lambda s: s.name, max_results, page_token)
    return ListProtocolSharesResponse(
        items=[ProtocolShare(name=s.name, id=s.id) for s in page],
        nextPageToken=next_token,
    )


@router.get(
    "/shares/{share}",
    response_model=GetProtocolShareResponse,
    response_model_exclude_none=True,
    summary="Get share (Delta Sharing protocol)",
)
def get_share(
    share: str,
    recipient: Recipient = Depends(get_recipient),
    db: Session = Depends(get_db),
) -> GetProtocolShareResponse:
    """Fetch one granted share by name.

    Args:
        share: Share name from the URL.
        recipient: Authenticated recipient (dependency).
        db: Database session dependency.

    Returns:
        GetProtocolShareResponse: The wrapped share.
    """
    row = protocol.get_recipient_share(db, recipient, share)
    return GetProtocolShareResponse(share=ProtocolShare(name=row.name, id=row.id))


@router.get(
    "/shares/{share}/schemas",
    response_model=ListProtocolSchemasResponse,
    response_model_exclude_none=True,
    summary="List schemas in share (Delta Sharing protocol)",
)
def list_schemas(
    share: str,
    max_results: int | None = Query(default=None, alias="maxResults"),
    page_token: str | None = Query(default=None, alias="pageToken"),
    recipient: Recipient = Depends(get_recipient),
    db: Session = Depends(get_db),
) -> ListProtocolSchemasResponse:
    """List the schemas of a share, derived from its table placements.

    Args:
        share: Share name from the URL.
        max_results: Protocol ``maxResults`` page-size hint.
        page_token: Protocol ``pageToken`` cursor.
        recipient: Authenticated recipient (dependency).
        db: Database session dependency.

    Returns:
        ListProtocolSchemasResponse: ``items`` plus ``nextPageToken``
            when more pages exist.
    """
    row = protocol.get_recipient_share(db, recipient, share)
    placements = protocol.list_share_placements(db, row)
    schema_names = sorted({p.schema_name for p in placements})
    page, next_token = protocol.paginate_items(schema_names, str, max_results, page_token)
    return ListProtocolSchemasResponse(
        items=[ProtocolSchema(name=name, share=row.name) for name in page],
        nextPageToken=next_token,
    )


def _to_protocol_table(
    placement: protocol.ProtocolPlacement,
    share_name: str,
    share_id: str,
) -> ProtocolTable:
    """Map a resolved placement to the protocol table item shape.

    Args:
        placement: The placement to render.
        share_name: Owning share's name.
        share_id: Owning share's opaque id.

    Returns:
        ProtocolTable: The wire item.
    """
    return ProtocolTable(
        name=placement.table_name,
        schema_name=placement.schema_name,
        share=share_name,
        shareId=share_id,
        id=placement.share_object.id,
    )


@router.get(
    "/shares/{share}/schemas/{schema}/tables",
    response_model=ListProtocolTablesResponse,
    response_model_exclude_none=True,
    summary="List tables in schema (Delta Sharing protocol)",
)
def list_tables(
    share: str,
    schema: str,
    max_results: int | None = Query(default=None, alias="maxResults"),
    page_token: str | None = Query(default=None, alias="pageToken"),
    recipient: Recipient = Depends(get_recipient),
    db: Session = Depends(get_db),
) -> ListProtocolTablesResponse:
    """List the tables of one schema of a share.

    Args:
        share: Share name from the URL.
        schema: Protocol schema name from the URL.
        max_results: Protocol ``maxResults`` page-size hint.
        page_token: Protocol ``pageToken`` cursor.
        recipient: Authenticated recipient (dependency).
        db: Database session dependency.

    Returns:
        ListProtocolTablesResponse: ``items`` plus ``nextPageToken``
            when more pages exist.
    """
    row = protocol.get_recipient_share(db, recipient, share)
    placements = [p for p in protocol.list_share_placements(db, row) if p.schema_name == schema]
    if not placements:
        raise SharingProtocolError(
            404,
            "RESOURCE_DOES_NOT_EXIST",
            f"schema '{share}.{schema}' does not exist",
        )
    page, next_token = protocol.paginate_items(
        placements,
        lambda p: p.table_name,
        max_results,
        page_token,
    )
    return ListProtocolTablesResponse(
        items=[_to_protocol_table(p, row.name, row.id) for p in page],
        nextPageToken=next_token,
    )


@router.get(
    "/shares/{share}/all-tables",
    response_model=ListProtocolTablesResponse,
    response_model_exclude_none=True,
    summary="List all tables in share (Delta Sharing protocol)",
)
def list_all_tables(
    share: str,
    max_results: int | None = Query(default=None, alias="maxResults"),
    page_token: str | None = Query(default=None, alias="pageToken"),
    recipient: Recipient = Depends(get_recipient),
    db: Session = Depends(get_db),
) -> ListProtocolTablesResponse:
    """List every table of a share across all of its schemas.

    Args:
        share: Share name from the URL.
        max_results: Protocol ``maxResults`` page-size hint.
        page_token: Protocol ``pageToken`` cursor.
        recipient: Authenticated recipient (dependency).
        db: Database session dependency.

    Returns:
        ListProtocolTablesResponse: ``items`` plus ``nextPageToken``
            when more pages exist.
    """
    row = protocol.get_recipient_share(db, recipient, share)
    placements = protocol.list_share_placements(db, row)
    page, next_token = protocol.paginate_items(
        placements,
        lambda p: f"{p.schema_name}.{p.table_name}",
        max_results,
        page_token,
    )
    return ListProtocolTablesResponse(
        items=[_to_protocol_table(p, row.name, row.id) for p in page],
        nextPageToken=next_token,
    )


@router.get(
    "/shares/{share}/schemas/{schema}/tables/{table}/version",
    summary="Query table version (Delta Sharing protocol)",
)
def query_table_version(
    share: str,
    schema: str,
    table: str,
    starting_timestamp: str | None = Query(default=None, alias="startingTimestamp"),
    recipient: Recipient = Depends(get_recipient),
    db: Session = Depends(get_db),
) -> Response:
    """Return the table's current version in the response header.

    Per the protocol the body is empty and the version travels in the
    ``Delta-Table-Version`` header. ``startingTimestamp`` belongs to
    the timestamp-resolution feature soyuz does not implement and is
    rejected loudly rather than ignored — silently returning the
    latest version for a timestamp query would be wrong data.

    Args:
        share: Share name from the URL.
        schema: Protocol schema name from the URL.
        table: Protocol table name from the URL.
        starting_timestamp: Protocol ``startingTimestamp`` parameter
            (unsupported).
        recipient: Authenticated recipient (dependency).
        db: Database session dependency.

    Returns:
        Response: Empty 200 with the ``Delta-Table-Version`` header.

    Raises:
        SharingProtocolError: 501 ``NOT_IMPLEMENTED`` when
            ``startingTimestamp`` is supplied.
    """
    if starting_timestamp is not None:
        raise SharingProtocolError(
            501,
            "NOT_IMPLEMENTED",
            "startingTimestamp is not supported by this server",
        )
    row = protocol.get_recipient_share(db, recipient, share)
    _placement, table_row = protocol.resolve_protocol_table(db, row, schema, table)
    snapshot = protocol.load_snapshot(table_row.storage_location)
    return Response(
        status_code=200,
        headers={DELTA_TABLE_VERSION_HEADER: str(snapshot.version)},
    )


@router.get(
    "/shares/{share}/schemas/{schema}/tables/{table}/metadata",
    summary="Query table metadata (Delta Sharing protocol)",
)
def query_table_metadata(
    share: str,
    schema: str,
    table: str,
    recipient: Recipient = Depends(get_recipient),
    db: Session = Depends(get_db),
) -> Response:
    """Return the table's protocol + metaData actions as NDJSON.

    Args:
        share: Share name from the URL.
        schema: Protocol schema name from the URL.
        table: Protocol table name from the URL.
        recipient: Authenticated recipient (dependency).
        db: Database session dependency.

    Returns:
        Response: Two NDJSON lines with the ``Delta-Table-Version``
            header.
    """
    row = protocol.get_recipient_share(db, recipient, share)
    _placement, table_row = protocol.resolve_protocol_table(db, row, schema, table)
    snapshot = protocol.load_snapshot(table_row.storage_location)
    body = protocol.protocol_line() + "\n" + protocol.metadata_line(snapshot) + "\n"
    return Response(
        content=body,
        media_type=NDJSON_MEDIA_TYPE,
        headers={DELTA_TABLE_VERSION_HEADER: str(snapshot.version)},
    )


@router.post(
    "/shares/{share}/schemas/{schema}/tables/{table}/query",
    summary="Read data from table (Delta Sharing protocol)",
)
def query_table(
    share: str,
    schema: str,
    table: str,
    request: Request,
    payload: QueryTableRequest | None = None,
    recipient: Recipient = Depends(get_recipient),
    db: Session = Depends(get_db),
) -> Response:
    """Return protocol, metaData, and per-file actions as NDJSON.

    Predicate and limit hints are accepted and ignored (the protocol
    defines them as hints the server may disregard); ``version`` pins
    the snapshot. Each file action's ``url`` points back at this
    server's pre-signed download endpoint — soyuz serves the parquet
    bytes itself for ``file://`` tables, taking the role a cloud
    object store's pre-signed URLs play elsewhere.

    Args:
        share: Share name from the URL.
        schema: Protocol schema name from the URL.
        table: Protocol table name from the URL.
        request: The live request, used to derive the absolute base
            URL embedded in the file actions.
        payload: Optional query body (hints / version pin).
        recipient: Authenticated recipient (dependency).
        db: Database session dependency.

    Returns:
        Response: NDJSON body with the ``Delta-Table-Version`` header.

    Raises:
        SharingProtocolError: 501 ``NOT_IMPLEMENTED`` when the body
            carries ``timestamp``, ``startingVersion``, or
            ``endingVersion`` — the timestamp-resolution and CDF
            features this server does not implement.
    """
    payload = payload or QueryTableRequest()
    if payload.timestamp is not None:
        raise SharingProtocolError(
            501,
            "NOT_IMPLEMENTED",
            "timestamp queries are not supported by this server",
        )
    if payload.startingVersion is not None or payload.endingVersion is not None:
        raise SharingProtocolError(
            501,
            "NOT_IMPLEMENTED",
            "startingVersion/endingVersion queries are not supported by this server",
        )
    row = protocol.get_recipient_share(db, recipient, share)
    _placement, table_row = protocol.resolve_protocol_table(db, row, schema, table)
    snapshot = protocol.load_snapshot(table_row.storage_location, version=payload.version)

    settings = get_settings()
    expires_at_ms = int(time.time() * 1000) + settings.sharing_file_url_ttl_seconds * 1000
    base_url = str(request.base_url)
    lines = [protocol.protocol_line(), protocol.metadata_line(snapshot)]
    for file in snapshot.files:
        token = sign_file_handle(file.abs_path, file.file_id, expires_at_ms)
        url = f"{base_url}delta-sharing/files/{file.file_id}?token={token}"
        lines.append(protocol.file_line(file, url, expires_at_ms))
    return Response(
        content="\n".join(lines) + "\n",
        media_type=NDJSON_MEDIA_TYPE,
        headers={DELTA_TABLE_VERSION_HEADER: str(snapshot.version)},
    )


@router.get(
    "/files/{file_id}",
    summary="Download shared parquet file (pre-signed)",
)
def download_file(file_id: str, token: str) -> FileResponse:
    """Stream one shared parquet file against a pre-signed handle.

    Deliberately **not** behind the bearer-token dependency: the
    signed handle is the authorisation, exactly like a cloud
    pre-signed URL — recipients' Delta Sharing clients fetch file
    URLs without re-attaching the bearer token. The handle's HMAC
    binds the path, this ``file_id``, and the expiry, so the only
    paths reachable through this route are ones the query endpoint
    signed minutes earlier.

    Args:
        file_id: Public file id from the query response.
        token: Signed handle from the query response's ``url``.

    Returns:
        FileResponse: The parquet bytes.

    Raises:
        SharingProtocolError: 403 on an invalid or expired handle,
            404 when the underlying file vanished after signing.
    """
    path = verify_file_handle(token, file_id)
    if not path.is_file():
        raise SharingProtocolError(
            404,
            "RESOURCE_DOES_NOT_EXIST",
            "shared file no longer exists",
        )
    return FileResponse(path, media_type="application/octet-stream")
