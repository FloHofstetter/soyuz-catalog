from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.lineage_graph_response import LineageGraphResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    full_name: str,
    *,
    depth: int | Unset = 3,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["depth"] = depth

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/lineage/downstream/{full_name}".format(
            full_name=quote(str(full_name), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | LineageGraphResponse | None:
    if response.status_code == 200:
        response_200 = LineageGraphResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | LineageGraphResponse]:
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
    depth: int | Unset = 3,
) -> Response[HTTPValidationError | LineageGraphResponse]:
    """Traverse downstream lineage

     Walk the lineage graph forward from a table.

    Mirror of :func:`get_upstream`: returns every securable that the
    table feeds, up to ``depth`` hops. Same cap and same single-node
    shape for tables with no recorded downstream lineage.

    Args:
        full_name: ``catalog.schema.table`` dotted address.
        depth: Maximum number of hops.
        db: Database session dependency.

    Returns:
        LineageGraphResponse: The reachable subgraph.

    Args:
        full_name (str):
        depth (int | Unset):  Default: 3.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | LineageGraphResponse]
    """

    kwargs = _get_kwargs(
        full_name=full_name,
        depth=depth,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    full_name: str,
    *,
    client: AuthenticatedClient | Client,
    depth: int | Unset = 3,
) -> HTTPValidationError | LineageGraphResponse | None:
    """Traverse downstream lineage

     Walk the lineage graph forward from a table.

    Mirror of :func:`get_upstream`: returns every securable that the
    table feeds, up to ``depth`` hops. Same cap and same single-node
    shape for tables with no recorded downstream lineage.

    Args:
        full_name: ``catalog.schema.table`` dotted address.
        depth: Maximum number of hops.
        db: Database session dependency.

    Returns:
        LineageGraphResponse: The reachable subgraph.

    Args:
        full_name (str):
        depth (int | Unset):  Default: 3.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | LineageGraphResponse
    """

    return sync_detailed(
        full_name=full_name,
        client=client,
        depth=depth,
    ).parsed


async def asyncio_detailed(
    full_name: str,
    *,
    client: AuthenticatedClient | Client,
    depth: int | Unset = 3,
) -> Response[HTTPValidationError | LineageGraphResponse]:
    """Traverse downstream lineage

     Walk the lineage graph forward from a table.

    Mirror of :func:`get_upstream`: returns every securable that the
    table feeds, up to ``depth`` hops. Same cap and same single-node
    shape for tables with no recorded downstream lineage.

    Args:
        full_name: ``catalog.schema.table`` dotted address.
        depth: Maximum number of hops.
        db: Database session dependency.

    Returns:
        LineageGraphResponse: The reachable subgraph.

    Args:
        full_name (str):
        depth (int | Unset):  Default: 3.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | LineageGraphResponse]
    """

    kwargs = _get_kwargs(
        full_name=full_name,
        depth=depth,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    full_name: str,
    *,
    client: AuthenticatedClient | Client,
    depth: int | Unset = 3,
) -> HTTPValidationError | LineageGraphResponse | None:
    """Traverse downstream lineage

     Walk the lineage graph forward from a table.

    Mirror of :func:`get_upstream`: returns every securable that the
    table feeds, up to ``depth`` hops. Same cap and same single-node
    shape for tables with no recorded downstream lineage.

    Args:
        full_name: ``catalog.schema.table`` dotted address.
        depth: Maximum number of hops.
        db: Database session dependency.

    Returns:
        LineageGraphResponse: The reachable subgraph.

    Args:
        full_name (str):
        depth (int | Unset):  Default: 3.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | LineageGraphResponse
    """

    return (
        await asyncio_detailed(
            full_name=full_name,
            client=client,
            depth=depth,
        )
    ).parsed
