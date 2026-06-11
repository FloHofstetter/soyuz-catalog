from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_recipient import CreateRecipient
from ...models.http_validation_error import HTTPValidationError
from ...models.recipient_info import RecipientInfo
from ...types import UNSET, Response


def _get_kwargs(
    *,
    body: CreateRecipient,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/2.1/unity-catalog/recipients",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | RecipientInfo | None:
    if response.status_code == 200:
        response_200 = RecipientInfo.from_dict(response.json())

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
) -> Response[HTTPValidationError | RecipientInfo]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateRecipient,
) -> Response[HTTPValidationError | RecipientInfo]:
    """Create recipient

     Create a new recipient and mint its bearer token.

    The response carries the plaintext ``token`` — the only time it
    is ever visible. Store it; soyuz cannot re-serve it.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        RecipientInfo: The created recipient including the one-time
            plaintext ``token``.

    Args:
        body (CreateRecipient): Request body for ``POST /recipients``.

            The bearer token is always server-generated — there is no field
            to supply one, so token entropy is never caller-controlled.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | RecipientInfo]
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
    body: CreateRecipient,
) -> HTTPValidationError | RecipientInfo | None:
    """Create recipient

     Create a new recipient and mint its bearer token.

    The response carries the plaintext ``token`` — the only time it
    is ever visible. Store it; soyuz cannot re-serve it.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        RecipientInfo: The created recipient including the one-time
            plaintext ``token``.

    Args:
        body (CreateRecipient): Request body for ``POST /recipients``.

            The bearer token is always server-generated — there is no field
            to supply one, so token entropy is never caller-controlled.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | RecipientInfo
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateRecipient,
) -> Response[HTTPValidationError | RecipientInfo]:
    """Create recipient

     Create a new recipient and mint its bearer token.

    The response carries the plaintext ``token`` — the only time it
    is ever visible. Store it; soyuz cannot re-serve it.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        RecipientInfo: The created recipient including the one-time
            plaintext ``token``.

    Args:
        body (CreateRecipient): Request body for ``POST /recipients``.

            The bearer token is always server-generated — there is no field
            to supply one, so token entropy is never caller-controlled.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | RecipientInfo]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreateRecipient,
) -> HTTPValidationError | RecipientInfo | None:
    """Create recipient

     Create a new recipient and mint its bearer token.

    The response carries the plaintext ``token`` — the only time it
    is ever visible. Store it; soyuz cannot re-serve it.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        RecipientInfo: The created recipient including the one-time
            plaintext ``token``.

    Args:
        body (CreateRecipient): Request body for ``POST /recipients``.

            The bearer token is always server-generated — there is no field
            to supply one, so token entropy is never caller-controlled.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | RecipientInfo
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
