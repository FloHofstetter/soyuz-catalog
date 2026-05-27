from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.response_delete_table_api_21_unity_catalog_tables_full_name_delete import (
    ResponseDeleteTableApi21UnityCatalogTablesFullNameDelete,
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
        "url": "/api/2.1/unity-catalog/tables/{full_name}".format(
            full_name=quote(str(full_name), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    HTTPValidationError
    | ResponseDeleteTableApi21UnityCatalogTablesFullNameDelete
    | None
):
    if response.status_code == 200:
        response_200 = (
            ResponseDeleteTableApi21UnityCatalogTablesFullNameDelete.from_dict(
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
    HTTPValidationError | ResponseDeleteTableApi21UnityCatalogTablesFullNameDelete
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
    HTTPValidationError | ResponseDeleteTableApi21UnityCatalogTablesFullNameDelete
]:
    """Delete table

     Delete a table and cascade through its columns.

    No PATCH verb is registered on this router: the UC OpenAPI spec
    defines no ``UpdateTable`` request model, and silently accepting
    unknown fields is the UC OSS Java bug this project exists to fix.
    FastAPI therefore returns 405 Method Not Allowed for any PATCH to a
    table, which is a deliberate and tested divergence — see
    ``DIVERGENCES.md``.

    Args:
        full_name: ``catalog_name.schema_name.table_name`` path parameter.
        force: Cascade flag (accepted for spec stability; currently
            a no-op — columns always cascade unconditionally because
            they have no independent existence).
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
        Response[HTTPValidationError | ResponseDeleteTableApi21UnityCatalogTablesFullNameDelete]
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
    | ResponseDeleteTableApi21UnityCatalogTablesFullNameDelete
    | None
):
    """Delete table

     Delete a table and cascade through its columns.

    No PATCH verb is registered on this router: the UC OpenAPI spec
    defines no ``UpdateTable`` request model, and silently accepting
    unknown fields is the UC OSS Java bug this project exists to fix.
    FastAPI therefore returns 405 Method Not Allowed for any PATCH to a
    table, which is a deliberate and tested divergence — see
    ``DIVERGENCES.md``.

    Args:
        full_name: ``catalog_name.schema_name.table_name`` path parameter.
        force: Cascade flag (accepted for spec stability; currently
            a no-op — columns always cascade unconditionally because
            they have no independent existence).
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
        HTTPValidationError | ResponseDeleteTableApi21UnityCatalogTablesFullNameDelete
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
    HTTPValidationError | ResponseDeleteTableApi21UnityCatalogTablesFullNameDelete
]:
    """Delete table

     Delete a table and cascade through its columns.

    No PATCH verb is registered on this router: the UC OpenAPI spec
    defines no ``UpdateTable`` request model, and silently accepting
    unknown fields is the UC OSS Java bug this project exists to fix.
    FastAPI therefore returns 405 Method Not Allowed for any PATCH to a
    table, which is a deliberate and tested divergence — see
    ``DIVERGENCES.md``.

    Args:
        full_name: ``catalog_name.schema_name.table_name`` path parameter.
        force: Cascade flag (accepted for spec stability; currently
            a no-op — columns always cascade unconditionally because
            they have no independent existence).
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
        Response[HTTPValidationError | ResponseDeleteTableApi21UnityCatalogTablesFullNameDelete]
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
    | ResponseDeleteTableApi21UnityCatalogTablesFullNameDelete
    | None
):
    """Delete table

     Delete a table and cascade through its columns.

    No PATCH verb is registered on this router: the UC OpenAPI spec
    defines no ``UpdateTable`` request model, and silently accepting
    unknown fields is the UC OSS Java bug this project exists to fix.
    FastAPI therefore returns 405 Method Not Allowed for any PATCH to a
    table, which is a deliberate and tested divergence — see
    ``DIVERGENCES.md``.

    Args:
        full_name: ``catalog_name.schema_name.table_name`` path parameter.
        force: Cascade flag (accepted for spec stability; currently
            a no-op — columns always cascade unconditionally because
            they have no independent existence).
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
        HTTPValidationError | ResponseDeleteTableApi21UnityCatalogTablesFullNameDelete
    """

    return (
        await asyncio_detailed(
            full_name=full_name,
            client=client,
            force=force,
        )
    ).parsed
