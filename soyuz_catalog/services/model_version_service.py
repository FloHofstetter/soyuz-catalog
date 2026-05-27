"""Business logic for the Model Versions resource."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from soyuz_catalog.api.schemas import CreateModelVersion, UpdateModelVersion
from soyuz_catalog.db import commit_or_conflict
from soyuz_catalog.exceptions import InvalidRequestError, NotFoundError
from soyuz_catalog.models import ModelVersion, RegisteredModel, _now_ms
from soyuz_catalog.pagination import apply_keyset, build_next_token
from soyuz_catalog.services.registered_model_service import (
    get_registered_model as _get_registered_model_by_full_name,
)
from soyuz_catalog.services.registered_model_service import (
    parse_full_name as _parse_model_full_name,
)
from soyuz_catalog.settings import get_settings


def _derive_storage_location(model_id: str, version: int) -> str:
    """Compute the storage URL for a new model version.

    Resolves the configured ``model_artifact_root`` (filesystem path or
    explicit ``file://`` URL) against the model's opaque id and the
    integer version. The MLflow UC-OSS client uploads artifacts to this
    URL between ``createModelVersion`` and ``finalizeModelVersion``.

    Args:
        model_id: Opaque 32-char hex id of the parent registered model
            (rename-invariant).
        version: Integer version number, 1-indexed.

    Returns:
        str: A ``file://`` URL pointing at the per-version artifact dir.
    """
    root = get_settings().model_artifact_root
    if root.startswith(("file://", "s3://", "s3a://", "abfss://", "gs://")):
        # Already a URL — append components directly.
        base = root.rstrip("/")
        return f"{base}/{model_id}/{version}"
    # Treat as a filesystem path; resolve to absolute and prepend file://
    abs_path = Path(root).resolve()
    return f"file://{abs_path}/{model_id}/{version}"


def _resolve_model_from_triple(
    session: Session,
    catalog_name: str,
    schema_name: str,
    model_name: str,
) -> RegisteredModel:
    """Resolve a registered model from its three-part address.

    The UC ``POST /models/versions`` endpoint addresses the parent
    registered model via three separate top-level fields in the
    request body — ``catalog_name``, ``schema_name``, ``model_name``
    — rather than a ``full_name`` path parameter, which is why this
    service does not take a single ``full_name`` string on create.
    We rebuild one internally and reuse the existing parser. Any
    ``NotFoundError`` from the wrapped lookup propagates unchanged.

    Args:
        session: Active SQLAlchemy session.
        catalog_name: Parent catalog name.
        schema_name: Parent schema name, relative to its catalog.
        model_name: Registered model name, relative to its schema.

    Returns:
        RegisteredModel: The matching parent model.
    """
    return _get_registered_model_by_full_name(
        session,
        f"{catalog_name}.{schema_name}.{model_name}",
    )


def create_model_version(
    session: Session,
    payload: CreateModelVersion,
) -> ModelVersion:
    """Insert a new model version under an existing registered model.

    The version integer is server-assigned: we compute ``MAX(version) + 1``
    scoped to the parent registered model in the same transaction as
    the insert. Under concurrent inserts both callers may resolve the
    same next-version and the second to commit fails the
    ``(registered_model_id, version)`` unique constraint — that race
    surfaces as 409, and the UC spec has no notion of version
    reservation so the retry is on the client. A heavier
    ``SELECT ... FOR UPDATE`` on the parent would cost a round-trip
    per create and still not survive SQLite (no row-level locking);
    the racy-retry behaviour is the same compromise UC OSS Java
    makes.

    Status is ``PENDING_REGISTRATION`` on create. The MLflow UC-OSS
    client uploads artifacts to the server-derived ``storage_location``
    and then calls :func:`finalize_model_version` to flip status to
    ``READY``. The two-step create-upload-finalize state machine is
    what lets MLflow stream artifacts to the server-derived path
    instead of having to know the location up front.

    ``storage_location`` is derived as
    ``{model_artifact_root}/{model_id}/{version}`` so concurrent
    versions never collide and the path is stable across renames of
    any ancestor (uses the opaque ``model_id``, not ``model_name``).

    Args:
        session: Active SQLAlchemy session.
        payload: Validated create request.

    Returns:
        ModelVersion: The newly created row.

    ``NotFoundError`` may propagate from
    :func:`_resolve_model_from_triple` if the parent address is bad.

    Raises:
        ConflictError: If a concurrent create raced us and claimed the
            same version number first.
    """
    model = _resolve_model_from_triple(
        session,
        payload.catalog_name,
        payload.schema_name,
        payload.model_name,
    )
    current_max = session.scalar(
        select(func.coalesce(func.max(ModelVersion.version), 0)).where(
            ModelVersion.registered_model_id == model.id,
        ),
    )
    next_version = int(current_max or 0) + 1
    version = ModelVersion(
        registered_model_id=model.id,
        version=next_version,
        source=payload.source,
        run_id=payload.run_id,
        status="PENDING_REGISTRATION",
        storage_location=_derive_storage_location(model.id, next_version),
        comment=payload.comment,
    )
    session.add(version)
    with commit_or_conflict(
        session,
        f"Model version {next_version} on '{payload.catalog_name}."
        f"{payload.schema_name}.{payload.model_name}' was claimed by a "
        "concurrent create; retry.",
    ):
        pass
    session.refresh(version)
    return version


def get_model_version(
    session: Session,
    full_name: str,
    version: int,
) -> ModelVersion:
    """Fetch a model version by ``(full_name, version)``.

    ``full_name`` resolves the parent registered model; ``version``
    is then a scoped lookup on the ``(registered_model_id, version)``
    unique key.

    Args:
        session: Active SQLAlchemy session.
        full_name: Parent ``catalog.schema.model`` path parameter.
        version: Integer version number, 1-indexed.

    Returns:
        ModelVersion: The matching row.

    ``InvalidRequestError`` may propagate from the shared
    :func:`soyuz_catalog.services.registered_model_service.parse_full_name`
    helper if ``full_name`` is malformed.

    Raises:
        NotFoundError: If the parent model or the requested version
            does not exist.
    """
    _parse_model_full_name(full_name)
    model = _get_registered_model_by_full_name(session, full_name)
    row = session.scalar(
        select(ModelVersion).where(
            ModelVersion.registered_model_id == model.id,
            ModelVersion.version == version,
        ),
    )
    if row is None:
        raise NotFoundError(
            f"Model version {version} of '{full_name}' does not exist",
        )
    return row


def list_model_versions(
    session: Session,
    full_name: str,
    max_results: int | None = None,
    page_token: str | None = None,
) -> tuple[list[ModelVersion], str | None]:
    """List model versions under a registered model.

    Ordering is ``(created_at ASC, id ASC)`` via the shared keyset
    helper, **not** by ``version`` — two versions created in the same
    millisecond would otherwise share a cursor key. ``NotFoundError``
    propagates if the parent registered model does not exist.

    Args:
        session: Active SQLAlchemy session.
        full_name: Parent ``catalog.schema.model`` path parameter.
        max_results: Spec-defined page size hint.
        page_token: Opaque pagination cursor.

    Returns:
        tuple[list[ModelVersion], str | None]: One page of versions
            plus the next page token.
    """
    model = _get_registered_model_by_full_name(session, full_name)
    stmt, limit = apply_keyset(
        select(ModelVersion).where(ModelVersion.registered_model_id == model.id),
        ModelVersion,
        page_token,
        max_results,
    )
    rows = list(session.scalars(stmt))
    return build_next_token(rows, limit)


def update_model_version(
    session: Session,
    full_name: str,
    version: int,
    payload: UpdateModelVersion,
    fields_set: set[str],
) -> ModelVersion:
    """Apply a PATCH to a model version.

    The UC spec permits only ``comment`` on update: ``source``,
    ``run_id``, ``status``, and the version number itself are all
    immutable after registration. The ``extra="forbid"`` on
    :class:`soyuz_catalog.api.schemas.UpdateModelVersion` enforces
    this at the Pydantic layer.

    Args:
        session: Active SQLAlchemy session.
        full_name: Parent ``catalog.schema.model`` path parameter.
        version: Integer version number.
        payload: Validated update request.
        fields_set: Names of fields explicitly present in the body.

    Returns:
        ModelVersion: The updated row.
    """
    row = get_model_version(session, full_name, version)

    if not fields_set:
        return row

    if "comment" in fields_set:
        row.comment = payload.comment

    row.updated_at = _now_ms()
    session.commit()
    session.refresh(row)
    return row


def delete_model_version(
    session: Session,
    full_name: str,
    version: int,
) -> None:
    """Delete a model version.

    ``NotFoundError`` may propagate from :func:`get_model_version`.

    Args:
        session: Active SQLAlchemy session.
        full_name: Parent ``catalog.schema.model`` path parameter.
        version: Integer version number.
    """
    row = get_model_version(session, full_name, version)
    session.delete(row)
    session.commit()


def finalize_model_version(
    session: Session,
    full_name: str,
    version: int,
) -> ModelVersion:
    """Transition a model version from ``PENDING_REGISTRATION`` to ``READY``.

    Implements MLflow's UC-OSS ``finalizeModelVersion`` RPC. The MLflow
    client calls this after uploading artifacts to the server-derived
    ``storage_location``. The state machine permits two transitions:

    - ``PENDING_REGISTRATION → READY`` (success path)
    - ``READY → READY`` (idempotent — re-finalize is no-op)

    Any other source state (notably ``FAILED_REGISTRATION``) raises
    :class:`InvalidRequestError`. Failed versions cannot be revived
    via finalize — the client must delete and recreate them.

    Args:
        session: Active SQLAlchemy session.
        full_name: Parent ``catalog.schema.model`` path parameter.
        version: Integer version number.

    Returns:
        ModelVersion: The updated (or unchanged, on idempotent re-call)
            row in ``READY`` status.

    Raises:
        InvalidRequestError: If the model version is in
            ``FAILED_REGISTRATION`` status.
    """
    row = get_model_version(session, full_name, version)
    if row.status == "READY":
        return row
    if row.status == "FAILED_REGISTRATION":
        raise InvalidRequestError(
            f"Cannot finalize model version {version} of '{full_name}': "
            "current status is FAILED_REGISTRATION. Delete and recreate the "
            "version instead.",
        )
    row.status = "READY"
    row.updated_at = _now_ms()
    session.commit()
    session.refresh(row)
    return row
