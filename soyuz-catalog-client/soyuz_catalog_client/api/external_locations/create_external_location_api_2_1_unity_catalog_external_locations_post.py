from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_external_location import CreateExternalLocation
from ...models.external_location_info import ExternalLocationInfo
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response


def _get_kwargs(
    *,
    body: CreateExternalLocation,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/2.1/unity-catalog/external-locations",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ExternalLocationInfo | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = ExternalLocationInfo.from_dict(response.json())

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
) -> Response[ExternalLocationInfo | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateExternalLocation,
) -> Response[ExternalLocationInfo | HTTPValidationError]:
    """Create external location

     Create a new external location.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        ExternalLocationInfo: The created row.

    Args:
        body (CreateExternalLocation): Request body for ``POST /external-locations``.

            The UC spec requires ``name``, ``url``, and ``credential_name`` on
            create. The service resolves ``credential_name`` to a persistent
            ``credential_id`` so a subsequent credential rename does not break
            the binding. ``extra="forbid"`` rejects unknown fields — including
            ``credential_id`` itself, which is a read-only server-derived
            field on the response and must not be accepted on create.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ExternalLocationInfo | HTTPValidationError]
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
    body: CreateExternalLocation,
) -> ExternalLocationInfo | HTTPValidationError | None:
    """Create external location

     Create a new external location.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        ExternalLocationInfo: The created row.

    Args:
        body (CreateExternalLocation): Request body for ``POST /external-locations``.

            The UC spec requires ``name``, ``url``, and ``credential_name`` on
            create. The service resolves ``credential_name`` to a persistent
            ``credential_id`` so a subsequent credential rename does not break
            the binding. ``extra="forbid"`` rejects unknown fields — including
            ``credential_id`` itself, which is a read-only server-derived
            field on the response and must not be accepted on create.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ExternalLocationInfo | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateExternalLocation,
) -> Response[ExternalLocationInfo | HTTPValidationError]:
    """Create external location

     Create a new external location.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        ExternalLocationInfo: The created row.

    Args:
        body (CreateExternalLocation): Request body for ``POST /external-locations``.

            The UC spec requires ``name``, ``url``, and ``credential_name`` on
            create. The service resolves ``credential_name`` to a persistent
            ``credential_id`` so a subsequent credential rename does not break
            the binding. ``extra="forbid"`` rejects unknown fields — including
            ``credential_id`` itself, which is a read-only server-derived
            field on the response and must not be accepted on create.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ExternalLocationInfo | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreateExternalLocation,
) -> ExternalLocationInfo | HTTPValidationError | None:
    """Create external location

     Create a new external location.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        ExternalLocationInfo: The created row.

    Args:
        body (CreateExternalLocation): Request body for ``POST /external-locations``.

            The UC spec requires ``name``, ``url``, and ``credential_name`` on
            create. The service resolves ``credential_name`` to a persistent
            ``credential_id`` so a subsequent credential rename does not break
            the binding. ``extra="forbid"`` rejects unknown fields — including
            ``credential_id`` itself, which is a read-only server-derived
            field on the response and must not be accepted on create.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ExternalLocationInfo | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
