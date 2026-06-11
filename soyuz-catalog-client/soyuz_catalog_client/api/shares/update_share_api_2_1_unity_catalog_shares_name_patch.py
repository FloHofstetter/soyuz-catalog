from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.share_info import ShareInfo
from ...models.update_share import UpdateShare
from ...types import UNSET, Response


def _get_kwargs(
    name: str,
    *,
    body: UpdateShare,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/api/2.1/unity-catalog/shares/{name}".format(
            name=quote(str(name), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | ShareInfo | None:
    if response.status_code == 200:
        response_200 = ShareInfo.from_dict(response.json())

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
) -> Response[HTTPValidationError | ShareInfo]:
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
    body: UpdateShare,
) -> Response[HTTPValidationError | ShareInfo]:
    """Update share

     Update an existing share's name, comment, or owner.

    Args:
        name: Current share name.
        payload: Patch body. Only fields explicitly present are
            applied; object membership has its own endpoints.
        db: Database session dependency.

    Returns:
        ShareInfo: The updated share.

    Args:
        name (str):
        body (UpdateShare): Request body for ``PATCH /shares/{name}``.

            Replace-style PATCH driven by ``model_fields_set``. Objects are
            not editable here — add/remove go through the dedicated object
            endpoints so every membership change is one auditable operation.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ShareInfo]
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
    body: UpdateShare,
) -> HTTPValidationError | ShareInfo | None:
    """Update share

     Update an existing share's name, comment, or owner.

    Args:
        name: Current share name.
        payload: Patch body. Only fields explicitly present are
            applied; object membership has its own endpoints.
        db: Database session dependency.

    Returns:
        ShareInfo: The updated share.

    Args:
        name (str):
        body (UpdateShare): Request body for ``PATCH /shares/{name}``.

            Replace-style PATCH driven by ``model_fields_set``. Objects are
            not editable here — add/remove go through the dedicated object
            endpoints so every membership change is one auditable operation.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ShareInfo
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
    body: UpdateShare,
) -> Response[HTTPValidationError | ShareInfo]:
    """Update share

     Update an existing share's name, comment, or owner.

    Args:
        name: Current share name.
        payload: Patch body. Only fields explicitly present are
            applied; object membership has its own endpoints.
        db: Database session dependency.

    Returns:
        ShareInfo: The updated share.

    Args:
        name (str):
        body (UpdateShare): Request body for ``PATCH /shares/{name}``.

            Replace-style PATCH driven by ``model_fields_set``. Objects are
            not editable here — add/remove go through the dedicated object
            endpoints so every membership change is one auditable operation.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ShareInfo]
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
    body: UpdateShare,
) -> HTTPValidationError | ShareInfo | None:
    """Update share

     Update an existing share's name, comment, or owner.

    Args:
        name: Current share name.
        payload: Patch body. Only fields explicitly present are
            applied; object membership has its own endpoints.
        db: Database session dependency.

    Returns:
        ShareInfo: The updated share.

    Args:
        name (str):
        body (UpdateShare): Request body for ``PATCH /shares/{name}``.

            Replace-style PATCH driven by ``model_fields_set``. Objects are
            not editable here — add/remove go through the dedicated object
            endpoints so every membership change is one auditable operation.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ShareInfo
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
            body=body,
        )
    ).parsed
