from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.catalog_info import CatalogInfo
from ...models.http_validation_error import HTTPValidationError
from ...models.update_catalog import UpdateCatalog
from ...types import UNSET, Response


def _get_kwargs(
    name: str,
    *,
    body: UpdateCatalog,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/api/2.1/unity-catalog/catalogs/{name}".format(
            name=quote(str(name), safe=""),
        ),
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
    name: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateCatalog,
) -> Response[CatalogInfo | HTTPValidationError]:
    """Update catalog

     Update an existing catalog.

    Args:
        name: Current catalog name.
        payload: Patch body. Only fields explicitly present are applied;
            ``properties={}`` clears all properties.
        db: Database session dependency.

    Returns:
        CatalogInfo: The updated catalog.

    Args:
        name (str):
        body (UpdateCatalog): Request body for ``PATCH /catalogs/{name}``.

            Replace-style PATCH semantics: every field is optional, but a field that
            *is* present in the request body — including ``properties: {}`` — is
            written through to the row. The service layer reads ``model_fields_set``
            rather than checking ``is None`` so it can distinguish "field omitted"
            from "field set to null/empty".

            ``extra="forbid"`` rejects unknown or read-only fields (e.g. ``owner``)
            with HTTP 422 instead of silently ignoring them as UC OSS Java does. This
            is one of the documented divergences from the Java reference; see
            ``DIVERGENCES.md``.

            The catalog ``type`` field is **deliberately not exposed** on this
            shape: flipping a managed catalog to foreign (or vice versa) would
            orphan the other variant's bookkeeping state (``storage_location``
            on managed, ``connection_id`` on foreign) and has no well-defined
            semantics. A catalog's type is decided at create time and frozen.
            ``connection_name`` PATCH is accepted on foreign catalogs only; the
            service rejects it with 400 on a managed catalog. ``options`` PATCH
            is allowed on both and is replace-style like ``properties``.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CatalogInfo | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        name=name,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateCatalog,
) -> CatalogInfo | HTTPValidationError | None:
    """Update catalog

     Update an existing catalog.

    Args:
        name: Current catalog name.
        payload: Patch body. Only fields explicitly present are applied;
            ``properties={}`` clears all properties.
        db: Database session dependency.

    Returns:
        CatalogInfo: The updated catalog.

    Args:
        name (str):
        body (UpdateCatalog): Request body for ``PATCH /catalogs/{name}``.

            Replace-style PATCH semantics: every field is optional, but a field that
            *is* present in the request body — including ``properties: {}`` — is
            written through to the row. The service layer reads ``model_fields_set``
            rather than checking ``is None`` so it can distinguish "field omitted"
            from "field set to null/empty".

            ``extra="forbid"`` rejects unknown or read-only fields (e.g. ``owner``)
            with HTTP 422 instead of silently ignoring them as UC OSS Java does. This
            is one of the documented divergences from the Java reference; see
            ``DIVERGENCES.md``.

            The catalog ``type`` field is **deliberately not exposed** on this
            shape: flipping a managed catalog to foreign (or vice versa) would
            orphan the other variant's bookkeeping state (``storage_location``
            on managed, ``connection_id`` on foreign) and has no well-defined
            semantics. A catalog's type is decided at create time and frozen.
            ``connection_name`` PATCH is accepted on foreign catalogs only; the
            service rejects it with 400 on a managed catalog. ``options`` PATCH
            is allowed on both and is replace-style like ``properties``.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CatalogInfo | HTTPValidationError
    """

    return sync_detailed(
        name=name,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateCatalog,
) -> Response[CatalogInfo | HTTPValidationError]:
    """Update catalog

     Update an existing catalog.

    Args:
        name: Current catalog name.
        payload: Patch body. Only fields explicitly present are applied;
            ``properties={}`` clears all properties.
        db: Database session dependency.

    Returns:
        CatalogInfo: The updated catalog.

    Args:
        name (str):
        body (UpdateCatalog): Request body for ``PATCH /catalogs/{name}``.

            Replace-style PATCH semantics: every field is optional, but a field that
            *is* present in the request body — including ``properties: {}`` — is
            written through to the row. The service layer reads ``model_fields_set``
            rather than checking ``is None`` so it can distinguish "field omitted"
            from "field set to null/empty".

            ``extra="forbid"`` rejects unknown or read-only fields (e.g. ``owner``)
            with HTTP 422 instead of silently ignoring them as UC OSS Java does. This
            is one of the documented divergences from the Java reference; see
            ``DIVERGENCES.md``.

            The catalog ``type`` field is **deliberately not exposed** on this
            shape: flipping a managed catalog to foreign (or vice versa) would
            orphan the other variant's bookkeeping state (``storage_location``
            on managed, ``connection_id`` on foreign) and has no well-defined
            semantics. A catalog's type is decided at create time and frozen.
            ``connection_name`` PATCH is accepted on foreign catalogs only; the
            service rejects it with 400 on a managed catalog. ``options`` PATCH
            is allowed on both and is replace-style like ``properties``.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CatalogInfo | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        name=name,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateCatalog,
) -> CatalogInfo | HTTPValidationError | None:
    """Update catalog

     Update an existing catalog.

    Args:
        name: Current catalog name.
        payload: Patch body. Only fields explicitly present are applied;
            ``properties={}`` clears all properties.
        db: Database session dependency.

    Returns:
        CatalogInfo: The updated catalog.

    Args:
        name (str):
        body (UpdateCatalog): Request body for ``PATCH /catalogs/{name}``.

            Replace-style PATCH semantics: every field is optional, but a field that
            *is* present in the request body — including ``properties: {}`` — is
            written through to the row. The service layer reads ``model_fields_set``
            rather than checking ``is None`` so it can distinguish "field omitted"
            from "field set to null/empty".

            ``extra="forbid"`` rejects unknown or read-only fields (e.g. ``owner``)
            with HTTP 422 instead of silently ignoring them as UC OSS Java does. This
            is one of the documented divergences from the Java reference; see
            ``DIVERGENCES.md``.

            The catalog ``type`` field is **deliberately not exposed** on this
            shape: flipping a managed catalog to foreign (or vice versa) would
            orphan the other variant's bookkeeping state (``storage_location``
            on managed, ``connection_id`` on foreign) and has no well-defined
            semantics. A catalog's type is decided at create time and frozen.
            ``connection_name`` PATCH is accepted on foreign catalogs only; the
            service rejects it with 400 on a managed catalog. ``options`` PATCH
            is allowed on both and is replace-style like ``properties``.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CatalogInfo | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
            body=body,
        )
    ).parsed
