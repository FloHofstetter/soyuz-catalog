from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.credential_info import CredentialInfo
from ...models.http_validation_error import HTTPValidationError
from ...models.update_credential_request import UpdateCredentialRequest
from ...types import UNSET, Response


def _get_kwargs(
    name: str,
    *,
    body: UpdateCredentialRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/api/2.1/unity-catalog/credentials/{name}".format(
            name=quote(str(name), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> CredentialInfo | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = CredentialInfo.from_dict(response.json())

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
) -> Response[CredentialInfo | HTTPValidationError]:
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
    body: UpdateCredentialRequest,
) -> Response[CredentialInfo | HTTPValidationError]:
    """Update storage credential

     Update an existing credential.

    Args:
        name: Current credential name.
        payload: Patch body. Only fields explicitly present are applied.
        db: Database session dependency.

    Returns:
        CredentialInfo: The updated credential.

    Args:
        name (str):
        body (UpdateCredentialRequest): Request body for ``PATCH /credentials/{name}``.

            Replace-style PATCH semantics driven by ``model_fields_set`` in
            the service layer, same as every other update endpoint. The spec
            allows ``new_name``, ``comment``, ``owner``, and a fresh
            ``aws_iam_role`` payload. ``extra="forbid"`` rejects unknown or
            read-only fields (``id``, ``purpose``, ``created_at``, …) with
            HTTP 422.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CredentialInfo | HTTPValidationError]
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
    body: UpdateCredentialRequest,
) -> CredentialInfo | HTTPValidationError | None:
    """Update storage credential

     Update an existing credential.

    Args:
        name: Current credential name.
        payload: Patch body. Only fields explicitly present are applied.
        db: Database session dependency.

    Returns:
        CredentialInfo: The updated credential.

    Args:
        name (str):
        body (UpdateCredentialRequest): Request body for ``PATCH /credentials/{name}``.

            Replace-style PATCH semantics driven by ``model_fields_set`` in
            the service layer, same as every other update endpoint. The spec
            allows ``new_name``, ``comment``, ``owner``, and a fresh
            ``aws_iam_role`` payload. ``extra="forbid"`` rejects unknown or
            read-only fields (``id``, ``purpose``, ``created_at``, …) with
            HTTP 422.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CredentialInfo | HTTPValidationError
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
    body: UpdateCredentialRequest,
) -> Response[CredentialInfo | HTTPValidationError]:
    """Update storage credential

     Update an existing credential.

    Args:
        name: Current credential name.
        payload: Patch body. Only fields explicitly present are applied.
        db: Database session dependency.

    Returns:
        CredentialInfo: The updated credential.

    Args:
        name (str):
        body (UpdateCredentialRequest): Request body for ``PATCH /credentials/{name}``.

            Replace-style PATCH semantics driven by ``model_fields_set`` in
            the service layer, same as every other update endpoint. The spec
            allows ``new_name``, ``comment``, ``owner``, and a fresh
            ``aws_iam_role`` payload. ``extra="forbid"`` rejects unknown or
            read-only fields (``id``, ``purpose``, ``created_at``, …) with
            HTTP 422.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CredentialInfo | HTTPValidationError]
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
    body: UpdateCredentialRequest,
) -> CredentialInfo | HTTPValidationError | None:
    """Update storage credential

     Update an existing credential.

    Args:
        name: Current credential name.
        payload: Patch body. Only fields explicitly present are applied.
        db: Database session dependency.

    Returns:
        CredentialInfo: The updated credential.

    Args:
        name (str):
        body (UpdateCredentialRequest): Request body for ``PATCH /credentials/{name}``.

            Replace-style PATCH semantics driven by ``model_fields_set`` in
            the service layer, same as every other update endpoint. The spec
            allows ``new_name``, ``comment``, ``owner``, and a fresh
            ``aws_iam_role`` payload. ``extra="forbid"`` rejects unknown or
            read-only fields (``id``, ``purpose``, ``created_at``, …) with
            HTTP 422.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CredentialInfo | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
            body=body,
        )
    ).parsed
