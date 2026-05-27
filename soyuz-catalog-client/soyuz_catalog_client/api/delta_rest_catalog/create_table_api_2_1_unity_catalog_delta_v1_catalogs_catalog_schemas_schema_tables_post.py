from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_table_request import CreateTableRequest
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response


def _get_kwargs(
    catalog: str,
    schema: str,
    *,
    body: CreateTableRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/2.1/unity-catalog/delta/v1/catalogs/{catalog}/schemas/{schema}/tables".format(
            catalog=quote(str(catalog), safe=""),
            schema=quote(str(schema), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | None:
    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    catalog: str,
    schema: str,
    *,
    client: AuthenticatedClient | Client,
    body: CreateTableRequest,
) -> Response[HTTPValidationError]:
    """Create Delta table

     Create a new Delta table under ``catalog.schema``.

    Args:
        catalog: Catalog path segment.
        schema: Schema path segment.
        payload: Validated Delta create request body.
        db: Database session dependency.

    Returns:
        LoadTableResponse: The freshly-created table's load
            response, matching a subsequent ``loadTable`` call
            byte-for-byte.

    Args:
        catalog (str):
        schema (str):
        body (CreateTableRequest): Request body for ``POST .../tables``.

            Every field mirrors the spec's ``CreateTableRequest``. The
            ``protocol`` and ``domain_metadata`` fields are **accepted and
            discarded** by the service layer — soyuz does not track per-table
            protocol versions or domain metadata and rejecting them would
            break Delta clients that always emit them. See ADR-0009.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError]
    """

    kwargs = _get_kwargs(
        catalog=catalog,
        schema=schema,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    catalog: str,
    schema: str,
    *,
    client: AuthenticatedClient | Client,
    body: CreateTableRequest,
) -> HTTPValidationError | None:
    """Create Delta table

     Create a new Delta table under ``catalog.schema``.

    Args:
        catalog: Catalog path segment.
        schema: Schema path segment.
        payload: Validated Delta create request body.
        db: Database session dependency.

    Returns:
        LoadTableResponse: The freshly-created table's load
            response, matching a subsequent ``loadTable`` call
            byte-for-byte.

    Args:
        catalog (str):
        schema (str):
        body (CreateTableRequest): Request body for ``POST .../tables``.

            Every field mirrors the spec's ``CreateTableRequest``. The
            ``protocol`` and ``domain_metadata`` fields are **accepted and
            discarded** by the service layer — soyuz does not track per-table
            protocol versions or domain metadata and rejecting them would
            break Delta clients that always emit them. See ADR-0009.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError
    """

    return sync_detailed(
        catalog=catalog,
        schema=schema,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    catalog: str,
    schema: str,
    *,
    client: AuthenticatedClient | Client,
    body: CreateTableRequest,
) -> Response[HTTPValidationError]:
    """Create Delta table

     Create a new Delta table under ``catalog.schema``.

    Args:
        catalog: Catalog path segment.
        schema: Schema path segment.
        payload: Validated Delta create request body.
        db: Database session dependency.

    Returns:
        LoadTableResponse: The freshly-created table's load
            response, matching a subsequent ``loadTable`` call
            byte-for-byte.

    Args:
        catalog (str):
        schema (str):
        body (CreateTableRequest): Request body for ``POST .../tables``.

            Every field mirrors the spec's ``CreateTableRequest``. The
            ``protocol`` and ``domain_metadata`` fields are **accepted and
            discarded** by the service layer — soyuz does not track per-table
            protocol versions or domain metadata and rejecting them would
            break Delta clients that always emit them. See ADR-0009.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError]
    """

    kwargs = _get_kwargs(
        catalog=catalog,
        schema=schema,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    catalog: str,
    schema: str,
    *,
    client: AuthenticatedClient | Client,
    body: CreateTableRequest,
) -> HTTPValidationError | None:
    """Create Delta table

     Create a new Delta table under ``catalog.schema``.

    Args:
        catalog: Catalog path segment.
        schema: Schema path segment.
        payload: Validated Delta create request body.
        db: Database session dependency.

    Returns:
        LoadTableResponse: The freshly-created table's load
            response, matching a subsequent ``loadTable`` call
            byte-for-byte.

    Args:
        catalog (str):
        schema (str):
        body (CreateTableRequest): Request body for ``POST .../tables``.

            Every field mirrors the spec's ``CreateTableRequest``. The
            ``protocol`` and ``domain_metadata`` fields are **accepted and
            discarded** by the service layer — soyuz does not track per-table
            protocol versions or domain metadata and rejecting them would
            break Delta clients that always emit them. See ADR-0009.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError
    """

    return (
        await asyncio_detailed(
            catalog=catalog,
            schema=schema,
            client=client,
            body=body,
        )
    ).parsed
