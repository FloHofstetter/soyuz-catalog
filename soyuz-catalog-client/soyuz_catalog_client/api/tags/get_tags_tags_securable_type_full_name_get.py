from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_tags_tags_securable_type_full_name_get_securable_type import (
    GetTagsTagsSecurableTypeFullNameGetSecurableType,
)
from ...models.http_validation_error import HTTPValidationError
from ...models.tag_list import TagList
from ...types import UNSET, Response


def _get_kwargs(
    securable_type: GetTagsTagsSecurableTypeFullNameGetSecurableType,
    full_name: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/tags/{securable_type}/{full_name}".format(
            securable_type=quote(str(securable_type), safe=""),
            full_name=quote(str(full_name), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | TagList | None:
    if response.status_code == 200:
        response_200 = TagList.from_dict(response.json())

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
) -> Response[HTTPValidationError | TagList]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    securable_type: GetTagsTagsSecurableTypeFullNameGetSecurableType,
    full_name: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[HTTPValidationError | TagList]:
    r"""Get tags for securable

     Return the current tag set of a securable.

    The response shape is identical to the ``PATCH`` response so clients
    can reuse the same deserialiser. Tags are sorted by key, and an empty
    result returns ``{\"tags\": []}`` rather than 404 — the absence of tags
    is a valid state, not an error.

    Args:
        securable_type: One of ``catalog``, ``schema``, ``table``, ``column``.
            Narrower than the full UC ``SecurableType`` enum (MVP scope —
            see ADR-0010).
        full_name: Dotted address of the securable. 1 segment for catalog,
            2 for schema, 3 for table, 4 for column.
        db: Database session dependency.

    Returns:
        TagList: The current tag set, sorted by key.

    Args:
        securable_type (GetTagsTagsSecurableTypeFullNameGetSecurableType):
        full_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TagList]
    """

    kwargs = _get_kwargs(
        securable_type=securable_type,
        full_name=full_name,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    securable_type: GetTagsTagsSecurableTypeFullNameGetSecurableType,
    full_name: str,
    *,
    client: AuthenticatedClient | Client,
) -> HTTPValidationError | TagList | None:
    r"""Get tags for securable

     Return the current tag set of a securable.

    The response shape is identical to the ``PATCH`` response so clients
    can reuse the same deserialiser. Tags are sorted by key, and an empty
    result returns ``{\"tags\": []}`` rather than 404 — the absence of tags
    is a valid state, not an error.

    Args:
        securable_type: One of ``catalog``, ``schema``, ``table``, ``column``.
            Narrower than the full UC ``SecurableType`` enum (MVP scope —
            see ADR-0010).
        full_name: Dotted address of the securable. 1 segment for catalog,
            2 for schema, 3 for table, 4 for column.
        db: Database session dependency.

    Returns:
        TagList: The current tag set, sorted by key.

    Args:
        securable_type (GetTagsTagsSecurableTypeFullNameGetSecurableType):
        full_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TagList
    """

    return sync_detailed(
        securable_type=securable_type,
        full_name=full_name,
        client=client,
    ).parsed


async def asyncio_detailed(
    securable_type: GetTagsTagsSecurableTypeFullNameGetSecurableType,
    full_name: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[HTTPValidationError | TagList]:
    r"""Get tags for securable

     Return the current tag set of a securable.

    The response shape is identical to the ``PATCH`` response so clients
    can reuse the same deserialiser. Tags are sorted by key, and an empty
    result returns ``{\"tags\": []}`` rather than 404 — the absence of tags
    is a valid state, not an error.

    Args:
        securable_type: One of ``catalog``, ``schema``, ``table``, ``column``.
            Narrower than the full UC ``SecurableType`` enum (MVP scope —
            see ADR-0010).
        full_name: Dotted address of the securable. 1 segment for catalog,
            2 for schema, 3 for table, 4 for column.
        db: Database session dependency.

    Returns:
        TagList: The current tag set, sorted by key.

    Args:
        securable_type (GetTagsTagsSecurableTypeFullNameGetSecurableType):
        full_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TagList]
    """

    kwargs = _get_kwargs(
        securable_type=securable_type,
        full_name=full_name,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    securable_type: GetTagsTagsSecurableTypeFullNameGetSecurableType,
    full_name: str,
    *,
    client: AuthenticatedClient | Client,
) -> HTTPValidationError | TagList | None:
    r"""Get tags for securable

     Return the current tag set of a securable.

    The response shape is identical to the ``PATCH`` response so clients
    can reuse the same deserialiser. Tags are sorted by key, and an empty
    result returns ``{\"tags\": []}`` rather than 404 — the absence of tags
    is a valid state, not an error.

    Args:
        securable_type: One of ``catalog``, ``schema``, ``table``, ``column``.
            Narrower than the full UC ``SecurableType`` enum (MVP scope —
            see ADR-0010).
        full_name: Dotted address of the securable. 1 segment for catalog,
            2 for schema, 3 for table, 4 for column.
        db: Database session dependency.

    Returns:
        TagList: The current tag set, sorted by key.

    Args:
        securable_type (GetTagsTagsSecurableTypeFullNameGetSecurableType):
        full_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TagList
    """

    return (
        await asyncio_detailed(
            securable_type=securable_type,
            full_name=full_name,
            client=client,
        )
    ).parsed
