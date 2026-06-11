from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.share_info import ShareInfo
from ...types import UNSET, Response


def _get_kwargs(
    name: str,
    *,
    table_full_name: str,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["table_full_name"] = table_full_name

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/api/2.1/unity-catalog/shares/{name}/objects".format(
            name=quote(str(name), safe=""),
        ),
        "params": params,
    }

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
    name: str,
    *,
    client: AuthenticatedClient | Client,
    table_full_name: str,
) -> Response[HTTPValidationError | ShareInfo]:
    """Remove table from share

     Remove a table from a share.

    Args:
        name: Share name.
        table_full_name: Required query parameter — the stored
            three-part name of the table to remove (not the
            ``shared_as`` alias).
        db: Database session dependency.

    Returns:
        ShareInfo: The share with its post-remove object list.

    Args:
        name (str):
        table_full_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ShareInfo]
    """

    kwargs = _get_kwargs(
        name=name,
        table_full_name=table_full_name,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    table_full_name: str,
) -> HTTPValidationError | ShareInfo | None:
    """Remove table from share

     Remove a table from a share.

    Args:
        name: Share name.
        table_full_name: Required query parameter — the stored
            three-part name of the table to remove (not the
            ``shared_as`` alias).
        db: Database session dependency.

    Returns:
        ShareInfo: The share with its post-remove object list.

    Args:
        name (str):
        table_full_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ShareInfo
    """

    return sync_detailed(
        name=name,
        client=client,
        table_full_name=table_full_name,
    ).parsed


async def asyncio_detailed(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    table_full_name: str,
) -> Response[HTTPValidationError | ShareInfo]:
    """Remove table from share

     Remove a table from a share.

    Args:
        name: Share name.
        table_full_name: Required query parameter — the stored
            three-part name of the table to remove (not the
            ``shared_as`` alias).
        db: Database session dependency.

    Returns:
        ShareInfo: The share with its post-remove object list.

    Args:
        name (str):
        table_full_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ShareInfo]
    """

    kwargs = _get_kwargs(
        name=name,
        table_full_name=table_full_name,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    table_full_name: str,
) -> HTTPValidationError | ShareInfo | None:
    """Remove table from share

     Remove a table from a share.

    Args:
        name: Share name.
        table_full_name: Required query parameter — the stored
            three-part name of the table to remove (not the
            ``shared_as`` alias).
        db: Database session dependency.

    Returns:
        ShareInfo: The share with its post-remove object list.

    Args:
        name (str):
        table_full_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ShareInfo
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
            table_full_name=table_full_name,
        )
    ).parsed
