from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_permissions_api_21_unity_catalog_permissions_securable_type_full_name_get_securable_type import (
    GetPermissionsApi21UnityCatalogPermissionsSecurableTypeFullNameGetSecurableType,
)
from ...models.http_validation_error import HTTPValidationError
from ...models.permissions_list import PermissionsList
from ...types import UNSET, Response, Unset


def _get_kwargs(
    securable_type: GetPermissionsApi21UnityCatalogPermissionsSecurableTypeFullNameGetSecurableType,
    full_name: str,
    *,
    principal: None | str | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    json_principal: None | str | Unset
    if isinstance(principal, Unset):
        json_principal = UNSET
    else:
        json_principal = principal
    params["principal"] = json_principal

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/2.1/unity-catalog/permissions/{securable_type}/{full_name}".format(
            securable_type=quote(str(securable_type), safe=""),
            full_name=quote(str(full_name), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | PermissionsList | None:
    if response.status_code == 200:
        response_200 = PermissionsList.from_dict(response.json())

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
) -> Response[HTTPValidationError | PermissionsList]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    securable_type: GetPermissionsApi21UnityCatalogPermissionsSecurableTypeFullNameGetSecurableType,
    full_name: str,
    *,
    client: AuthenticatedClient | Client,
    principal: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | PermissionsList]:
    """Get permissions for securable

     Return the permission assignments on a securable.

    Args:
        securable_type: One of the nine UC ``SecurableType`` values.
            Typed as a ``Literal`` so unknown values surface as 422.
        full_name: Spec-shaped dotted address — 1 segment for
            catalog / credential / external location, 2 for schema,
            3 for table / volume / function / registered model, or
            the live metastore id for metastore.
        principal: Optional filter. When set, only that principal's
            grants appear in the response.
        db: Database session dependency.

    Returns:
        PermissionsList: The current grant state of the securable.

    Args:
        securable_type
            (GetPermissionsApi21UnityCatalogPermissionsSecurableTypeFullNameGetSecurableType):
        full_name (str):
        principal (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | PermissionsList]
    """

    kwargs = _get_kwargs(
        securable_type=securable_type,
        full_name=full_name,
        principal=principal,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    securable_type: GetPermissionsApi21UnityCatalogPermissionsSecurableTypeFullNameGetSecurableType,
    full_name: str,
    *,
    client: AuthenticatedClient | Client,
    principal: None | str | Unset = UNSET,
) -> HTTPValidationError | PermissionsList | None:
    """Get permissions for securable

     Return the permission assignments on a securable.

    Args:
        securable_type: One of the nine UC ``SecurableType`` values.
            Typed as a ``Literal`` so unknown values surface as 422.
        full_name: Spec-shaped dotted address — 1 segment for
            catalog / credential / external location, 2 for schema,
            3 for table / volume / function / registered model, or
            the live metastore id for metastore.
        principal: Optional filter. When set, only that principal's
            grants appear in the response.
        db: Database session dependency.

    Returns:
        PermissionsList: The current grant state of the securable.

    Args:
        securable_type
            (GetPermissionsApi21UnityCatalogPermissionsSecurableTypeFullNameGetSecurableType):
        full_name (str):
        principal (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | PermissionsList
    """

    return sync_detailed(
        securable_type=securable_type,
        full_name=full_name,
        client=client,
        principal=principal,
    ).parsed


async def asyncio_detailed(
    securable_type: GetPermissionsApi21UnityCatalogPermissionsSecurableTypeFullNameGetSecurableType,
    full_name: str,
    *,
    client: AuthenticatedClient | Client,
    principal: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | PermissionsList]:
    """Get permissions for securable

     Return the permission assignments on a securable.

    Args:
        securable_type: One of the nine UC ``SecurableType`` values.
            Typed as a ``Literal`` so unknown values surface as 422.
        full_name: Spec-shaped dotted address — 1 segment for
            catalog / credential / external location, 2 for schema,
            3 for table / volume / function / registered model, or
            the live metastore id for metastore.
        principal: Optional filter. When set, only that principal's
            grants appear in the response.
        db: Database session dependency.

    Returns:
        PermissionsList: The current grant state of the securable.

    Args:
        securable_type
            (GetPermissionsApi21UnityCatalogPermissionsSecurableTypeFullNameGetSecurableType):
        full_name (str):
        principal (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | PermissionsList]
    """

    kwargs = _get_kwargs(
        securable_type=securable_type,
        full_name=full_name,
        principal=principal,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    securable_type: GetPermissionsApi21UnityCatalogPermissionsSecurableTypeFullNameGetSecurableType,
    full_name: str,
    *,
    client: AuthenticatedClient | Client,
    principal: None | str | Unset = UNSET,
) -> HTTPValidationError | PermissionsList | None:
    """Get permissions for securable

     Return the permission assignments on a securable.

    Args:
        securable_type: One of the nine UC ``SecurableType`` values.
            Typed as a ``Literal`` so unknown values surface as 422.
        full_name: Spec-shaped dotted address — 1 segment for
            catalog / credential / external location, 2 for schema,
            3 for table / volume / function / registered model, or
            the live metastore id for metastore.
        principal: Optional filter. When set, only that principal's
            grants appear in the response.
        db: Database session dependency.

    Returns:
        PermissionsList: The current grant state of the securable.

    Args:
        securable_type
            (GetPermissionsApi21UnityCatalogPermissionsSecurableTypeFullNameGetSecurableType):
        full_name (str):
        principal (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | PermissionsList
    """

    return (
        await asyncio_detailed(
            securable_type=securable_type,
            full_name=full_name,
            client=client,
            principal=principal,
        )
    ).parsed
