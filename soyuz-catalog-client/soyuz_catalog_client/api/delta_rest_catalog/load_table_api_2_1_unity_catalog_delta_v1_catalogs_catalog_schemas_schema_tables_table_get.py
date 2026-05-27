from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response


def _get_kwargs(
    catalog: str,
    schema: str,
    table: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/2.1/unity-catalog/delta/v1/catalogs/{catalog}/schemas/{schema}/tables/{table}".format(
            catalog=quote(str(catalog), safe=""),
            schema=quote(str(schema), safe=""),
            table=quote(str(table), safe=""),
        ),
    }

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
    table: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[HTTPValidationError]:
    """Load Delta table

     Load a single table's full Delta metadata.

    Args:
        catalog: Catalog segment.
        schema: Schema segment.
        table: Table segment.
        db: Database session dependency.

    Returns:
        LoadTableResponse: Full Delta wire metadata for the table.

    Args:
        catalog (str):
        schema (str):
        table (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError]
    """

    kwargs = _get_kwargs(
        catalog=catalog,
        schema=schema,
        table=table,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    catalog: str,
    schema: str,
    table: str,
    *,
    client: AuthenticatedClient | Client,
) -> HTTPValidationError | None:
    """Load Delta table

     Load a single table's full Delta metadata.

    Args:
        catalog: Catalog segment.
        schema: Schema segment.
        table: Table segment.
        db: Database session dependency.

    Returns:
        LoadTableResponse: Full Delta wire metadata for the table.

    Args:
        catalog (str):
        schema (str):
        table (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError
    """

    return sync_detailed(
        catalog=catalog,
        schema=schema,
        table=table,
        client=client,
    ).parsed


async def asyncio_detailed(
    catalog: str,
    schema: str,
    table: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[HTTPValidationError]:
    """Load Delta table

     Load a single table's full Delta metadata.

    Args:
        catalog: Catalog segment.
        schema: Schema segment.
        table: Table segment.
        db: Database session dependency.

    Returns:
        LoadTableResponse: Full Delta wire metadata for the table.

    Args:
        catalog (str):
        schema (str):
        table (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError]
    """

    kwargs = _get_kwargs(
        catalog=catalog,
        schema=schema,
        table=table,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    catalog: str,
    schema: str,
    table: str,
    *,
    client: AuthenticatedClient | Client,
) -> HTTPValidationError | None:
    """Load Delta table

     Load a single table's full Delta metadata.

    Args:
        catalog: Catalog segment.
        schema: Schema segment.
        table: Table segment.
        db: Database session dependency.

    Returns:
        LoadTableResponse: Full Delta wire metadata for the table.

    Args:
        catalog (str):
        schema (str):
        table (str):

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
            table=table,
            client=client,
        )
    ).parsed
