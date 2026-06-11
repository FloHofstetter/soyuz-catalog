from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.recipient_info import RecipientInfo
from ...models.update_recipient import UpdateRecipient
from ...types import UNSET, Response


def _get_kwargs(
    name: str,
    *,
    body: UpdateRecipient,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/api/2.1/unity-catalog/recipients/{name}".format(
            name=quote(str(name), safe=""),
        ),
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
    name: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateRecipient,
) -> Response[HTTPValidationError | RecipientInfo]:
    """Update recipient

     Update an existing recipient's name, comment, or owner.

    Args:
        name: Current recipient name.
        payload: Patch body. Only fields explicitly present are
            applied; the bearer token has its own rotation endpoint.
        db: Database session dependency.

    Returns:
        RecipientInfo: The updated recipient.

    Args:
        name (str):
        body (UpdateRecipient): Request body for ``PATCH /recipients/{name}``.

            Replace-style PATCH driven by ``model_fields_set``. The bearer
            token is not editable here — rotation has its own endpoint
            (``POST /recipients/{name}/rotate-token``) because it is a
            credential event worth a dedicated audit entry, not a metadata
            edit.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | RecipientInfo]
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
    body: UpdateRecipient,
) -> HTTPValidationError | RecipientInfo | None:
    """Update recipient

     Update an existing recipient's name, comment, or owner.

    Args:
        name: Current recipient name.
        payload: Patch body. Only fields explicitly present are
            applied; the bearer token has its own rotation endpoint.
        db: Database session dependency.

    Returns:
        RecipientInfo: The updated recipient.

    Args:
        name (str):
        body (UpdateRecipient): Request body for ``PATCH /recipients/{name}``.

            Replace-style PATCH driven by ``model_fields_set``. The bearer
            token is not editable here — rotation has its own endpoint
            (``POST /recipients/{name}/rotate-token``) because it is a
            credential event worth a dedicated audit entry, not a metadata
            edit.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | RecipientInfo
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
    body: UpdateRecipient,
) -> Response[HTTPValidationError | RecipientInfo]:
    """Update recipient

     Update an existing recipient's name, comment, or owner.

    Args:
        name: Current recipient name.
        payload: Patch body. Only fields explicitly present are
            applied; the bearer token has its own rotation endpoint.
        db: Database session dependency.

    Returns:
        RecipientInfo: The updated recipient.

    Args:
        name (str):
        body (UpdateRecipient): Request body for ``PATCH /recipients/{name}``.

            Replace-style PATCH driven by ``model_fields_set``. The bearer
            token is not editable here — rotation has its own endpoint
            (``POST /recipients/{name}/rotate-token``) because it is a
            credential event worth a dedicated audit entry, not a metadata
            edit.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | RecipientInfo]
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
    body: UpdateRecipient,
) -> HTTPValidationError | RecipientInfo | None:
    """Update recipient

     Update an existing recipient's name, comment, or owner.

    Args:
        name: Current recipient name.
        payload: Patch body. Only fields explicitly present are
            applied; the bearer token has its own rotation endpoint.
        db: Database session dependency.

    Returns:
        RecipientInfo: The updated recipient.

    Args:
        name (str):
        body (UpdateRecipient): Request body for ``PATCH /recipients/{name}``.

            Replace-style PATCH driven by ``model_fields_set``. The bearer
            token is not editable here — rotation has its own endpoint
            (``POST /recipients/{name}/rotate-token``) because it is a
            credential event worth a dedicated audit entry, not a metadata
            edit.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | RecipientInfo
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
            body=body,
        )
    ).parsed
