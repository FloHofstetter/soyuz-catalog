from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.list_protocol_shares_response import ListProtocolSharesResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    max_results: int | None | Unset = UNSET,
    page_token: None | str | Unset = UNSET,
    authorization: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(authorization, Unset):
        headers["authorization"] = authorization

    params: dict[str, Any] = {}

    json_max_results: int | None | Unset
    if isinstance(max_results, Unset):
        json_max_results = UNSET
    else:
        json_max_results = max_results
    params["maxResults"] = json_max_results

    json_page_token: None | str | Unset
    if isinstance(page_token, Unset):
        json_page_token = UNSET
    else:
        json_page_token = page_token
    params["pageToken"] = json_page_token

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/delta-sharing/shares",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | ListProtocolSharesResponse | None:
    if response.status_code == 200:
        response_200 = ListProtocolSharesResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | ListProtocolSharesResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    max_results: int | None | Unset = UNSET,
    page_token: None | str | Unset = UNSET,
    authorization: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | ListProtocolSharesResponse]:
    """List shares (Delta Sharing protocol)

     List the shares granted to the calling recipient.

    Args:
        max_results: Protocol ``maxResults`` page-size hint.
        page_token: Protocol ``pageToken`` cursor.
        recipient: Authenticated recipient (dependency).
        db: Database session dependency.

    Returns:
        ListProtocolSharesResponse: ``items`` plus ``nextPageToken``
            when more pages exist.

    Args:
        max_results (int | None | Unset):
        page_token (None | str | Unset):
        authorization (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ListProtocolSharesResponse]
    """

    kwargs = _get_kwargs(
        max_results=max_results,
        page_token=page_token,
        authorization=authorization,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    max_results: int | None | Unset = UNSET,
    page_token: None | str | Unset = UNSET,
    authorization: None | str | Unset = UNSET,
) -> HTTPValidationError | ListProtocolSharesResponse | None:
    """List shares (Delta Sharing protocol)

     List the shares granted to the calling recipient.

    Args:
        max_results: Protocol ``maxResults`` page-size hint.
        page_token: Protocol ``pageToken`` cursor.
        recipient: Authenticated recipient (dependency).
        db: Database session dependency.

    Returns:
        ListProtocolSharesResponse: ``items`` plus ``nextPageToken``
            when more pages exist.

    Args:
        max_results (int | None | Unset):
        page_token (None | str | Unset):
        authorization (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ListProtocolSharesResponse
    """

    return sync_detailed(
        client=client,
        max_results=max_results,
        page_token=page_token,
        authorization=authorization,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    max_results: int | None | Unset = UNSET,
    page_token: None | str | Unset = UNSET,
    authorization: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | ListProtocolSharesResponse]:
    """List shares (Delta Sharing protocol)

     List the shares granted to the calling recipient.

    Args:
        max_results: Protocol ``maxResults`` page-size hint.
        page_token: Protocol ``pageToken`` cursor.
        recipient: Authenticated recipient (dependency).
        db: Database session dependency.

    Returns:
        ListProtocolSharesResponse: ``items`` plus ``nextPageToken``
            when more pages exist.

    Args:
        max_results (int | None | Unset):
        page_token (None | str | Unset):
        authorization (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ListProtocolSharesResponse]
    """

    kwargs = _get_kwargs(
        max_results=max_results,
        page_token=page_token,
        authorization=authorization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    max_results: int | None | Unset = UNSET,
    page_token: None | str | Unset = UNSET,
    authorization: None | str | Unset = UNSET,
) -> HTTPValidationError | ListProtocolSharesResponse | None:
    """List shares (Delta Sharing protocol)

     List the shares granted to the calling recipient.

    Args:
        max_results: Protocol ``maxResults`` page-size hint.
        page_token: Protocol ``pageToken`` cursor.
        recipient: Authenticated recipient (dependency).
        db: Database session dependency.

    Returns:
        ListProtocolSharesResponse: ``items`` plus ``nextPageToken``
            when more pages exist.

    Args:
        max_results (int | None | Unset):
        page_token (None | str | Unset):
        authorization (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ListProtocolSharesResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            max_results=max_results,
            page_token=page_token,
            authorization=authorization,
        )
    ).parsed
