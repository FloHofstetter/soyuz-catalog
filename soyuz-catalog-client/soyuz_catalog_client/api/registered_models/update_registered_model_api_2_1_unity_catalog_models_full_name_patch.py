from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.registered_model_info import RegisteredModelInfo
from ...models.update_registered_model import UpdateRegisteredModel
from ...types import UNSET, Response


def _get_kwargs(
    full_name: str,
    *,
    body: UpdateRegisteredModel,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/api/2.1/unity-catalog/models/{full_name}".format(
            full_name=quote(str(full_name), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | RegisteredModelInfo | None:
    if response.status_code == 200:
        response_200 = RegisteredModelInfo.from_dict(response.json())

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
) -> Response[HTTPValidationError | RegisteredModelInfo]:
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
    body: UpdateRegisteredModel,
) -> Response[HTTPValidationError | RegisteredModelInfo]:
    """Update registered model

     Update an existing registered model.

    Args:
        full_name: Current ``catalog.schema.model`` path parameter.
        payload: Patch body. Only fields explicitly present are applied.
        db: Database session dependency.

    Returns:
        RegisteredModelInfo: The updated row.

    Args:
        full_name (str):
        body (UpdateRegisteredModel): Request body for ``PATCH /models/{full_name}``.

            Replace-style PATCH semantics driven by ``model_fields_set`` in
            the service layer. The UC-OSS proto's ``UpdateRegisteredModel``
            message includes ``full_name`` as a body field that duplicates
            the URL path parameter (`unity_catalog_oss_messages.proto:82-95`)
            — MLflow's UC-OSS client sends it on every request, so we accept
            it and ignore it (the URL is the source of truth). ``extra="forbid"``
            still rejects truly unknown fields (storage_location, owner, …)
            with HTTP 422.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | RegisteredModelInfo]
    """

    kwargs = _get_kwargs(
        full_name=full_name,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    full_name: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateRegisteredModel,
) -> HTTPValidationError | RegisteredModelInfo | None:
    """Update registered model

     Update an existing registered model.

    Args:
        full_name: Current ``catalog.schema.model`` path parameter.
        payload: Patch body. Only fields explicitly present are applied.
        db: Database session dependency.

    Returns:
        RegisteredModelInfo: The updated row.

    Args:
        full_name (str):
        body (UpdateRegisteredModel): Request body for ``PATCH /models/{full_name}``.

            Replace-style PATCH semantics driven by ``model_fields_set`` in
            the service layer. The UC-OSS proto's ``UpdateRegisteredModel``
            message includes ``full_name`` as a body field that duplicates
            the URL path parameter (`unity_catalog_oss_messages.proto:82-95`)
            — MLflow's UC-OSS client sends it on every request, so we accept
            it and ignore it (the URL is the source of truth). ``extra="forbid"``
            still rejects truly unknown fields (storage_location, owner, …)
            with HTTP 422.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | RegisteredModelInfo
    """

    return sync_detailed(
        full_name=full_name,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    full_name: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateRegisteredModel,
) -> Response[HTTPValidationError | RegisteredModelInfo]:
    """Update registered model

     Update an existing registered model.

    Args:
        full_name: Current ``catalog.schema.model`` path parameter.
        payload: Patch body. Only fields explicitly present are applied.
        db: Database session dependency.

    Returns:
        RegisteredModelInfo: The updated row.

    Args:
        full_name (str):
        body (UpdateRegisteredModel): Request body for ``PATCH /models/{full_name}``.

            Replace-style PATCH semantics driven by ``model_fields_set`` in
            the service layer. The UC-OSS proto's ``UpdateRegisteredModel``
            message includes ``full_name`` as a body field that duplicates
            the URL path parameter (`unity_catalog_oss_messages.proto:82-95`)
            — MLflow's UC-OSS client sends it on every request, so we accept
            it and ignore it (the URL is the source of truth). ``extra="forbid"``
            still rejects truly unknown fields (storage_location, owner, …)
            with HTTP 422.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | RegisteredModelInfo]
    """

    kwargs = _get_kwargs(
        full_name=full_name,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    full_name: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateRegisteredModel,
) -> HTTPValidationError | RegisteredModelInfo | None:
    """Update registered model

     Update an existing registered model.

    Args:
        full_name: Current ``catalog.schema.model`` path parameter.
        payload: Patch body. Only fields explicitly present are applied.
        db: Database session dependency.

    Returns:
        RegisteredModelInfo: The updated row.

    Args:
        full_name (str):
        body (UpdateRegisteredModel): Request body for ``PATCH /models/{full_name}``.

            Replace-style PATCH semantics driven by ``model_fields_set`` in
            the service layer. The UC-OSS proto's ``UpdateRegisteredModel``
            message includes ``full_name`` as a body field that duplicates
            the URL path parameter (`unity_catalog_oss_messages.proto:82-95`)
            — MLflow's UC-OSS client sends it on every request, so we accept
            it and ignore it (the URL is the source of truth). ``extra="forbid"``
            still rejects truly unknown fields (storage_location, owner, …)
            with HTTP 422.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | RegisteredModelInfo
    """

    return (
        await asyncio_detailed(
            full_name=full_name,
            client=client,
            body=body,
        )
    ).parsed
