from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_staging_table import CreateStagingTable
from ...models.http_validation_error import HTTPValidationError
from ...models.staging_table_info import StagingTableInfo
from ...types import UNSET, Response


def _get_kwargs(
    *,
    body: CreateStagingTable,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/2.1/unity-catalog/staging-tables",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | StagingTableInfo | None:
    if response.status_code == 200:
        response_200 = StagingTableInfo.from_dict(response.json())

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
) -> Response[HTTPValidationError | StagingTableInfo]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateStagingTable,
) -> Response[HTTPValidationError | StagingTableInfo]:
    """Allocate staging table

     Allocate a new staging table.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        StagingTableInfo: The allocated row.

    Args:
        body (CreateStagingTable): Request body for ``POST /staging-tables``.

            The UC spec marks every field as required: a staging table is
            addressed by ``(catalog_name, schema_name, name)`` and has no
            other client-supplied inputs. ``extra="forbid"`` rejects unknown
            fields — notably including ``storage_location`` and ``id``, which
            are server-derived on the response and must not be accepted on
            create.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | StagingTableInfo]
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
    body: CreateStagingTable,
) -> HTTPValidationError | StagingTableInfo | None:
    """Allocate staging table

     Allocate a new staging table.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        StagingTableInfo: The allocated row.

    Args:
        body (CreateStagingTable): Request body for ``POST /staging-tables``.

            The UC spec marks every field as required: a staging table is
            addressed by ``(catalog_name, schema_name, name)`` and has no
            other client-supplied inputs. ``extra="forbid"`` rejects unknown
            fields — notably including ``storage_location`` and ``id``, which
            are server-derived on the response and must not be accepted on
            create.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | StagingTableInfo
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateStagingTable,
) -> Response[HTTPValidationError | StagingTableInfo]:
    """Allocate staging table

     Allocate a new staging table.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        StagingTableInfo: The allocated row.

    Args:
        body (CreateStagingTable): Request body for ``POST /staging-tables``.

            The UC spec marks every field as required: a staging table is
            addressed by ``(catalog_name, schema_name, name)`` and has no
            other client-supplied inputs. ``extra="forbid"`` rejects unknown
            fields — notably including ``storage_location`` and ``id``, which
            are server-derived on the response and must not be accepted on
            create.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | StagingTableInfo]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreateStagingTable,
) -> HTTPValidationError | StagingTableInfo | None:
    """Allocate staging table

     Allocate a new staging table.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        StagingTableInfo: The allocated row.

    Args:
        body (CreateStagingTable): Request body for ``POST /staging-tables``.

            The UC spec marks every field as required: a staging table is
            addressed by ``(catalog_name, schema_name, name)`` and has no
            other client-supplied inputs. ``extra="forbid"`` rejects unknown
            fields — notably including ``storage_location`` and ``id``, which
            are server-derived on the response and must not be accepted on
            create.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | StagingTableInfo
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
