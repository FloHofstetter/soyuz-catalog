from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.response_delete_share_api_21_unity_catalog_shares_name_delete import (
    ResponseDeleteShareApi21UnityCatalogSharesNameDelete,
)
from ...types import UNSET, Response


def _get_kwargs(
    name: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/api/2.1/unity-catalog/shares/{name}".format(
            name=quote(str(name), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | ResponseDeleteShareApi21UnityCatalogSharesNameDelete | None:
    if response.status_code == 200:
        response_200 = ResponseDeleteShareApi21UnityCatalogSharesNameDelete.from_dict(
            response.json()
        )

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
) -> Response[
    HTTPValidationError | ResponseDeleteShareApi21UnityCatalogSharesNameDelete
]:
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
) -> Response[
    HTTPValidationError | ResponseDeleteShareApi21UnityCatalogSharesNameDelete
]:
    """Delete share

     Delete a share together with its objects and grants.

    Args:
        name: Share name.
        db: Database session dependency.

    Returns:
        dict[str, str]: Empty success payload.

    Args:
        name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ResponseDeleteShareApi21UnityCatalogSharesNameDelete]
    """

    kwargs = _get_kwargs(
        name=name,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    name: str,
    *,
    client: AuthenticatedClient | Client,
) -> HTTPValidationError | ResponseDeleteShareApi21UnityCatalogSharesNameDelete | None:
    """Delete share

     Delete a share together with its objects and grants.

    Args:
        name: Share name.
        db: Database session dependency.

    Returns:
        dict[str, str]: Empty success payload.

    Args:
        name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ResponseDeleteShareApi21UnityCatalogSharesNameDelete
    """

    return sync_detailed(
        name=name,
        client=client,
    ).parsed


async def asyncio_detailed(
    name: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    HTTPValidationError | ResponseDeleteShareApi21UnityCatalogSharesNameDelete
]:
    """Delete share

     Delete a share together with its objects and grants.

    Args:
        name: Share name.
        db: Database session dependency.

    Returns:
        dict[str, str]: Empty success payload.

    Args:
        name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ResponseDeleteShareApi21UnityCatalogSharesNameDelete]
    """

    kwargs = _get_kwargs(
        name=name,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    name: str,
    *,
    client: AuthenticatedClient | Client,
) -> HTTPValidationError | ResponseDeleteShareApi21UnityCatalogSharesNameDelete | None:
    """Delete share

     Delete a share together with its objects and grants.

    Args:
        name: Share name.
        db: Database session dependency.

    Returns:
        dict[str, str]: Empty success payload.

    Args:
        name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ResponseDeleteShareApi21UnityCatalogSharesNameDelete
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
        )
    ).parsed
