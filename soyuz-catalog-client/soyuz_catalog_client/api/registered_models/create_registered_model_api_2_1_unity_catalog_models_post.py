from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_registered_model import CreateRegisteredModel
from ...models.http_validation_error import HTTPValidationError
from ...models.registered_model_info import RegisteredModelInfo
from ...types import UNSET, Response


def _get_kwargs(
    *,
    body: CreateRegisteredModel,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/2.1/unity-catalog/models",
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
    *,
    client: AuthenticatedClient | Client,
    body: CreateRegisteredModel,
) -> Response[HTTPValidationError | RegisteredModelInfo]:
    """Create registered model

     Create a new registered model under an existing schema.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        RegisteredModelInfo: The created row.

    Args:
        body (CreateRegisteredModel): Request body for ``POST /models``.

            The UC spec requires ``name``, ``catalog_name``, and
            ``schema_name``; ``comment`` is the only optional field.
            ``extra="forbid"`` rejects unknown fields — notably including
            ``storage_location``, which is a server-derived field on the
            response and must not be accepted on create.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | RegisteredModelInfo]
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
    body: CreateRegisteredModel,
) -> HTTPValidationError | RegisteredModelInfo | None:
    """Create registered model

     Create a new registered model under an existing schema.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        RegisteredModelInfo: The created row.

    Args:
        body (CreateRegisteredModel): Request body for ``POST /models``.

            The UC spec requires ``name``, ``catalog_name``, and
            ``schema_name``; ``comment`` is the only optional field.
            ``extra="forbid"`` rejects unknown fields — notably including
            ``storage_location``, which is a server-derived field on the
            response and must not be accepted on create.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | RegisteredModelInfo
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateRegisteredModel,
) -> Response[HTTPValidationError | RegisteredModelInfo]:
    """Create registered model

     Create a new registered model under an existing schema.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        RegisteredModelInfo: The created row.

    Args:
        body (CreateRegisteredModel): Request body for ``POST /models``.

            The UC spec requires ``name``, ``catalog_name``, and
            ``schema_name``; ``comment`` is the only optional field.
            ``extra="forbid"`` rejects unknown fields — notably including
            ``storage_location``, which is a server-derived field on the
            response and must not be accepted on create.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | RegisteredModelInfo]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreateRegisteredModel,
) -> HTTPValidationError | RegisteredModelInfo | None:
    """Create registered model

     Create a new registered model under an existing schema.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        RegisteredModelInfo: The created row.

    Args:
        body (CreateRegisteredModel): Request body for ``POST /models``.

            The UC spec requires ``name``, ``catalog_name``, and
            ``schema_name``; ``comment`` is the only optional field.
            ``extra="forbid"`` rejects unknown fields — notably including
            ``storage_location``, which is a server-derived field on the
            response and must not be accepted on create.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | RegisteredModelInfo
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
