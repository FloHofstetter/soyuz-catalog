from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.response_grant_share_api_21_unity_catalog_shares_name_recipients_recipient_name_put import (
    ResponseGrantShareApi21UnityCatalogSharesNameRecipientsRecipientNamePut,
)
from ...types import UNSET, Response


def _get_kwargs(
    name: str,
    recipient_name: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": "/api/2.1/unity-catalog/shares/{name}/recipients/{recipient_name}".format(
            name=quote(str(name), safe=""),
            recipient_name=quote(str(recipient_name), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    HTTPValidationError
    | ResponseGrantShareApi21UnityCatalogSharesNameRecipientsRecipientNamePut
    | None
):
    if response.status_code == 200:
        response_200 = ResponseGrantShareApi21UnityCatalogSharesNameRecipientsRecipientNamePut.from_dict(
            response.json()
        )

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
) -> Response[
    HTTPValidationError
    | ResponseGrantShareApi21UnityCatalogSharesNameRecipientsRecipientNamePut
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    name: str,
    recipient_name: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    HTTPValidationError
    | ResponseGrantShareApi21UnityCatalogSharesNameRecipientsRecipientNamePut
]:
    """Grant share to recipient

     Make a share visible to a recipient (idempotent).

    Args:
        name: Share name.
        recipient_name: Recipient name.
        db: Database session dependency.

    Returns:
        dict[str, str]: Empty success payload.

    Args:
        name (str):
        recipient_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ResponseGrantShareApi21UnityCatalogSharesNameRecipientsRecipientNamePut]
    """

    kwargs = _get_kwargs(
        name=name,
        recipient_name=recipient_name,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    name: str,
    recipient_name: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    HTTPValidationError
    | ResponseGrantShareApi21UnityCatalogSharesNameRecipientsRecipientNamePut
    | None
):
    """Grant share to recipient

     Make a share visible to a recipient (idempotent).

    Args:
        name: Share name.
        recipient_name: Recipient name.
        db: Database session dependency.

    Returns:
        dict[str, str]: Empty success payload.

    Args:
        name (str):
        recipient_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ResponseGrantShareApi21UnityCatalogSharesNameRecipientsRecipientNamePut
    """

    return sync_detailed(
        name=name,
        recipient_name=recipient_name,
        client=client,
    ).parsed


async def asyncio_detailed(
    name: str,
    recipient_name: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    HTTPValidationError
    | ResponseGrantShareApi21UnityCatalogSharesNameRecipientsRecipientNamePut
]:
    """Grant share to recipient

     Make a share visible to a recipient (idempotent).

    Args:
        name: Share name.
        recipient_name: Recipient name.
        db: Database session dependency.

    Returns:
        dict[str, str]: Empty success payload.

    Args:
        name (str):
        recipient_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ResponseGrantShareApi21UnityCatalogSharesNameRecipientsRecipientNamePut]
    """

    kwargs = _get_kwargs(
        name=name,
        recipient_name=recipient_name,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    name: str,
    recipient_name: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    HTTPValidationError
    | ResponseGrantShareApi21UnityCatalogSharesNameRecipientsRecipientNamePut
    | None
):
    """Grant share to recipient

     Make a share visible to a recipient (idempotent).

    Args:
        name: Share name.
        recipient_name: Recipient name.
        db: Database session dependency.

    Returns:
        dict[str, str]: Empty success payload.

    Args:
        name (str):
        recipient_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ResponseGrantShareApi21UnityCatalogSharesNameRecipientsRecipientNamePut
    """

    return (
        await asyncio_detailed(
            name=name,
            recipient_name=recipient_name,
            client=client,
        )
    ).parsed
