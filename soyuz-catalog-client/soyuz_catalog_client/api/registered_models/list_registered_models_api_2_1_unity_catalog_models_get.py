from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.list_registered_models_response import ListRegisteredModelsResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    catalog_name: None | str | Unset = UNSET,
    schema_name: None | str | Unset = UNSET,
    max_results: int | None | Unset = UNSET,
    page_token: None | str | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    json_catalog_name: None | str | Unset
    if isinstance(catalog_name, Unset):
        json_catalog_name = UNSET
    else:
        json_catalog_name = catalog_name
    params["catalog_name"] = json_catalog_name

    json_schema_name: None | str | Unset
    if isinstance(schema_name, Unset):
        json_schema_name = UNSET
    else:
        json_schema_name = schema_name
    params["schema_name"] = json_schema_name

    json_max_results: int | None | Unset
    if isinstance(max_results, Unset):
        json_max_results = UNSET
    else:
        json_max_results = max_results
    params["max_results"] = json_max_results

    json_page_token: None | str | Unset
    if isinstance(page_token, Unset):
        json_page_token = UNSET
    else:
        json_page_token = page_token
    params["page_token"] = json_page_token

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/2.1/unity-catalog/models",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | ListRegisteredModelsResponse | None:
    if response.status_code == 200:
        response_200 = ListRegisteredModelsResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | ListRegisteredModelsResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    catalog_name: None | str | Unset = UNSET,
    schema_name: None | str | Unset = UNSET,
    max_results: int | None | Unset = UNSET,
    page_token: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | ListRegisteredModelsResponse]:
    """List registered models

     List registered models with keyset pagination and optional parent filters.

    Both ``catalog_name`` and ``schema_name`` are optional per the
    UC spec — a metastore-wide listing is legal. ``schema_name``
    alone without ``catalog_name`` is 400 because schema names are
    not metastore-unique.

    Args:
        catalog_name: Optional parent catalog filter.
        schema_name: Optional parent schema filter.
        max_results: Page size hint, 1..1000.
        page_token: Opaque cursor from a previous ``next_page_token``.
        db: Database session dependency.

    Returns:
        ListRegisteredModelsResponse: One page of rows plus the next
            page token.

    Args:
        catalog_name (None | str | Unset):
        schema_name (None | str | Unset):
        max_results (int | None | Unset):
        page_token (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ListRegisteredModelsResponse]
    """

    kwargs = _get_kwargs(
        catalog_name=catalog_name,
        schema_name=schema_name,
        max_results=max_results,
        page_token=page_token,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    catalog_name: None | str | Unset = UNSET,
    schema_name: None | str | Unset = UNSET,
    max_results: int | None | Unset = UNSET,
    page_token: None | str | Unset = UNSET,
) -> HTTPValidationError | ListRegisteredModelsResponse | None:
    """List registered models

     List registered models with keyset pagination and optional parent filters.

    Both ``catalog_name`` and ``schema_name`` are optional per the
    UC spec — a metastore-wide listing is legal. ``schema_name``
    alone without ``catalog_name`` is 400 because schema names are
    not metastore-unique.

    Args:
        catalog_name: Optional parent catalog filter.
        schema_name: Optional parent schema filter.
        max_results: Page size hint, 1..1000.
        page_token: Opaque cursor from a previous ``next_page_token``.
        db: Database session dependency.

    Returns:
        ListRegisteredModelsResponse: One page of rows plus the next
            page token.

    Args:
        catalog_name (None | str | Unset):
        schema_name (None | str | Unset):
        max_results (int | None | Unset):
        page_token (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ListRegisteredModelsResponse
    """

    return sync_detailed(
        client=client,
        catalog_name=catalog_name,
        schema_name=schema_name,
        max_results=max_results,
        page_token=page_token,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    catalog_name: None | str | Unset = UNSET,
    schema_name: None | str | Unset = UNSET,
    max_results: int | None | Unset = UNSET,
    page_token: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | ListRegisteredModelsResponse]:
    """List registered models

     List registered models with keyset pagination and optional parent filters.

    Both ``catalog_name`` and ``schema_name`` are optional per the
    UC spec — a metastore-wide listing is legal. ``schema_name``
    alone without ``catalog_name`` is 400 because schema names are
    not metastore-unique.

    Args:
        catalog_name: Optional parent catalog filter.
        schema_name: Optional parent schema filter.
        max_results: Page size hint, 1..1000.
        page_token: Opaque cursor from a previous ``next_page_token``.
        db: Database session dependency.

    Returns:
        ListRegisteredModelsResponse: One page of rows plus the next
            page token.

    Args:
        catalog_name (None | str | Unset):
        schema_name (None | str | Unset):
        max_results (int | None | Unset):
        page_token (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ListRegisteredModelsResponse]
    """

    kwargs = _get_kwargs(
        catalog_name=catalog_name,
        schema_name=schema_name,
        max_results=max_results,
        page_token=page_token,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    catalog_name: None | str | Unset = UNSET,
    schema_name: None | str | Unset = UNSET,
    max_results: int | None | Unset = UNSET,
    page_token: None | str | Unset = UNSET,
) -> HTTPValidationError | ListRegisteredModelsResponse | None:
    """List registered models

     List registered models with keyset pagination and optional parent filters.

    Both ``catalog_name`` and ``schema_name`` are optional per the
    UC spec — a metastore-wide listing is legal. ``schema_name``
    alone without ``catalog_name`` is 400 because schema names are
    not metastore-unique.

    Args:
        catalog_name: Optional parent catalog filter.
        schema_name: Optional parent schema filter.
        max_results: Page size hint, 1..1000.
        page_token: Opaque cursor from a previous ``next_page_token``.
        db: Database session dependency.

    Returns:
        ListRegisteredModelsResponse: One page of rows plus the next
            page token.

    Args:
        catalog_name (None | str | Unset):
        schema_name (None | str | Unset):
        max_results (int | None | Unset):
        page_token (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ListRegisteredModelsResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            catalog_name=catalog_name,
            schema_name=schema_name,
            max_results=max_results,
            page_token=page_token,
        )
    ).parsed
