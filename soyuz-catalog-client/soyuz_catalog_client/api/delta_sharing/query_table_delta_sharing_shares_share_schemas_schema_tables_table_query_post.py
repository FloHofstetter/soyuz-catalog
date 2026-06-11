from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.query_table_request import QueryTableRequest
from ...types import UNSET, Response, Unset


def _get_kwargs(
    share: str,
    schema: str,
    table: str,
    *,
    body: None | QueryTableRequest | Unset = UNSET,
    authorization: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(authorization, Unset):
        headers["authorization"] = authorization

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/delta-sharing/shares/{share}/schemas/{schema}/tables/{table}/query".format(
            share=quote(str(share), safe=""),
            schema=quote(str(schema), safe=""),
            table=quote(str(table), safe=""),
        ),
    }

    if isinstance(body, QueryTableRequest):
        _kwargs["json"] = body.to_dict()
    else:
        _kwargs["json"] = body

    headers["Content-Type"] = "application/json"

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
    body: None | QueryTableRequest | Unset = UNSET,
    authorization: None | str | Unset = UNSET,
) -> Response[Any | HTTPValidationError]:
    """Read data from table (Delta Sharing protocol)

     Return protocol, metaData, and per-file actions as NDJSON.

    Predicate and limit hints are accepted and ignored (the protocol
    defines them as hints the server may disregard); ``version`` pins
    the snapshot. Each file action's ``url`` points back at this
    server's pre-signed download endpoint — soyuz serves the parquet
    bytes itself for ``file://`` tables, taking the role a cloud
    object store's pre-signed URLs play elsewhere.

    Args:
        share: Share name from the URL.
        schema: Protocol schema name from the URL.
        table: Protocol table name from the URL.
        request: The live request, used to derive the absolute base
            URL embedded in the file actions.
        payload: Optional query body (hints / version pin).
        recipient: Authenticated recipient (dependency).
        db: Database session dependency.

    Returns:
        Response: NDJSON body with the ``Delta-Table-Version`` header.

    Raises:
        SharingProtocolError: 501 ``NOT_IMPLEMENTED`` when the body
            carries ``timestamp``, ``startingVersion``, or
            ``endingVersion`` — the timestamp-resolution and CDF
            features this server does not implement.

    Args:
        share (str):
        schema (str):
        table (str):
        authorization (None | str | Unset):
        body (None | QueryTableRequest | Unset):

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
        body=body,
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
    body: None | QueryTableRequest | Unset = UNSET,
    authorization: None | str | Unset = UNSET,
) -> Any | HTTPValidationError | None:
    """Read data from table (Delta Sharing protocol)

     Return protocol, metaData, and per-file actions as NDJSON.

    Predicate and limit hints are accepted and ignored (the protocol
    defines them as hints the server may disregard); ``version`` pins
    the snapshot. Each file action's ``url`` points back at this
    server's pre-signed download endpoint — soyuz serves the parquet
    bytes itself for ``file://`` tables, taking the role a cloud
    object store's pre-signed URLs play elsewhere.

    Args:
        share: Share name from the URL.
        schema: Protocol schema name from the URL.
        table: Protocol table name from the URL.
        request: The live request, used to derive the absolute base
            URL embedded in the file actions.
        payload: Optional query body (hints / version pin).
        recipient: Authenticated recipient (dependency).
        db: Database session dependency.

    Returns:
        Response: NDJSON body with the ``Delta-Table-Version`` header.

    Raises:
        SharingProtocolError: 501 ``NOT_IMPLEMENTED`` when the body
            carries ``timestamp``, ``startingVersion``, or
            ``endingVersion`` — the timestamp-resolution and CDF
            features this server does not implement.

    Args:
        share (str):
        schema (str):
        table (str):
        authorization (None | str | Unset):
        body (None | QueryTableRequest | Unset):

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
        body=body,
        authorization=authorization,
    ).parsed


async def asyncio_detailed(
    share: str,
    schema: str,
    table: str,
    *,
    client: AuthenticatedClient | Client,
    body: None | QueryTableRequest | Unset = UNSET,
    authorization: None | str | Unset = UNSET,
) -> Response[Any | HTTPValidationError]:
    """Read data from table (Delta Sharing protocol)

     Return protocol, metaData, and per-file actions as NDJSON.

    Predicate and limit hints are accepted and ignored (the protocol
    defines them as hints the server may disregard); ``version`` pins
    the snapshot. Each file action's ``url`` points back at this
    server's pre-signed download endpoint — soyuz serves the parquet
    bytes itself for ``file://`` tables, taking the role a cloud
    object store's pre-signed URLs play elsewhere.

    Args:
        share: Share name from the URL.
        schema: Protocol schema name from the URL.
        table: Protocol table name from the URL.
        request: The live request, used to derive the absolute base
            URL embedded in the file actions.
        payload: Optional query body (hints / version pin).
        recipient: Authenticated recipient (dependency).
        db: Database session dependency.

    Returns:
        Response: NDJSON body with the ``Delta-Table-Version`` header.

    Raises:
        SharingProtocolError: 501 ``NOT_IMPLEMENTED`` when the body
            carries ``timestamp``, ``startingVersion``, or
            ``endingVersion`` — the timestamp-resolution and CDF
            features this server does not implement.

    Args:
        share (str):
        schema (str):
        table (str):
        authorization (None | str | Unset):
        body (None | QueryTableRequest | Unset):

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
        body=body,
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
    body: None | QueryTableRequest | Unset = UNSET,
    authorization: None | str | Unset = UNSET,
) -> Any | HTTPValidationError | None:
    """Read data from table (Delta Sharing protocol)

     Return protocol, metaData, and per-file actions as NDJSON.

    Predicate and limit hints are accepted and ignored (the protocol
    defines them as hints the server may disregard); ``version`` pins
    the snapshot. Each file action's ``url`` points back at this
    server's pre-signed download endpoint — soyuz serves the parquet
    bytes itself for ``file://`` tables, taking the role a cloud
    object store's pre-signed URLs play elsewhere.

    Args:
        share: Share name from the URL.
        schema: Protocol schema name from the URL.
        table: Protocol table name from the URL.
        request: The live request, used to derive the absolute base
            URL embedded in the file actions.
        payload: Optional query body (hints / version pin).
        recipient: Authenticated recipient (dependency).
        db: Database session dependency.

    Returns:
        Response: NDJSON body with the ``Delta-Table-Version`` header.

    Raises:
        SharingProtocolError: 501 ``NOT_IMPLEMENTED`` when the body
            carries ``timestamp``, ``startingVersion``, or
            ``endingVersion`` — the timestamp-resolution and CDF
            features this server does not implement.

    Args:
        share (str):
        schema (str):
        table (str):
        authorization (None | str | Unset):
        body (None | QueryTableRequest | Unset):

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
            body=body,
            authorization=authorization,
        )
    ).parsed
