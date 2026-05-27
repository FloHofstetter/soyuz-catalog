from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_table import CreateTable
from ...models.http_validation_error import HTTPValidationError
from ...models.table_info import TableInfo
from ...types import UNSET, Response


def _get_kwargs(
    *,
    body: CreateTable,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/2.1/unity-catalog/tables",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | TableInfo | None:
    if response.status_code == 200:
        response_200 = TableInfo.from_dict(response.json())

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
) -> Response[HTTPValidationError | TableInfo]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateTable,
) -> Response[HTTPValidationError | TableInfo]:
    """Create table

     Create a new table under an existing schema.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        TableInfo: The created table.

    Args:
        body (CreateTable): Request body for ``POST /tables``.

            The UC spec requires ``name``, ``catalog_name``, ``schema_name``,
            ``table_type``, ``data_source_format``, ``columns``, and
            ``storage_location`` on create — there is no legitimate table without
            a physical storage location or a declared format, even for managed
            tables where the server will later rewrite it.

            ``extra="forbid"`` rejects unknown fields; the same policy applies to
            each element of ``columns`` via :class:`ColumnInfo`. There is no
            ``UpdateTable`` counterpart: the UC OpenAPI spec defines no
            ``PATCH /tables`` endpoint and soyuz registers no handler for it, so
            the route returns 405 Method Not Allowed (see ``DIVERGENCES.md``).

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TableInfo]
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
    body: CreateTable,
) -> HTTPValidationError | TableInfo | None:
    """Create table

     Create a new table under an existing schema.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        TableInfo: The created table.

    Args:
        body (CreateTable): Request body for ``POST /tables``.

            The UC spec requires ``name``, ``catalog_name``, ``schema_name``,
            ``table_type``, ``data_source_format``, ``columns``, and
            ``storage_location`` on create — there is no legitimate table without
            a physical storage location or a declared format, even for managed
            tables where the server will later rewrite it.

            ``extra="forbid"`` rejects unknown fields; the same policy applies to
            each element of ``columns`` via :class:`ColumnInfo`. There is no
            ``UpdateTable`` counterpart: the UC OpenAPI spec defines no
            ``PATCH /tables`` endpoint and soyuz registers no handler for it, so
            the route returns 405 Method Not Allowed (see ``DIVERGENCES.md``).

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TableInfo
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateTable,
) -> Response[HTTPValidationError | TableInfo]:
    """Create table

     Create a new table under an existing schema.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        TableInfo: The created table.

    Args:
        body (CreateTable): Request body for ``POST /tables``.

            The UC spec requires ``name``, ``catalog_name``, ``schema_name``,
            ``table_type``, ``data_source_format``, ``columns``, and
            ``storage_location`` on create — there is no legitimate table without
            a physical storage location or a declared format, even for managed
            tables where the server will later rewrite it.

            ``extra="forbid"`` rejects unknown fields; the same policy applies to
            each element of ``columns`` via :class:`ColumnInfo`. There is no
            ``UpdateTable`` counterpart: the UC OpenAPI spec defines no
            ``PATCH /tables`` endpoint and soyuz registers no handler for it, so
            the route returns 405 Method Not Allowed (see ``DIVERGENCES.md``).

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TableInfo]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreateTable,
) -> HTTPValidationError | TableInfo | None:
    """Create table

     Create a new table under an existing schema.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        TableInfo: The created table.

    Args:
        body (CreateTable): Request body for ``POST /tables``.

            The UC spec requires ``name``, ``catalog_name``, ``schema_name``,
            ``table_type``, ``data_source_format``, ``columns``, and
            ``storage_location`` on create — there is no legitimate table without
            a physical storage location or a declared format, even for managed
            tables where the server will later rewrite it.

            ``extra="forbid"`` rejects unknown fields; the same policy applies to
            each element of ``columns`` via :class:`ColumnInfo`. There is no
            ``UpdateTable`` counterpart: the UC OpenAPI spec defines no
            ``PATCH /tables`` endpoint and soyuz registers no handler for it, so
            the route returns 405 Method Not Allowed (see ``DIVERGENCES.md``).

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TableInfo
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
