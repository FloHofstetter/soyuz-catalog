from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_staging_table_request import CreateStagingTableRequest
from ...models.http_validation_error import HTTPValidationError
from ...models.staging_table_response import StagingTableResponse
from ...types import UNSET, Response


def _get_kwargs(
    catalog: str,
    schema: str,
    *,
    body: CreateStagingTableRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/2.1/unity-catalog/delta/v1/catalogs/{catalog}/schemas/{schema}/staging-tables".format(
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
) -> HTTPValidationError | StagingTableResponse | None:
    if response.status_code == 200:
        response_200 = StagingTableResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | StagingTableResponse]:
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
    body: CreateStagingTableRequest,
) -> Response[HTTPValidationError | StagingTableResponse]:
    """Allocate Delta staging table

     Allocate a staging-table UUID and storage location.

    Args:
        catalog: Catalog segment.
        schema: Schema segment.
        payload: Validated staging-table create body.
        db: Database session dependency.

    Returns:
        StagingTableResponse: The allocated UUID + location with
            Delta-shaped protocol and credential stubs.

    Args:
        catalog (str):
        schema (str):
        body (CreateStagingTableRequest): Request body for ``POST .../staging-tables``.

            Single field: the leaf name of the staging-table allocation.
            The parent catalog and schema come from the path. soyuz reuses
            the existing
            :func:`soyuz_catalog.services.staging_table_service.create_staging_table`
            under the hood and augments the response with the Delta-specific
            protocol and credential fields.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | StagingTableResponse]
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
    body: CreateStagingTableRequest,
) -> HTTPValidationError | StagingTableResponse | None:
    """Allocate Delta staging table

     Allocate a staging-table UUID and storage location.

    Args:
        catalog: Catalog segment.
        schema: Schema segment.
        payload: Validated staging-table create body.
        db: Database session dependency.

    Returns:
        StagingTableResponse: The allocated UUID + location with
            Delta-shaped protocol and credential stubs.

    Args:
        catalog (str):
        schema (str):
        body (CreateStagingTableRequest): Request body for ``POST .../staging-tables``.

            Single field: the leaf name of the staging-table allocation.
            The parent catalog and schema come from the path. soyuz reuses
            the existing
            :func:`soyuz_catalog.services.staging_table_service.create_staging_table`
            under the hood and augments the response with the Delta-specific
            protocol and credential fields.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | StagingTableResponse
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
    body: CreateStagingTableRequest,
) -> Response[HTTPValidationError | StagingTableResponse]:
    """Allocate Delta staging table

     Allocate a staging-table UUID and storage location.

    Args:
        catalog: Catalog segment.
        schema: Schema segment.
        payload: Validated staging-table create body.
        db: Database session dependency.

    Returns:
        StagingTableResponse: The allocated UUID + location with
            Delta-shaped protocol and credential stubs.

    Args:
        catalog (str):
        schema (str):
        body (CreateStagingTableRequest): Request body for ``POST .../staging-tables``.

            Single field: the leaf name of the staging-table allocation.
            The parent catalog and schema come from the path. soyuz reuses
            the existing
            :func:`soyuz_catalog.services.staging_table_service.create_staging_table`
            under the hood and augments the response with the Delta-specific
            protocol and credential fields.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | StagingTableResponse]
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
    body: CreateStagingTableRequest,
) -> HTTPValidationError | StagingTableResponse | None:
    """Allocate Delta staging table

     Allocate a staging-table UUID and storage location.

    Args:
        catalog: Catalog segment.
        schema: Schema segment.
        payload: Validated staging-table create body.
        db: Database session dependency.

    Returns:
        StagingTableResponse: The allocated UUID + location with
            Delta-shaped protocol and credential stubs.

    Args:
        catalog (str):
        schema (str):
        body (CreateStagingTableRequest): Request body for ``POST .../staging-tables``.

            Single field: the leaf name of the staging-table allocation.
            The parent catalog and schema come from the path. soyuz reuses
            the existing
            :func:`soyuz_catalog.services.staging_table_service.create_staging_table`
            under the hood and augments the response with the Delta-specific
            protocol and credential fields.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | StagingTableResponse
    """

    return (
        await asyncio_detailed(
            catalog=catalog,
            schema=schema,
            client=client,
            body=body,
        )
    ).parsed
