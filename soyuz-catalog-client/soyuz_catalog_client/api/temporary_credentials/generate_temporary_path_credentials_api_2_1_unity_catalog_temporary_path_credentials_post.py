from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.generate_temporary_path_credential import GenerateTemporaryPathCredential
from ...models.http_validation_error import HTTPValidationError
from ...models.temporary_credentials import TemporaryCredentials
from ...types import UNSET, Response


def _get_kwargs(
    *,
    body: GenerateTemporaryPathCredential,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/2.1/unity-catalog/temporary-path-credentials",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | TemporaryCredentials | None:
    if response.status_code == 200:
        response_200 = TemporaryCredentials.from_dict(response.json())

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
) -> Response[HTTPValidationError | TemporaryCredentials]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: GenerateTemporaryPathCredential,
) -> Response[HTTPValidationError | TemporaryCredentials]:
    """Vend temporary path credentials

     Generate temporary credentials for an arbitrary storage path.

    Args:
        payload: Request body with ``url`` and ``operation``.
        db: Database session dependency (unused, see service layer).

    Returns:
        TemporaryCredentials: Stub response routed on the URL's
            storage scheme — same shape the table/volume variants
            return for an equivalent ``storage_location``.

    Args:
        body (GenerateTemporaryPathCredential): Request body for ``POST /temporary-path-
            credentials``.

            Mirrors :class:`GenerateTemporaryTableCredential` / ...Volume: the
            request carries a user-supplied storage URL and a ``PathOperation``
            enum. ``PATH_READ`` / ``PATH_READ_WRITE`` / ``PATH_CREATE_TABLE``
            are the three real values; the protobuf-default
            ``UNKNOWN_PATH_OPERATION`` sentinel is accepted at the Pydantic
            layer and rejected at the service layer for the same reason the
            table/volume variants reject their own sentinels. Unknown keys
            surface as 422 via ``extra="forbid"``.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TemporaryCredentials]
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
    body: GenerateTemporaryPathCredential,
) -> HTTPValidationError | TemporaryCredentials | None:
    """Vend temporary path credentials

     Generate temporary credentials for an arbitrary storage path.

    Args:
        payload: Request body with ``url`` and ``operation``.
        db: Database session dependency (unused, see service layer).

    Returns:
        TemporaryCredentials: Stub response routed on the URL's
            storage scheme — same shape the table/volume variants
            return for an equivalent ``storage_location``.

    Args:
        body (GenerateTemporaryPathCredential): Request body for ``POST /temporary-path-
            credentials``.

            Mirrors :class:`GenerateTemporaryTableCredential` / ...Volume: the
            request carries a user-supplied storage URL and a ``PathOperation``
            enum. ``PATH_READ`` / ``PATH_READ_WRITE`` / ``PATH_CREATE_TABLE``
            are the three real values; the protobuf-default
            ``UNKNOWN_PATH_OPERATION`` sentinel is accepted at the Pydantic
            layer and rejected at the service layer for the same reason the
            table/volume variants reject their own sentinels. Unknown keys
            surface as 422 via ``extra="forbid"``.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TemporaryCredentials
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: GenerateTemporaryPathCredential,
) -> Response[HTTPValidationError | TemporaryCredentials]:
    """Vend temporary path credentials

     Generate temporary credentials for an arbitrary storage path.

    Args:
        payload: Request body with ``url`` and ``operation``.
        db: Database session dependency (unused, see service layer).

    Returns:
        TemporaryCredentials: Stub response routed on the URL's
            storage scheme — same shape the table/volume variants
            return for an equivalent ``storage_location``.

    Args:
        body (GenerateTemporaryPathCredential): Request body for ``POST /temporary-path-
            credentials``.

            Mirrors :class:`GenerateTemporaryTableCredential` / ...Volume: the
            request carries a user-supplied storage URL and a ``PathOperation``
            enum. ``PATH_READ`` / ``PATH_READ_WRITE`` / ``PATH_CREATE_TABLE``
            are the three real values; the protobuf-default
            ``UNKNOWN_PATH_OPERATION`` sentinel is accepted at the Pydantic
            layer and rejected at the service layer for the same reason the
            table/volume variants reject their own sentinels. Unknown keys
            surface as 422 via ``extra="forbid"``.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TemporaryCredentials]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: GenerateTemporaryPathCredential,
) -> HTTPValidationError | TemporaryCredentials | None:
    """Vend temporary path credentials

     Generate temporary credentials for an arbitrary storage path.

    Args:
        payload: Request body with ``url`` and ``operation``.
        db: Database session dependency (unused, see service layer).

    Returns:
        TemporaryCredentials: Stub response routed on the URL's
            storage scheme — same shape the table/volume variants
            return for an equivalent ``storage_location``.

    Args:
        body (GenerateTemporaryPathCredential): Request body for ``POST /temporary-path-
            credentials``.

            Mirrors :class:`GenerateTemporaryTableCredential` / ...Volume: the
            request carries a user-supplied storage URL and a ``PathOperation``
            enum. ``PATH_READ`` / ``PATH_READ_WRITE`` / ``PATH_CREATE_TABLE``
            are the three real values; the protobuf-default
            ``UNKNOWN_PATH_OPERATION`` sentinel is accepted at the Pydantic
            layer and rejected at the service layer for the same reason the
            table/volume variants reject their own sentinels. Unknown keys
            surface as 422 via ``extra="forbid"``.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TemporaryCredentials
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
