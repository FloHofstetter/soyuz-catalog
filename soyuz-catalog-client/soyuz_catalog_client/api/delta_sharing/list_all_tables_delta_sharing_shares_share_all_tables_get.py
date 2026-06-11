from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.list_protocol_tables_response import ListProtocolTablesResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    share: str,
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
        "url": "/delta-sharing/shares/{share}/all-tables".format(
            share=quote(str(share), safe=""),
        ),
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | ListProtocolTablesResponse | None:
    if response.status_code == 200:
        response_200 = ListProtocolTablesResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | ListProtocolTablesResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    share: str,
    *,
    client: AuthenticatedClient | Client,
    max_results: int | None | Unset = UNSET,
    page_token: None | str | Unset = UNSET,
    authorization: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | ListProtocolTablesResponse]:
    """List all tables in share (Delta Sharing protocol)

     List every table of a share across all of its schemas.

    Args:
        share: Share name from the URL.
        max_results: Protocol ``maxResults`` page-size hint.
        page_token: Protocol ``pageToken`` cursor.
        recipient: Authenticated recipient (dependency).
        db: Database session dependency.

    Returns:
        ListProtocolTablesResponse: ``items`` plus ``nextPageToken``
            when more pages exist.

    Args:
        share (str):
        max_results (int | None | Unset):
        page_token (None | str | Unset):
        authorization (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ListProtocolTablesResponse]
    """

    kwargs = _get_kwargs(
        share=share,
        max_results=max_results,
        page_token=page_token,
        authorization=authorization,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    share: str,
    *,
    client: AuthenticatedClient | Client,
    max_results: int | None | Unset = UNSET,
    page_token: None | str | Unset = UNSET,
    authorization: None | str | Unset = UNSET,
) -> HTTPValidationError | ListProtocolTablesResponse | None:
    """List all tables in share (Delta Sharing protocol)

     List every table of a share across all of its schemas.

    Args:
        share: Share name from the URL.
        max_results: Protocol ``maxResults`` page-size hint.
        page_token: Protocol ``pageToken`` cursor.
        recipient: Authenticated recipient (dependency).
        db: Database session dependency.

    Returns:
        ListProtocolTablesResponse: ``items`` plus ``nextPageToken``
            when more pages exist.

    Args:
        share (str):
        max_results (int | None | Unset):
        page_token (None | str | Unset):
        authorization (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ListProtocolTablesResponse
    """

    return sync_detailed(
        share=share,
        client=client,
        max_results=max_results,
        page_token=page_token,
        authorization=authorization,
    ).parsed


async def asyncio_detailed(
    share: str,
    *,
    client: AuthenticatedClient | Client,
    max_results: int | None | Unset = UNSET,
    page_token: None | str | Unset = UNSET,
    authorization: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | ListProtocolTablesResponse]:
    """List all tables in share (Delta Sharing protocol)

     List every table of a share across all of its schemas.

    Args:
        share: Share name from the URL.
        max_results: Protocol ``maxResults`` page-size hint.
        page_token: Protocol ``pageToken`` cursor.
        recipient: Authenticated recipient (dependency).
        db: Database session dependency.

    Returns:
        ListProtocolTablesResponse: ``items`` plus ``nextPageToken``
            when more pages exist.

    Args:
        share (str):
        max_results (int | None | Unset):
        page_token (None | str | Unset):
        authorization (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ListProtocolTablesResponse]
    """

    kwargs = _get_kwargs(
        share=share,
        max_results=max_results,
        page_token=page_token,
        authorization=authorization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    share: str,
    *,
    client: AuthenticatedClient | Client,
    max_results: int | None | Unset = UNSET,
    page_token: None | str | Unset = UNSET,
    authorization: None | str | Unset = UNSET,
) -> HTTPValidationError | ListProtocolTablesResponse | None:
    """List all tables in share (Delta Sharing protocol)

     List every table of a share across all of its schemas.

    Args:
        share: Share name from the URL.
        max_results: Protocol ``maxResults`` page-size hint.
        page_token: Protocol ``pageToken`` cursor.
        recipient: Authenticated recipient (dependency).
        db: Database session dependency.

    Returns:
        ListProtocolTablesResponse: ``items`` plus ``nextPageToken``
            when more pages exist.

    Args:
        share (str):
        max_results (int | None | Unset):
        page_token (None | str | Unset):
        authorization (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ListProtocolTablesResponse
    """

    return (
        await asyncio_detailed(
            share=share,
            client=client,
            max_results=max_results,
            page_token=page_token,
            authorization=authorization,
        )
    ).parsed
