from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_model_version import CreateModelVersion
from ...models.http_validation_error import HTTPValidationError
from ...models.model_version_info import ModelVersionInfo
from ...types import UNSET, Response


def _get_kwargs(
    *,
    body: CreateModelVersion,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/2.1/unity-catalog/models/versions",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | ModelVersionInfo | None:
    if response.status_code == 200:
        response_200 = ModelVersionInfo.from_dict(response.json())

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
) -> Response[HTTPValidationError | ModelVersionInfo]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateModelVersion,
) -> Response[HTTPValidationError | ModelVersionInfo]:
    """Create model version

     Create a new model version under an existing registered model.

    The UC spec addresses the parent via three separate body fields
    (``catalog_name``, ``schema_name``, ``model_name``) rather than a
    URL path parameter — see :func:`_resolve_model_from_triple` in
    the service module for the rebuild-to-full_name dance.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        ModelVersionInfo: The created row.

    Args:
        body (CreateModelVersion): Request body for ``POST /models/versions``.

            The UC spec addresses the parent registered model by the triple
            ``(catalog_name, schema_name, model_name)`` on the create body
            rather than via a nested URL, which is why this endpoint is
            mounted at ``/models/versions`` instead of
            ``/models/{full_name}/versions``. ``source`` is required; the
            server assigns a monotonic ``version`` integer unique per
            registered model.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ModelVersionInfo]
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
    body: CreateModelVersion,
) -> HTTPValidationError | ModelVersionInfo | None:
    """Create model version

     Create a new model version under an existing registered model.

    The UC spec addresses the parent via three separate body fields
    (``catalog_name``, ``schema_name``, ``model_name``) rather than a
    URL path parameter — see :func:`_resolve_model_from_triple` in
    the service module for the rebuild-to-full_name dance.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        ModelVersionInfo: The created row.

    Args:
        body (CreateModelVersion): Request body for ``POST /models/versions``.

            The UC spec addresses the parent registered model by the triple
            ``(catalog_name, schema_name, model_name)`` on the create body
            rather than via a nested URL, which is why this endpoint is
            mounted at ``/models/versions`` instead of
            ``/models/{full_name}/versions``. ``source`` is required; the
            server assigns a monotonic ``version`` integer unique per
            registered model.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ModelVersionInfo
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateModelVersion,
) -> Response[HTTPValidationError | ModelVersionInfo]:
    """Create model version

     Create a new model version under an existing registered model.

    The UC spec addresses the parent via three separate body fields
    (``catalog_name``, ``schema_name``, ``model_name``) rather than a
    URL path parameter — see :func:`_resolve_model_from_triple` in
    the service module for the rebuild-to-full_name dance.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        ModelVersionInfo: The created row.

    Args:
        body (CreateModelVersion): Request body for ``POST /models/versions``.

            The UC spec addresses the parent registered model by the triple
            ``(catalog_name, schema_name, model_name)`` on the create body
            rather than via a nested URL, which is why this endpoint is
            mounted at ``/models/versions`` instead of
            ``/models/{full_name}/versions``. ``source`` is required; the
            server assigns a monotonic ``version`` integer unique per
            registered model.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ModelVersionInfo]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreateModelVersion,
) -> HTTPValidationError | ModelVersionInfo | None:
    """Create model version

     Create a new model version under an existing registered model.

    The UC spec addresses the parent via three separate body fields
    (``catalog_name``, ``schema_name``, ``model_name``) rather than a
    URL path parameter — see :func:`_resolve_model_from_triple` in
    the service module for the rebuild-to-full_name dance.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        ModelVersionInfo: The created row.

    Args:
        body (CreateModelVersion): Request body for ``POST /models/versions``.

            The UC spec addresses the parent registered model by the triple
            ``(catalog_name, schema_name, model_name)`` on the create body
            rather than via a nested URL, which is why this endpoint is
            mounted at ``/models/versions`` instead of
            ``/models/{full_name}/versions``. ``source`` is required; the
            server assigns a monotonic ``version`` integer unique per
            registered model.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ModelVersionInfo
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
