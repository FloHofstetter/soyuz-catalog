"""Wire shapes for the recipient-facing Delta Sharing protocol (ADR-0015).

These models pin the open `Delta Sharing protocol
<https://github.com/delta-io/delta-sharing/blob/main/PROTOCOL.md>`_
exactly, which is why they live in their own module instead of
:mod:`soyuz_catalog.api.schemas`: the field names are camelCase
(``nextPageToken``, ``shareId``) because the protocol says so, not
because soyuz chose them — the same external-contract posture as the
OpenLineage shapes. The NDJSON action lines (``protocol`` /
``metaData`` / ``file``) are assembled as plain dicts in
:mod:`soyuz_catalog.services.delta_sharing_service` rather than
modelled here, because NDJSON bypasses FastAPI's response-model
machinery entirely.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ProtocolShare(BaseModel):
    """One share as listed on the protocol surface.

    Only ``name`` and ``id`` are populated — the protocol marks
    ``displayName`` / ``comment`` / ``properties`` optional and soyuz
    keeps descriptive metadata on the management surface, where the
    data provider (not the recipient) reads it.
    """

    name: str
    id: str | None = None


class ListProtocolSharesResponse(BaseModel):
    """Response shape for ``GET /delta-sharing/shares``.

    ``nextPageToken`` is omitted (not ``null``) on the last page —
    the reference client treats presence of the key as "fetch more",
    so the route serialises with ``exclude_none``.
    """

    items: list[ProtocolShare]
    nextPageToken: str | None = None  # noqa: N815 — protocol wire name is camelCase.


class GetProtocolShareResponse(BaseModel):
    """Response shape for ``GET /delta-sharing/shares/{share}``."""

    share: ProtocolShare


class ProtocolSchema(BaseModel):
    """One schema of a share, derived from the shared tables' placements."""

    name: str
    share: str


class ListProtocolSchemasResponse(BaseModel):
    """Response shape for ``GET /delta-sharing/shares/{share}/schemas``."""

    items: list[ProtocolSchema]
    nextPageToken: str | None = None  # noqa: N815 — protocol wire name is camelCase.


class ProtocolTable(BaseModel):
    """One table as exposed on the protocol surface.

    The wire field ``schema`` is carried by the Python attribute
    ``schema_name`` (serialisation alias) because pydantic reserves
    ``schema`` as a ``BaseModel`` attribute name. FastAPI serialises
    response models with ``by_alias=True``, so the alias is what
    recipients see. ``id`` is the share-object row id (stable per
    placement within the share) and ``shareId`` the share row id,
    both per the protocol's optional-identifier slots.
    """

    name: str
    schema_name: str = Field(serialization_alias="schema")
    share: str
    shareId: str | None = None  # noqa: N815 — protocol wire name is camelCase.
    id: str | None = None


class ListProtocolTablesResponse(BaseModel):
    """Response for both protocol table-listing endpoints.

    Used by ``GET .../schemas/{schema}/tables`` and
    ``GET .../all-tables`` — the protocol gives both the same item
    shape.
    """

    items: list[ProtocolTable]
    nextPageToken: str | None = None  # noqa: N815 — protocol wire name is camelCase.


class QueryTableRequest(BaseModel):
    """Request body for ``POST .../tables/{table}/query``.

    Permissively validated (``extra="allow"``): the protocol evolves
    independently of soyuz and clients legitimately send fields from
    newer revisions (``maxFiles``, ``includeRefreshToken``, …) —
    rejecting them with 422 would break real recipients. This is the
    same documented exception to the project-wide ``extra="forbid"``
    policy that the OpenLineage ingest shapes use (ADR-0008).

    ``predicateHints``, ``jsonPredicateHints``, and ``limitHint`` are
    accepted and ignored — the protocol defines all three as hints
    the server may disregard, and soyuz returns the full file list.
    ``version`` pins the snapshot. ``timestamp``,
    ``startingVersion``, and ``endingVersion`` belong to the
    timestamp-resolution / CDF features soyuz does not implement and
    are rejected with 501 at the service layer.
    """

    model_config = ConfigDict(extra="allow")

    predicateHints: list[str] | None = None  # noqa: N815 — protocol wire name.
    jsonPredicateHints: str | None = None  # noqa: N815 — protocol wire name.
    limitHint: int | None = None  # noqa: N815 — protocol wire name.
    version: int | None = None
    timestamp: str | None = None
    startingVersion: int | None = None  # noqa: N815 — protocol wire name.
    endingVersion: int | None = None  # noqa: N815 — protocol wire name.
