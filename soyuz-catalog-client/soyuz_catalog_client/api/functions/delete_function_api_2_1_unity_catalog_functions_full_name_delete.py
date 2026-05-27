from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.response_delete_function_api_21_unity_catalog_functions_full_name_delete import (
    ResponseDeleteFunctionApi21UnityCatalogFunctionsFullNameDelete,
)
from ...types import UNSET, Response


def _get_kwargs(
    full_name: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/api/2.1/unity-catalog/functions/{full_name}".format(
            full_name=quote(str(full_name), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    HTTPValidationError
    | ResponseDeleteFunctionApi21UnityCatalogFunctionsFullNameDelete
    | None
):
    if response.status_code == 200:
        response_200 = (
            ResponseDeleteFunctionApi21UnityCatalogFunctionsFullNameDelete.from_dict(
                response.json()
            )
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
    HTTPValidationError | ResponseDeleteFunctionApi21UnityCatalogFunctionsFullNameDelete
]:
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
) -> Response[
    HTTPValidationError | ResponseDeleteFunctionApi21UnityCatalogFunctionsFullNameDelete
]:
    """Delete function

     Delete a function.

    The UC REST spec defines no ``UpdateFunction`` — soyuz does not
    register a PATCH handler and FastAPI returns 405 Method Not
    Allowed for that method, same shape as the tables resource.

    Args:
        full_name: ``catalog.schema.function`` path parameter.
        db: Database session dependency.

    Returns:
        dict[str, str]: Empty success payload.

    Args:
        full_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ResponseDeleteFunctionApi21UnityCatalogFunctionsFullNameDelete]
    """

    kwargs = _get_kwargs(
        full_name=full_name,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    full_name: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    HTTPValidationError
    | ResponseDeleteFunctionApi21UnityCatalogFunctionsFullNameDelete
    | None
):
    """Delete function

     Delete a function.

    The UC REST spec defines no ``UpdateFunction`` — soyuz does not
    register a PATCH handler and FastAPI returns 405 Method Not
    Allowed for that method, same shape as the tables resource.

    Args:
        full_name: ``catalog.schema.function`` path parameter.
        db: Database session dependency.

    Returns:
        dict[str, str]: Empty success payload.

    Args:
        full_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ResponseDeleteFunctionApi21UnityCatalogFunctionsFullNameDelete
    """

    return sync_detailed(
        full_name=full_name,
        client=client,
    ).parsed


async def asyncio_detailed(
    full_name: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    HTTPValidationError | ResponseDeleteFunctionApi21UnityCatalogFunctionsFullNameDelete
]:
    """Delete function

     Delete a function.

    The UC REST spec defines no ``UpdateFunction`` — soyuz does not
    register a PATCH handler and FastAPI returns 405 Method Not
    Allowed for that method, same shape as the tables resource.

    Args:
        full_name: ``catalog.schema.function`` path parameter.
        db: Database session dependency.

    Returns:
        dict[str, str]: Empty success payload.

    Args:
        full_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ResponseDeleteFunctionApi21UnityCatalogFunctionsFullNameDelete]
    """

    kwargs = _get_kwargs(
        full_name=full_name,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    full_name: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    HTTPValidationError
    | ResponseDeleteFunctionApi21UnityCatalogFunctionsFullNameDelete
    | None
):
    """Delete function

     Delete a function.

    The UC REST spec defines no ``UpdateFunction`` — soyuz does not
    register a PATCH handler and FastAPI returns 405 Method Not
    Allowed for that method, same shape as the tables resource.

    Args:
        full_name: ``catalog.schema.function`` path parameter.
        db: Database session dependency.

    Returns:
        dict[str, str]: Empty success payload.

    Args:
        full_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ResponseDeleteFunctionApi21UnityCatalogFunctionsFullNameDelete
    """

    return (
        await asyncio_detailed(
            full_name=full_name,
            client=client,
        )
    ).parsed
