"""HTTP routes for the TemporaryCredentials resource.

Two sibling POST endpoints, one for tables and one for volumes, both
under the same UC API prefix. They share neither a path prefix nor a tag
with tables / volumes because the UC OpenAPI spec groups them under a
dedicated ``TemporaryCredentials`` tag at the root of the API surface.

The routes are **stubs** — see
:mod:`soyuz_catalog.services.credentials_service` for why — and
serialise with ``response_model_exclude_none=True`` so the wire JSON for
a ``file://`` (or any non-cloud) table is just
``{"expiration_time": <ms>}`` instead of a document full of nulls.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from soyuz_catalog.api.deps import get_db
from soyuz_catalog.api.schemas import (
    GenerateTemporaryModelVersionCredential,
    GenerateTemporaryPathCredential,
    GenerateTemporaryTableCredential,
    GenerateTemporaryVolumeCredential,
    TemporaryCredentials,
)
from soyuz_catalog.services import credentials_service

router = APIRouter(tags=["temporary-credentials"])


@router.post(
    "/temporary-table-credentials",
    response_model=TemporaryCredentials,
    response_model_exclude_none=True,
    summary="Vend temporary table credentials",
)
def generate_temporary_table_credentials(
    payload: GenerateTemporaryTableCredential,
    db: Session = Depends(get_db),
) -> TemporaryCredentials:
    """Generate temporary credentials for a table.

    Args:
        payload: Request body with ``table_id`` and ``operation``.
        db: Database session dependency.

    Returns:
        TemporaryCredentials: Stub response with only ``expiration_time``
            populated. See ``DIVERGENCES.md`` for why cloud-specific
            fields are never populated (metadata-only design).
    """
    return credentials_service.generate_table_credentials(db, payload)


@router.post(
    "/temporary-volume-credentials",
    response_model=TemporaryCredentials,
    response_model_exclude_none=True,
    summary="Vend temporary volume credentials",
)
def generate_temporary_volume_credentials(
    payload: GenerateTemporaryVolumeCredential,
    db: Session = Depends(get_db),
) -> TemporaryCredentials:
    """Generate temporary credentials for a volume.

    Args:
        payload: Request body with ``volume_id`` and ``operation``.
        db: Database session dependency.

    Returns:
        TemporaryCredentials: Stub response with only ``expiration_time``
            populated.
    """
    return credentials_service.generate_volume_credentials(db, payload)


@router.post(
    "/temporary-path-credentials",
    response_model=TemporaryCredentials,
    response_model_exclude_none=True,
    summary="Vend temporary path credentials",
)
def generate_temporary_path_credentials(
    payload: GenerateTemporaryPathCredential,
    db: Session = Depends(get_db),
) -> TemporaryCredentials:
    """Generate temporary credentials for an arbitrary storage path.

    Args:
        payload: Request body with ``url`` and ``operation``.
        db: Database session dependency (unused, see service layer).

    Returns:
        TemporaryCredentials: Stub response routed on the URL's
            storage scheme — same shape the table/volume variants
            return for an equivalent ``storage_location``.
    """
    return credentials_service.generate_path_credentials(db, payload)


@router.post(
    "/temporary-model-version-credentials",
    response_model=TemporaryCredentials,
    response_model_exclude_none=True,
    summary="Vend temporary model version credentials",
)
def generate_temporary_model_version_credentials(
    payload: GenerateTemporaryModelVersionCredential,
    db: Session = Depends(get_db),
) -> TemporaryCredentials:
    """Generate temporary credentials for a model version.

    Implements MLflow's UC-OSS
    ``generateTemporaryModelVersionCredential`` RPC. The MLflow client
    calls this between ``createModelVersion`` (which returns a
    ``PENDING_REGISTRATION`` row plus a server-derived
    ``storage_location``) and ``finalizeModelVersion``.

    Args:
        payload: Request body with the four-part address
            ``(catalog_name, schema_name, model_name, version)`` plus
            ``operation`` (``READ_MODEL_VERSION`` or
            ``READ_WRITE_MODEL_VERSION``).
        db: Database session dependency.

    Returns:
        TemporaryCredentials: Stub response shape-routed by the
            model version's ``storage_location`` scheme — for
            ``file://`` locations the response is expiration-only and
            the MLflow client falls back to ``LocalArtifactRepository``.
    """
    return credentials_service.generate_model_version_credentials(db, payload)
