from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_share import CreateShare
from ...models.http_validation_error import HTTPValidationError
from ...models.share_info import ShareInfo
from ...types import UNSET, Response


def _get_kwargs(
    *,
    body: CreateShare,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/2.1/unity-catalog/shares",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | ShareInfo | None:
    if response.status_code == 200:
        response_200 = ShareInfo.from_dict(response.json())

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
) -> Response[HTTPValidationError | ShareInfo]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateShare,
) -> Response[HTTPValidationError | ShareInfo]:
    """Create share

     Create a new, empty share.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        ShareInfo: The created share.

    Args:
        body (CreateShare): Request body for ``POST /shares``.

            ``extra="forbid"`` rejects unknown fields (including ``id``,
            ``objects``, …) with 422 — tables enter a share through the
            dedicated ``POST /shares/{name}/objects`` endpoint, never inline
            on create.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ShareInfo]
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
    body: CreateShare,
) -> HTTPValidationError | ShareInfo | None:
    """Create share

     Create a new, empty share.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        ShareInfo: The created share.

    Args:
        body (CreateShare): Request body for ``POST /shares``.

            ``extra="forbid"`` rejects unknown fields (including ``id``,
            ``objects``, …) with 422 — tables enter a share through the
            dedicated ``POST /shares/{name}/objects`` endpoint, never inline
            on create.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ShareInfo
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateShare,
) -> Response[HTTPValidationError | ShareInfo]:
    """Create share

     Create a new, empty share.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        ShareInfo: The created share.

    Args:
        body (CreateShare): Request body for ``POST /shares``.

            ``extra="forbid"`` rejects unknown fields (including ``id``,
            ``objects``, …) with 422 — tables enter a share through the
            dedicated ``POST /shares/{name}/objects`` endpoint, never inline
            on create.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ShareInfo]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreateShare,
) -> HTTPValidationError | ShareInfo | None:
    """Create share

     Create a new, empty share.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        ShareInfo: The created share.

    Args:
        body (CreateShare): Request body for ``POST /shares``.

            ``extra="forbid"`` rejects unknown fields (including ``id``,
            ``objects``, …) with 422 — tables enter a share through the
            dedicated ``POST /shares/{name}/objects`` endpoint, never inline
            on create.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ShareInfo
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
