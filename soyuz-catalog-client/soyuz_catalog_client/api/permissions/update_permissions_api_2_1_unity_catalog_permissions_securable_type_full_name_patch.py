from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.permissions_list import PermissionsList
from ...models.update_permissions import UpdatePermissions
from ...models.update_permissions_api_21_unity_catalog_permissions_securable_type_full_name_patch_securable_type import (
    UpdatePermissionsApi21UnityCatalogPermissionsSecurableTypeFullNamePatchSecurableType,
)
from ...types import UNSET, Response


def _get_kwargs(
    securable_type: UpdatePermissionsApi21UnityCatalogPermissionsSecurableTypeFullNamePatchSecurableType,
    full_name: str,
    *,
    body: UpdatePermissions,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/api/2.1/unity-catalog/permissions/{securable_type}/{full_name}".format(
            securable_type=quote(str(securable_type), safe=""),
            full_name=quote(str(full_name), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
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
    securable_type: UpdatePermissionsApi21UnityCatalogPermissionsSecurableTypeFullNamePatchSecurableType,
    full_name: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdatePermissions,
) -> Response[HTTPValidationError | PermissionsList]:
    """Update permissions for securable

     Apply a batch of add/remove changes to a securable's grants.

    Unlike the other PATCH routes in this project, the update shape
    is additive, not replace-style. The service layer validates
    every ``add`` against the per-type allow-set before any write
    and rolls back the whole batch if any single entry is invalid.

    Args:
        securable_type: One of the nine UC ``SecurableType`` values.
        full_name: Spec-shaped dotted address.
        payload: The ``UpdatePermissions`` body containing the
            ordered list of changes.
        db: Database session dependency.

    Returns:
        PermissionsList: The full post-change grant state.

    Args:
        securable_type
            (UpdatePermissionsApi21UnityCatalogPermissionsSecurableTypeFullNamePatchSecurableType):
        full_name (str):
        body (UpdatePermissions): Request body for ``PATCH
            /permissions/{securable_type}/{full_name}``.

            Unlike every other PATCH in this project, this shape is **not**
            replace-style: the client submits a list of additive/subtractive
            changes rather than a full desired state. This matches the
            upstream ``UpdatePermissions`` schema exactly — see
            ``DIVERGENCES.md`` for why the asymmetry with our catalog /
            schema / table PATCH routes is intentional.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | PermissionsList]
    """

    kwargs = _get_kwargs(
        securable_type=securable_type,
        full_name=full_name,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    securable_type: UpdatePermissionsApi21UnityCatalogPermissionsSecurableTypeFullNamePatchSecurableType,
    full_name: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdatePermissions,
) -> HTTPValidationError | PermissionsList | None:
    """Update permissions for securable

     Apply a batch of add/remove changes to a securable's grants.

    Unlike the other PATCH routes in this project, the update shape
    is additive, not replace-style. The service layer validates
    every ``add`` against the per-type allow-set before any write
    and rolls back the whole batch if any single entry is invalid.

    Args:
        securable_type: One of the nine UC ``SecurableType`` values.
        full_name: Spec-shaped dotted address.
        payload: The ``UpdatePermissions`` body containing the
            ordered list of changes.
        db: Database session dependency.

    Returns:
        PermissionsList: The full post-change grant state.

    Args:
        securable_type
            (UpdatePermissionsApi21UnityCatalogPermissionsSecurableTypeFullNamePatchSecurableType):
        full_name (str):
        body (UpdatePermissions): Request body for ``PATCH
            /permissions/{securable_type}/{full_name}``.

            Unlike every other PATCH in this project, this shape is **not**
            replace-style: the client submits a list of additive/subtractive
            changes rather than a full desired state. This matches the
            upstream ``UpdatePermissions`` schema exactly — see
            ``DIVERGENCES.md`` for why the asymmetry with our catalog /
            schema / table PATCH routes is intentional.

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
        body=body,
    ).parsed


async def asyncio_detailed(
    securable_type: UpdatePermissionsApi21UnityCatalogPermissionsSecurableTypeFullNamePatchSecurableType,
    full_name: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdatePermissions,
) -> Response[HTTPValidationError | PermissionsList]:
    """Update permissions for securable

     Apply a batch of add/remove changes to a securable's grants.

    Unlike the other PATCH routes in this project, the update shape
    is additive, not replace-style. The service layer validates
    every ``add`` against the per-type allow-set before any write
    and rolls back the whole batch if any single entry is invalid.

    Args:
        securable_type: One of the nine UC ``SecurableType`` values.
        full_name: Spec-shaped dotted address.
        payload: The ``UpdatePermissions`` body containing the
            ordered list of changes.
        db: Database session dependency.

    Returns:
        PermissionsList: The full post-change grant state.

    Args:
        securable_type
            (UpdatePermissionsApi21UnityCatalogPermissionsSecurableTypeFullNamePatchSecurableType):
        full_name (str):
        body (UpdatePermissions): Request body for ``PATCH
            /permissions/{securable_type}/{full_name}``.

            Unlike every other PATCH in this project, this shape is **not**
            replace-style: the client submits a list of additive/subtractive
            changes rather than a full desired state. This matches the
            upstream ``UpdatePermissions`` schema exactly — see
            ``DIVERGENCES.md`` for why the asymmetry with our catalog /
            schema / table PATCH routes is intentional.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | PermissionsList]
    """

    kwargs = _get_kwargs(
        securable_type=securable_type,
        full_name=full_name,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    securable_type: UpdatePermissionsApi21UnityCatalogPermissionsSecurableTypeFullNamePatchSecurableType,
    full_name: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdatePermissions,
) -> HTTPValidationError | PermissionsList | None:
    """Update permissions for securable

     Apply a batch of add/remove changes to a securable's grants.

    Unlike the other PATCH routes in this project, the update shape
    is additive, not replace-style. The service layer validates
    every ``add`` against the per-type allow-set before any write
    and rolls back the whole batch if any single entry is invalid.

    Args:
        securable_type: One of the nine UC ``SecurableType`` values.
        full_name: Spec-shaped dotted address.
        payload: The ``UpdatePermissions`` body containing the
            ordered list of changes.
        db: Database session dependency.

    Returns:
        PermissionsList: The full post-change grant state.

    Args:
        securable_type
            (UpdatePermissionsApi21UnityCatalogPermissionsSecurableTypeFullNamePatchSecurableType):
        full_name (str):
        body (UpdatePermissions): Request body for ``PATCH
            /permissions/{securable_type}/{full_name}``.

            Unlike every other PATCH in this project, this shape is **not**
            replace-style: the client submits a list of additive/subtractive
            changes rather than a full desired state. This matches the
            upstream ``UpdatePermissions`` schema exactly — see
            ``DIVERGENCES.md`` for why the asymmetry with our catalog /
            schema / table PATCH routes is intentional.

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
            body=body,
        )
    ).parsed
