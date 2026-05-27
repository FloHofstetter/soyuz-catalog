from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.list_model_versions_response import ListModelVersionsResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    full_name: str,
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
        "url": "/api/2.1/unity-catalog/models/{full_name}/versions".format(
            full_name=quote(str(full_name), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | ListModelVersionsResponse | None:
    if response.status_code == 200:
        response_200 = ListModelVersionsResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | ListModelVersionsResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    full_name: str,
    *,
    client: AuthenticatedClient | Client,
    max_results: int | None | Unset = UNSET,
    page_token: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | ListModelVersionsResponse]:
    """List model versions

     List model versions of a registered model with keyset pagination.

    Args:
        full_name: Parent ``catalog.schema.model`` path parameter.
        max_results: Page size hint, 1..1000.
        page_token: Opaque cursor from a previous ``next_page_token``.
        db: Database session dependency.

    Returns:
        ListModelVersionsResponse: One page of versions plus the next
            page token.

    Args:
        full_name (str):
        max_results (int | None | Unset):
        page_token (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ListModelVersionsResponse]
    """

    kwargs = _get_kwargs(
        full_name=full_name,
        max_results=max_results,
        page_token=page_token,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    full_name: str,
    *,
    client: AuthenticatedClient | Client,
    max_results: int | None | Unset = UNSET,
    page_token: None | str | Unset = UNSET,
) -> HTTPValidationError | ListModelVersionsResponse | None:
    """List model versions

     List model versions of a registered model with keyset pagination.

    Args:
        full_name: Parent ``catalog.schema.model`` path parameter.
        max_results: Page size hint, 1..1000.
        page_token: Opaque cursor from a previous ``next_page_token``.
        db: Database session dependency.

    Returns:
        ListModelVersionsResponse: One page of versions plus the next
            page token.

    Args:
        full_name (str):
        max_results (int | None | Unset):
        page_token (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ListModelVersionsResponse
    """

    return sync_detailed(
        full_name=full_name,
        client=client,
        max_results=max_results,
        page_token=page_token,
    ).parsed


async def asyncio_detailed(
    full_name: str,
    *,
    client: AuthenticatedClient | Client,
    max_results: int | None | Unset = UNSET,
    page_token: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | ListModelVersionsResponse]:
    """List model versions

     List model versions of a registered model with keyset pagination.

    Args:
        full_name: Parent ``catalog.schema.model`` path parameter.
        max_results: Page size hint, 1..1000.
        page_token: Opaque cursor from a previous ``next_page_token``.
        db: Database session dependency.

    Returns:
        ListModelVersionsResponse: One page of versions plus the next
            page token.

    Args:
        full_name (str):
        max_results (int | None | Unset):
        page_token (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ListModelVersionsResponse]
    """

    kwargs = _get_kwargs(
        full_name=full_name,
        max_results=max_results,
        page_token=page_token,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    full_name: str,
    *,
    client: AuthenticatedClient | Client,
    max_results: int | None | Unset = UNSET,
    page_token: None | str | Unset = UNSET,
) -> HTTPValidationError | ListModelVersionsResponse | None:
    """List model versions

     List model versions of a registered model with keyset pagination.

    Args:
        full_name: Parent ``catalog.schema.model`` path parameter.
        max_results: Page size hint, 1..1000.
        page_token: Opaque cursor from a previous ``next_page_token``.
        db: Database session dependency.

    Returns:
        ListModelVersionsResponse: One page of versions plus the next
            page token.

    Args:
        full_name (str):
        max_results (int | None | Unset):
        page_token (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ListModelVersionsResponse
    """

    return (
        await asyncio_detailed(
            full_name=full_name,
            client=client,
            max_results=max_results,
            page_token=page_token,
        )
    ).parsed
