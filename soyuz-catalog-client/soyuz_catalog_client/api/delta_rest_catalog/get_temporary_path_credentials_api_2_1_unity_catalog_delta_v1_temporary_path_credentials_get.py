from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.credentials_response import CredentialsResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response


def _get_kwargs(
    *,
    location: str,
    operation: str,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["location"] = location

    params["operation"] = operation

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/2.1/unity-catalog/delta/v1/temporary-path-credentials",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> CredentialsResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = CredentialsResponse.from_dict(response.json())

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
) -> Response[CredentialsResponse | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    location: str,
    operation: str,
) -> Response[CredentialsResponse | HTTPValidationError]:
    r"""Get Delta temporary path credentials

     Return an empty credentials list for an arbitrary path.

    Exists so Delta clients that walk the ``/config`` endpoint
    list and check for path-credential support see a spec-shaped
    200 instead of a 404. soyuz vends nothing; the empty list is
    the same stub posture as every other credential endpoint.

    Args:
        location: Storage path from the query string.
        operation: Required by spec; ignored by soyuz.

    Returns:
        CredentialsResponse: Always ``{\"storage-credentials\": []}``.

    Args:
        location (str): Storage location path
        operation (str): READ or READ_WRITE

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CredentialsResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        location=location,
        operation=operation,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    location: str,
    operation: str,
) -> CredentialsResponse | HTTPValidationError | None:
    r"""Get Delta temporary path credentials

     Return an empty credentials list for an arbitrary path.

    Exists so Delta clients that walk the ``/config`` endpoint
    list and check for path-credential support see a spec-shaped
    200 instead of a 404. soyuz vends nothing; the empty list is
    the same stub posture as every other credential endpoint.

    Args:
        location: Storage path from the query string.
        operation: Required by spec; ignored by soyuz.

    Returns:
        CredentialsResponse: Always ``{\"storage-credentials\": []}``.

    Args:
        location (str): Storage location path
        operation (str): READ or READ_WRITE

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CredentialsResponse | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        location=location,
        operation=operation,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    location: str,
    operation: str,
) -> Response[CredentialsResponse | HTTPValidationError]:
    r"""Get Delta temporary path credentials

     Return an empty credentials list for an arbitrary path.

    Exists so Delta clients that walk the ``/config`` endpoint
    list and check for path-credential support see a spec-shaped
    200 instead of a 404. soyuz vends nothing; the empty list is
    the same stub posture as every other credential endpoint.

    Args:
        location: Storage path from the query string.
        operation: Required by spec; ignored by soyuz.

    Returns:
        CredentialsResponse: Always ``{\"storage-credentials\": []}``.

    Args:
        location (str): Storage location path
        operation (str): READ or READ_WRITE

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CredentialsResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        location=location,
        operation=operation,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    location: str,
    operation: str,
) -> CredentialsResponse | HTTPValidationError | None:
    r"""Get Delta temporary path credentials

     Return an empty credentials list for an arbitrary path.

    Exists so Delta clients that walk the ``/config`` endpoint
    list and check for path-credential support see a spec-shaped
    200 instead of a 404. soyuz vends nothing; the empty list is
    the same stub posture as every other credential endpoint.

    Args:
        location: Storage path from the query string.
        operation: Required by spec; ignored by soyuz.

    Returns:
        CredentialsResponse: Always ``{\"storage-credentials\": []}``.

    Args:
        location (str): Storage location path
        operation (str): READ or READ_WRITE

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CredentialsResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            location=location,
            operation=operation,
        )
    ).parsed
