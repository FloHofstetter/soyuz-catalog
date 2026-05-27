from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.response_delete_external_location_api_21_unity_catalog_external_locations_name_delete import (
    ResponseDeleteExternalLocationApi21UnityCatalogExternalLocationsNameDelete,
)
from ...types import UNSET, Response


def _get_kwargs(
    name: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/api/2.1/unity-catalog/external-locations/{name}".format(
            name=quote(str(name), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    HTTPValidationError
    | ResponseDeleteExternalLocationApi21UnityCatalogExternalLocationsNameDelete
    | None
):
    if response.status_code == 200:
        response_200 = ResponseDeleteExternalLocationApi21UnityCatalogExternalLocationsNameDelete.from_dict(
            response.json()
        )

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
) -> Response[
    HTTPValidationError
    | ResponseDeleteExternalLocationApi21UnityCatalogExternalLocationsNameDelete
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    name: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    HTTPValidationError
    | ResponseDeleteExternalLocationApi21UnityCatalogExternalLocationsNameDelete
]:
    """Delete external location

     Delete an external location.

    Args:
        name: External location name.
        db: Database session dependency.

    Returns:
        dict[str, str]: Empty success payload.

    Args:
        name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ResponseDeleteExternalLocationApi21UnityCatalogExternalLocationsNameDelete]
    """

    kwargs = _get_kwargs(
        name=name,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    name: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    HTTPValidationError
    | ResponseDeleteExternalLocationApi21UnityCatalogExternalLocationsNameDelete
    | None
):
    """Delete external location

     Delete an external location.

    Args:
        name: External location name.
        db: Database session dependency.

    Returns:
        dict[str, str]: Empty success payload.

    Args:
        name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ResponseDeleteExternalLocationApi21UnityCatalogExternalLocationsNameDelete
    """

    return sync_detailed(
        name=name,
        client=client,
    ).parsed


async def asyncio_detailed(
    name: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    HTTPValidationError
    | ResponseDeleteExternalLocationApi21UnityCatalogExternalLocationsNameDelete
]:
    """Delete external location

     Delete an external location.

    Args:
        name: External location name.
        db: Database session dependency.

    Returns:
        dict[str, str]: Empty success payload.

    Args:
        name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ResponseDeleteExternalLocationApi21UnityCatalogExternalLocationsNameDelete]
    """

    kwargs = _get_kwargs(
        name=name,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    name: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    HTTPValidationError
    | ResponseDeleteExternalLocationApi21UnityCatalogExternalLocationsNameDelete
    | None
):
    """Delete external location

     Delete an external location.

    Args:
        name: External location name.
        db: Database session dependency.

    Returns:
        dict[str, str]: Empty success payload.

    Args:
        name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ResponseDeleteExternalLocationApi21UnityCatalogExternalLocationsNameDelete
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
        )
    ).parsed
