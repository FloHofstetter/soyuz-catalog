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
    table_id: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/2.1/unity-catalog/delta/v1/staging-tables/{table_id}/credentials".format(
            table_id=quote(str(table_id), safe=""),
        ),
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
    table_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[CredentialsResponse | HTTPValidationError]:
    r"""Get Delta staging table credentials

     Return an empty credentials list for a staging table.

    soyuz verifies the staging table exists so an unknown UUID
    surfaces as 404; otherwise returns the same empty stub as
    :func:`get_table_credentials`.

    Args:
        table_id: Staging table opaque id.
        db: Database session dependency.

    Returns:
        CredentialsResponse: Always ``{\"storage-credentials\": []}``.

    Args:
        table_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CredentialsResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        table_id=table_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    table_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> CredentialsResponse | HTTPValidationError | None:
    r"""Get Delta staging table credentials

     Return an empty credentials list for a staging table.

    soyuz verifies the staging table exists so an unknown UUID
    surfaces as 404; otherwise returns the same empty stub as
    :func:`get_table_credentials`.

    Args:
        table_id: Staging table opaque id.
        db: Database session dependency.

    Returns:
        CredentialsResponse: Always ``{\"storage-credentials\": []}``.

    Args:
        table_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CredentialsResponse | HTTPValidationError
    """

    return sync_detailed(
        table_id=table_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    table_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[CredentialsResponse | HTTPValidationError]:
    r"""Get Delta staging table credentials

     Return an empty credentials list for a staging table.

    soyuz verifies the staging table exists so an unknown UUID
    surfaces as 404; otherwise returns the same empty stub as
    :func:`get_table_credentials`.

    Args:
        table_id: Staging table opaque id.
        db: Database session dependency.

    Returns:
        CredentialsResponse: Always ``{\"storage-credentials\": []}``.

    Args:
        table_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CredentialsResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        table_id=table_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    table_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> CredentialsResponse | HTTPValidationError | None:
    r"""Get Delta staging table credentials

     Return an empty credentials list for a staging table.

    soyuz verifies the staging table exists so an unknown UUID
    surfaces as 404; otherwise returns the same empty stub as
    :func:`get_table_credentials`.

    Args:
        table_id: Staging table opaque id.
        db: Database session dependency.

    Returns:
        CredentialsResponse: Always ``{\"storage-credentials\": []}``.

    Args:
        table_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CredentialsResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            table_id=table_id,
            client=client,
        )
    ).parsed
