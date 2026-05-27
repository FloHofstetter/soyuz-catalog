"""Pydantic schemas for the Delta REST Catalog API (ADR-0009).

These models implement the wire shapes defined in
``~/git/unitycatalog/api/delta.yaml`` — the *second* REST spec surface
that unitycatalog OSS ships alongside the main UC API. The Delta
variant is Delta-centric and uses native Delta protocol shapes
(``DeltaColumn``, ``DeltaProtocol``, ``TableMetadata``) with a
distinctive **kebab-case** wire convention (``data-source-format``,
``min-reader-version``, …) that the main UC API does not use.

Conventions in this module:

* Every model uses ``ConfigDict(extra="forbid", populate_by_name=True)``
  so the Python attribute stays snake_case (``data_source_format``)
  while the wire name uses the spec's kebab-case via ``Field(alias=…)``.
  This keeps the rest of soyuz' Python code idiomatic and the wire
  output spec-conformant with a single source of truth.
* Response models are strict. The main UC API's
  ``ConfigDict(extra="allow")`` exception for ``OpenLineageEvent``
  (see [ADR-0008](https://github.com/FloHofstetter/soyuz-catalog/blob/main/docs/adr/0008-openlineage-as-lineage-contract.md))
  does **not** carry over to the Delta surface — spec-sourced shapes
  always stay strict.
* The discriminated unions (``TableUpdate``, ``TableRequirement``)
  are modelled with Pydantic's ``Field(discriminator=…)``, mapped
  through the spec's ``action`` / ``type`` discriminator keys, so a
  client that sends an unknown variant gets a 422 at the routing
  layer before any service code runs.
* ``DeltaColumn.type`` is deliberately ``str | dict[str, Any]`` —
  the upstream spec notes that OpenAPI cannot express this union
  cleanly, and Delta clients parse it through their own type
  serialiser. soyuz round-trips the value verbatim; see
  :mod:`soyuz_catalog.services.delta_rest_service` for the storage
  strategy.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from soyuz_catalog.api.schemas import TableConstraint as TableConstraintPayload

# ---------------------------------------------------------------------------
# Shared primitives
# ---------------------------------------------------------------------------


class DeltaProtocol(BaseModel):
    """Delta table protocol version and feature flags.

    soyuz does not track per-table protocol versions — the project
    treats every table as readable by the standard Delta reader and
    writer versions — so on load responses this model is synthesised
    with a fixed default. On write paths (``createTable``,
    ``set-protocol`` update), the model is accepted from the client
    but its values are discarded; the response echoes the client's
    values so well-behaved clients see no drift within a single
    session. Documented in ADR-0009.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    min_reader_version: int = Field(alias="min-reader-version")
    min_writer_version: int = Field(alias="min-writer-version")
    reader_features: list[str] = Field(default_factory=list, alias="reader-features")
    writer_features: list[str] = Field(default_factory=list, alias="writer-features")


class DeltaColumn(BaseModel):
    """One column in a Delta table as carried on the Delta REST wire.

    The ``type`` field is a **string-or-object union**: a primitive
    like ``"long"`` or ``"decimal(10,2)"`` is a bare JSON string,
    while a complex type (``array``, ``map``, ``struct``) is a nested
    JSON object whose own ``type`` field discriminates the variant.
    OpenAPI cannot express this union, so upstream
    ``delta.yaml`` leaves the field untyped and Delta clients parse
    it through their own type serialiser. soyuz therefore models it
    as ``str | dict[str, Any]`` and round-trips it verbatim via
    :class:`soyuz_catalog.models.Column.type_json`; see
    ADR-0009 for the storage strategy.

    ``metadata`` carries arbitrary Spark/Delta per-column metadata
    (comments, column-mapping ids, generated-column expressions).
    soyuz accepts any JSON object and stores it in the column's
    ``type_json`` payload alongside the type — clients are free to
    attach whatever they need.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: str
    type: str | dict[str, Any]
    nullable: bool
    metadata: dict[str, Any] = Field(default_factory=dict)


class DomainMetadataUpdates(BaseModel):
    """Known Delta domain-metadata subkeys, plus a catch-all via ``extra``.

    soyuz does not store domain metadata (clustering config, row
    tracking) because nothing in the project consumes it. The model
    still validates the shape so that ``set-domain-metadata`` updates
    can be parsed and then silently discarded — rejecting them would
    break Delta clients that always emit them. See ADR-0009.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True)


# ---------------------------------------------------------------------------
# Table metadata + list/load responses
# ---------------------------------------------------------------------------


class DeltaLogCommit(BaseModel):
    """One unbackfilled CCv2 commit.

    soyuz does not act as a Delta commit coordinator (see ADR-0006),
    so this model only exists so :class:`LoadTableResponse` can
    declare ``commits: list[DeltaLogCommit]`` — the list is always
    empty on the wire. Kept in the module so the generated OpenAPI
    schema matches the upstream ``delta.yaml`` field-for-field.

    Named ``DeltaLogCommit`` rather than ``DeltaCommit`` to avoid
    an OpenAPI schema-name collision with the unrelated
    :class:`soyuz_catalog.api.schemas.DeltaCommit` request body
    for the commit coordinator endpoint — openapi-python-client
    cannot disambiguate two schemas that share a leaf name.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    version: int
    timestamp: int
    file_name: str = Field(alias="file-name")
    file_size: int = Field(alias="file-size")
    file_modification_timestamp: int = Field(alias="file-modification-timestamp")


class TableMetadata(BaseModel):
    """Complete table metadata in the Delta REST wire format.

    Mirrors the spec's ``TableMetadata`` shape but populated entirely
    from soyuz' existing :class:`soyuz_catalog.models.Table` state:

    * ``etag`` is synthesised from ``Table.updated_at`` so optimistic
      concurrency works without adding a database column.
    * ``table_uuid`` is the opaque row id (already 32-char hex).
    * ``protocol`` is a fixed default; see :class:`DeltaProtocol`.
    * ``columns`` is reconstructed from the live :class:`Column` rows.
    * ``partition_columns`` is derived from ``Column.partition_index``.
    * ``securable_type`` is always ``"TABLE"`` in the MVP; the spec
      also lists ``"VIEW"`` but soyuz has no views.
    * ``last-commit-version`` / ``last-commit-timestamp-ms`` are
      optional in the spec and always absent in soyuz because there
      is no commit coordinator.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    etag: str
    data_source_format: str = Field(alias="data-source-format")
    table_type: str = Field(alias="table-type")
    table_uuid: str = Field(alias="table-uuid")
    location: str
    created_time: int = Field(alias="created-time")
    updated_time: int = Field(alias="updated-time")
    securable_type: Literal["TABLE", "VIEW"] = Field(alias="securable-type")
    columns: list[DeltaColumn]
    partition_columns: list[str] = Field(default_factory=list, alias="partition-columns")
    protocol: DeltaProtocol
    properties: dict[str, str] = Field(default_factory=dict)


class LoadTableResponse(BaseModel):
    """Response body for ``GET .../tables/{table}`` and ``createTable``.

    soyuz always returns ``commits = []`` (ADR-0006, no coordinator)
    and omits ``uniform`` and ``latest_table_version``. The metadata
    field carries the full :class:`TableMetadata`. Strict-``forbid``
    so clients see a byte-identical body across calls against an
    unchanged row.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    metadata: TableMetadata
    commits: list[DeltaLogCommit] = Field(default_factory=list)


class TableIdentifierWithDataSourceFormat(BaseModel):
    """One entry in a ``listTables`` response.

    Only the leaf name and the data-source-format are exposed — the
    parent catalog and schema are implicit from the request path, so
    echoing them would be redundant with the URL.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: str
    data_source_format: str = Field(alias="data-source-format")


class DeltaListTablesResponse(BaseModel):
    """Paginated ``listTables`` response.

    Shape matches the spec verbatim: a list of
    :class:`TableIdentifierWithDataSourceFormat` entries plus an
    optional ``next-page-token`` (absent on the last page). soyuz'
    existing keyset pagination is reused under the hood; see
    :func:`soyuz_catalog.services.table_service.list_tables`.

    Named ``DeltaListTablesResponse`` rather than ``ListTablesResponse``
    to avoid an OpenAPI schema-name collision with the unrelated
    :class:`soyuz_catalog.api.schemas.ListTablesResponse` (the UC
    ``/tables`` response) — openapi-python-client cannot disambiguate
    two schemas that share a leaf name.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    identifiers: list[TableIdentifierWithDataSourceFormat] = Field(default_factory=list)
    next_page_token: str | None = Field(default=None, alias="next-page-token")


# ---------------------------------------------------------------------------
# Create / update / rename request bodies
# ---------------------------------------------------------------------------


class CreateTableRequest(BaseModel):
    """Request body for ``POST .../tables``.

    Every field mirrors the spec's ``CreateTableRequest``. The
    ``protocol`` and ``domain_metadata`` fields are **accepted and
    discarded** by the service layer — soyuz does not track per-table
    protocol versions or domain metadata and rejecting them would
    break Delta clients that always emit them. See ADR-0009.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: str
    location: str
    table_type: Literal["MANAGED", "EXTERNAL"] = Field(alias="table-type")
    data_source_format: Literal[
        "DELTA",
        "ICEBERG",
        "CSV",
        "JSON",
        "AVRO",
        "PARQUET",
        "ORC",
        "TEXT",
    ] = Field(alias="data-source-format")
    comment: str | None = None
    columns: list[DeltaColumn]
    partition_columns: list[str] = Field(default_factory=list, alias="partition-columns")
    protocol: DeltaProtocol
    properties: dict[str, str] = Field(default_factory=dict)
    domain_metadata: DomainMetadataUpdates | None = Field(default=None, alias="domain-metadata")


class RenameTableRequest(BaseModel):
    """Request body for ``POST .../tables/{table}/rename``.

    The spec is minimal — a single ``new-name`` field. soyuz surfaces
    an empty string as 400 ``INVALID_ARGUMENT`` at the service layer
    rather than relying on pydantic's ``min_length`` so the error
    message matches the rest of the service's 400 envelope shape.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    new_name: str = Field(alias="new-name")


# ---------------------------------------------------------------------------
# Discriminated unions: TableRequirement and TableUpdate
# ---------------------------------------------------------------------------


class AssertTableUUID(BaseModel):
    """``assert-table-uuid`` pre-condition variant of ``TableRequirement``.

    soyuz implements this as a plain string equality check against
    :class:`soyuz_catalog.models.Table.id`. A failure maps to 409
    :class:`soyuz_catalog.exceptions.ConflictError` with the
    dedicated ``REQUIREMENT_NOT_MET`` error_code so clients can tell
    the failure apart from a duplicate-name conflict.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    type: Literal["assert-table-uuid"]
    uuid: str


class AssertEtag(BaseModel):
    """``assert-etag`` pre-condition variant of ``TableRequirement``.

    The etag soyuz synthesises is ``str(Table.updated_at)`` — every
    mutation bumps ``updated_at``, so a stale etag fails the
    assertion. A failure maps to 409 ``REQUIREMENT_NOT_MET`` just
    like :class:`AssertTableUUID`.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    type: Literal["assert-etag"]
    etag: str


TableRequirement = Annotated[
    AssertTableUUID | AssertEtag,
    Field(discriminator="type"),
]


class SetPropertiesUpdate(BaseModel):
    """Merge the given ``updates`` dict into the table's ``properties``.

    Semantics match Delta's own ``setTableProperties``: keys in
    ``updates`` overwrite existing entries; keys absent from
    ``updates`` are left untouched (it is **not** a replace of the
    full properties map — use the combination
    ``remove-properties`` + ``set-properties`` for that).
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    action: Literal["set-properties"]
    updates: dict[str, str]


class RemovePropertiesUpdate(BaseModel):
    """Remove the listed property keys from the table.

    Silently ignores keys that are not present, matching Delta's own
    ``unsetTableProperties`` semantics and every other idempotent
    delete path in soyuz.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    action: Literal["remove-properties"]
    removals: list[str]


class SetSchemaUpdate(BaseModel):
    """Replace the table's column list in full.

    The ``columns`` array is applied as a full replacement; the
    existing :class:`soyuz_catalog.models.Column` rows are dropped
    and re-inserted by the service layer in the order given. This
    matches Delta's own schema-evolution wire shape (the client
    always sends the full post-state) and avoids soyuz having to
    model per-column diffs.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    action: Literal["set-columns"]
    columns: list[DeltaColumn]


class SetTableCommentUpdate(BaseModel):
    """Overwrite the table's comment in place.

    Empty string is accepted as "clear the comment" — soyuz stores
    it as ``NULL`` in that case, matching the ``UpdateTable``
    convention from the main UC API.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    action: Literal["set-table-comment"]
    comment: str


class AddCommitUpdate(BaseModel):
    """Register a CCv2 commit — **rejected** by soyuz as 501.

    soyuz does not act as a Delta commit coordinator (ADR-0006). The
    model still parses so the discriminated union round-trips and
    the route handler emits a dedicated
    ``COMMIT_COORDINATOR_UNSUPPORTED`` envelope instead of a generic
    422. See
    :class:`soyuz_catalog.exceptions.CommitCoordinatorUnsupportedError`.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    action: Literal["add-commit"]
    commit: DeltaLogCommit
    uniform: dict[str, Any] | None = None


class SetLatestBackfilledVersionUpdate(BaseModel):
    """``set-latest-backfilled-version`` — **rejected** as 501.

    Same posture as :class:`AddCommitUpdate`: this is
    commit-coordinator territory and soyuz rejects the whole class
    with a dedicated error code. ADR-0006.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    action: Literal["set-latest-backfilled-version"]
    latest_published_version: int = Field(alias="latest-published-version")


class SetProtocolUpdate(BaseModel):
    """``set-protocol`` — accepted as a no-op.

    soyuz does not track per-table protocol versions; rejecting
    these would break clients that always bump protocol on write.
    The service layer logs a warning and discards the payload; the
    response echoes the original client value so well-behaved
    clients see no drift. ADR-0009.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    action: Literal["set-protocol"]
    protocol: DeltaProtocol


class SetDomainMetadataUpdate(BaseModel):
    """``set-domain-metadata`` variant of :data:`TableUpdate`.

    Delta clients emit this action whenever clustering config or row
    tracking changes; soyuz does not store domain metadata at all
    because nothing in the project consumes it. The payload is
    validated so malformed shapes still surface as 422, but the
    service layer silently discards it. Rejecting would break every
    Delta client that always emits ``delta.clustering`` or
    ``delta.rowTracking`` on schema evolution. ADR-0009 covers the
    accept-and-discard posture.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    action: Literal["set-domain-metadata"]
    updates: DomainMetadataUpdates


class RemoveDomainMetadataUpdate(BaseModel):
    """``remove-domain-metadata`` variant of :data:`TableUpdate`.

    Complementary to :class:`SetDomainMetadataUpdate`: clients use it
    to drop a domain entry (clustering config, row tracking) that
    they previously set. soyuz never stored those entries in the
    first place, so the action is parsed and then silently
    discarded. ADR-0009.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    action: Literal["remove-domain-metadata"]
    domains: list[str]


class SetPartitionColumnsUpdate(BaseModel):
    """Replace the set of partition-column names.

    soyuz stores this information on the child
    :class:`soyuz_catalog.models.Column` rows via ``partition_index``
    rather than as a separate array; the service layer rebuilds
    ``partition_index`` for every column on each update so the two
    representations stay in sync.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    action: Literal["set-partition-columns"]
    partition_columns: list[str] = Field(alias="partition-columns")


class UpdateSnapshotVersionUpdate(BaseModel):
    """``update-metadata-snapshot-version`` — **rejected** as 501.

    External-tables-only post-commit-hook update; soyuz has no
    commit hook and no commit coordinator. ADR-0006 territory.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    action: Literal["update-metadata-snapshot-version"]
    last_commit_version: int = Field(alias="last-commit-version")
    last_commit_timestamp_ms: int = Field(alias="last-commit-timestamp-ms")


class AddConstraintUpdate(BaseModel):
    """``add-constraint`` variant of :data:`TableUpdate` (ADR-0012).

    Implemented in full: the service layer validates the
    constraint per type (column existence, at-most-one PK, FK
    parent resolution) and inserts a fresh row on the new
    ``table_constraints`` table. Rejecting duplicates by name on
    the same table returns 409 ``ALREADY_EXISTS`` via the
    ``(table_id, name)`` unique constraint — same race-safety
    posture as every other create path. See ADR-0012 for the
    rename-invariance and metadata-only rationale.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    action: Literal["add-constraint"]
    constraint: TableConstraintPayload


class DropConstraintUpdate(BaseModel):
    """``drop-constraint`` variant of :data:`TableUpdate` (ADR-0012).

    Drops the constraint with the given ``name`` from the target
    table. With ``if_exists=False`` (the default) a missing
    constraint raises 404 ``NOT_FOUND``; with ``if_exists=True``
    the call is a no-op. Matches the Delta spec's tri-state
    ``NOT_FOUND | found | noop`` pattern for idempotent DDL and
    aligns with ``RemovePropertiesUpdate``'s silent-ignore posture
    on missing keys.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    action: Literal["drop-constraint"]
    name: str
    if_exists: bool = Field(default=False, alias="if-exists")


TableUpdate = Annotated[
    SetPropertiesUpdate
    | RemovePropertiesUpdate
    | SetSchemaUpdate
    | SetTableCommentUpdate
    | AddCommitUpdate
    | SetLatestBackfilledVersionUpdate
    | SetProtocolUpdate
    | SetDomainMetadataUpdate
    | RemoveDomainMetadataUpdate
    | SetPartitionColumnsUpdate
    | UpdateSnapshotVersionUpdate
    | AddConstraintUpdate
    | DropConstraintUpdate,
    Field(discriminator="action"),
]


class UpdateTableRequest(BaseModel):
    """Request body for ``POST .../tables/{table}``.

    Pre-conditions in ``requirements`` are validated first and a
    failure on any of them short-circuits the whole batch with 409
    before any mutation runs. Updates in ``updates`` are applied in
    order; a 501 on a commit-coordinator action (``add-commit`` et
    al.) happens at the very first such entry, leaving earlier
    entries in place — consistent with Delta's own
    "append-only commit" story for the parts that are applied and
    soyuz' "fail fast on unsupported" posture everywhere else.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    requirements: list[TableRequirement] = Field(default_factory=list)
    updates: list[TableUpdate] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Staging tables
# ---------------------------------------------------------------------------


class CreateStagingTableRequest(BaseModel):
    """Request body for ``POST .../staging-tables``.

    Single field: the leaf name of the staging-table allocation.
    The parent catalog and schema come from the path. soyuz reuses
    the existing
    :func:`soyuz_catalog.services.staging_table_service.create_staging_table`
    under the hood and augments the response with the Delta-specific
    protocol and credential fields.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: str


class SuggestedProtocol(BaseModel):
    """Suggested Delta features a client should enable if supported.

    soyuz advertises none — it does not have an opinion about which
    features a staging-table writer *should* use, only a minimum it
    *must* satisfy, which is carried by :class:`DeltaProtocol` on the
    ``required_protocol`` field.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    reader_features: list[str] = Field(default_factory=list, alias="reader-features")
    writer_features: list[str] = Field(default_factory=list, alias="writer-features")


class StorageCredential(BaseModel):
    """Temporary storage credential — always empty on the wire in soyuz.

    soyuz does not vend cloud credentials (explicitly out of scope —
    metadata-only is design principle 3 in the README). The model exists so
    :class:`CredentialsResponse` and :class:`StagingTableResponse`
    can declare the field on the spec-defined shape; the list is
    always empty. Clients that use the returned storage location
    directly via ``file://`` or an externally-configured credential
    see no difference.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    prefix: str
    operation: Literal["READ", "READ_WRITE"]
    expiration_time_ms: int = Field(alias="expiration-time-ms")
    config: dict[str, str] = Field(default_factory=dict)


class StagingTableResponse(BaseModel):
    """Response body for ``createStagingTable``.

    The ``location`` is derived from the existing
    :class:`soyuz_catalog.models.StagingTable.staging_location` so a
    Delta client reaches the same UC-managed path through either the
    main UC API or the Delta API. ``required_protocol`` is soyuz'
    fixed default; ``storage_credentials`` is always empty; the
    ``required_properties`` and ``suggested_properties`` maps are
    always empty too — soyuz has no opinion on Delta-specific
    property constraints at allocation time.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    table_id: str = Field(alias="table-id")
    table_type: Literal["MANAGED"] = Field(alias="table-type")
    location: str
    storage_credentials: list[StorageCredential] = Field(
        default_factory=list,
        alias="storage-credentials",
    )
    required_protocol: DeltaProtocol = Field(alias="required-protocol")
    suggested_protocol: SuggestedProtocol = Field(
        default_factory=SuggestedProtocol,
        alias="suggested-protocol",
    )
    required_properties: dict[str, str | None] = Field(
        default_factory=dict,
        alias="required-properties",
    )
    suggested_properties: dict[str, str | None] = Field(
        default_factory=dict,
        alias="suggested-properties",
    )


# ---------------------------------------------------------------------------
# Credentials and metrics (stubs)
# ---------------------------------------------------------------------------


class CredentialsResponse(BaseModel):
    """Response for every credential-vending endpoint in the Delta API.

    soyuz always returns ``storage_credentials = []``. This matches
    the existing soyuz temporary-credentials stub posture (see
    ``DIVERGENCES.md``) and is preferred over a 501 because Delta
    clients interpret an empty list as "use the URL directly" and
    keep progressing, whereas a 501 would abort the whole write
    path on a non-feature. ADR-0009 covers the rationale.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    storage_credentials: list[StorageCredential] = Field(
        default_factory=list,
        alias="storage-credentials",
    )


class FileSizeHistogram(BaseModel):
    """Histogram payload inside a ``reportMetrics`` commit report.

    Accepted but discarded. Present only so the request body parses
    cleanly — no soyuz code reads any field.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    sorted_bin_boundaries: list[int] = Field(alias="sorted-bin-boundaries")
    file_counts: list[int] = Field(alias="file-counts")
    total_bytes: list[int] = Field(alias="total-bytes")
    commit_version: int | None = Field(default=None, alias="commit-version")


class CommitReport(BaseModel):
    """Commit-level metrics inside a ``reportMetrics`` request.

    Accepted but discarded. Every field is optional because Delta
    clients emit slightly different shapes depending on the commit
    type (data-only vs metadata vs mixed). soyuz stores nothing.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    num_files_added: int | None = Field(default=None, alias="num-files-added")
    num_bytes_added: int | None = Field(default=None, alias="num-bytes-added")
    num_files_removed: int | None = Field(default=None, alias="num-files-removed")
    num_bytes_removed: int | None = Field(default=None, alias="num-bytes-removed")
    num_rows_inserted: int | None = Field(default=None, alias="num-rows-inserted")
    num_rows_removed: int | None = Field(default=None, alias="num-rows-removed")
    num_rows_updated: int | None = Field(default=None, alias="num-rows-updated")
    file_size_histogram: FileSizeHistogram | None = Field(
        default=None,
        alias="file-size-histogram",
    )


class MetricsReport(BaseModel):
    """``report`` block of a ``reportMetrics`` request.

    Accepted but discarded. Wraps :class:`CommitReport` with room
    for future metric kinds the Delta spec may add.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    commit_report: CommitReport | None = Field(default=None, alias="commit-report")


class ReportMetricsRequest(BaseModel):
    """Request body for ``POST .../tables/{table}/metrics``.

    soyuz parses the body (so a malformed payload surfaces as 422)
    and then discards it — there is no metrics sink in the project.
    The 204 response is accept-and-discard; ADR-0009 explains why
    this beats 501 for Delta client compatibility.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    table_id: str = Field(alias="table-id")
    report: MetricsReport | None = None


# ---------------------------------------------------------------------------
# /v1/config
# ---------------------------------------------------------------------------


class CatalogConfig(BaseModel):
    """Response body for ``GET /v1/config``.

    Advertises the list of endpoint paths soyuz implements under
    the Delta surface and the negotiated protocol version. soyuz
    has exactly one implementation (``"1.0"``) so the
    ``protocol-versions`` query parameter does not branch behaviour.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    endpoints: list[str]
    protocol_version: str = Field(alias="protocol-version")
