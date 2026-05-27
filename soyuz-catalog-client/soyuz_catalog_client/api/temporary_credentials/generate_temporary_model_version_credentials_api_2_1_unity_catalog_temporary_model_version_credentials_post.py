from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.generate_temporary_model_version_credential import (
    GenerateTemporaryModelVersionCredential,
)
from ...models.http_validation_error import HTTPValidationError
from ...models.temporary_credentials import TemporaryCredentials
from ...types import UNSET, Response


def _get_kwargs(
    *,
    body: GenerateTemporaryModelVersionCredential,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/2.1/unity-catalog/temporary-model-version-credentials",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | TemporaryCredentials | None:
    if response.status_code == 200:
        response_200 = TemporaryCredentials.from_dict(response.json())

        return response_200

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[HTTPValidationError | TemporaryCredentials]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: GenerateTemporaryModelVersionCredential,
) -> Response[HTTPValidationError | TemporaryCredentials]:
    """Vend temporary model version credentials

     Generate temporary credentials for a model version.

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

    Args:
        body (GenerateTemporaryModelVersionCredential): Request body for ``POST /temporary-model-
            version-credentials``.

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

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TemporaryCredentials]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: GenerateTemporaryModelVersionCredential,
) -> HTTPValidationError | TemporaryCredentials | None:
    """Vend temporary model version credentials

     Generate temporary credentials for a model version.

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

    Args:
        body (GenerateTemporaryModelVersionCredential): Request body for ``POST /temporary-model-
            version-credentials``.

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

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TemporaryCredentials
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: GenerateTemporaryModelVersionCredential,
) -> Response[HTTPValidationError | TemporaryCredentials]:
    """Vend temporary model version credentials

     Generate temporary credentials for a model version.

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

    Args:
        body (GenerateTemporaryModelVersionCredential): Request body for ``POST /temporary-model-
            version-credentials``.

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

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TemporaryCredentials]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: GenerateTemporaryModelVersionCredential,
) -> HTTPValidationError | TemporaryCredentials | None:
    """Vend temporary model version credentials

     Generate temporary credentials for a model version.

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

    Args:
        body (GenerateTemporaryModelVersionCredential): Request body for ``POST /temporary-model-
            version-credentials``.

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

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TemporaryCredentials
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
