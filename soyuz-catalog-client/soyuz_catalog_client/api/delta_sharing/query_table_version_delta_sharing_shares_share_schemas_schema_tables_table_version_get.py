from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    share: str,
    schema: str,
    table: str,
    *,
    starting_timestamp: None | str | Unset = UNSET,
    authorization: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(authorization, Unset):
        headers["authorization"] = authorization

    params: dict[str, Any] = {}

    json_starting_timestamp: None | str | Unset
    if isinstance(starting_timestamp, Unset):
        json_starting_timestamp = UNSET
    else:
        json_starting_timestamp = starting_timestamp
    params["startingTimestamp"] = json_starting_timestamp

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/delta-sharing/shares/{share}/schemas/{schema}/tables/{table}/version".format(
            share=quote(str(share), safe=""),
            schema=quote(str(schema), safe=""),
            table=quote(str(table), safe=""),
        ),
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = response.json()
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
) -> Response[Any | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    share: str,
    schema: str,
    table: str,
    *,
    client: AuthenticatedClient | Client,
    starting_timestamp: None | str | Unset = UNSET,
    authorization: None | str | Unset = UNSET,
) -> Response[Any | HTTPValidationError]:
    """Query table version (Delta Sharing protocol)

     Return the table's current version in the response header.

    Per the protocol the body is empty and the version travels in the
    ``Delta-Table-Version`` header. ``startingTimestamp`` belongs to
    the timestamp-resolution feature soyuz does not implement and is
    rejected loudly rather than ignored — silently returning the
    latest version for a timestamp query would be wrong data.

    Args:
        share: Share name from the URL.
        schema: Protocol schema name from the URL.
        table: Protocol table name from the URL.
        starting_timestamp: Protocol ``startingTimestamp`` parameter
            (unsupported).
        recipient: Authenticated recipient (dependency).
        db: Database session dependency.

    Returns:
        Response: Empty 200 with the ``Delta-Table-Version`` header.

    Raises:
        SharingProtocolError: 501 ``NOT_IMPLEMENTED`` when
            ``startingTimestamp`` is supplied.

    Args:
        share (str):
        schema (str):
        table (str):
        starting_timestamp (None | str | Unset):
        authorization (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        share=share,
        schema=schema,
        table=table,
        starting_timestamp=starting_timestamp,
        authorization=authorization,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    share: str,
    schema: str,
    table: str,
    *,
    client: AuthenticatedClient | Client,
    starting_timestamp: None | str | Unset = UNSET,
    authorization: None | str | Unset = UNSET,
) -> Any | HTTPValidationError | None:
    """Query table version (Delta Sharing protocol)

     Return the table's current version in the response header.

    Per the protocol the body is empty and the version travels in the
    ``Delta-Table-Version`` header. ``startingTimestamp`` belongs to
    the timestamp-resolution feature soyuz does not implement and is
    rejected loudly rather than ignored — silently returning the
    latest version for a timestamp query would be wrong data.

    Args:
        share: Share name from the URL.
        schema: Protocol schema name from the URL.
        table: Protocol table name from the URL.
        starting_timestamp: Protocol ``startingTimestamp`` parameter
            (unsupported).
        recipient: Authenticated recipient (dependency).
        db: Database session dependency.

    Returns:
        Response: Empty 200 with the ``Delta-Table-Version`` header.

    Raises:
        SharingProtocolError: 501 ``NOT_IMPLEMENTED`` when
            ``startingTimestamp`` is supplied.

    Args:
        share (str):
        schema (str):
        table (str):
        starting_timestamp (None | str | Unset):
        authorization (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError
    """

    return sync_detailed(
        share=share,
        schema=schema,
        table=table,
        client=client,
        starting_timestamp=starting_timestamp,
        authorization=authorization,
    ).parsed


async def asyncio_detailed(
    share: str,
    schema: str,
    table: str,
    *,
    client: AuthenticatedClient | Client,
    starting_timestamp: None | str | Unset = UNSET,
    authorization: None | str | Unset = UNSET,
) -> Response[Any | HTTPValidationError]:
    """Query table version (Delta Sharing protocol)

     Return the table's current version in the response header.

    Per the protocol the body is empty and the version travels in the
    ``Delta-Table-Version`` header. ``startingTimestamp`` belongs to
    the timestamp-resolution feature soyuz does not implement and is
    rejected loudly rather than ignored — silently returning the
    latest version for a timestamp query would be wrong data.

    Args:
        share: Share name from the URL.
        schema: Protocol schema name from the URL.
        table: Protocol table name from the URL.
        starting_timestamp: Protocol ``startingTimestamp`` parameter
            (unsupported).
        recipient: Authenticated recipient (dependency).
        db: Database session dependency.

    Returns:
        Response: Empty 200 with the ``Delta-Table-Version`` header.

    Raises:
        SharingProtocolError: 501 ``NOT_IMPLEMENTED`` when
            ``startingTimestamp`` is supplied.

    Args:
        share (str):
        schema (str):
        table (str):
        starting_timestamp (None | str | Unset):
        authorization (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        share=share,
        schema=schema,
        table=table,
        starting_timestamp=starting_timestamp,
        authorization=authorization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    share: str,
    schema: str,
    table: str,
    *,
    client: AuthenticatedClient | Client,
    starting_timestamp: None | str | Unset = UNSET,
    authorization: None | str | Unset = UNSET,
) -> Any | HTTPValidationError | None:
    """Query table version (Delta Sharing protocol)

     Return the table's current version in the response header.

    Per the protocol the body is empty and the version travels in the
    ``Delta-Table-Version`` header. ``startingTimestamp`` belongs to
    the timestamp-resolution feature soyuz does not implement and is
    rejected loudly rather than ignored — silently returning the
    latest version for a timestamp query would be wrong data.

    Args:
        share: Share name from the URL.
        schema: Protocol schema name from the URL.
        table: Protocol table name from the URL.
        starting_timestamp: Protocol ``startingTimestamp`` parameter
            (unsupported).
        recipient: Authenticated recipient (dependency).
        db: Database session dependency.

    Returns:
        Response: Empty 200 with the ``Delta-Table-Version`` header.

    Raises:
        SharingProtocolError: 501 ``NOT_IMPLEMENTED`` when
            ``startingTimestamp`` is supplied.

    Args:
        share (str):
        schema (str):
        table (str):
        starting_timestamp (None | str | Unset):
        authorization (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            share=share,
            schema=schema,
            table=table,
            client=client,
            starting_timestamp=starting_timestamp,
            authorization=authorization,
        )
    ).parsed
