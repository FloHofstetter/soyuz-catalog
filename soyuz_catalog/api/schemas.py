"""Pydantic request/response schemas for the soyuz-catalog REST API."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CatalogInfo(BaseModel):
    """Response shape for a Unity Catalog catalog.

    All fields are optional in the spec; we always populate the system
    fields we own. ``type``, ``connection_name``, and ``options`` back
    the Lakehouse-Federation foreign-catalog variant (ADR-0013): a
    managed catalog serialises with ``type="MANAGED"`` and leaves the
    two connection fields
    ``None`` (the route's ``exclude_none`` drops them from the wire);
    a foreign catalog flips ``type`` to ``"FOREIGN"``, populates
    ``connection_name`` from the live :class:`soyuz_catalog.models.Connection`
    relationship (rename-invariant, same trick as
    :class:`ExternalLocationInfo.credential_name`), and leaves
    ``storage_root`` / ``storage_location`` ``None``.
    """

    model_config = ConfigDict(from_attributes=True)

    name: str | None = None
    comment: str | None = None
    properties: dict[str, str] | None = None
    owner: str | None = None
    created_at: int | None = None
    created_by: str | None = None
    updated_at: int | None = None
    updated_by: str | None = None
    id: str | None = None
    storage_root: str | None = None
    storage_location: str | None = None
    type: Literal["MANAGED", "FOREIGN"] | None = None
    connection_name: str | None = None
    options: dict[str, str] | None = None


class CreateCatalog(BaseModel):
    """Request body for ``POST /catalogs``.

    Only ``name`` is required by the spec; everything else is optional and
    defaults to ``None`` / empty. ``extra="forbid"`` mirrors the same policy
    used on ``UpdateCatalog``: silently dropping unknown fields is the UC OSS
    Java bug we exist to fix, so we reject them with HTTP 422 on create as
    well as on update.

    The Lakehouse-Federation foreign-catalog variant is opt-in: pass ``type="FOREIGN"``
    together with ``connection_name`` (and optional per-connector
    ``options``) and leave ``storage_root`` absent. The managed default
    is ``type="MANAGED"`` and the service layer rejects the two shapes'
    fields cross-contaminating — see ``catalog_service.create_catalog``
    for the exact gates and ``DIVERGENCES.md`` for the rule set.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    comment: str | None = None
    properties: dict[str, str] | None = None
    storage_root: str | None = None
    type: Literal["MANAGED", "FOREIGN"] | None = None
    connection_name: str | None = None
    options: dict[str, str] | None = None


class UpdateCatalog(BaseModel):
    """Request body for ``PATCH /catalogs/{name}``.

    Replace-style PATCH semantics: every field is optional, but a field that
    *is* present in the request body — including ``properties: {}`` — is
    written through to the row. The service layer reads ``model_fields_set``
    rather than checking ``is None`` so it can distinguish "field omitted"
    from "field set to null/empty".

    ``extra="forbid"`` rejects unknown or read-only fields (e.g. ``owner``)
    with HTTP 422 instead of silently ignoring them as UC OSS Java does. This
    is one of the documented divergences from the Java reference; see
    ``DIVERGENCES.md``.

    The catalog ``type`` field is **deliberately not exposed** on this
    shape: flipping a managed catalog to foreign (or vice versa) would
    orphan the other variant's bookkeeping state (``storage_location``
    on managed, ``connection_id`` on foreign) and has no well-defined
    semantics. A catalog's type is decided at create time and frozen.
    ``connection_name`` PATCH is accepted on foreign catalogs only; the
    service rejects it with 400 on a managed catalog. ``options`` PATCH
    is allowed on both and is replace-style like ``properties``.
    """

    model_config = ConfigDict(extra="forbid")

    new_name: str | None = None
    comment: str | None = None
    properties: dict[str, str] | None = None
    connection_name: str | None = None
    options: dict[str, str] | None = None


class SchemaInfo(BaseModel):
    """Response shape for a Unity Catalog schema.

    ``full_name`` is always populated by the API layer from the parent
    catalog's current name plus the schema's own name. It is never read from
    the database — see :class:`soyuz_catalog.models.Schema` for the rationale.
    All other fields mirror ``CatalogInfo``: optional on the wire, always
    populated for rows the server owns.
    """

    model_config = ConfigDict(from_attributes=True)

    name: str | None = None
    catalog_name: str | None = None
    full_name: str | None = None
    comment: str | None = None
    properties: dict[str, str] | None = None
    owner: str | None = None
    created_at: int | None = None
    created_by: str | None = None
    updated_at: int | None = None
    updated_by: str | None = None
    schema_id: str | None = None
    storage_root: str | None = None
    storage_location: str | None = None


class CreateSchema(BaseModel):
    """Request body for ``POST /schemas``.

    ``name`` and ``catalog_name`` are both required — a schema cannot exist
    without knowing which catalog it lives under, and the spec addresses
    schemas by relative name. ``extra="forbid"`` rejects unknown fields, same
    policy as :class:`CreateCatalog`.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    catalog_name: str = Field(min_length=1)
    comment: str | None = None
    properties: dict[str, str] | None = None
    storage_root: str | None = None


class UpdateSchema(BaseModel):
    """Request body for ``PATCH /schemas/{full_name}``.

    Shape is intentionally identical to :class:`UpdateCatalog`: replace-style
    PATCH semantics driven by ``model_fields_set`` in the service layer, and
    ``extra="forbid"`` rejects unknown or read-only fields (including
    ``owner``, ``catalog_name``, ``full_name``) with HTTP 422 instead of
    silently dropping them.
    """

    model_config = ConfigDict(extra="forbid")

    new_name: str | None = None
    comment: str | None = None
    properties: dict[str, str] | None = None


class ListSchemasResponse(BaseModel):
    """Response shape for ``GET /schemas``.

    ``next_page_token`` is the opaque keyset cursor — ``None`` on the
    last page, otherwise the encoded ``(created_at, id)`` tuple to
    feed back as ``page_token`` on the next call. See
    :mod:`soyuz_catalog.pagination` and ADR-0003.
    """

    schemas: list[SchemaInfo]
    next_page_token: str | None = None


class ColumnInfo(BaseModel):
    """A single column in a Unity Catalog table.

    The same shape is used for both create requests (as an element of
    ``CreateTable.columns``) and read responses (as an element of
    ``TableInfo.columns``) — UC OpenAPI defines one ``ColumnInfo`` schema
    for both directions. On create every field is logically optional at
    the Pydantic level; the service layer relies on the fact that the
    non-nullable ORM columns (``name``, ``type_text``, ``type_json``,
    ``type_name``, ``position``) will raise an ``IntegrityError`` if
    omitted, which is surfaced as a 422 by the request validator when the
    field is missing from the payload entirely.

    ``extra="forbid"`` rejects unknown fields inside a column the same way
    it does on the top-level request: a typo like ``type_neme`` must not
    be silently dropped.
    """

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    name: str | None = None
    type_text: str | None = None
    type_json: str | None = None
    type_name: str | None = None
    type_precision: int | None = None
    type_scale: int | None = None
    type_interval_type: str | None = None
    position: int | None = None
    comment: str | None = None
    nullable: bool | None = None
    partition_index: int | None = None


class PrimaryKeyConstraint(BaseModel):
    """``PRIMARY KEY`` constraint payload (ADR-0012).

    A metadata-only declaration that the listed columns form the
    primary key of the table. soyuz does not enforce the declaration
    at write time — there is no query engine to check it against —
    but round-trips it verbatim so Spark / dbt / downstream catalog
    UIs that read declared constraints see the same metadata they
    would against Databricks.

    At most one :class:`PrimaryKeyConstraint` is allowed per table;
    adding a second one raises 409 ``ALREADY_EXISTS``. The spec does
    not pin this uniqueness rule but every SQL engine soyuz interoperates
    with does, so rejecting at write time is less confusing than a
    silent last-write-wins semantic.
    """

    model_config = ConfigDict(extra="forbid")

    child_columns: list[str] = Field(min_length=1)


class ForeignKeyConstraint(BaseModel):
    """``FOREIGN KEY`` constraint payload (ADR-0012).

    A metadata-only declaration that the ``child_columns`` on the
    owning table reference ``parent_columns`` on ``parent_table``.
    ``parent_table`` is a three-part dotted full_name on the wire
    and is resolved to an opaque ``parent_table_id`` at write time
    so a rename of *either* side leaves the declaration intact —
    the same rename-invariance trick permissions / tags / lineage
    use. On response the opaque id is reconstructed back into a
    live three-part name.

    soyuz does not enforce referential integrity — there is no
    query engine — but the presence of the declaration is enough
    for catalog UIs and query planners that do.
    """

    model_config = ConfigDict(extra="forbid")

    child_columns: list[str] = Field(min_length=1)
    parent_table: str = Field(min_length=1)
    parent_columns: list[str] = Field(min_length=1)


class CheckConstraint(BaseModel):
    """``CHECK`` constraint payload (ADR-0012).

    A metadata-only declaration that ``sql_text`` should hold for
    every row of the table. soyuz does **not** parse the predicate
    — the string is stored verbatim and round-tripped unchanged —
    because the dialect of the predicate depends on the query
    engine that will eventually evaluate it (Spark SQL, Trino SQL,
    DuckDB SQL, …) and pinning a single parser here would reject
    perfectly valid predicates for other engines.

    ``child_columns`` is informational: clients that produce the
    constraint from an AST pre-computed the referenced column set
    and include it so readers do not have to re-parse the predicate.
    The list is not validated against the table's columns.
    """

    model_config = ConfigDict(extra="forbid")

    child_columns: list[str] = Field(default_factory=list)
    sql_text: str = Field(min_length=1)


class NotNullConstraint(BaseModel):
    """Named ``NOT NULL`` constraint payload (ADR-0012).

    Named NOT NULL constraints are a *second* concept alongside the
    unnamed :class:`soyuz_catalog.models.Column.nullable` flag, not
    a replacement: the column flag stays authoritative for the
    column's nullability, and adding / dropping this named
    constraint deliberately does *not* flip it. Databricks models
    them the same way — the two can disagree in practice, and
    soyuz does not second-guess that — and flipping the column
    flag as a side effect of adding a constraint would reintroduce
    the silent-side-effects class that the "no table PATCH"
    invariant (Tables resource has no update endpoint in the UC
    spec) was designed to prevent.
    """

    model_config = ConfigDict(extra="forbid")

    child_column: str = Field(min_length=1)


class TableConstraint(BaseModel):
    """A single declared constraint on a table (ADR-0012).

    The wire shape mirrors the Databricks public SDK
    ``databricks.sdk.service.catalog.TableConstraint`` envelope so
    that a client that already knows Databricks' shape does not
    have to relearn. Exactly one of the four per-type fields is
    populated on the wire — the envelope is a thin discriminated
    union over :class:`PrimaryKeyConstraint` /
    :class:`ForeignKeyConstraint` / :class:`CheckConstraint` /
    :class:`NotNullConstraint`. A request with zero or more than
    one populated is rejected by the service layer with
    400 ``INVALID_ARGUMENT``.

    ``name`` is a user-chosen identifier unique per table (the
    ORM table enforces ``(table_id, name)``). It is the address
    used by ``drop-constraint`` — rename / re-add is not in scope.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    primary_key_constraint: PrimaryKeyConstraint | None = None
    foreign_key_constraint: ForeignKeyConstraint | None = None
    check_constraint: CheckConstraint | None = None
    named_table_constraint: NotNullConstraint | None = None


class TableInfo(BaseModel):
    """Response shape for a Unity Catalog table.

    ``full_name`` is computed from the live parent catalog and schema names
    at response time — never stored — so a rename of either parent
    propagates to every child table for free. ``columns`` is always
    populated from the live ``table_columns`` rows, ordered by ``position``
    via the ORM relationship's ``order_by``.

    ``table_constraints`` (ADR-0012) is the ordered list of
    declared constraints; it is populated from live ``table_constraints``
    rows at response time and is ``None`` (not ``[]``) when the table has
    no declared constraints — matches how other optional nested fields
    behave and keeps existing fixtures stable.
    """

    model_config = ConfigDict(from_attributes=True)

    name: str | None = None
    catalog_name: str | None = None
    schema_name: str | None = None
    full_name: str | None = None
    table_type: str | None = None
    data_source_format: str | None = None
    columns: list[ColumnInfo] | None = None
    storage_location: str | None = None
    comment: str | None = None
    properties: dict[str, str] | None = None
    owner: str | None = None
    created_at: int | None = None
    created_by: str | None = None
    updated_at: int | None = None
    updated_by: str | None = None
    table_id: str | None = None
    table_constraints: list[TableConstraint] | None = None


class CreateTable(BaseModel):
    """Request body for ``POST /tables``.

    The UC spec requires ``name``, ``catalog_name``, ``schema_name``,
    ``table_type``, ``data_source_format``, ``columns``, and
    ``storage_location`` on create — there is no legitimate table without
    a physical storage location or a declared format, even for managed
    tables where the server will later rewrite it.

    ``extra="forbid"`` rejects unknown fields; the same policy applies to
    each element of ``columns`` via :class:`ColumnInfo`. There is no
    ``UpdateTable`` counterpart: the UC OpenAPI spec defines no
    ``PATCH /tables`` endpoint and soyuz registers no handler for it, so
    the route returns 405 Method Not Allowed (see ``DIVERGENCES.md``).
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    catalog_name: str = Field(min_length=1)
    schema_name: str = Field(min_length=1)
    table_type: str = Field(min_length=1)
    data_source_format: str = Field(min_length=1)
    columns: list[ColumnInfo]
    storage_location: str = Field(min_length=1)
    comment: str | None = None
    properties: dict[str, str] | None = None


class ListTablesResponse(BaseModel):
    """Response shape for ``GET /tables``.

    ``next_page_token`` is the opaque keyset cursor — ``None`` on the
    last page, otherwise the encoded ``(created_at, id)`` tuple to
    feed back as ``page_token`` on the next call. See
    :mod:`soyuz_catalog.pagination` and ADR-0003.
    """

    tables: list[TableInfo]
    next_page_token: str | None = None


class VolumeInfo(BaseModel):
    """Response shape for a Unity Catalog volume.

    Mirrors :class:`TableInfo`: ``full_name`` is computed at response time
    from the live parent catalog and schema names, never stored, so a
    rename of either parent propagates to every child volume for free.

    Unlike :class:`CatalogInfo` and :class:`SchemaInfo` there is no
    ``properties`` field — the UC OpenAPI ``VolumeInfo`` shape does not
    define one, and we do not silently extend the spec.
    """

    model_config = ConfigDict(from_attributes=True)

    name: str | None = None
    catalog_name: str | None = None
    schema_name: str | None = None
    full_name: str | None = None
    volume_type: str | None = None
    storage_location: str | None = None
    comment: str | None = None
    owner: str | None = None
    created_at: int | None = None
    created_by: str | None = None
    updated_at: int | None = None
    updated_by: str | None = None
    volume_id: str | None = None


class CreateVolume(BaseModel):
    """Request body for ``POST /volumes``.

    The UC spec requires ``catalog_name``, ``schema_name``, ``name``, and
    ``volume_type`` on create. ``storage_location`` and ``comment`` are
    optional. ``volume_type`` is constrained to the spec enum
    ``{"MANAGED", "EXTERNAL"}`` at the Pydantic layer so that a typo
    surfaces as 422 rather than reaching the database as a free-form
    string.

    ``extra="forbid"`` rejects unknown fields, same UC OSS bug-fix policy
    as every other request body in this module.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    catalog_name: str = Field(min_length=1)
    schema_name: str = Field(min_length=1)
    volume_type: Literal["MANAGED", "EXTERNAL"]
    storage_location: str | None = None
    comment: str | None = None


class UpdateVolume(BaseModel):
    """Request body for ``PATCH /volumes/{name}``.

    The UC spec is explicit that *only* ``new_name`` and ``comment`` may
    be updated on a volume — ``storage_location`` and ``volume_type`` are
    immutable (a managed volume cannot become external mid-life, and the
    underlying storage path cannot be moved without re-registering the
    volume). Volumes have no ``properties`` field on the wire, so there
    is no PATCH path for them either.

    ``extra="forbid"`` rejects unknown or read-only fields (including
    ``storage_location``, ``volume_type``, ``owner``, ``catalog_name``)
    with HTTP 422 instead of silently dropping them.
    """

    model_config = ConfigDict(extra="forbid")

    new_name: str | None = None
    comment: str | None = None


class ListVolumesResponse(BaseModel):
    """Response shape for ``GET /volumes``.

    ``next_page_token`` is the opaque keyset cursor — ``None`` on the
    last page, otherwise the encoded ``(created_at, id)`` tuple to
    feed back as ``page_token`` on the next call. See
    :mod:`soyuz_catalog.pagination` and ADR-0003.
    """

    volumes: list[VolumeInfo]
    next_page_token: str | None = None


class GenerateTemporaryTableCredential(BaseModel):
    """Request body for ``POST /temporary-table-credentials``.

    The UC spec addresses the table by its opaque ``table_id`` rather than
    its ``full_name`` because credentials are scoped to the physical
    storage identity, not the namespace path: a rename of the parent
    catalog or schema must not invalidate an outstanding credential.

    ``operation`` is a tri-state enum in the spec
    (``UNKNOWN_TABLE_OPERATION``, ``READ``, ``READ_WRITE``). We accept the
    two real values via :class:`typing.Literal` so a typo surfaces as 422
    at the Pydantic layer and reject ``UNKNOWN_TABLE_OPERATION`` at the
    service layer as an invalid request — the sentinel exists in the spec
    only as a protobuf default and accepting it here would reproduce the
    same silently-accept-garbage behaviour that ``extra="forbid"`` is
    everywhere else written to prevent (see ``DIVERGENCES.md``).
    """

    model_config = ConfigDict(extra="forbid")

    table_id: str = Field(min_length=1)
    operation: Literal["UNKNOWN_TABLE_OPERATION", "READ", "READ_WRITE"]


class GenerateTemporaryVolumeCredential(BaseModel):
    """Request body for ``POST /temporary-volume-credentials``.

    Mirrors :class:`GenerateTemporaryTableCredential`: addresses the
    volume by its opaque ``volume_id`` and restricts ``operation`` to the
    spec enum. ``UNKNOWN_VOLUME_OPERATION`` is accepted at the Pydantic
    layer but rejected as an invalid request at the service layer for the
    same reason the table variant rejects its own sentinel.
    """

    model_config = ConfigDict(extra="forbid")

    volume_id: str = Field(min_length=1)
    operation: Literal["UNKNOWN_VOLUME_OPERATION", "READ_VOLUME", "WRITE_VOLUME"]


class GenerateTemporaryPathCredential(BaseModel):
    """Request body for ``POST /temporary-path-credentials``.

    Mirrors :class:`GenerateTemporaryTableCredential` / ...Volume: the
    request carries a user-supplied storage URL and a ``PathOperation``
    enum. ``PATH_READ`` / ``PATH_READ_WRITE`` / ``PATH_CREATE_TABLE``
    are the three real values; the protobuf-default
    ``UNKNOWN_PATH_OPERATION`` sentinel is accepted at the Pydantic
    layer and rejected at the service layer for the same reason the
    table/volume variants reject their own sentinels. Unknown keys
    surface as 422 via ``extra="forbid"``.
    """

    model_config = ConfigDict(extra="forbid")

    url: str = Field(min_length=1)
    operation: Literal[
        "UNKNOWN_PATH_OPERATION",
        "PATH_READ",
        "PATH_READ_WRITE",
        "PATH_CREATE_TABLE",
    ]


class GenerateTemporaryModelVersionCredential(BaseModel):
    """Request body for ``POST /temporary-model-version-credentials``.

    Implements MLflow's UC-OSS
    ``generateTemporaryModelVersionCredential`` RPC. The version is
    addressed by the four-part triple ``(catalog_name, schema_name,
    model_name, version)`` rather than an opaque ``model_version_id``
    because that is what the proto specifies — see
    ``unity_catalog_oss_messages.proto:GenerateTemporaryModelVersionCredential``.

    The operation enum follows the proto's ``ModelVersionOperation``:
    ``READ_MODEL_VERSION`` for downloads, ``READ_WRITE_MODEL_VERSION``
    for the create-then-upload flow. ``UNKNOWN_MODEL_VERSION_OPERATION``
    is the proto's default sentinel and is rejected as 400 at the
    service layer for the same reason the table/volume variants reject
    their own sentinels.
    """

    model_config = ConfigDict(extra="forbid")

    catalog_name: str = Field(min_length=1)
    schema_name: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    version: int = Field(ge=1)
    operation: Literal[
        "UNKNOWN_MODEL_VERSION_OPERATION",
        "READ_MODEL_VERSION",
        "READ_WRITE_MODEL_VERSION",
    ]


class AwsCredentials(BaseModel):
    """AWS STS temporary credentials payload (nested in ``TemporaryCredentials``).

    Shape mirrors the UC OpenAPI ``AwsCredentials`` schema exactly. soyuz
    never populates this object — real STS vending is out of scope (no
    credential vending; see README design principle 3) — but the class
    exists so the response schema is 1:1 with the spec for clients
    that rely on OpenAPI-generated types.
    """

    model_config = ConfigDict(from_attributes=True)

    access_key_id: str | None = None
    secret_access_key: str | None = None
    session_token: str | None = None


class AzureUserDelegationSAS(BaseModel):
    """Azure user delegation SAS payload (nested in ``TemporaryCredentials``).

    Same "defined for spec parity but never populated" story as
    :class:`AwsCredentials`.
    """

    model_config = ConfigDict(from_attributes=True)

    sas_token: str | None = None


class GcpOauthToken(BaseModel):
    """GCP OAuth token payload (nested in ``TemporaryCredentials``).

    Same "defined for spec parity but never populated" story as
    :class:`AwsCredentials`.
    """

    model_config = ConfigDict(from_attributes=True)

    oauth_token: str | None = None


class TemporaryCredentials(BaseModel):
    """Response shape for the two ``/temporary-*-credentials`` endpoints.

    Every field is optional in the spec, which is fortunate because soyuz
    ships this endpoint as a spec-conformant **stub**: we always return
    ``expiration_time`` (so clients that cache on it behave correctly)
    but leave every cloud-specific field unset. The route serialises with
    ``response_model_exclude_none=True`` so the wire JSON is
    ``{"expiration_time": …}`` rather than a document full of nulls.

    The stub is deliberate: actual STS / SAS / OAuth vending requires
    boto3 / azure-identity / google-auth as runtime dependencies and
    per-deployment IAM configuration, which is out of scope for the
    metadata-only design (see README design principle 3 and
    ``DIVERGENCES.md`` for the full rationale).
    """

    model_config = ConfigDict(from_attributes=True)

    aws_temp_credentials: AwsCredentials | None = None
    azure_user_delegation_sas: AzureUserDelegationSAS | None = None
    gcp_oauth_token: GcpOauthToken | None = None
    expiration_time: int | None = None


class AwsIamRoleRequest(BaseModel):
    """AWS IAM role payload nested in credential create/update requests.

    The UC spec defines exactly one required field, ``role_arn``.
    ``extra="forbid"`` rejects typos (e.g. ``rolearn``) with 422
    instead of silently dropping them — same bug-fix policy as every
    other request body.
    """

    model_config = ConfigDict(extra="forbid")

    role_arn: str = Field(min_length=1)


class AwsIamRoleResponse(BaseModel):
    """AWS IAM role payload on ``CredentialInfo`` responses.

    Mirrors the UC spec's ``AwsIamRoleResponse``: ``role_arn`` is the
    one the client supplied, ``external_id`` is the confused-deputy
    mitigation (server-minted once on create, never rotated by
    PATCH), and ``unity_catalog_iam_arn`` is the IAM identity the
    Unity Catalog server itself runs as. soyuz has no such identity —
    see ``DIVERGENCES.md`` — so that field is always ``None`` and the
    route serialises with ``exclude_none`` to keep it off the wire.
    """

    model_config = ConfigDict(from_attributes=True)

    role_arn: str | None = None
    external_id: str | None = None
    unity_catalog_iam_arn: str | None = None


class CredentialInfo(BaseModel):
    """Response shape for a Unity Catalog storage credential.

    Credentials live at the root of the metastore namespace (no catalog
    or schema parent), so there is no ``full_name`` trick to compute —
    the user-facing identifier is just ``name`` and the spec does not
    even define ``full_name`` for this resource. ``aws_iam_role`` is
    always populated on credentials that were created with a role, with
    ``external_id`` as the server-minted confused-deputy mitigation.
    """

    model_config = ConfigDict(from_attributes=True)

    name: str | None = None
    id: str | None = None
    purpose: Literal["STORAGE"] | None = None
    comment: str | None = None
    owner: str | None = None
    aws_iam_role: AwsIamRoleResponse | None = None
    created_at: int | None = None
    created_by: str | None = None
    updated_at: int | None = None
    updated_by: str | None = None


class CreateCredentialRequest(BaseModel):
    """Request body for ``POST /credentials``.

    ``name`` is required. ``aws_iam_role`` is the only supported
    credential payload because the upstream UC OpenAPI ``all.yaml`` we
    pin as the contract defines only that shape; Azure and GCP
    variants that exist in forks are deliberately not modelled (see
    :class:`soyuz_catalog.models.Credential` for the reasoning).

    ``purpose`` is optional and defaults to ``STORAGE`` — the only
    value defined by ``CredentialPurpose`` today. Typing it as a
    ``Literal`` means a typo (``STORGE``) surfaces as 422 at the
    Pydantic layer instead of silently landing in the DB.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    comment: str | None = None
    aws_iam_role: AwsIamRoleRequest | None = None
    purpose: Literal["STORAGE"] | None = None


class UpdateCredentialRequest(BaseModel):
    """Request body for ``PATCH /credentials/{name}``.

    Replace-style PATCH semantics driven by ``model_fields_set`` in
    the service layer, same as every other update endpoint. The spec
    allows ``new_name``, ``comment``, ``owner``, and a fresh
    ``aws_iam_role`` payload. ``extra="forbid"`` rejects unknown or
    read-only fields (``id``, ``purpose``, ``created_at``, …) with
    HTTP 422.
    """

    model_config = ConfigDict(extra="forbid")

    new_name: str | None = None
    comment: str | None = None
    owner: str | None = None
    aws_iam_role: AwsIamRoleRequest | None = None


class ListCredentialsResponse(BaseModel):
    """Response shape for ``GET /credentials``.

    Keyset pagination via ``next_page_token``; ``?purpose=`` query
    filter is accepted (currently only ``STORAGE`` exists) and
    validated as a ``Literal`` in the route signature.
    """

    credentials: list[CredentialInfo]
    next_page_token: str | None = None


class ExternalLocationInfo(BaseModel):
    """Response shape for a Unity Catalog external location.

    ``credential_name`` is **not** a stored column: it is reconstructed
    at response time from the bound credential's current ``name`` so a
    credential rename propagates for free without a fan-out UPDATE.
    ``credential_id`` is the persistent binding and is what the service
    layer actually stores on the row.
    """

    model_config = ConfigDict(from_attributes=True)

    name: str | None = None
    id: str | None = None
    url: str | None = None
    credential_name: str | None = None
    credential_id: str | None = None
    comment: str | None = None
    owner: str | None = None
    created_at: int | None = None
    created_by: str | None = None
    updated_at: int | None = None
    updated_by: str | None = None


class CreateExternalLocation(BaseModel):
    """Request body for ``POST /external-locations``.

    The UC spec requires ``name``, ``url``, and ``credential_name`` on
    create. The service resolves ``credential_name`` to a persistent
    ``credential_id`` so a subsequent credential rename does not break
    the binding. ``extra="forbid"`` rejects unknown fields — including
    ``credential_id`` itself, which is a read-only server-derived
    field on the response and must not be accepted on create.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    url: str = Field(min_length=1)
    credential_name: str = Field(min_length=1)
    comment: str | None = None


class UpdateExternalLocation(BaseModel):
    """Request body for ``PATCH /external-locations/{name}``.

    Replace-style PATCH semantics, same as every other update
    endpoint. All fields are optional; ``credential_name`` triggers a
    re-resolution to ``credential_id`` at the service layer.
    ``extra="forbid"`` rejects read-only fields (``id``,
    ``credential_id``, ``created_at``, …).
    """

    model_config = ConfigDict(extra="forbid")

    new_name: str | None = None
    url: str | None = None
    credential_name: str | None = None
    comment: str | None = None
    owner: str | None = None


class ListExternalLocationsResponse(BaseModel):
    """Response shape for ``GET /external-locations``.

    Keyset pagination via ``next_page_token``; same shape as every
    other list response in this module.
    """

    external_locations: list[ExternalLocationInfo]
    next_page_token: str | None = None


ConnectionType = Literal[
    "SNOWFLAKE",
    "MYSQL",
    "POSTGRESQL",
    "REDSHIFT",
    "BIGQUERY",
    "DATABRICKS",
    "HTTP",
    "SQLSERVER",
    "GLUE",
]


class ConnectionInfo(BaseModel):
    """Response shape for a Lakehouse-Federation connection.

    Over-the-spec addition (ADR-0013): upstream UC OSS
    ``all.yaml`` defines no ``Connection`` schema at all, so there is
    no upstream row to mirror — this shape is soyuz' contract for the
    metadata Databricks' ``Connection`` surface round-trips. soyuz
    does not store credential-bearing fields separately from
    ``options``; a future secrets-integration sprint can add a
    dedicated ``credential`` subresource without touching this wire
    shape.
    """

    model_config = ConfigDict(from_attributes=True)

    name: str | None = None
    id: str | None = None
    connection_type: ConnectionType | None = None
    options: dict[str, str] | None = None
    read_only: bool | None = None
    comment: str | None = None
    owner: str | None = None
    created_at: int | None = None
    created_by: str | None = None
    updated_at: int | None = None
    updated_by: str | None = None


class CreateConnection(BaseModel):
    """Request body for ``POST /connections``.

    ``name``, ``connection_type``, and ``options`` are required;
    everything else is optional. ``extra="forbid"`` rejects unknown
    fields (including ``id``, ``created_at``, …) with 422 instead of
    silently dropping them — the same bug class soyuz exists to fix.

    ``connection_type`` is a ``Literal`` pinned to the common connector
    set so typos (``POSTGRES`` vs ``POSTGRESQL``) surface at the
    pydantic layer. The DB column is stored as a free string for
    future extensibility — see
    :class:`soyuz_catalog.models.Connection` for the rationale and
    ``DIVERGENCES.md`` for the soyuz-vs-Databricks difference.

    ``options`` is a free-form ``dict[str, str]`` passthrough. soyuz
    does **not** validate per-connector option sets (there is no query
    side to enforce them against) and **does not** encrypt sensitive
    values (``password``, ``token``, …); both postures are documented
    in ``DIVERGENCES.md``.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    connection_type: ConnectionType
    options: dict[str, str] = Field(default_factory=dict)
    read_only: bool | None = None
    comment: str | None = None
    owner: str | None = None


class UpdateConnection(BaseModel):
    """Request body for ``PATCH /connections/{name}``.

    Replace-style PATCH semantics driven by ``model_fields_set`` in
    the service layer. ``connection_type`` is **not** exposed: flipping
    a live connection from Postgres to Snowflake would orphan every
    bound foreign catalog's ``options`` dictionary, so it is frozen at
    create time. ``new_name`` renames propagate to every bound foreign
    catalog automatically because the catalog row stores
    ``connection_id`` and reconstructs ``connection_name`` at response
    time.

    ``extra="forbid"`` rejects read-only fields (``id``, ``created_at``,
    …) with 422.
    """

    model_config = ConfigDict(extra="forbid")

    new_name: str | None = None
    options: dict[str, str] | None = None
    read_only: bool | None = None
    comment: str | None = None
    owner: str | None = None


class ListConnectionsResponse(BaseModel):
    """Response shape for ``GET /connections``.

    Keyset pagination via ``next_page_token``; same shape as every
    other list response in this module.
    """

    connections: list[ConnectionInfo]
    next_page_token: str | None = None


class FunctionParameterInfo(BaseModel):
    """A single function parameter (input or return) in ``FunctionInfo``.

    Used symmetrically on request and response because the UC OpenAPI
    spec reuses the same schema for both directions. ``extra="forbid"``
    rejects typos on write — the service layer stores the parameter
    list as an opaque JSON object, so an unchecked unknown key would
    round-trip silently and mask a client bug. On the response side
    the forbid policy is a no-op because soyuz never emits extras.
    """

    model_config = ConfigDict(extra="forbid")

    name: str
    type_text: str
    type_json: str
    type_name: str
    position: int
    type_precision: int | None = None
    type_scale: int | None = None
    type_interval_type: str | None = None
    parameter_mode: Literal["IN"] | None = None
    parameter_type: Literal["PARAM", "COLUMN"] | None = None
    parameter_default: str | None = None
    comment: str | None = None


class FunctionParameterInfos(BaseModel):
    """Wrapper around the ``parameters`` array of a function's params.

    The UC spec defines this wrapper object so that a function without
    parameters round-trips as ``{"parameters": []}`` instead of
    ``null``, and so that a future spec revision can add sibling
    metadata fields without breaking the wire shape. soyuz stores the
    wrapped array verbatim in a JSON column and reconstructs this
    model from it at response time.
    """

    model_config = ConfigDict(extra="forbid")

    parameters: list[FunctionParameterInfo] = Field(default_factory=list)


class CreateFunction(BaseModel):
    """Inner payload of ``CreateFunctionRequest`` — a full ``FunctionInfo`` body.

    The UC spec requires the client to send every structural field on
    create: ``input_params``, ``data_type``, ``full_data_type``,
    ``routine_body``, ``routine_definition``, ``parameter_style``,
    ``is_deterministic``, ``sql_data_access``, ``is_null_call``,
    ``security_type``, and ``specific_name``. ``return_params`` is
    optional because an EXTERNAL routine does not have one.
    ``extra="forbid"`` rejects unknown fields, same bug-fix policy
    as every other request body.

    ``properties`` is a free-form JSON-encoded string, not a dict, per
    the spec's *"JSON-serialized key-value pair map, encoded
    (escaped) as a string"* contract. soyuz stores it verbatim.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    catalog_name: str = Field(min_length=1)
    schema_name: str = Field(min_length=1)
    input_params: FunctionParameterInfos
    data_type: str = Field(min_length=1)
    full_data_type: str = Field(min_length=1)
    routine_body: Literal["SQL", "EXTERNAL"]
    routine_definition: str
    parameter_style: Literal["S"]
    is_deterministic: bool
    sql_data_access: Literal["CONTAINS_SQL", "READS_SQL_DATA", "NO_SQL"]
    is_null_call: bool
    security_type: Literal["DEFINER"]
    specific_name: str = Field(min_length=1)
    return_params: FunctionParameterInfos | None = None
    routine_dependencies: dict | None = None
    external_language: str | None = None
    comment: str | None = None
    properties: str | None = None


class CreateFunctionRequest(BaseModel):
    """Outer wrapper for ``POST /functions``.

    The UC spec defines the create request as ``{"function_info":
    CreateFunction}`` rather than a flat body — an unusual nesting
    driven by the way the protobuf IDL is translated into JSON. We
    mirror the wrapper exactly so OpenAPI-generated clients keep
    working.
    """

    model_config = ConfigDict(extra="forbid")

    function_info: CreateFunction


class FunctionInfo(BaseModel):
    """Response shape for a Unity Catalog function.

    ``full_name`` / ``catalog_name`` / ``schema_name`` are *not*
    stored columns — they are computed at response time from the
    live parent schema's (and its parent catalog's) names so that a
    rename of either parent propagates to every child function for
    free, same trick as :class:`TableInfo` and :class:`VolumeInfo`.
    """

    model_config = ConfigDict(from_attributes=True)

    name: str | None = None
    catalog_name: str | None = None
    schema_name: str | None = None
    full_name: str | None = None
    input_params: FunctionParameterInfos | None = None
    data_type: str | None = None
    full_data_type: str | None = None
    return_params: FunctionParameterInfos | None = None
    routine_body: Literal["SQL", "EXTERNAL"] | None = None
    routine_definition: str | None = None
    routine_dependencies: dict | None = None
    parameter_style: Literal["S"] | None = None
    is_deterministic: bool | None = None
    sql_data_access: Literal["CONTAINS_SQL", "READS_SQL_DATA", "NO_SQL"] | None = None
    is_null_call: bool | None = None
    security_type: Literal["DEFINER"] | None = None
    specific_name: str | None = None
    external_language: str | None = None
    comment: str | None = None
    properties: str | None = None
    owner: str | None = None
    created_at: int | None = None
    created_by: str | None = None
    updated_at: int | None = None
    updated_by: str | None = None
    function_id: str | None = None


class ListFunctionsResponse(BaseModel):
    """Response shape for ``GET /functions``.

    Keyset pagination via ``next_page_token``; same shape as every
    other list response in this module.
    """

    functions: list[FunctionInfo]
    next_page_token: str | None = None


class RegisteredModelInfo(BaseModel):
    """Response shape for a Unity Catalog registered model.

    ``full_name`` / ``catalog_name`` / ``schema_name`` are computed
    at response time from the live parent schema. ``storage_location``
    is always ``None`` in soyuz because ``CreateRegisteredModel``
    takes no ``storage_root`` and soyuz does not derive one — see
    :class:`soyuz_catalog.models.RegisteredModel` for the rationale.
    """

    model_config = ConfigDict(from_attributes=True)

    name: str | None = None
    catalog_name: str | None = None
    schema_name: str | None = None
    full_name: str | None = None
    storage_location: str | None = None
    comment: str | None = None
    owner: str | None = None
    created_at: int | None = None
    created_by: str | None = None
    updated_at: int | None = None
    updated_by: str | None = None
    id: str | None = None


class CreateRegisteredModel(BaseModel):
    """Request body for ``POST /models``.

    The UC spec requires ``name``, ``catalog_name``, and
    ``schema_name``; ``comment`` is the only optional field.
    ``extra="forbid"`` rejects unknown fields — notably including
    ``storage_location``, which is a server-derived field on the
    response and must not be accepted on create.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    catalog_name: str = Field(min_length=1)
    schema_name: str = Field(min_length=1)
    comment: str | None = None


class UpdateRegisteredModel(BaseModel):
    """Request body for ``PATCH /models/{full_name}``.

    Replace-style PATCH semantics driven by ``model_fields_set`` in
    the service layer. The UC-OSS proto's ``UpdateRegisteredModel``
    message includes ``full_name`` as a body field that duplicates
    the URL path parameter (`unity_catalog_oss_messages.proto:82-95`)
    — MLflow's UC-OSS client sends it on every request, so we accept
    it and ignore it (the URL is the source of truth). ``extra="forbid"``
    still rejects truly unknown fields (storage_location, owner, …)
    with HTTP 422.
    """

    model_config = ConfigDict(extra="forbid")

    full_name: str | None = None
    new_name: str | None = None
    comment: str | None = None


class ListRegisteredModelsResponse(BaseModel):
    """Response shape for ``GET /models``.

    Keyset pagination via ``next_page_token``. Both ``catalog_name``
    and ``schema_name`` query filters are *optional* — the spec
    allows a metastore-wide list — which differs from
    :class:`ListFunctionsResponse` where both are required.
    """

    registered_models: list[RegisteredModelInfo]
    next_page_token: str | None = None


class ModelVersionInfo(BaseModel):
    """Response shape for a single registered-model version.

    Addressed in the URL by ``(full_name, version_int)`` and in this
    payload the ``model_name`` / ``catalog_name`` / ``schema_name``
    are computed from the live parent registered model at response
    time, same rename-propagation trick as every other nested
    resource in this module.

    ``status`` is always ``READY`` on rows soyuz creates — see
    :class:`soyuz_catalog.models.ModelVersion` and DIVERGENCES.
    """

    model_config = ConfigDict(from_attributes=True)

    model_name: str | None = None
    catalog_name: str | None = None
    schema_name: str | None = None
    version: int | None = None
    source: str | None = None
    run_id: str | None = None
    status: (
        Literal[
            "MODEL_VERSION_STATUS_UNKNOWN",
            "PENDING_REGISTRATION",
            "FAILED_REGISTRATION",
            "READY",
        ]
        | None
    ) = None
    storage_location: str | None = None
    comment: str | None = None
    created_at: int | None = None
    created_by: str | None = None
    updated_at: int | None = None
    updated_by: str | None = None
    id: str | None = None


class CreateModelVersion(BaseModel):
    """Request body for ``POST /models/versions``.

    The UC spec addresses the parent registered model by the triple
    ``(catalog_name, schema_name, model_name)`` on the create body
    rather than via a nested URL, which is why this endpoint is
    mounted at ``/models/versions`` instead of
    ``/models/{full_name}/versions``. ``source`` is required; the
    server assigns a monotonic ``version`` integer unique per
    registered model.
    """

    model_config = ConfigDict(extra="forbid")

    model_name: str = Field(min_length=1)
    catalog_name: str = Field(min_length=1)
    schema_name: str = Field(min_length=1)
    source: str = Field(min_length=1)
    run_id: str | None = None
    comment: str | None = None


class UpdateModelVersion(BaseModel):
    """Request body for ``PATCH /models/{full_name}/versions/{version}``.

    The UC-OSS proto's ``UpdateModelVersion`` message duplicates the
    URL parameters (``full_name``, ``version``) in the body
    (`unity_catalog_oss_messages.proto:215-228`) — MLflow's UC-OSS
    client sends them on every request, so we accept and ignore them
    (URL parameters are the source of truth). The only mutable field
    is ``comment``: ``source``, ``run_id``, and ``status`` are
    immutable after registration. ``extra="forbid"`` still rejects
    truly unknown fields with 422.
    """

    model_config = ConfigDict(extra="forbid")

    full_name: str | None = None
    version: int | None = None
    comment: str | None = None


class ListModelVersionsResponse(BaseModel):
    """Response shape for ``GET /models/{full_name}/versions``.

    Keyset pagination via ``next_page_token``; ordered by
    ``(created_at, id)`` like every other list endpoint, not by
    ``version`` (two versions created in the same millisecond
    disambiguate on ``id``).
    """

    model_versions: list[ModelVersionInfo]
    next_page_token: str | None = None


class GetMetastoreSummaryResponse(BaseModel):
    """Response shape for ``GET /metastore_summary``.

    The upstream UC OpenAPI spec defines a single field on this
    object: ``metastore_id``. soyuz does not silently extend it with
    ``name``, ``storage_root``, ``region``, ``owner``, or any of the
    other fields that appear on Databricks-flavoured forks of the
    spec — same no-silent-spec-extensions policy as every other
    response model in this module.
    """

    model_config = ConfigDict(from_attributes=True)

    metastore_id: str | None = None


class StagingTableInfo(BaseModel):
    """Response shape for ``POST /staging-tables``.

    Returned directly from the create endpoint — there is no GET /
    LIST / DELETE route for staging tables in the spec, so this is
    the only shape the resource ever takes on the wire.
    ``staging_location`` is the server-derived URL the client should
    write data to before promoting the allocation to a real managed
    table.
    """

    model_config = ConfigDict(from_attributes=True)

    name: str | None = None
    catalog_name: str | None = None
    schema_name: str | None = None
    id: str | None = None
    staging_location: str | None = None


class CreateStagingTable(BaseModel):
    """Request body for ``POST /staging-tables``.

    The UC spec marks every field as required: a staging table is
    addressed by ``(catalog_name, schema_name, name)`` and has no
    other client-supplied inputs. ``extra="forbid"`` rejects unknown
    fields — notably including ``storage_location`` and ``id``, which
    are server-derived on the response and must not be accepted on
    create.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    catalog_name: str = Field(min_length=1)
    schema_name: str = Field(min_length=1)


class ListCatalogsResponse(BaseModel):
    """Response shape for ``GET /catalogs``.

    ``next_page_token`` is the opaque keyset cursor — ``None`` on the
    last page, otherwise the encoded ``(created_at, id)`` tuple to
    feed back as ``page_token`` on the next call. See
    :mod:`soyuz_catalog.pagination` and ADR-0003.
    """

    catalogs: list[CatalogInfo]
    next_page_token: str | None = None


Privilege = Literal[
    "CREATE CATALOG",
    "USE CATALOG",
    "CREATE SCHEMA",
    "USE SCHEMA",
    "CREATE TABLE",
    "SELECT",
    "MODIFY",
    "CREATE FUNCTION",
    "EXECUTE",
    "CREATE VOLUME",
    "READ VOLUME",
    "CREATE MODEL",
    "CREATE EXTERNAL LOCATION",
    "READ FILES",
    "WRITE FILES",
    "CREATE EXTERNAL TABLE",
    "CREATE EXTERNAL VOLUME",
    "CREATE MANAGED STORAGE",
    "CREATE STORAGE CREDENTIAL",
]
"""The full set of Unity Catalog ``Privilege`` enum values.

Verbatim from ``unitycatalog/api/all.yaml`` (components.schemas.Privilege).
Kept as a ``typing.Literal`` rather than a Python ``Enum`` so FastAPI
surfaces typos in request bodies as 422 ``INVALID_ARGUMENT`` without
any hand-written validator. The per-securable-type allow-set lives in
:mod:`soyuz_catalog.services.permissions_service` and is a soyuz
addition, not part of the spec — see ``DIVERGENCES.md``.
"""


SecurableType = Literal[
    "metastore",
    "catalog",
    "schema",
    "table",
    "function",
    "volume",
    "registered_model",
    "external_location",
    "credential",
]
"""The full set of Unity Catalog ``SecurableType`` enum values.

Verbatim from ``unitycatalog/api/all.yaml`` (components.schemas.SecurableType).
Used as a FastAPI path-parameter type on the permissions routes so an
unknown securable type surfaces as 422 at routing time, before any
service-layer code runs.
"""


class PermissionsChange(BaseModel):
    """One element of an ``UpdatePermissions`` request body.

    ``add`` and ``remove`` are spec-required arrays: clients that want
    to only add must still send an empty ``remove`` list (and vice
    versa). Overlapping entries within a single change are handled by
    the service layer: removes are applied first, then adds, so if
    the same privilege appears in both lists the net effect is *add
    wins*. That tiebreaker is soyuz-specific and documented in
    ``DIVERGENCES.md``; the upstream spec does not pin a winner.
    """

    model_config = ConfigDict(extra="forbid")

    principal: str = Field(min_length=1)
    add: list[Privilege]
    remove: list[Privilege]


class UpdatePermissions(BaseModel):
    """Request body for ``PATCH /permissions/{securable_type}/{full_name}``.

    Unlike every other PATCH in this project, this shape is **not**
    replace-style: the client submits a list of additive/subtractive
    changes rather than a full desired state. This matches the
    upstream ``UpdatePermissions`` schema exactly — see
    ``DIVERGENCES.md`` for why the asymmetry with our catalog /
    schema / table PATCH routes is intentional.
    """

    model_config = ConfigDict(extra="forbid")

    changes: list[PermissionsChange]


class PrivilegeAssignment(BaseModel):
    """A single principal's privileges on one securable.

    The wire shape pivots the flat ``permissions`` rows onto the
    per-principal view the UC spec defines: instead of ``N`` rows of
    ``(principal, privilege)``, the response groups by principal and
    carries the privilege list inline. The service layer does the
    grouping and stable sorting; the route just serialises the
    result.
    """

    model_config = ConfigDict(extra="forbid")

    principal: str
    privileges: list[Privilege]


class PermissionsList(BaseModel):
    """Response shape for ``GET`` / ``PATCH /permissions/...``.

    Both endpoints return the same shape: ``GET`` returns the current
    state (optionally filtered by ``?principal=``), ``PATCH`` returns
    the state after the submitted changes have been applied. The
    optional ``?principal=`` filter applies only to ``GET``; ``PATCH``
    always returns the full current state to avoid the client having
    to re-fetch after every update.
    """

    model_config = ConfigDict(extra="forbid")

    privilege_assignments: list[PrivilegeAssignment]


class DeltaGetCommits(BaseModel):
    """Request body for ``GET /delta/preview/commits``.

    The UC OpenAPI spec models this endpoint as a GET-with-body — unusual
    but unambiguous — so the request shape is a Pydantic model rather than
    query parameters. ``table_id`` and ``table_uri`` must both be present:
    the spec requires the server to reject a request whose ``table_uri``
    does not match the currently-registered storage location of
    ``table_id``, so sending one without the other is a client bug.
    ``start_version`` bounds the returned row set inclusively from below;
    ``end_version`` bounds it inclusively from above when present.

    Per ADR-0011 the coordinator tracks unbackfilled commits, so
    ``start_version`` and ``end_version`` carry a real filtering
    role. See :mod:`soyuz_catalog.services.delta_commits_service`
    for how the service applies them.
    """

    model_config = ConfigDict(extra="forbid")

    table_id: str = Field(min_length=1)
    table_uri: str = Field(min_length=1)
    start_version: int
    end_version: int | None = None


class DeltaCommitInfo(BaseModel):
    """One unbackfilled Delta commit tracked by the coordinator.

    The five fields are required by the upstream spec and describe a
    staged commit file the Delta Kernel client has written to
    ``_delta_log/.tmp/<uuid>.json`` but has not yet published to
    ``_delta_log/NNNNN.json``. soyuz persists one row of these values
    in :class:`soyuz_catalog.models.DeltaUnbackfilledCommit` per
    ``(table_id, version)`` and returns them from ``GET /delta/preview/
    commits`` until the client signals a completed publish via a
    follow-up ``POST`` carrying ``latest_backfilled_version``.
    """

    model_config = ConfigDict(extra="forbid")

    version: int
    timestamp: int
    file_name: str
    file_size: int
    file_modification_timestamp: int


class DeltaGetCommitsResponse(BaseModel):
    """Response body for ``GET /delta/preview/commits``.

    ``commits`` carries the rows currently tracked by the coordinator
    (ADR-0011) for the requested table in
    ``[start_version, end_version]``. ``latest_table_version`` is the
    highest version the coordinator has ever seen for the table — max
    over live rows (including the one marked
    ``is_backfilled_latest_commit`` as the anchor after pruning), or
    :py:meth:`deltalake.DeltaTable.version` on the on-disk log when
    the coordinator has no rows for the table (the read-path for
    freshly-attached tables that never staged a commit through
    soyuz). Delta Kernel readers apply the returned ``commits``
    **in-memory** — they do not themselves backfill to disk.
    """

    model_config = ConfigDict(extra="forbid")

    commits: list[DeltaCommitInfo] = Field(default_factory=list)
    latest_table_version: int


class DeltaCommit(BaseModel):
    """Request body for ``POST /delta/preview/commits``.

    Request shape for the passthrough Delta commit coordinator
    (ADR-0011). The request fuses two conceptually
    independent operations the Delta Kernel client may send in a
    single call: a **commit** registration (``commit_info`` set,
    carrying the metadata of a freshly-staged ``_delta_log/.tmp/``
    file) and a **backfill acknowledgement** (``latest_backfilled_version``
    set, signalling that the client has published everything up to
    that version and the coordinator can prune). Either field, or
    both, may be present — the spec's ``oneOf-ish`` requirement is
    enforced by :meth:`_require_at_least_one_action` below and
    re-checked defensively in
    :func:`soyuz_catalog.services.delta_commits_service.commit`.

    ``metadata`` and ``uniform`` are accepted as opaque pass-through
    dicts: the upstream protocol forwards them to downstream Delta
    Kernel consumers (protocol upgrades, Iceberg conversion hints)
    and soyuz stores neither. Their shapes are not pinned on this
    side because doing so would couple soyuz to a Kernel-side
    contract that evolves independently and does not participate in
    the `all.yaml` conformance test.
    """

    model_config = ConfigDict(extra="forbid")

    table_id: str = Field(min_length=1)
    table_uri: str = Field(min_length=1)
    commit_info: DeltaCommitInfo | None = None
    latest_backfilled_version: int | None = None
    metadata: dict[str, Any] | None = None
    uniform: dict[str, Any] | None = None

    @model_validator(mode="after")
    def _require_at_least_one_action(self) -> DeltaCommit:
        """Reject a request that carries neither a commit nor a backfill ack.

        The upstream spec models ``commit_info`` and ``latest_backfilled_version``
        as independently-optional fields but implicitly requires at least
        one of them — a ``POST`` with neither has no effect and no
        meaningful response shape. Catching the empty-request case here
        turns a silent no-op into an explicit 422 from FastAPI's validation
        layer before the service is invoked.

        Returns:
            DeltaCommit: ``self`` unchanged when validation passes.

        Raises:
            ValueError: If both ``commit_info`` and ``latest_backfilled_version``
                are ``None``.
        """
        if self.commit_info is None and self.latest_backfilled_version is None:
            raise ValueError(
                "DeltaCommit must carry at least one of 'commit_info' "
                "(commit registration) or 'latest_backfilled_version' "
                "(backfill acknowledgement)",
            )
        return self


class DeltaCommitResponse(BaseModel):
    """Response body for ``POST /delta/preview/commits``.

    Deliberately empty: the upstream ``DeltaCommitResponse`` schema
    defines no fields, and the coordinator's ``commit`` operation
    communicates success through the HTTP status alone (200 = the
    row was accepted; 4xx carries the semantic failure). The class
    exists to give the route a strict ``response_model`` so FastAPI
    serialises ``{}`` on the wire and rejects any accidental
    response-shape drift during review.
    """

    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------------------
# Lineage (OpenLineage ingestion + traversal) — over-the-spec, ADR-0008.
#
# The ingestion body is intentionally permissive (``extra="allow"``) so the
# soyuz endpoint acts as a drop-in OpenLineage receiver: the external
# standard evolves independently of soyuz and new facets should not crash
# producers. This is a scoped exception to the project-wide
# ``extra="forbid"`` policy — every *response* model below stays strict.
# See ADR-0008 for the full rationale and the tables-only MVP scope.
# ---------------------------------------------------------------------------


class OpenLineageJob(BaseModel):
    """The ``job`` block of an OpenLineage event.

    Only ``namespace`` and ``name`` are pulled out at this layer; any
    ``facets`` that OpenLineage producers attach are kept via
    ``extra="allow"`` but not interpreted — soyuz does not want its
    storage shape pinned to any one producer's facet conventions. See
    ADR-0008 for why ``job.name`` alone is stored as the edge
    ``operation``.
    """

    model_config = ConfigDict(extra="allow")

    namespace: str
    name: str


class OpenLineageRun(BaseModel):
    """The ``run`` block of an OpenLineage event.

    ``runId`` is the OpenLineage producer's UUID for this execution.
    soyuz stores it verbatim as the :class:`LineageRun` primary key with
    hyphens stripped, so two soyuz instances that happen to receive the
    same event produce the same row. ``facets`` are accepted but ignored.
    """

    model_config = ConfigDict(extra="allow")

    runId: str  # noqa: N815 — the OpenLineage wire name is camelCase.


class OpenLineageDataset(BaseModel):
    """One input or output dataset entry on an OpenLineage event.

    soyuz expects ``name`` to be a UC-style dotted full_name
    (``catalog.schema.table``) so that
    :func:`soyuz_catalog.services.permissions_service.resolve_securable`
    can translate it into an opaque row id. Datasets that do **not**
    resolve are silently dropped and counted in the ingest response —
    OpenLineage producers legitimately emit events for tables outside
    Unity Catalog, and rejecting those events with 400 would make
    soyuz unusable as a drop-in sink.
    """

    model_config = ConfigDict(extra="allow")

    namespace: str
    name: str


class OpenLineageEvent(BaseModel):
    """An OpenLineage ``RunEvent`` body posted to ``/lineage/v1/events``.

    Permissively validated: unknown top-level fields and unknown
    sub-fields are accepted because OpenLineage evolves independently of
    soyuz and the endpoint must not crash producers when a new facet
    ships. The strict-``forbid`` policy still applies to every soyuz
    *response* shape and every spec-sourced request shape; this is the
    only documented exception. See ADR-0008.

    soyuz extracts a small fixed set of fields:

    * ``eventType`` drives the :class:`LineageRun.state` transition.
    * ``eventTime`` (ISO-8601) is parsed to epoch milliseconds and
      stored as ``started_at`` on the first event (``ended_at`` on the
      terminal event).
    * ``run.runId`` is the run primary key.
    * ``job.namespace`` / ``job.name`` populate the run's denormalised
      job columns and ``job.name`` also becomes each edge's
      ``operation`` label.
    * ``inputs`` × ``outputs`` cross product produces
      :class:`LineageEdge` rows, dropping datasets whose names do not
      resolve to an existing soyuz table.
    * Two additional facets are ingested when present on output
      datasets:

      * ``columnLineage`` — OpenLineage 1.x standard.  Each
        ``fields[target_column].inputFields`` entry produces one
        :class:`LineageColumnEdge` row.  ``transformations[0].type``
        (when present) populates ``transformation_type`` verbatim.
      * ``valueChange`` — **non-spec producer extension**, identified
        on the wire by its ``_producer`` URI on the facet payload.
        The body shape is ``{changes: [{rowId, column, oldValue,
        newValue}]}``; one :class:`LineageValueChange` row per
        entry.  soyuz stores the values verbatim and does no
        redaction of its own — producers handling PII are expected
        to redact upstream.  The shape is producer-defined, not
        part of OpenLineage 1.x.
    """

    model_config = ConfigDict(extra="allow")

    eventType: Literal[  # noqa: N815 — OpenLineage wire name.
        "START",
        "RUNNING",
        "COMPLETE",
        "ABORT",
        "FAIL",
        "OTHER",
    ]
    eventTime: str  # noqa: N815 — OpenLineage wire name. ISO-8601 timestamp.
    run: OpenLineageRun
    job: OpenLineageJob
    inputs: list[OpenLineageDataset] = Field(default_factory=list)
    outputs: list[OpenLineageDataset] = Field(default_factory=list)


class LineageIngestResponse(BaseModel):
    """Response body for ``POST /lineage/v1/events``.

    Unlike the ingestion body, the response is strict-``forbid``: no
    ambiguity about what soyuz returned. ``accepted_edges`` counts the
    rows actually inserted on this call (redeliveries report ``0``);
    ``rejected_datasets`` counts dataset entries whose ``name`` failed
    to resolve to a soyuz table and were therefore dropped. The
    combination lets producers tell "soyuz saw my event but couldn't
    map it" apart from "soyuz already had it".

    Two more counters cover the optional column-lineage and
    (non-spec, producer-defined) value-change facets:
    ``accepted_column_edges`` / ``accepted_value_changes``.
    Producers that don't emit either facet always see ``0`` for both
    — the response shape is additive.
    """

    model_config = ConfigDict(extra="forbid")

    run_id: str
    state: str
    accepted_edges: int
    rejected_datasets: int
    accepted_column_edges: int = 0
    accepted_value_changes: int = 0


class LineageNode(BaseModel):
    """One node in a lineage traversal response.

    ``securable_id`` is always the opaque row id. ``full_name`` is
    reconstructed at query time by joining
    :class:`soyuz_catalog.models.Table` → ``Schema`` → ``Catalog``; it
    is ``None`` for ids that no longer resolve (the underlying table
    was deleted after the edge was recorded). Clients that want to
    distinguish "never existed" from "used to exist" can read the
    ``null`` full_name as the latter.
    """

    model_config = ConfigDict(extra="forbid")

    securable_id: str
    full_name: str | None = None
    depth: int


class LineageEdgeOut(BaseModel):
    """One directed edge in a lineage traversal response.

    ``source_full_name`` and ``target_full_name`` follow the same
    "null means the securable id no longer resolves" rule as
    :class:`LineageNode`. ``run_id`` is exposed so a client can pivot
    from "show me the graph" to "show me the job that produced this
    edge" without a second round-trip.
    """

    model_config = ConfigDict(extra="forbid")

    source_securable_id: str
    target_securable_id: str
    source_full_name: str | None = None
    target_full_name: str | None = None
    run_id: str
    operation: str | None = None


class LineageGraphResponse(BaseModel):
    """Response body for ``GET /lineage/{upstream,downstream}/{full_name}``.

    The shape is symmetric between upstream and downstream queries —
    ``direction`` is the only hint about which way the graph was
    walked. ``root`` echoes the path parameter (unnormalised) so the
    client can render a breadcrumb without re-parsing its own request.
    ``nodes`` contains one entry per reachable securable id including
    the root at ``depth=0``; ``edges`` contains every edge traversed in
    reaching those nodes, deduplicated.
    """

    model_config = ConfigDict(extra="forbid")

    root: str
    direction: Literal["upstream", "downstream"]
    nodes: list[LineageNode] = Field(default_factory=list)
    edges: list[LineageEdgeOut] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Tags (ADR-0010).
#
# Over-the-spec extension: UC OSS / ``all.yaml`` have no tags. MVP scope is
# catalog / schema / table / column; volume / function / registered_model are
# a non-breaking additive extension because tags key on the opaque resource id.
# ---------------------------------------------------------------------------


TagSecurableType = Literal["catalog", "schema", "table", "column"]
"""The subset of securable types that accept tags in the MVP scope.

Deliberately narrower than ``SecurableType``: volumes, functions, and
registered models are a non-breaking additive extension (the storage column
is just a 32-char hex). Used as a FastAPI path-parameter type on the tags
routes so an unsupported type surfaces as 422 at routing time.
"""


class TagChange(BaseModel):
    """One element of an ``UpdateTags`` request body.

    The additive shape mirrors :class:`PermissionsChange`: instead of a full
    desired state the client submits a list of set/remove operations and the
    service applies them transactionally. ``op="set"`` upserts the key with
    the given ``value``; ``op="remove"`` deletes the key if present and is a
    no-op otherwise. ``value`` is ignored on remove (and must not be sent —
    ``extra="forbid"`` catches stray fields but the service also treats
    ``value`` on a remove as meaningless).

    Overlapping operations within a single PATCH resolve as *set wins*: the
    service applies removes first, then sets, so a ``(remove key, set key)``
    pair ends with the key present.
    """

    model_config = ConfigDict(extra="forbid")

    op: Literal["set", "remove"]
    key: str = Field(min_length=1, max_length=255)
    value: str | None = None


class UpdateTags(BaseModel):
    """Request body for ``PATCH /tags/{securable_type}/{full_name}``.

    Like :class:`UpdatePermissions`, this shape is **not** replace-style: the
    client submits a list of additive/subtractive changes rather than a full
    desired state. This makes multi-writer workflows safe — two clients
    editing disjoint key sets do not clobber each other's tags — and matches
    the Databricks ``UpdateTags`` wire shape. See ``DIVERGENCES.md`` and
    ADR-0010 for the over-the-spec rationale.
    """

    model_config = ConfigDict(extra="forbid")

    changes: list[TagChange]


class TagEntry(BaseModel):
    """A single ``(key, value)`` tag on a securable.

    ``value`` is optional because Databricks supports valueless tags (flag
    semantics, e.g. ``pii``). Timestamps are exposed as epoch milliseconds to
    match every other resource response in the project.
    """

    model_config = ConfigDict(extra="forbid")

    key: str
    value: str | None = None
    created_at: int
    updated_at: int


class TagList(BaseModel):
    """Response shape for ``GET`` / ``PATCH /tags/{securable_type}/{full_name}``.

    Both endpoints return the same shape: ``GET`` returns the current tag
    set, ``PATCH`` returns the state after the submitted changes have been
    applied. Tags are sorted by ``key`` so two calls against an unchanged
    state return byte-identical bodies — a property tests rely on and a
    convenience for clients that diff responses.
    """

    model_config = ConfigDict(extra="forbid")

    tags: list[TagEntry] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Metric views — over-the-spec extension (ADR-0014)
# ---------------------------------------------------------------------------


class MetricViewDimension(BaseModel):
    """One dimension in a metric-view spec.

    ``expr`` is an opaque SQL expression string — soyuz never parses
    it (there is no query side to validate it against; the consumer's
    compiler is where a malformed expression surfaces). ``name`` is
    the column name the compiled view exposes, so it shares one flat
    namespace with measure names — uniqueness across the combined set
    is enforced by the service layer.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    expr: str = Field(min_length=1)
    comment: str | None = None


class MetricViewMeasure(BaseModel):
    """One measure in a metric-view spec.

    Same shape as :class:`MetricViewDimension`; kept as a separate
    class because the two lists carry different compile-time
    semantics in the consumer (GROUP BY columns vs. aggregations)
    and a future revision may grow measure-only fields (e.g. a
    window specification) without disturbing dimensions.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    expr: str = Field(min_length=1)
    comment: str | None = None


class MetricViewSpec(BaseModel):
    """The semantic-layer definition stored on a metric view.

    ``measures`` requires at least one entry (``min_length=1`` —
    surfacing as 422): a metric view without a measure is just a
    projection and belongs in a plain SQL view. ``dimensions`` may be
    empty (a single-row summary view is legitimate). ``filter`` is an
    optional opaque SQL predicate applied by the consumer before
    aggregation.
    """

    model_config = ConfigDict(extra="forbid")

    dimensions: list[MetricViewDimension] = Field(default_factory=list)
    measures: list[MetricViewMeasure] = Field(min_length=1)
    filter: str | None = None


class MetricViewInfo(BaseModel):
    """Response shape for a metric view.

    Over-the-spec addition (ADR-0014): upstream UC OSS ``all.yaml``
    has no semantic-layer schema, so this shape is soyuz' contract.
    ``catalog_name`` / ``schema_name`` / ``full_name`` are
    reconstructed from the live parent chain at response time — same
    rename-invariance trick :class:`TableInfo` uses.
    """

    model_config = ConfigDict(from_attributes=True)

    name: str | None = None
    catalog_name: str | None = None
    schema_name: str | None = None
    full_name: str | None = None
    source_table_full_name: str | None = None
    spec: MetricViewSpec | None = None
    comment: str | None = None
    owner: str | None = None
    id: str | None = None
    created_at: int | None = None
    created_by: str | None = None
    updated_at: int | None = None
    updated_by: str | None = None


class CreateMetricView(BaseModel):
    """Request body for ``POST /metric-views``.

    ``source_table_full_name`` must be a syntactically valid
    three-part name but is *not* resolved against the tables surface
    — a metric view may be authored before its source table is
    registered, exactly like a SQL view body referencing a yet-to-be
    created table. The parent catalog and schema, by contrast, must
    exist (404 otherwise). ``extra="forbid"`` rejects unknown fields
    with 422 instead of silently dropping them.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    catalog_name: str = Field(min_length=1)
    schema_name: str = Field(min_length=1)
    source_table_full_name: str = Field(min_length=1)
    spec: MetricViewSpec
    comment: str | None = None
    owner: str | None = None


class UpdateMetricView(BaseModel):
    """Request body for ``PATCH /metric-views/{full_name}``.

    Replace-style PATCH semantics driven by ``model_fields_set`` in
    the service layer: ``spec`` replaces the whole stored definition
    (a per-dimension merge would have no predictable semantics), and
    an empty body is a no-op. ``new_name`` renames within the same
    schema — moving a metric view across schemas is a
    delete-and-recreate, same posture as every other child resource.
    """

    model_config = ConfigDict(extra="forbid")

    new_name: str | None = None
    source_table_full_name: str | None = None
    spec: MetricViewSpec | None = None
    comment: str | None = None
    owner: str | None = None


class ListMetricViewsResponse(BaseModel):
    """Response shape for ``GET /metric-views``.

    Keyset pagination via ``next_page_token``; same shape as every
    other list response in this module.
    """

    metric_views: list[MetricViewInfo]
    next_page_token: str | None = None
