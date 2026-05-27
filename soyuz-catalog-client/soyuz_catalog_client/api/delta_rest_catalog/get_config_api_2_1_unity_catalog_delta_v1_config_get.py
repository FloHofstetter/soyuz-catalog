from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.catalog_config import CatalogConfig
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response


def _get_kwargs(
    *,
    catalog: str,
    protocol_versions: str,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["catalog"] = catalog

    params["protocol-versions"] = protocol_versions

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/2.1/unity-catalog/delta/v1/config",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> CatalogConfig | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = CatalogConfig.from_dict(response.json())

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
) -> Response[CatalogConfig | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    catalog: str,
    protocol_versions: str,
) -> Response[CatalogConfig | HTTPValidationError]:
    r"""Get Delta REST Catalog config

     Advertise the supported Delta REST Catalog endpoints and version.

    Args:
        catalog: Required by spec; soyuz has one implementation and
            does not branch on catalog name.
        protocol_versions: Required by spec; soyuz only implements
            version ``\"1.0\"`` so the response is the same regardless
            of the client's request.

    Returns:
        CatalogConfig: Fixed list of implemented endpoints plus
            protocol version ``\"1.0\"``.

    Args:
        catalog (str): Catalog name (required per spec; not used)
        protocol_versions (str): Comma-separated list of client-supported protocol versions

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CatalogConfig | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        catalog=catalog,
        protocol_versions=protocol_versions,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    catalog: str,
    protocol_versions: str,
) -> CatalogConfig | HTTPValidationError | None:
    r"""Get Delta REST Catalog config

     Advertise the supported Delta REST Catalog endpoints and version.

    Args:
        catalog: Required by spec; soyuz has one implementation and
            does not branch on catalog name.
        protocol_versions: Required by spec; soyuz only implements
            version ``\"1.0\"`` so the response is the same regardless
            of the client's request.

    Returns:
        CatalogConfig: Fixed list of implemented endpoints plus
            protocol version ``\"1.0\"``.

    Args:
        catalog (str): Catalog name (required per spec; not used)
        protocol_versions (str): Comma-separated list of client-supported protocol versions

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CatalogConfig | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        catalog=catalog,
        protocol_versions=protocol_versions,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    catalog: str,
    protocol_versions: str,
) -> Response[CatalogConfig | HTTPValidationError]:
    r"""Get Delta REST Catalog config

     Advertise the supported Delta REST Catalog endpoints and version.

    Args:
        catalog: Required by spec; soyuz has one implementation and
            does not branch on catalog name.
        protocol_versions: Required by spec; soyuz only implements
            version ``\"1.0\"`` so the response is the same regardless
            of the client's request.

    Returns:
        CatalogConfig: Fixed list of implemented endpoints plus
            protocol version ``\"1.0\"``.

    Args:
        catalog (str): Catalog name (required per spec; not used)
        protocol_versions (str): Comma-separated list of client-supported protocol versions

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CatalogConfig | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        catalog=catalog,
        protocol_versions=protocol_versions,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    catalog: str,
    protocol_versions: str,
) -> CatalogConfig | HTTPValidationError | None:
    r"""Get Delta REST Catalog config

     Advertise the supported Delta REST Catalog endpoints and version.

    Args:
        catalog: Required by spec; soyuz has one implementation and
            does not branch on catalog name.
        protocol_versions: Required by spec; soyuz only implements
            version ``\"1.0\"`` so the response is the same regardless
            of the client's request.

    Returns:
        CatalogConfig: Fixed list of implemented endpoints plus
            protocol version ``\"1.0\"``.

    Args:
        catalog (str): Catalog name (required per spec; not used)
        protocol_versions (str): Comma-separated list of client-supported protocol versions

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CatalogConfig | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            catalog=catalog,
            protocol_versions=protocol_versions,
        )
    ).parsed
