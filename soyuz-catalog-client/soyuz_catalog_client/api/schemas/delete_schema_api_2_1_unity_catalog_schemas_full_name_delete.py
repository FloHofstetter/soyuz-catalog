from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.response_delete_schema_api_21_unity_catalog_schemas_full_name_delete import (
    ResponseDeleteSchemaApi21UnityCatalogSchemasFullNameDelete,
)
from ...types import UNSET, Response, Unset


def _get_kwargs(
    full_name: str,
    *,
    force: bool | Unset = False,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["force"] = force

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/api/2.1/unity-catalog/schemas/{full_name}".format(
            full_name=quote(str(full_name), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    HTTPValidationError
    | ResponseDeleteSchemaApi21UnityCatalogSchemasFullNameDelete
    | None
):
    if response.status_code == 200:
        response_200 = (
            ResponseDeleteSchemaApi21UnityCatalogSchemasFullNameDelete.from_dict(
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
    HTTPValidationError | ResponseDeleteSchemaApi21UnityCatalogSchemasFullNameDelete
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
    force: bool | Unset = False,
) -> Response[
    HTTPValidationError | ResponseDeleteSchemaApi21UnityCatalogSchemasFullNameDelete
]:
    """Delete schema

     Delete a schema.

    Args:
        full_name: ``catalog_name.schema_name`` path parameter.
        force: When true, cascade-delete child tables, volumes,
            functions and registered models before removing the
            schema. Defaults to false, in which case a non-empty
            schema rejects the delete with 409.
        db: Database session dependency.

    Returns:
        dict[str, str]: Empty success payload.

    Args:
        full_name (str):
        force (bool | Unset):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ResponseDeleteSchemaApi21UnityCatalogSchemasFullNameDelete]
    """

    kwargs = _get_kwargs(
        full_name=full_name,
        force=force,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    full_name: str,
    *,
    client: AuthenticatedClient | Client,
    force: bool | Unset = False,
) -> (
    HTTPValidationError
    | ResponseDeleteSchemaApi21UnityCatalogSchemasFullNameDelete
    | None
):
    """Delete schema

     Delete a schema.

    Args:
        full_name: ``catalog_name.schema_name`` path parameter.
        force: When true, cascade-delete child tables, volumes,
            functions and registered models before removing the
            schema. Defaults to false, in which case a non-empty
            schema rejects the delete with 409.
        db: Database session dependency.

    Returns:
        dict[str, str]: Empty success payload.

    Args:
        full_name (str):
        force (bool | Unset):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ResponseDeleteSchemaApi21UnityCatalogSchemasFullNameDelete
    """

    return sync_detailed(
        full_name=full_name,
        client=client,
        force=force,
    ).parsed


async def asyncio_detailed(
    full_name: str,
    *,
    client: AuthenticatedClient | Client,
    force: bool | Unset = False,
) -> Response[
    HTTPValidationError | ResponseDeleteSchemaApi21UnityCatalogSchemasFullNameDelete
]:
    """Delete schema

     Delete a schema.

    Args:
        full_name: ``catalog_name.schema_name`` path parameter.
        force: When true, cascade-delete child tables, volumes,
            functions and registered models before removing the
            schema. Defaults to false, in which case a non-empty
            schema rejects the delete with 409.
        db: Database session dependency.

    Returns:
        dict[str, str]: Empty success payload.

    Args:
        full_name (str):
        force (bool | Unset):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ResponseDeleteSchemaApi21UnityCatalogSchemasFullNameDelete]
    """

    kwargs = _get_kwargs(
        full_name=full_name,
        force=force,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    full_name: str,
    *,
    client: AuthenticatedClient | Client,
    force: bool | Unset = False,
) -> (
    HTTPValidationError
    | ResponseDeleteSchemaApi21UnityCatalogSchemasFullNameDelete
    | None
):
    """Delete schema

     Delete a schema.

    Args:
        full_name: ``catalog_name.schema_name`` path parameter.
        force: When true, cascade-delete child tables, volumes,
            functions and registered models before removing the
            schema. Defaults to false, in which case a non-empty
            schema rejects the delete with 409.
        db: Database session dependency.

    Returns:
        dict[str, str]: Empty success payload.

    Args:
        full_name (str):
        force (bool | Unset):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ResponseDeleteSchemaApi21UnityCatalogSchemasFullNameDelete
    """

    return (
        await asyncio_detailed(
            full_name=full_name,
            client=client,
            force=force,
        )
    ).parsed
