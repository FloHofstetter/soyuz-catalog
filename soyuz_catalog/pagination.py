"""Keyset pagination helpers shared by every ``list_*`` service call.

soyuz-catalog paginates list endpoints with an opaque ``page_token``
cursor that encodes the ``(created_at, id)`` tuple of the last row of
the previous page. ``created_at`` is ms-epoch and never mutated after
insert, ``id`` is a UUID4 hex primary key — together they are a stable
total order that survives concurrent inserts without the phantom-page
and skipped-row problems of OFFSET-based pagination.

The helpers here are deliberately generic: a service passes its
pre-filtered ``select(Model).where(...)`` statement plus the model
class and gets back a statement with ``ORDER BY created_at, id``, the
keyset WHERE, and ``LIMIT`` applied. The fetch-and-trim sentinel row
trick (request ``limit + 1`` rows, emit a token only if the sentinel
exists) handles the boundary case where the last page has exactly
``max_results`` rows without ever returning an empty final page.

See :doc:`/adr/0003-keyset-pagination` for the cursor design rationale.
"""

from __future__ import annotations

import base64
import binascii
import json
from typing import Any

from sqlalchemy import Select, and_, or_

from soyuz_catalog.exceptions import InvalidRequestError

DEFAULT_MAX_RESULTS = 100
MAX_MAX_RESULTS = 1000


def _effective_limit(max_results: int | None) -> int:
    """Resolve the caller's ``max_results`` to a concrete page size.

    ``None`` **and** ``0`` both resolve to :data:`DEFAULT_MAX_RESULTS`.
    Treating ``0`` as "use the server default" rather than 422 matches
    what the upstream JVM ``UCSingleCatalog`` connector sends when it
    wants the default — rejecting ``0`` with 422 would break that
    connector's ``listTables`` call, so we pin the divergence here.
    Negative values and anything above :data:`MAX_MAX_RESULTS` are
    still rejected as ``INVALID_ARGUMENT`` so a client that bypasses
    the route-level ``Query(ge=0, le=MAX)`` (for example by calling
    the service directly from a test) still gets a loud failure.

    Args:
        max_results: Caller-supplied page size hint, or ``None``.

    Returns:
        int: The concrete page size to apply.

    Raises:
        InvalidRequestError: If ``max_results`` is negative or greater
            than :data:`MAX_MAX_RESULTS`.
    """
    if max_results is None or max_results == 0:
        return DEFAULT_MAX_RESULTS
    if max_results < 0 or max_results > MAX_MAX_RESULTS:
        raise InvalidRequestError(
            f"max_results must be between 0 and {MAX_MAX_RESULTS}, got {max_results}",
        )
    return max_results


def encode_page_token(created_at_ms: int, row_id: str) -> str:
    """Build an opaque page token from a ``(created_at, id)`` tuple.

    The token is ``base64url( json({"c": created_at_ms, "i": row_id}) )``
    with no padding. JSON rather than a raw tuple so that a future
    cursor field (e.g. a filter-hash guard) can be added without a new
    token format or version byte. The token is not a security
    boundary — it is not HMACed — but it is tamper-evident enough that
    any hand-edit fails the round-trip in :func:`decode_page_token`.

    Args:
        created_at_ms: Row's ``created_at`` column value (ms epoch).
        row_id: Row's opaque ``id`` column value.

    Returns:
        str: The opaque, URL-safe page token.
    """
    payload = json.dumps({"c": created_at_ms, "i": row_id}, separators=(",", ":"))
    encoded = base64.urlsafe_b64encode(payload.encode("utf-8")).rstrip(b"=")
    return encoded.decode("ascii")


def decode_page_token(token: str) -> tuple[int, str]:
    """Parse a page token back into its ``(created_at, id)`` tuple.

    Every decode failure — non-base64, non-JSON, wrong shape, wrong
    value types — surfaces as ``InvalidRequestError`` (400
    ``INVALID_ARGUMENT``) rather than a silent reset to the first page,
    so a tampered or stale token fails loudly instead of quietly
    serving a surprising result set. This is the same
    silently-accept-garbage bug class that ``extra="forbid"`` rejects
    on request bodies.

    Args:
        token: The opaque ``page_token`` as sent by the client.

    Returns:
        tuple[int, str]: ``(created_at_ms, row_id)``.

    Raises:
        InvalidRequestError: On any decode, shape, or type mismatch.
    """
    try:
        padded = token + "=" * (-len(token) % 4)
        raw = base64.urlsafe_b64decode(padded.encode("ascii"))
        data = json.loads(raw.decode("utf-8"))
    except (ValueError, binascii.Error, UnicodeDecodeError) as exc:
        raise InvalidRequestError(f"page_token is not a valid token: {token!r}") from exc
    if not isinstance(data, dict) or set(data.keys()) != {"c", "i"}:
        raise InvalidRequestError(f"page_token has unexpected shape: {token!r}")
    created_at = data["c"]
    row_id = data["i"]
    if not isinstance(created_at, int) or isinstance(created_at, bool):
        raise InvalidRequestError(f"page_token 'c' field must be int: {token!r}")
    if not isinstance(row_id, str):
        raise InvalidRequestError(f"page_token 'i' field must be str: {token!r}")
    return created_at, row_id


def apply_keyset(
    stmt: Select[Any],
    model: Any,
    page_token: str | None,
    max_results: int | None,
) -> tuple[Select[Any], int]:
    """Apply keyset WHERE, ORDER BY, and LIMIT to a list-query statement.

    The caller passes a pre-filtered ``select(Model).where(parent_fk ==
    ...)`` plus the model class (which must have ``created_at`` and
    ``id`` columns). This helper adds a strict-greater-than cursor
    comparison on ``(created_at, id)`` if ``page_token`` is present,
    then the canonical ``ORDER BY created_at ASC, id ASC`` and a
    ``LIMIT effective_limit + 1`` — the sentinel row is how
    :func:`build_next_token` detects "is there more after this page".
    ``InvalidRequestError`` propagates from :func:`_effective_limit`
    (out-of-range ``max_results``) or :func:`decode_page_token`
    (tampered / unparseable cursor).

    Args:
        stmt: The list query, already filtered by parent relationships.
        model: The ORM model class (must expose ``created_at`` and
            ``id`` as mapped columns).
        page_token: Opaque cursor from the previous page, or ``None``
            for the first page.
        max_results: Caller-supplied page size hint, or ``None`` for
            the :data:`DEFAULT_MAX_RESULTS` default.

    Returns:
        tuple[Select[Any], int]: The fully-paginated statement and the
            effective page size (used by :func:`build_next_token` to
            tell the sentinel row from a real row).
    """
    limit = _effective_limit(max_results)
    if page_token is not None:
        cursor_c, cursor_i = decode_page_token(page_token)
        stmt = stmt.where(
            or_(
                model.created_at > cursor_c,
                and_(model.created_at == cursor_c, model.id > cursor_i),
            ),
        )
    stmt = stmt.order_by(model.created_at.asc(), model.id.asc()).limit(limit + 1)
    return stmt, limit


def build_next_token[T](rows: list[T], limit: int) -> tuple[list[T], str | None]:
    """Trim the sentinel row and build the next page's token.

    If ``apply_keyset`` fetched ``limit + 1`` rows and the extra row is
    present, the current page is full and another page exists — return
    the first ``limit`` rows plus a cursor built from the **last
    returned** row. If only ``limit`` or fewer rows came back, there is
    no next page and the token is ``None``. This is the standard
    fetch-one-extra keyset trick; it sidesteps the phantom-empty-page
    bug where the last page has exactly ``max_results`` rows.

    The trailing row's ``created_at`` and ``id`` are read by attribute,
    so the caller's ``rows`` list must contain ORM instances (or
    anything else with those two attributes).

    Args:
        rows: Rows returned from ``session.scalars(stmt).all()``. Must
            contain at most ``limit + 1`` entries.
        limit: The effective page size from :func:`apply_keyset`.

    Returns:
        tuple[list[T], str | None]: The trimmed page of rows and the
            next page token (or ``None`` if there is no next page).
    """
    if len(rows) <= limit:
        return rows, None
    trimmed = rows[:limit]
    last = trimmed[-1]
    return trimmed, encode_page_token(last.created_at, last.id)  # type: ignore[attr-defined]
