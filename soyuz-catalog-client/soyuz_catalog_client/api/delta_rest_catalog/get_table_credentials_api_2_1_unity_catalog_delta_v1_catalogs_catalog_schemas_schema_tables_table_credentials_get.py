from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.credentials_response import CredentialsResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response


def _get_kwargs(
    catalog: str,
    schema: str,
    table: str,
    *,
    operation: str,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["operation"] = operation

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/2.1/unity-catalog/delta/v1/catalogs/{catalog}/schemas/{schema}/tables/{table}/credentials".format(
            catalog=quote(str(catalog), safe=""),
            schema=quote(str(schema), safe=""),
            table=quote(str(table), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> CredentialsResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = CredentialsResponse.from_dict(response.json())

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
) -> Response[CredentialsResponse | HTTPValidationError]:
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
    operation: str,
) -> Response[CredentialsResponse | HTTPValidationError]:
    r"""Get Delta table credentials

     Return an empty credentials list.

    soyuz does not vend cloud credentials (ADR-0009, consistent
    with the existing temporary-credentials stub posture). Empty
    list keeps Delta clients progressing through their write
    paths when they use a storage URL directly.

    Args:
        catalog: Catalog segment.
        schema: Schema segment.
        table: Table segment.
        operation: Required by spec; ignored by soyuz.
        db: Database session dependency; used only to verify the
            table exists so a 404 surfaces for an unknown address.

    Returns:
        CredentialsResponse: Always ``{\"storage-credentials\": []}``.

    Args:
        catalog (str):
        schema (str):
        table (str):
        operation (str): READ or READ_WRITE

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CredentialsResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        catalog=catalog,
        schema=schema,
        table=table,
        operation=operation,
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
    operation: str,
) -> CredentialsResponse | HTTPValidationError | None:
    r"""Get Delta table credentials

     Return an empty credentials list.

    soyuz does not vend cloud credentials (ADR-0009, consistent
    with the existing temporary-credentials stub posture). Empty
    list keeps Delta clients progressing through their write
    paths when they use a storage URL directly.

    Args:
        catalog: Catalog segment.
        schema: Schema segment.
        table: Table segment.
        operation: Required by spec; ignored by soyuz.
        db: Database session dependency; used only to verify the
            table exists so a 404 surfaces for an unknown address.

    Returns:
        CredentialsResponse: Always ``{\"storage-credentials\": []}``.

    Args:
        catalog (str):
        schema (str):
        table (str):
        operation (str): READ or READ_WRITE

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CredentialsResponse | HTTPValidationError
    """

    return sync_detailed(
        catalog=catalog,
        schema=schema,
        table=table,
        client=client,
        operation=operation,
    ).parsed


async def asyncio_detailed(
    catalog: str,
    schema: str,
    table: str,
    *,
    client: AuthenticatedClient | Client,
    operation: str,
) -> Response[CredentialsResponse | HTTPValidationError]:
    r"""Get Delta table credentials

     Return an empty credentials list.

    soyuz does not vend cloud credentials (ADR-0009, consistent
    with the existing temporary-credentials stub posture). Empty
    list keeps Delta clients progressing through their write
    paths when they use a storage URL directly.

    Args:
        catalog: Catalog segment.
        schema: Schema segment.
        table: Table segment.
        operation: Required by spec; ignored by soyuz.
        db: Database session dependency; used only to verify the
            table exists so a 404 surfaces for an unknown address.

    Returns:
        CredentialsResponse: Always ``{\"storage-credentials\": []}``.

    Args:
        catalog (str):
        schema (str):
        table (str):
        operation (str): READ or READ_WRITE

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CredentialsResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        catalog=catalog,
        schema=schema,
        table=table,
        operation=operation,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    catalog: str,
    schema: str,
    table: str,
    *,
    client: AuthenticatedClient | Client,
    operation: str,
) -> CredentialsResponse | HTTPValidationError | None:
    r"""Get Delta table credentials

     Return an empty credentials list.

    soyuz does not vend cloud credentials (ADR-0009, consistent
    with the existing temporary-credentials stub posture). Empty
    list keeps Delta clients progressing through their write
    paths when they use a storage URL directly.

    Args:
        catalog: Catalog segment.
        schema: Schema segment.
        table: Table segment.
        operation: Required by spec; ignored by soyuz.
        db: Database session dependency; used only to verify the
            table exists so a 404 surfaces for an unknown address.

    Returns:
        CredentialsResponse: Always ``{\"storage-credentials\": []}``.

    Args:
        catalog (str):
        schema (str):
        table (str):
        operation (str): READ or READ_WRITE

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CredentialsResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            catalog=catalog,
            schema=schema,
            table=table,
            client=client,
            operation=operation,
        )
    ).parsed
