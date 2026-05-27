from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_metastore_summary_response import GetMetastoreSummaryResponse
from ...types import UNSET, Response


def _get_kwargs() -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/2.1/unity-catalog/metastore_summary",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> GetMetastoreSummaryResponse | None:
    if response.status_code == 200:
        response_200 = GetMetastoreSummaryResponse.from_dict(response.json())

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[GetMetastoreSummaryResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[GetMetastoreSummaryResponse]:
    """Get metastore summary

     Return the metastore identity summary.

    The backing row is created lazily on the first call — see
    :func:`soyuz_catalog.services.metastore_service.get_metastore_summary`
    for the bootstrap rationale.

    Args:
        db: Database session dependency.

    Returns:
        GetMetastoreSummaryResponse: The singleton metastore identity.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetMetastoreSummaryResponse]
    """

    kwargs = _get_kwargs()

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
) -> GetMetastoreSummaryResponse | None:
    """Get metastore summary

     Return the metastore identity summary.

    The backing row is created lazily on the first call — see
    :func:`soyuz_catalog.services.metastore_service.get_metastore_summary`
    for the bootstrap rationale.

    Args:
        db: Database session dependency.

    Returns:
        GetMetastoreSummaryResponse: The singleton metastore identity.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetMetastoreSummaryResponse
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[GetMetastoreSummaryResponse]:
    """Get metastore summary

     Return the metastore identity summary.

    The backing row is created lazily on the first call — see
    :func:`soyuz_catalog.services.metastore_service.get_metastore_summary`
    for the bootstrap rationale.

    Args:
        db: Database session dependency.

    Returns:
        GetMetastoreSummaryResponse: The singleton metastore identity.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetMetastoreSummaryResponse]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
) -> GetMetastoreSummaryResponse | None:
    """Get metastore summary

     Return the metastore identity summary.

    The backing row is created lazily on the first call — see
    :func:`soyuz_catalog.services.metastore_service.get_metastore_summary`
    for the bootstrap rationale.

    Args:
        db: Database session dependency.

    Returns:
        GetMetastoreSummaryResponse: The singleton metastore identity.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetMetastoreSummaryResponse
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
