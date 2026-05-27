from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.rename_table_request import RenameTableRequest
from ...types import UNSET, Response


def _get_kwargs(
    catalog: str,
    schema: str,
    table: str,
    *,
    body: RenameTableRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/2.1/unity-catalog/delta/v1/catalogs/{catalog}/schemas/{schema}/tables/{table}/rename".format(
            catalog=quote(str(catalog), safe=""),
            schema=quote(str(schema), safe=""),
            table=quote(str(table), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | HTTPValidationError | None:
    if response.status_code == 204:
        response_204 = cast(Any, None)
        return response_204

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
    catalog: str,
    schema: str,
    table: str,
    *,
    client: AuthenticatedClient | Client,
    body: RenameTableRequest,
) -> Response[Any | HTTPValidationError]:
    """Rename Delta table

     Rename a table in place. Returns 204 No Content.

    Args:
        catalog: Catalog segment.
        schema: Schema segment.
        table: Current table segment.
        payload: Validated rename request body.
        db: Database session dependency.

    Returns:
        Response: Empty 204 body.

    Args:
        catalog (str):
        schema (str):
        table (str):
        body (RenameTableRequest): Request body for ``POST .../tables/{table}/rename``.

            The spec is minimal — a single ``new-name`` field. soyuz surfaces
            an empty string as 400 ``INVALID_ARGUMENT`` at the service layer
            rather than relying on pydantic's ``min_length`` so the error
            message matches the rest of the service's 400 envelope shape.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        catalog=catalog,
        schema=schema,
        table=table,
        body=body,
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
    body: RenameTableRequest,
) -> Any | HTTPValidationError | None:
    """Rename Delta table

     Rename a table in place. Returns 204 No Content.

    Args:
        catalog: Catalog segment.
        schema: Schema segment.
        table: Current table segment.
        payload: Validated rename request body.
        db: Database session dependency.

    Returns:
        Response: Empty 204 body.

    Args:
        catalog (str):
        schema (str):
        table (str):
        body (RenameTableRequest): Request body for ``POST .../tables/{table}/rename``.

            The spec is minimal — a single ``new-name`` field. soyuz surfaces
            an empty string as 400 ``INVALID_ARGUMENT`` at the service layer
            rather than relying on pydantic's ``min_length`` so the error
            message matches the rest of the service's 400 envelope shape.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError
    """

    return sync_detailed(
        catalog=catalog,
        schema=schema,
        table=table,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    catalog: str,
    schema: str,
    table: str,
    *,
    client: AuthenticatedClient | Client,
    body: RenameTableRequest,
) -> Response[Any | HTTPValidationError]:
    """Rename Delta table

     Rename a table in place. Returns 204 No Content.

    Args:
        catalog: Catalog segment.
        schema: Schema segment.
        table: Current table segment.
        payload: Validated rename request body.
        db: Database session dependency.

    Returns:
        Response: Empty 204 body.

    Args:
        catalog (str):
        schema (str):
        table (str):
        body (RenameTableRequest): Request body for ``POST .../tables/{table}/rename``.

            The spec is minimal — a single ``new-name`` field. soyuz surfaces
            an empty string as 400 ``INVALID_ARGUMENT`` at the service layer
            rather than relying on pydantic's ``min_length`` so the error
            message matches the rest of the service's 400 envelope shape.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        catalog=catalog,
        schema=schema,
        table=table,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    catalog: str,
    schema: str,
    table: str,
    *,
    client: AuthenticatedClient | Client,
    body: RenameTableRequest,
) -> Any | HTTPValidationError | None:
    """Rename Delta table

     Rename a table in place. Returns 204 No Content.

    Args:
        catalog: Catalog segment.
        schema: Schema segment.
        table: Current table segment.
        payload: Validated rename request body.
        db: Database session dependency.

    Returns:
        Response: Empty 204 body.

    Args:
        catalog (str):
        schema (str):
        table (str):
        body (RenameTableRequest): Request body for ``POST .../tables/{table}/rename``.

            The spec is minimal — a single ``new-name`` field. soyuz surfaces
            an empty string as 400 ``INVALID_ARGUMENT`` at the service layer
            rather than relying on pydantic's ``min_length`` so the error
            message matches the rest of the service's 400 envelope shape.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            catalog=catalog,
            schema=schema,
            table=table,
            client=client,
            body=body,
        )
    ).parsed
