"""Business logic for the TemporaryCredentials resource.

These endpoints default to **spec-conformant stubs**: the response shape
matches the UC OpenAPI ``TemporaryCredentials`` schema exactly, and by
default no **real** credential values are populated. The response
reflects *which* cloud path the server would route a real credential
through — ``s3``/``s3a`` attach an ``AwsCredentials``, ``abfss`` an
empty ``AzureUserDelegationSAS``, ``gs`` an empty ``GcpOauthToken``, and
``file`` / legacy / unparseable locations stay ``expiration_time``-only.

**Opt-in real S3 vending.** When ``SOYUZ_ENABLE_STS_VENDING`` is set and
the target path resolves to a registered external location bound to a
credential with an ``aws_iam_role_arn``, soyuz assumes that role via STS
and returns the short-lived keys (see :func:`_mint_aws_credentials`).
Off by default — the metadata-only stance stays the default and Azure /
GCS vending remains out of scope. See ``DIVERGENCES.md`` for the
rationale.

The service still performs the two checks that matter for client
behaviour:

1. The referenced table / volume must exist (otherwise a client that
   cached a stale id would get an opaque 200 with an empty credential
   instead of a clear 404).
2. ``operation`` must be a real operation, not the protobuf-default
   ``UNKNOWN_*_OPERATION`` sentinel. Accepting the sentinel would be the
   same "silently accept garbage" behaviour that ``extra="forbid"`` is
   everywhere else written to prevent.
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from soyuz_catalog.api.schemas import (
    AwsCredentials,
    AzureUserDelegationSAS,
    GcpOauthToken,
    GenerateTemporaryModelVersionCredential,
    GenerateTemporaryPathCredential,
    GenerateTemporaryTableCredential,
    GenerateTemporaryVolumeCredential,
    TemporaryCredentials,
)
from soyuz_catalog.exceptions import InvalidRequestError, NotFoundError
from soyuz_catalog.models import _now_ms
from soyuz_catalog.services import (
    aws_sts,
    external_location_service,
    model_version_service,
    staging_table_service,
    table_service,
    volume_service,
)
from soyuz_catalog.settings import get_settings
from soyuz_catalog.storage import parse_storage_uri

_logger = logging.getLogger(__name__)

_CREDENTIAL_LIFETIME_MS = 3_600_000


def _stub_credentials(scheme: str | None) -> TemporaryCredentials:
    """Build the stub ``TemporaryCredentials`` response for a storage scheme.

    ``expiration_time`` is always populated (one hour from now) so clients
    that cache on it continue to behave correctly. The cloud-specific
    field is selected from the parsed storage scheme:

    - ``s3`` / ``s3a`` → empty :class:`AwsCredentials`
    - ``abfss`` → empty :class:`AzureUserDelegationSAS`
    - ``gs`` → empty :class:`GcpOauthToken`
    - ``file`` / ``None`` / unparseable → nothing (expiration-only)

    The nested object is **empty**, not populated with placeholder tokens:
    every nested field is ``None`` so Pydantic's ``exclude_none`` recurses
    into an empty dict. Its *presence* on the wire documents which cloud
    path the server routed through; its emptiness makes it impossible for
    a client to mistake the stub for a real credential. Real token
    vending stays explicitly out of scope (metadata-only design,
    README design principle 3).

    Args:
        scheme: The parsed storage scheme, or ``None`` for legacy /
            unparseable / missing ``storage_location`` values.

    Returns:
        TemporaryCredentials: A stub response routed to the correct
            cloud-shape, or expiration-only for ``file`` / ``None``.
    """
    expiration = _now_ms() + _CREDENTIAL_LIFETIME_MS
    if scheme in {"s3", "s3a"}:
        return TemporaryCredentials(
            aws_temp_credentials=AwsCredentials(),
            expiration_time=expiration,
        )
    if scheme == "abfss":
        return TemporaryCredentials(
            azure_user_delegation_sas=AzureUserDelegationSAS(),
            expiration_time=expiration,
        )
    if scheme == "gs":
        return TemporaryCredentials(
            gcp_oauth_token=GcpOauthToken(),
            expiration_time=expiration,
        )
    return TemporaryCredentials(expiration_time=expiration)


def _s3_credentials(session: Session, location: str, operation: str) -> TemporaryCredentials:
    """Build the ``TemporaryCredentials`` response for an S3 location.

    The ``aws_temp_credentials`` object is real STS output when vending
    is enabled and the path is governed by a role-bound external
    location, and an empty stub otherwise — both cases carry the same
    ``expiration_time`` so a client that caches on it behaves
    identically.

    Args:
        session: Active SQLAlchemy session.
        location: The resolved S3 ``storage_location``.
        operation: The requested operation, used to label the STS
            session.

    Returns:
        TemporaryCredentials: An S3-shaped response, populated or stub.
    """
    return TemporaryCredentials(
        aws_temp_credentials=_mint_aws_credentials(session, location, operation),
        expiration_time=_now_ms() + _CREDENTIAL_LIFETIME_MS,
    )


def _mint_aws_credentials(session: Session, location: str, operation: str) -> AwsCredentials:
    """Mint real STS credentials for an S3 path, or an empty stub.

    Returns an empty :class:`AwsCredentials` — preserving the
    metadata-only default — unless **all** of these hold: STS vending is
    enabled (``SOYUZ_ENABLE_STS_VENDING``); the path resolves to a
    registered external location; and that location's credential carries
    an ``aws_iam_role_arn``. When they do, the role is assumed via STS
    and the short-lived keys are returned.

    An STS failure (network, denied assume-role, clamped duration) is
    logged and downgraded to the empty stub rather than raised: the
    caller can still fall back to its own static configuration, so a
    vending hiccup degrades gracefully instead of failing the read.

    Args:
        session: Active SQLAlchemy session.
        location: The resolved S3 ``storage_location``.
        operation: The requested operation, used to label the STS
            session.

    Returns:
        AwsCredentials: Real STS keys, or an empty stub.
    """
    settings = get_settings()
    if not settings.enable_sts_vending:
        return AwsCredentials()
    external_location = external_location_service.resolve_external_location_for_path(
        session, location
    )
    if external_location is None or not external_location.credential.aws_iam_role_arn:
        return AwsCredentials()
    try:
        return aws_sts.assume_role_credentials(
            role_arn=external_location.credential.aws_iam_role_arn,
            external_id=external_location.credential.aws_iam_role_external_id,
            region=settings.sts_region,
            duration_seconds=settings.sts_credential_duration_seconds,
            session_name=f"soyuz-{operation.lower()}"[:64],
        )
    except Exception:  # noqa: BLE001 — vending is best-effort; degrade to stub
        _logger.warning(
            "STS vending failed for %s; returning an empty credential stub",
            location,
            exc_info=True,
        )
        return AwsCredentials()


def generate_table_credentials(
    session: Session,
    payload: GenerateTemporaryTableCredential,
) -> TemporaryCredentials:
    """Generate stub temporary credentials for a table.

    The table is resolved by its opaque ``table_id`` so the credential
    remains valid across a rename of any parent. ``UNKNOWN_TABLE_OPERATION``
    is rejected as a 400 invalid request — it exists in the spec only as
    a protobuf default and a real client must send either ``READ`` or
    ``READ_WRITE``. ``NotFoundError`` may propagate from
    :func:`soyuz_catalog.services.table_service.get_table_by_id` when no
    table with that id exists.

    The lookup falls through to
    :func:`soyuz_catalog.services.staging_table_service.get_staging_table_by_id`
    when no real table matches. The upstream JVM ``UCSingleCatalog``
    connector creates a staging table and then immediately calls this
    endpoint with the staging row's id (see
    ``connectors/spark/src/main/scala/io/unitycatalog/spark/UCSingleCatalog.scala``
    in the upstream ``unitycatalog`` repo). The JVM connector does
    not honour a strict split between staging rows and real tables
    here — it expects this endpoint to resolve staging ids — so the
    staging fallthrough is required for wire compatibility. The
    staging row's ``staging_location`` feeds the same per-scheme
    dispatcher.

    The response shape is selected from the resolved table's
    ``storage_location`` scheme by :func:`_resolve_scheme` +
    :func:`_stub_credentials`: ``s3`` / ``s3a`` → empty
    ``aws_temp_credentials``, ``abfss`` → empty
    ``azure_user_delegation_sas``, ``gs`` → empty ``gcp_oauth_token``,
    ``file`` / legacy → ``expiration_time``-only. No real token is ever
    vended — see the module docstring and ``DIVERGENCES.md``.

    Args:
        session: Active SQLAlchemy session.
        payload: Validated request body.

    Returns:
        TemporaryCredentials: Stub response routed to the correct
            cloud-shape for the table's storage scheme.

    Raises:
        InvalidRequestError: If ``operation`` is ``UNKNOWN_TABLE_OPERATION``.
    """
    if payload.operation == "UNKNOWN_TABLE_OPERATION":
        raise InvalidRequestError(
            "operation 'UNKNOWN_TABLE_OPERATION' is not a valid table operation; "
            "use 'READ' or 'READ_WRITE'",
        )
    try:
        table = table_service.get_table_by_id(session, payload.table_id)
    except NotFoundError:
        staging = staging_table_service.get_staging_table_by_id(session, payload.table_id)
        location = staging.staging_location
        scheme = _resolve_scheme("staging_table", staging.id, location)
        if location is not None and scheme in {"s3", "s3a"}:
            return _s3_credentials(session, location, payload.operation)
        return _stub_credentials(scheme)
    location = table.storage_location
    scheme = _resolve_scheme("table", table.id, location)
    if location is not None and scheme in {"s3", "s3a"}:
        return _s3_credentials(session, location, payload.operation)
    return _stub_credentials(scheme)


def generate_volume_credentials(
    session: Session,
    payload: GenerateTemporaryVolumeCredential,
) -> TemporaryCredentials:
    """Generate stub temporary credentials for a volume.

    Mirrors :func:`generate_table_credentials`: rejects the
    ``UNKNOWN_VOLUME_OPERATION`` sentinel, resolves the volume by opaque
    id, and returns a stub response whose cloud-shape is selected from
    the volume's ``storage_location`` scheme (see
    :func:`_stub_credentials`). ``NotFoundError`` may propagate from
    :func:`soyuz_catalog.services.volume_service.get_volume_by_id` when
    no volume with that id exists.

    Args:
        session: Active SQLAlchemy session.
        payload: Validated request body.

    Returns:
        TemporaryCredentials: Stub response routed to the correct
            cloud-shape for the volume's storage scheme.

    Raises:
        InvalidRequestError: If ``operation`` is ``UNKNOWN_VOLUME_OPERATION``.
    """
    if payload.operation == "UNKNOWN_VOLUME_OPERATION":
        raise InvalidRequestError(
            "operation 'UNKNOWN_VOLUME_OPERATION' is not a valid volume operation; "
            "use 'READ_VOLUME' or 'WRITE_VOLUME'",
        )
    volume = volume_service.get_volume_by_id(session, payload.volume_id)
    location = volume.storage_location
    scheme = _resolve_scheme("volume", volume.id, location)
    if location is not None and scheme in {"s3", "s3a"}:
        return _s3_credentials(session, location, payload.operation)
    return _stub_credentials(scheme)


def generate_path_credentials(
    session: Session,
    payload: GenerateTemporaryPathCredential,
) -> TemporaryCredentials:
    """Generate temporary credentials for an arbitrary storage path.

    Unlike the table/volume variants this endpoint does not resolve a
    database row from an id — the client supplies the URL directly. The
    session is still used to resolve the governing external location
    when S3 vending is enabled. The URL is run through
    :func:`parse_storage_uri` with write-path strictness:
    an unsupported or malformed scheme surfaces as
    ``InvalidRequestError`` → 400, because the client *asked* us to
    vend for this URL and an unparseable one is almost certainly a
    typo the client wants to hear about.

    ``UNKNOWN_PATH_OPERATION`` is rejected for the same reason the
    table/volume variants reject their own sentinels. The returned
    response shape is routed through the shared
    :func:`_stub_credentials` so the wire representation is identical
    to the per-table/volume variants for the same storage scheme —
    see DIVERGENCES.md.

    Args:
        session: Active SQLAlchemy session (unused, see above).
        payload: Validated request body.

    Returns:
        TemporaryCredentials: Stub response routed to the correct
            cloud-shape for the requested URL's scheme.

    Raises:
        InvalidRequestError: If ``operation`` is
            ``UNKNOWN_PATH_OPERATION`` or if ``url`` is empty / has an
            unsupported scheme (propagated from
            :func:`parse_storage_uri`).
    """
    if payload.operation == "UNKNOWN_PATH_OPERATION":
        raise InvalidRequestError(
            "operation 'UNKNOWN_PATH_OPERATION' is not a valid path operation; "
            "use 'PATH_READ', 'PATH_READ_WRITE', or 'PATH_CREATE_TABLE'",
        )
    parsed = parse_storage_uri(payload.url)
    _logger.debug("credentials: path %s resolved to scheme=%s", parsed.raw, parsed.scheme)
    if parsed.scheme in {"s3", "s3a"}:
        return _s3_credentials(session, payload.url, payload.operation)
    return _stub_credentials(parsed.scheme)


def generate_model_version_credentials(
    session: Session,
    payload: GenerateTemporaryModelVersionCredential,
) -> TemporaryCredentials:
    """Generate stub temporary credentials for a model version.

    Implements MLflow's UC-OSS
    ``generateTemporaryModelVersionCredential`` RPC. Resolves the
    model version from its four-part triple (catalog, schema, model,
    version) and pairs with the ``finalizeModelVersion`` endpoint to
    support MLflow's create-upload-finalize flow.

    The response is the same shape-routed stub the other variants
    return: cloud schemes get an empty cloud-cred object, ``file://``
    locations get expiration-only. The MLflow client handles the
    expiration-only case via ``LocalArtifactRepository`` (writes
    directly to the local path with no presigning).

    ``UNKNOWN_MODEL_VERSION_OPERATION`` is rejected at this service
    layer for the same reason the table/volume variants reject their
    own sentinels — accepting the proto-default would mask client
    bugs.

    Args:
        session: Active SQLAlchemy session.
        payload: Validated request body with the four-part address.

    Returns:
        TemporaryCredentials: Stub response routed to the correct
            cloud-shape for the model version's storage scheme.

    Raises:
        InvalidRequestError: If ``operation`` is
            ``UNKNOWN_MODEL_VERSION_OPERATION``.
    """
    if payload.operation == "UNKNOWN_MODEL_VERSION_OPERATION":
        raise InvalidRequestError(
            "operation 'UNKNOWN_MODEL_VERSION_OPERATION' is not a valid "
            "model-version operation; use 'READ_MODEL_VERSION' or "
            "'READ_WRITE_MODEL_VERSION'",
        )
    full_name = f"{payload.catalog_name}.{payload.schema_name}.{payload.model_name}"
    row = model_version_service.get_model_version(session, full_name, payload.version)
    location = row.storage_location
    scheme = _resolve_scheme("model_version", row.id, location)
    if location is not None and scheme in {"s3", "s3a"}:
        return _s3_credentials(session, location, payload.operation)
    return _stub_credentials(scheme)


def _resolve_scheme(kind: str, resource_id: str, location: str | None) -> str | None:
    """Resolve the storage scheme of the resolved table/volume.

    The parsed scheme is logged at DEBUG for operator correlation
    and is also the return value that decides which empty
    cloud-credential object the response will carry.

    Rows may legitimately have a ``None`` or legacy free-form
    ``storage_location`` (the read path is lax — only writes gate on
    parseability): parser errors are swallowed here on purpose.
    Both branches return ``None``, which routes to the expiration-only
    response — the same shape a ``file://`` table produces.

    Args:
        kind: ``"table"`` or ``"volume"``; used only for the log line.
        resource_id: Opaque id of the resolved row, for correlation.
        location: The stored ``storage_location``, possibly ``None``.

    Returns:
        str | None: The parsed storage scheme (one of ``file``, ``s3``,
            ``s3a``, ``abfss``, ``gs``) when the stored location parses
            cleanly, or ``None`` for a missing / unparseable location.
    """
    if location is None:
        _logger.debug("credentials: %s %s has no storage_location", kind, resource_id)
        return None
    try:
        parsed = parse_storage_uri(location)
    except InvalidRequestError:
        _logger.debug(
            "credentials: %s %s has legacy unparseable storage_location",
            kind,
            resource_id,
        )
        return None
    _logger.debug(
        "credentials: %s %s resolved to scheme=%s",
        kind,
        resource_id,
        parsed.scheme,
    )
    return parsed.scheme
