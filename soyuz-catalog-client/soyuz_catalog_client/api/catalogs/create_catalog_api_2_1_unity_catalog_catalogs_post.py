from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.catalog_info import CatalogInfo
from ...models.create_catalog import CreateCatalog
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response


def _get_kwargs(
    *,
    body: CreateCatalog,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/2.1/unity-catalog/catalogs",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> CatalogInfo | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = CatalogInfo.from_dict(response.json())

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
) -> Response[CatalogInfo | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateCatalog,
) -> Response[CatalogInfo | HTTPValidationError]:
    """Create catalog

     Create a new catalog.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        CatalogInfo: The created catalog.

    Args:
        body (CreateCatalog): Request body for ``POST /catalogs``.

            Only ``name`` is required by the spec; everything else is optional and
            defaults to ``None`` / empty. ``extra="forbid"`` mirrors the same policy
            used on ``UpdateCatalog``: silently dropping unknown fields is the UC OSS
            Java bug we exist to fix, so we reject them with HTTP 422 on create as
            well as on update.

            The Lakehouse-Federation foreign-catalog variant is opt-in: pass ``type="FOREIGN"``
            together with ``connection_name`` (and optional per-connector
            ``options``) and leave ``storage_root`` absent. The managed default
            is ``type="MANAGED"`` and the service layer rejects the two shapes'
            fields cross-contaminating — see ``catalog_service.create_catalog``
            for the exact gates and ``DIVERGENCES.md`` for the rule set.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CatalogInfo | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: CreateCatalog,
) -> CatalogInfo | HTTPValidationError | None:
    """Create catalog

     Create a new catalog.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        CatalogInfo: The created catalog.

    Args:
        body (CreateCatalog): Request body for ``POST /catalogs``.

            Only ``name`` is required by the spec; everything else is optional and
            defaults to ``None`` / empty. ``extra="forbid"`` mirrors the same policy
            used on ``UpdateCatalog``: silently dropping unknown fields is the UC OSS
            Java bug we exist to fix, so we reject them with HTTP 422 on create as
            well as on update.

            The Lakehouse-Federation foreign-catalog variant is opt-in: pass ``type="FOREIGN"``
            together with ``connection_name`` (and optional per-connector
            ``options``) and leave ``storage_root`` absent. The managed default
            is ``type="MANAGED"`` and the service layer rejects the two shapes'
            fields cross-contaminating — see ``catalog_service.create_catalog``
            for the exact gates and ``DIVERGENCES.md`` for the rule set.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CatalogInfo | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateCatalog,
) -> Response[CatalogInfo | HTTPValidationError]:
    """Create catalog

     Create a new catalog.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        CatalogInfo: The created catalog.

    Args:
        body (CreateCatalog): Request body for ``POST /catalogs``.

            Only ``name`` is required by the spec; everything else is optional and
            defaults to ``None`` / empty. ``extra="forbid"`` mirrors the same policy
            used on ``UpdateCatalog``: silently dropping unknown fields is the UC OSS
            Java bug we exist to fix, so we reject them with HTTP 422 on create as
            well as on update.

            The Lakehouse-Federation foreign-catalog variant is opt-in: pass ``type="FOREIGN"``
            together with ``connection_name`` (and optional per-connector
            ``options``) and leave ``storage_root`` absent. The managed default
            is ``type="MANAGED"`` and the service layer rejects the two shapes'
            fields cross-contaminating — see ``catalog_service.create_catalog``
            for the exact gates and ``DIVERGENCES.md`` for the rule set.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CatalogInfo | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreateCatalog,
) -> CatalogInfo | HTTPValidationError | None:
    """Create catalog

     Create a new catalog.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        CatalogInfo: The created catalog.

    Args:
        body (CreateCatalog): Request body for ``POST /catalogs``.

            Only ``name`` is required by the spec; everything else is optional and
            defaults to ``None`` / empty. ``extra="forbid"`` mirrors the same policy
            used on ``UpdateCatalog``: silently dropping unknown fields is the UC OSS
            Java bug we exist to fix, so we reject them with HTTP 422 on create as
            well as on update.

            The Lakehouse-Federation foreign-catalog variant is opt-in: pass ``type="FOREIGN"``
            together with ``connection_name`` (and optional per-connector
            ``options``) and leave ``storage_root`` absent. The managed default
            is ``type="MANAGED"`` and the service layer rejects the two shapes'
            fields cross-contaminating — see ``catalog_service.create_catalog``
            for the exact gates and ``DIVERGENCES.md`` for the rule set.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CatalogInfo | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
