from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.delta_list_tables_response import DeltaListTablesResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    catalog: str,
    schema: str,
    *,
    max_results: int | None | Unset = UNSET,
    page_token: None | str | Unset = UNSET,
) -> dict[str, Any]:

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
        "url": "/api/2.1/unity-catalog/delta/v1/catalogs/{catalog}/schemas/{schema}/tables".format(
            catalog=quote(str(catalog), safe=""),
            schema=quote(str(schema), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DeltaListTablesResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = DeltaListTablesResponse.from_dict(response.json())

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
) -> Response[DeltaListTablesResponse | HTTPValidationError]:
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
    max_results: int | None | Unset = UNSET,
    page_token: None | str | Unset = UNSET,
) -> Response[DeltaListTablesResponse | HTTPValidationError]:
    """List Delta tables

     Return one page of tables under a schema.

    Args:
        catalog: Catalog segment.
        schema: Schema segment.
        max_results: Client-side page size hint, capped by the
            existing pagination helper.
        page_token: Opaque keyset token from a previous call.
        db: Database session dependency.

    Returns:
        DeltaListTablesResponse: One page of Delta-shaped identifiers.

    Args:
        catalog (str):
        schema (str):
        max_results (int | None | Unset):
        page_token (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DeltaListTablesResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        catalog=catalog,
        schema=schema,
        max_results=max_results,
        page_token=page_token,
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
    max_results: int | None | Unset = UNSET,
    page_token: None | str | Unset = UNSET,
) -> DeltaListTablesResponse | HTTPValidationError | None:
    """List Delta tables

     Return one page of tables under a schema.

    Args:
        catalog: Catalog segment.
        schema: Schema segment.
        max_results: Client-side page size hint, capped by the
            existing pagination helper.
        page_token: Opaque keyset token from a previous call.
        db: Database session dependency.

    Returns:
        DeltaListTablesResponse: One page of Delta-shaped identifiers.

    Args:
        catalog (str):
        schema (str):
        max_results (int | None | Unset):
        page_token (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DeltaListTablesResponse | HTTPValidationError
    """

    return sync_detailed(
        catalog=catalog,
        schema=schema,
        client=client,
        max_results=max_results,
        page_token=page_token,
    ).parsed


async def asyncio_detailed(
    catalog: str,
    schema: str,
    *,
    client: AuthenticatedClient | Client,
    max_results: int | None | Unset = UNSET,
    page_token: None | str | Unset = UNSET,
) -> Response[DeltaListTablesResponse | HTTPValidationError]:
    """List Delta tables

     Return one page of tables under a schema.

    Args:
        catalog: Catalog segment.
        schema: Schema segment.
        max_results: Client-side page size hint, capped by the
            existing pagination helper.
        page_token: Opaque keyset token from a previous call.
        db: Database session dependency.

    Returns:
        DeltaListTablesResponse: One page of Delta-shaped identifiers.

    Args:
        catalog (str):
        schema (str):
        max_results (int | None | Unset):
        page_token (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DeltaListTablesResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        catalog=catalog,
        schema=schema,
        max_results=max_results,
        page_token=page_token,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    catalog: str,
    schema: str,
    *,
    client: AuthenticatedClient | Client,
    max_results: int | None | Unset = UNSET,
    page_token: None | str | Unset = UNSET,
) -> DeltaListTablesResponse | HTTPValidationError | None:
    """List Delta tables

     Return one page of tables under a schema.

    Args:
        catalog: Catalog segment.
        schema: Schema segment.
        max_results: Client-side page size hint, capped by the
            existing pagination helper.
        page_token: Opaque keyset token from a previous call.
        db: Database session dependency.

    Returns:
        DeltaListTablesResponse: One page of Delta-shaped identifiers.

    Args:
        catalog (str):
        schema (str):
        max_results (int | None | Unset):
        page_token (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DeltaListTablesResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            catalog=catalog,
            schema=schema,
            client=client,
            max_results=max_results,
            page_token=page_token,
        )
    ).parsed
