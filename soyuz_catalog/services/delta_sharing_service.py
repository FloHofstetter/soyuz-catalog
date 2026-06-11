"""Read side of the Delta Sharing protocol surface (ADR-0015).

This module backs the recipient-facing routes under
``/delta-sharing/``: bearer-token authentication, the share → schema
→ table namespace derived from
:class:`soyuz_catalog.models.ShareObject` rows, and the Delta
snapshot reads (version / metadata / file list) that the protocol's
NDJSON responses are assembled from. The *write* side — who may read
what — lives in :mod:`soyuz_catalog.services.sharing_service`.

Two deliberate departures from the rest of the service layer:

* Errors are :class:`soyuz_catalog.exceptions.SharingProtocolError`,
  not the soyuz domain exceptions, because the open protocol pins its
  own ``{"errorCode", "message"}`` envelope.
* List pagination is in-memory over the resolved item lists rather
  than DB keyset (ADR-0003): every protocol list is *derived* — a
  share's schemas and table placements only exist after applying
  ``shared_as`` aliasing — and bounded by the share's object count,
  which is management-surface small. The cursor is still an opaque
  resumable token (last item key, not an offset), so pages stay
  stable under concurrent inserts.

Snapshot reads go through :py:class:`deltalake.DeltaTable` — the same
optional-dependency posture as the Delta commit coordinator: a
missing ``delta`` extra surfaces as 501, and non-``file://`` storage
is 501 because cloud-side reads would need the out-of-scope
credential-vending layer.
"""

from __future__ import annotations

import hashlib
import json
from base64 import urlsafe_b64decode, urlsafe_b64encode
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from sqlalchemy import select
from sqlalchemy.orm import Session

from soyuz_catalog.exceptions import NotFoundError, SharingProtocolError
from soyuz_catalog.models import Recipient, Share, ShareGrant, ShareObject, Table
from soyuz_catalog.pagination import DEFAULT_MAX_RESULTS, MAX_MAX_RESULTS
from soyuz_catalog.services import table_service
from soyuz_catalog.services.sharing_service import effective_placement, hash_token

PROTOCOL_MIN_READER_VERSION = 1
"""The only Delta reader protocol version soyuz serves over parquet format.

Tables whose ``_delta_log`` protocol demands reader version 2+
(column mapping, deletion vectors, …) cannot be represented in the
protocol's parquet response format without client-side feature
support, so the query/metadata endpoints reject them instead of
serving silently-wrong data.
"""


# ---------------------------------------------------------------------------
# Authentication + namespace resolution
# ---------------------------------------------------------------------------


def authenticate_recipient(session: Session, authorization: str | None) -> Recipient:
    """Resolve the ``Authorization: Bearer`` header to a recipient row.

    The token is hashed with the same SHA-256 primitive used at mint
    time and looked up by the unique ``bearer_token_hash`` index —
    constant work regardless of recipient count, and the database
    never sees the plaintext. Missing header, non-Bearer scheme, and
    unknown token all map to the same 401 so probing clients cannot
    distinguish "bad token" from "no such recipient".

    Args:
        session: Active SQLAlchemy session.
        authorization: Raw ``Authorization`` header value, or ``None``.

    Returns:
        Recipient: The authenticated recipient row.

    Raises:
        SharingProtocolError: 401 ``UNAUTHENTICATED`` when the header
            is absent, malformed, or does not match any recipient.
    """
    denied = SharingProtocolError(
        401,
        "UNAUTHENTICATED",
        "missing or invalid bearer token",
    )
    if authorization is None:
        raise denied
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise denied
    recipient = session.scalar(
        select(Recipient).where(Recipient.bearer_token_hash == hash_token(token.strip())),
    )
    if recipient is None:
        raise denied
    return recipient


def list_recipient_shares(session: Session, recipient: Recipient) -> list[Share]:
    """Return every share granted to a recipient, sorted by name.

    Args:
        session: Active SQLAlchemy session.
        recipient: The authenticated recipient.

    Returns:
        list[Share]: Granted shares in name order (the protocol
            pagination key).
    """
    rows = session.scalars(
        select(Share)
        .join(ShareGrant, ShareGrant.share_id == Share.id)
        .where(ShareGrant.recipient_id == recipient.id)
        .order_by(Share.name.asc()),
    )
    return list(rows)


def get_recipient_share(session: Session, recipient: Recipient, share_name: str) -> Share:
    """Fetch one share by name, gated on the recipient's grants.

    A share that exists but is not granted to the caller returns the
    same 404 as a share that does not exist at all — anything else
    would let any token holder enumerate the server's share names.

    Args:
        session: Active SQLAlchemy session.
        recipient: The authenticated recipient.
        share_name: Share name from the URL path.

    Returns:
        Share: The granted share row.

    Raises:
        SharingProtocolError: 404 ``RESOURCE_DOES_NOT_EXIST`` when
            the name does not resolve to a granted share.
    """
    share = session.scalar(
        select(Share)
        .join(ShareGrant, ShareGrant.share_id == Share.id)
        .where(ShareGrant.recipient_id == recipient.id, Share.name == share_name),
    )
    if share is None:
        raise SharingProtocolError(
            404,
            "RESOURCE_DOES_NOT_EXIST",
            f"share '{share_name}' does not exist",
        )
    return share


@dataclass(frozen=True, slots=True)
class ProtocolPlacement:
    """One shared table's protocol-side address inside a share.

    Attributes:
        schema_name: Effective schema segment (``shared_as`` wins
            over the stored full name's schema part).
        table_name: Effective table segment.
        share_object: The backing row, kept so callers can reach the
            stored ``table_full_name`` and the row id.
    """

    schema_name: str
    table_name: str
    share_object: ShareObject


def list_share_placements(session: Session, share: Share) -> list[ProtocolPlacement]:
    """Resolve every object of a share to its protocol placement.

    Sorted by ``(schema_name, table_name)`` — the stable total order
    the in-memory pagination cursors key on. Placement uniqueness
    within a share is enforced at add time by
    :func:`soyuz_catalog.services.sharing_service.add_share_object`,
    so the sort key is unique here.

    Args:
        session: Active SQLAlchemy session.
        share: The share whose namespace is being listed.

    Returns:
        list[ProtocolPlacement]: All placements in protocol order.
    """
    rows = session.scalars(
        select(ShareObject).where(ShareObject.share_id == share.id),
    )
    placements = [
        ProtocolPlacement(*effective_placement(o.table_full_name, o.shared_as), o) for o in rows
    ]
    placements.sort(key=lambda p: (p.schema_name, p.table_name))
    return placements


def resolve_protocol_table(
    session: Session,
    share: Share,
    schema_name: str,
    table_name: str,
) -> tuple[ProtocolPlacement, Table]:
    """Resolve a protocol ``share/schema/table`` address to a live table.

    Two-step lookup: the placement match against the share's objects,
    then the stored ``table_full_name`` against the live tables
    surface. A shared table that was renamed or dropped since it was
    added fails the second step — by design the share binds by name
    (see :class:`soyuz_catalog.models.ShareObject`) — and surfaces as
    the same 404 as an address that never existed.

    Args:
        session: Active SQLAlchemy session.
        share: The (already grant-checked) share.
        schema_name: Protocol schema segment from the URL.
        table_name: Protocol table segment from the URL.

    Returns:
        tuple[ProtocolPlacement, Table]: The matched placement and
            the live table row.

    Raises:
        SharingProtocolError: 404 ``RESOURCE_DOES_NOT_EXIST`` when no
            placement matches or the underlying table no longer
            resolves.
    """
    not_found = SharingProtocolError(
        404,
        "RESOURCE_DOES_NOT_EXIST",
        f"table '{share.name}.{schema_name}.{table_name}' does not exist",
    )
    placement = next(
        (
            p
            for p in list_share_placements(session, share)
            if p.schema_name == schema_name and p.table_name == table_name
        ),
        None,
    )
    if placement is None:
        raise not_found
    try:
        table = table_service.get_table(session, placement.share_object.table_full_name)
    except NotFoundError as exc:
        raise not_found from exc
    return placement, table


# ---------------------------------------------------------------------------
# In-memory pagination over derived lists
# ---------------------------------------------------------------------------


def paginate_items[T](
    items: list[T],
    key_of: Callable[[T], str],
    max_results: int | None,
    page_token: str | None,
) -> tuple[list[T], str | None]:
    """Paginate a fully-resolved, key-sorted item list.

    The cursor encodes the **key of the last served item** (not an
    offset), so a page boundary survives concurrent inserts the same
    way the DB keyset cursors do — an item added before the cursor is
    skipped, one added after shows up, and nothing is double-served.
    ``max_results`` carries the house semantics: ``None``/``0`` mean
    the server default, out-of-range values are rejected.

    Args:
        items: All items, already sorted by their key.
        key_of: Callable mapping an item to its unique string key.
        max_results: Page size hint from the ``maxResults`` query
            parameter.
        page_token: Cursor from a previous ``nextPageToken``.

    Returns:
        tuple[list[T], str | None]: The page and the next cursor
            (``None`` on the last page).

    Raises:
        SharingProtocolError: 400 ``INVALID_PARAMETER_VALUE`` on an
            out-of-range ``maxResults`` or an undecodable
            ``pageToken``.
    """
    if max_results is None or max_results == 0:
        limit = DEFAULT_MAX_RESULTS
    elif max_results < 0 or max_results > MAX_MAX_RESULTS:
        raise SharingProtocolError(
            400,
            "INVALID_PARAMETER_VALUE",
            f"maxResults must be between 0 and {MAX_MAX_RESULTS}, got {max_results}",
        )
    else:
        limit = max_results

    start = 0
    if page_token is not None:
        try:
            padded = page_token + "=" * (-len(page_token) % 4)
            cursor = json.loads(urlsafe_b64decode(padded.encode("ascii")))
            last_key = cursor["k"]
        except Exception as exc:  # noqa: BLE001 — every decode failure is the same 400
            raise SharingProtocolError(
                400,
                "INVALID_PARAMETER_VALUE",
                f"pageToken is not a valid token: {page_token!r}",
            ) from exc
        start = next(
            (i + 1 for i in reversed(range(len(items))) if key_of(items[i]) <= last_key),
            0,
        )

    page = items[start : start + limit]
    next_token: str | None = None
    if start + limit < len(items) and page:
        payload = json.dumps({"k": key_of(page[-1])}, separators=(",", ":"))
        next_token = urlsafe_b64encode(payload.encode("utf-8")).rstrip(b"=").decode("ascii")
    return page, next_token


# ---------------------------------------------------------------------------
# Delta snapshot reads
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SnapshotFile:
    """One active parquet file of a snapshot.

    Attributes:
        rel_path: Path from the Delta ``add`` action, relative to the
            table root.
        abs_path: Resolved absolute filesystem path (verified to be
            under the table root).
        file_id: Stable public id — SHA-256 of ``rel_path``, so the
            same file keeps the same id across requests as the
            protocol requires.
        size: File size in bytes per the ``add`` action.
        partition_values: Partition column → string value map.
        num_records: Row count when the log carries stats, else
            ``None``.
    """

    rel_path: str
    abs_path: Path
    file_id: str
    size: int
    partition_values: dict[str, str | None]
    num_records: int | None


@dataclass(frozen=True, slots=True)
class TableSnapshot:
    """Everything the protocol responses need from one Delta snapshot.

    Attributes:
        version: Snapshot version (the ``Delta-Table-Version``
            header).
        metadata_id: Delta metadata GUID (the ``metaData.id`` wire
            field).
        name: Table name from the Delta metadata, if set.
        description: Table description from the Delta metadata, if
            set.
        schema_string: Delta-format JSON schema string.
        partition_columns: Partition column names in partition order.
        configuration: Table configuration map from the Delta
            metadata.
        files: Active parquet files of the snapshot.
    """

    version: int
    metadata_id: str
    name: str | None
    description: str | None
    schema_string: str
    partition_columns: list[str]
    configuration: dict[str, str]
    files: list[SnapshotFile]


def _table_root(storage_location: str | None) -> Path:
    """Validate a shared table's storage location and return its root.

    Args:
        storage_location: The table's registered ``storage_location``.

    Returns:
        Path: Resolved absolute root directory.

    Raises:
        SharingProtocolError: 501 ``NOT_IMPLEMENTED`` for cloud
            schemes (serving them would require the out-of-scope
            credential-vending layer) or 400 when the table has no
            materialised storage location at all.
    """
    if storage_location is None or not storage_location.strip():
        raise SharingProtocolError(
            400,
            "INVALID_PARAMETER_VALUE",
            "shared table has no materialised storage location",
        )
    parsed = urlsplit(storage_location)
    if parsed.scheme != "file":
        raise SharingProtocolError(
            501,
            "NOT_IMPLEMENTED",
            "delta sharing on this deployment serves file:// tables only; "
            f"got scheme {parsed.scheme!r}",
        )
    return Path(parsed.path).resolve()


def load_snapshot(storage_location: str | None, version: int | None = None) -> TableSnapshot:
    """Read one Delta snapshot's protocol-relevant state from disk.

    Goes through :py:class:`deltalake.DeltaTable` (rather than
    replaying ``_delta_log`` JSON by hand) so checkpointed and
    log-cleaned tables resolve correctly — the same reason the Delta
    commit coordinator uses it for its version fallback. Stats are
    reduced to ``numRecords``: that is what the kernel exposes
    per-file, the field is optional on the wire, and recipients use
    it only as a scan hint.

    Every ``add``-action path is resolved and verified to live under
    the table root before it is trusted — a crafted ``_delta_log``
    must not be able to point the file-serving surface outside the
    table directory.

    Args:
        storage_location: The table's registered ``file://`` storage
            location.
        version: Snapshot version to pin, or ``None`` for latest.

    Returns:
        TableSnapshot: The resolved snapshot state.

    Raises:
        SharingProtocolError: 501 when the ``delta`` extra is not
            installed or the scheme is not ``file://``; 404 when the
            location has no Delta log; 400 when ``version`` does not
            exist or the table's reader protocol exceeds
            :data:`PROTOCOL_MIN_READER_VERSION`.
    """
    root = _table_root(storage_location)
    try:
        import pyarrow  # noqa: PLC0415
        from deltalake import DeltaTable  # noqa: PLC0415
        from deltalake.exceptions import DeltaError, TableNotFoundError  # noqa: PLC0415
    except ImportError as exc:  # pragma: no cover
        raise SharingProtocolError(
            501,
            "NOT_IMPLEMENTED",
            "the 'delta' optional extra is not installed; reinstall with "
            "'pip install soyuz-catalog[delta]' to enable delta sharing",
        ) from exc

    try:
        dt = DeltaTable(str(root), version=version)
    except TableNotFoundError as exc:
        raise SharingProtocolError(
            404,
            "RESOURCE_DOES_NOT_EXIST",
            "shared table has no Delta log at its storage location",
        ) from exc
    except DeltaError as exc:
        # The kernel raises one error family for both "no such
        # version" and other log defects; with the latest-version
        # load already excluded above, a pinned-version failure is a
        # client-input problem.
        raise SharingProtocolError(
            400,
            "INVALID_PARAMETER_VALUE",
            f"version {version} does not exist for this table",
        ) from exc

    protocol = dt.protocol()
    if protocol.min_reader_version > PROTOCOL_MIN_READER_VERSION:
        features = sorted(protocol.reader_features or [])
        raise SharingProtocolError(
            400,
            "UNSUPPORTED_TABLE_FEATURES",
            "shared table requires Delta reader version "
            f"{protocol.min_reader_version}"
            + (f" with reader features {features}" if features else "")
            + "; this server shares minReaderVersion=1 tables only",
        )

    metadata = dt.metadata()
    files: list[SnapshotFile] = []
    for row in pyarrow.table(dt.get_add_actions(flatten=False)).to_pylist():
        rel_path = row["path"]
        abs_path = (root / rel_path).resolve()
        if not abs_path.is_relative_to(root):
            raise SharingProtocolError(
                400,
                "INVALID_PARAMETER_VALUE",
                f"delta log entry escapes the table root: {rel_path!r}",
            )
        partition_values: dict[str, str | None] = {
            k: None if v is None else str(v) for k, v in (row.get("partition") or {}).items()
        }
        files.append(
            SnapshotFile(
                rel_path=rel_path,
                abs_path=abs_path,
                file_id=hashlib.sha256(rel_path.encode("utf-8")).hexdigest()[:32],
                size=int(row["size_bytes"]),
                partition_values=partition_values,
                num_records=row.get("num_records"),
            ),
        )

    return TableSnapshot(
        version=int(dt.version()),
        metadata_id=str(metadata.id),
        name=metadata.name,
        description=metadata.description,
        schema_string=dt.schema().to_json(),
        partition_columns=list(metadata.partition_columns),
        configuration=dict(metadata.configuration or {}),
        files=files,
    )


# ---------------------------------------------------------------------------
# NDJSON line assembly
# ---------------------------------------------------------------------------


def protocol_line() -> str:
    """Render the protocol action line of an NDJSON response.

    Always ``minReaderVersion=1``: :func:`load_snapshot` rejects
    tables that demand more, so by the time a response is being
    assembled this constant is the truth.

    Returns:
        str: One JSON line, no trailing newline.
    """
    return json.dumps(
        {"protocol": {"minReaderVersion": PROTOCOL_MIN_READER_VERSION}},
        separators=(",", ":"),
    )


def metadata_line(snapshot: TableSnapshot) -> str:
    """Render the metaData action line of an NDJSON response.

    Optional fields (``name`` / ``description``) are emitted only
    when the Delta metadata carries them; ``configuration`` is always
    present (``{}`` when empty) because the reference client reads it
    unconditionally.

    Args:
        snapshot: The snapshot being served.

    Returns:
        str: One JSON line, no trailing newline.
    """
    meta: dict[str, Any] = {"id": snapshot.metadata_id}
    if snapshot.name is not None:
        meta["name"] = snapshot.name
    if snapshot.description is not None:
        meta["description"] = snapshot.description
    meta["format"] = {"provider": "parquet"}
    meta["schemaString"] = snapshot.schema_string
    meta["partitionColumns"] = snapshot.partition_columns
    meta["configuration"] = snapshot.configuration
    return json.dumps({"metaData": meta}, separators=(",", ":"))


def file_line(
    file: SnapshotFile,
    url: str,
    expiration_timestamp_ms: int,
) -> str:
    """Render one file action line of a query NDJSON response.

    ``stats`` is included as a JSON-encoded string (per the protocol,
    stats is a *string* field containing JSON) when the log carried a
    row count, and omitted otherwise — the field is optional and an
    empty stats object would be noise.

    Args:
        file: The snapshot file to render.
        url: Pre-signed download URL for the file bytes.
        expiration_timestamp_ms: Epoch-ms expiry of that URL.

    Returns:
        str: One JSON line, no trailing newline.
    """
    action: dict[str, Any] = {
        "url": url,
        "id": file.file_id,
        "partitionValues": file.partition_values,
        "size": file.size,
    }
    if file.num_records is not None:
        action["stats"] = json.dumps({"numRecords": file.num_records}, separators=(",", ":"))
    action["expirationTimestamp"] = expiration_timestamp_ms
    return json.dumps({"file": action}, separators=(",", ":"))
