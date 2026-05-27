from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_volume import CreateVolume
from ...models.http_validation_error import HTTPValidationError
from ...models.volume_info import VolumeInfo
from ...types import UNSET, Response


def _get_kwargs(
    *,
    body: CreateVolume,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/2.1/unity-catalog/volumes",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | VolumeInfo | None:
    if response.status_code == 200:
        response_200 = VolumeInfo.from_dict(response.json())

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
) -> Response[HTTPValidationError | VolumeInfo]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateVolume,
) -> Response[HTTPValidationError | VolumeInfo]:
    """Create volume

     Create a new volume under an existing schema.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        VolumeInfo: The created volume.

    Args:
        body (CreateVolume): Request body for ``POST /volumes``.

            The UC spec requires ``catalog_name``, ``schema_name``, ``name``, and
            ``volume_type`` on create. ``storage_location`` and ``comment`` are
            optional. ``volume_type`` is constrained to the spec enum
            ``{"MANAGED", "EXTERNAL"}`` at the Pydantic layer so that a typo
            surfaces as 422 rather than reaching the database as a free-form
            string.

            ``extra="forbid"`` rejects unknown fields, same UC OSS bug-fix policy
            as every other request body in this module.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | VolumeInfo]
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
    body: CreateVolume,
) -> HTTPValidationError | VolumeInfo | None:
    """Create volume

     Create a new volume under an existing schema.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        VolumeInfo: The created volume.

    Args:
        body (CreateVolume): Request body for ``POST /volumes``.

            The UC spec requires ``catalog_name``, ``schema_name``, ``name``, and
            ``volume_type`` on create. ``storage_location`` and ``comment`` are
            optional. ``volume_type`` is constrained to the spec enum
            ``{"MANAGED", "EXTERNAL"}`` at the Pydantic layer so that a typo
            surfaces as 422 rather than reaching the database as a free-form
            string.

            ``extra="forbid"`` rejects unknown fields, same UC OSS bug-fix policy
            as every other request body in this module.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | VolumeInfo
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateVolume,
) -> Response[HTTPValidationError | VolumeInfo]:
    """Create volume

     Create a new volume under an existing schema.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        VolumeInfo: The created volume.

    Args:
        body (CreateVolume): Request body for ``POST /volumes``.

            The UC spec requires ``catalog_name``, ``schema_name``, ``name``, and
            ``volume_type`` on create. ``storage_location`` and ``comment`` are
            optional. ``volume_type`` is constrained to the spec enum
            ``{"MANAGED", "EXTERNAL"}`` at the Pydantic layer so that a typo
            surfaces as 422 rather than reaching the database as a free-form
            string.

            ``extra="forbid"`` rejects unknown fields, same UC OSS bug-fix policy
            as every other request body in this module.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | VolumeInfo]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreateVolume,
) -> HTTPValidationError | VolumeInfo | None:
    """Create volume

     Create a new volume under an existing schema.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        VolumeInfo: The created volume.

    Args:
        body (CreateVolume): Request body for ``POST /volumes``.

            The UC spec requires ``catalog_name``, ``schema_name``, ``name``, and
            ``volume_type`` on create. ``storage_location`` and ``comment`` are
            optional. ``volume_type`` is constrained to the spec enum
            ``{"MANAGED", "EXTERNAL"}`` at the Pydantic layer so that a typo
            surfaces as 422 rather than reaching the database as a free-form
            string.

            ``extra="forbid"`` rejects unknown fields, same UC OSS bug-fix policy
            as every other request body in this module.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | VolumeInfo
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
