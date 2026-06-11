from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_protocol_share_response import GetProtocolShareResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    share: str,
    *,
    authorization: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(authorization, Unset):
        headers["authorization"] = authorization

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/delta-sharing/shares/{share}".format(
            share=quote(str(share), safe=""),
        ),
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> GetProtocolShareResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = GetProtocolShareResponse.from_dict(response.json())

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
) -> Response[GetProtocolShareResponse | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    share: str,
    *,
    client: AuthenticatedClient | Client,
    authorization: None | str | Unset = UNSET,
) -> Response[GetProtocolShareResponse | HTTPValidationError]:
    """Get share (Delta Sharing protocol)

     Fetch one granted share by name.

    Args:
        share: Share name from the URL.
        recipient: Authenticated recipient (dependency).
        db: Database session dependency.

    Returns:
        GetProtocolShareResponse: The wrapped share.

    Args:
        share (str):
        authorization (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetProtocolShareResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        share=share,
        authorization=authorization,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    share: str,
    *,
    client: AuthenticatedClient | Client,
    authorization: None | str | Unset = UNSET,
) -> GetProtocolShareResponse | HTTPValidationError | None:
    """Get share (Delta Sharing protocol)

     Fetch one granted share by name.

    Args:
        share: Share name from the URL.
        recipient: Authenticated recipient (dependency).
        db: Database session dependency.

    Returns:
        GetProtocolShareResponse: The wrapped share.

    Args:
        share (str):
        authorization (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetProtocolShareResponse | HTTPValidationError
    """

    return sync_detailed(
        share=share,
        client=client,
        authorization=authorization,
    ).parsed


async def asyncio_detailed(
    share: str,
    *,
    client: AuthenticatedClient | Client,
    authorization: None | str | Unset = UNSET,
) -> Response[GetProtocolShareResponse | HTTPValidationError]:
    """Get share (Delta Sharing protocol)

     Fetch one granted share by name.

    Args:
        share: Share name from the URL.
        recipient: Authenticated recipient (dependency).
        db: Database session dependency.

    Returns:
        GetProtocolShareResponse: The wrapped share.

    Args:
        share (str):
        authorization (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetProtocolShareResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        share=share,
        authorization=authorization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    share: str,
    *,
    client: AuthenticatedClient | Client,
    authorization: None | str | Unset = UNSET,
) -> GetProtocolShareResponse | HTTPValidationError | None:
    """Get share (Delta Sharing protocol)

     Fetch one granted share by name.

    Args:
        share: Share name from the URL.
        recipient: Authenticated recipient (dependency).
        db: Database session dependency.

    Returns:
        GetProtocolShareResponse: The wrapped share.

    Args:
        share (str):
        authorization (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetProtocolShareResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            share=share,
            client=client,
            authorization=authorization,
        )
    ).parsed
