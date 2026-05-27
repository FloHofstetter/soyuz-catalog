from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.model_version_info import ModelVersionInfo
from ...types import UNSET, Response


def _get_kwargs(
    full_name: str,
    version: int,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/2.1/unity-catalog/models/{full_name}/versions/{version}".format(
            full_name=quote(str(full_name), safe=""),
            version=quote(str(version), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | ModelVersionInfo | None:
    if response.status_code == 200:
        response_200 = ModelVersionInfo.from_dict(response.json())

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
) -> Response[HTTPValidationError | ModelVersionInfo]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    full_name: str,
    version: int,
    *,
    client: AuthenticatedClient | Client,
) -> Response[HTTPValidationError | ModelVersionInfo]:
    """Get model version

     Fetch a single model version by parent full name and version number.

    Args:
        full_name: Parent ``catalog.schema.model`` path parameter.
        version: Integer version number, 1-indexed.
        db: Database session dependency.

    Returns:
        ModelVersionInfo: The requested row.

    Args:
        full_name (str):
        version (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ModelVersionInfo]
    """

    kwargs = _get_kwargs(
        full_name=full_name,
        version=version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    full_name: str,
    version: int,
    *,
    client: AuthenticatedClient | Client,
) -> HTTPValidationError | ModelVersionInfo | None:
    """Get model version

     Fetch a single model version by parent full name and version number.

    Args:
        full_name: Parent ``catalog.schema.model`` path parameter.
        version: Integer version number, 1-indexed.
        db: Database session dependency.

    Returns:
        ModelVersionInfo: The requested row.

    Args:
        full_name (str):
        version (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ModelVersionInfo
    """

    return sync_detailed(
        full_name=full_name,
        version=version,
        client=client,
    ).parsed


async def asyncio_detailed(
    full_name: str,
    version: int,
    *,
    client: AuthenticatedClient | Client,
) -> Response[HTTPValidationError | ModelVersionInfo]:
    """Get model version

     Fetch a single model version by parent full name and version number.

    Args:
        full_name: Parent ``catalog.schema.model`` path parameter.
        version: Integer version number, 1-indexed.
        db: Database session dependency.

    Returns:
        ModelVersionInfo: The requested row.

    Args:
        full_name (str):
        version (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ModelVersionInfo]
    """

    kwargs = _get_kwargs(
        full_name=full_name,
        version=version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    full_name: str,
    version: int,
    *,
    client: AuthenticatedClient | Client,
) -> HTTPValidationError | ModelVersionInfo | None:
    """Get model version

     Fetch a single model version by parent full name and version number.

    Args:
        full_name: Parent ``catalog.schema.model`` path parameter.
        version: Integer version number, 1-indexed.
        db: Database session dependency.

    Returns:
        ModelVersionInfo: The requested row.

    Args:
        full_name (str):
        version (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ModelVersionInfo
    """

    return (
        await asyncio_detailed(
            full_name=full_name,
            version=version,
            client=client,
        )
    ).parsed
