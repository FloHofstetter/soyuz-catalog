from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.add_share_object import AddShareObject
from ...models.http_validation_error import HTTPValidationError
from ...models.share_info import ShareInfo
from ...types import UNSET, Response


def _get_kwargs(
    name: str,
    *,
    body: AddShareObject,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/2.1/unity-catalog/shares/{name}/objects".format(
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
    body: AddShareObject,
) -> Response[HTTPValidationError | ShareInfo]:
    """Add table to share

     Place an existing table inside a share.

    Args:
        name: Share name.
        payload: The table reference and optional ``shared_as`` alias.
        db: Database session dependency.

    Returns:
        ShareInfo: The share with its post-add object list.

    Args:
        name (str):
        body (AddShareObject): Request body for ``POST /shares/{name}/objects``.

            ``table_full_name`` must resolve to an existing table at add time
            (404 otherwise). ``shared_as`` optionally re-homes the table
            inside the share's namespace as a two-part ``schema.table`` alias;
            when absent the protocol placement derives from the table's own
            schema and table name segments.

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
    body: AddShareObject,
) -> HTTPValidationError | ShareInfo | None:
    """Add table to share

     Place an existing table inside a share.

    Args:
        name: Share name.
        payload: The table reference and optional ``shared_as`` alias.
        db: Database session dependency.

    Returns:
        ShareInfo: The share with its post-add object list.

    Args:
        name (str):
        body (AddShareObject): Request body for ``POST /shares/{name}/objects``.

            ``table_full_name`` must resolve to an existing table at add time
            (404 otherwise). ``shared_as`` optionally re-homes the table
            inside the share's namespace as a two-part ``schema.table`` alias;
            when absent the protocol placement derives from the table's own
            schema and table name segments.

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
    body: AddShareObject,
) -> Response[HTTPValidationError | ShareInfo]:
    """Add table to share

     Place an existing table inside a share.

    Args:
        name: Share name.
        payload: The table reference and optional ``shared_as`` alias.
        db: Database session dependency.

    Returns:
        ShareInfo: The share with its post-add object list.

    Args:
        name (str):
        body (AddShareObject): Request body for ``POST /shares/{name}/objects``.

            ``table_full_name`` must resolve to an existing table at add time
            (404 otherwise). ``shared_as`` optionally re-homes the table
            inside the share's namespace as a two-part ``schema.table`` alias;
            when absent the protocol placement derives from the table's own
            schema and table name segments.

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
    body: AddShareObject,
) -> HTTPValidationError | ShareInfo | None:
    """Add table to share

     Place an existing table inside a share.

    Args:
        name: Share name.
        payload: The table reference and optional ``shared_as`` alias.
        db: Database session dependency.

    Returns:
        ShareInfo: The share with its post-add object list.

    Args:
        name (str):
        body (AddShareObject): Request body for ``POST /shares/{name}/objects``.

            ``table_full_name`` must resolve to an existing table at add time
            (404 otherwise). ``shared_as`` optionally re-homes the table
            inside the share's namespace as a two-part ``schema.table`` alias;
            when absent the protocol placement derives from the table's own
            schema and table name segments.

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
