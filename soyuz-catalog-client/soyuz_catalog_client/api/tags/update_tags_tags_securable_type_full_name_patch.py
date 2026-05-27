from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.tag_list import TagList
from ...models.update_tags import UpdateTags
from ...models.update_tags_tags_securable_type_full_name_patch_securable_type import (
    UpdateTagsTagsSecurableTypeFullNamePatchSecurableType,
)
from ...types import UNSET, Response


def _get_kwargs(
    securable_type: UpdateTagsTagsSecurableTypeFullNamePatchSecurableType,
    full_name: str,
    *,
    body: UpdateTags,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/tags/{securable_type}/{full_name}".format(
            securable_type=quote(str(securable_type), safe=""),
            full_name=quote(str(full_name), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
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
    securable_type: UpdateTagsTagsSecurableTypeFullNamePatchSecurableType,
    full_name: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateTags,
) -> Response[HTTPValidationError | TagList]:
    """Update tags for securable

     Apply an additive batch of set/remove changes to a securable's tags.

    The shape is not replace-style: the client submits set/remove
    operations and the service applies them transactionally. Overlapping
    operations within a single batch resolve as *set wins*
    (``remove key`` followed by ``set key`` ends with the key present) to
    keep multi-writer workflows safe. See
    :func:`soyuz_catalog.services.tags_service.update_tags` for the full
    semantics and ``DIVERGENCES.md`` for the over-the-spec notes.

    Args:
        securable_type: One of ``catalog``, ``schema``, ``table``, ``column``.
        full_name: Dotted address of the securable.
        payload: The batch of changes to apply.
        db: Database session dependency.

    Returns:
        TagList: The full post-change tag set, sorted by key.

    Args:
        securable_type (UpdateTagsTagsSecurableTypeFullNamePatchSecurableType):
        full_name (str):
        body (UpdateTags): Request body for ``PATCH /tags/{securable_type}/{full_name}``.

            Like :class:`UpdatePermissions`, this shape is **not** replace-style: the
            client submits a list of additive/subtractive changes rather than a full
            desired state. This makes multi-writer workflows safe — two clients
            editing disjoint key sets do not clobber each other's tags — and matches
            the Databricks ``UpdateTags`` wire shape. See ``DIVERGENCES.md`` and
            ADR-0010 for the over-the-spec rationale.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TagList]
    """

    kwargs = _get_kwargs(
        securable_type=securable_type,
        full_name=full_name,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    securable_type: UpdateTagsTagsSecurableTypeFullNamePatchSecurableType,
    full_name: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateTags,
) -> HTTPValidationError | TagList | None:
    """Update tags for securable

     Apply an additive batch of set/remove changes to a securable's tags.

    The shape is not replace-style: the client submits set/remove
    operations and the service applies them transactionally. Overlapping
    operations within a single batch resolve as *set wins*
    (``remove key`` followed by ``set key`` ends with the key present) to
    keep multi-writer workflows safe. See
    :func:`soyuz_catalog.services.tags_service.update_tags` for the full
    semantics and ``DIVERGENCES.md`` for the over-the-spec notes.

    Args:
        securable_type: One of ``catalog``, ``schema``, ``table``, ``column``.
        full_name: Dotted address of the securable.
        payload: The batch of changes to apply.
        db: Database session dependency.

    Returns:
        TagList: The full post-change tag set, sorted by key.

    Args:
        securable_type (UpdateTagsTagsSecurableTypeFullNamePatchSecurableType):
        full_name (str):
        body (UpdateTags): Request body for ``PATCH /tags/{securable_type}/{full_name}``.

            Like :class:`UpdatePermissions`, this shape is **not** replace-style: the
            client submits a list of additive/subtractive changes rather than a full
            desired state. This makes multi-writer workflows safe — two clients
            editing disjoint key sets do not clobber each other's tags — and matches
            the Databricks ``UpdateTags`` wire shape. See ``DIVERGENCES.md`` and
            ADR-0010 for the over-the-spec rationale.

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
        body=body,
    ).parsed


async def asyncio_detailed(
    securable_type: UpdateTagsTagsSecurableTypeFullNamePatchSecurableType,
    full_name: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateTags,
) -> Response[HTTPValidationError | TagList]:
    """Update tags for securable

     Apply an additive batch of set/remove changes to a securable's tags.

    The shape is not replace-style: the client submits set/remove
    operations and the service applies them transactionally. Overlapping
    operations within a single batch resolve as *set wins*
    (``remove key`` followed by ``set key`` ends with the key present) to
    keep multi-writer workflows safe. See
    :func:`soyuz_catalog.services.tags_service.update_tags` for the full
    semantics and ``DIVERGENCES.md`` for the over-the-spec notes.

    Args:
        securable_type: One of ``catalog``, ``schema``, ``table``, ``column``.
        full_name: Dotted address of the securable.
        payload: The batch of changes to apply.
        db: Database session dependency.

    Returns:
        TagList: The full post-change tag set, sorted by key.

    Args:
        securable_type (UpdateTagsTagsSecurableTypeFullNamePatchSecurableType):
        full_name (str):
        body (UpdateTags): Request body for ``PATCH /tags/{securable_type}/{full_name}``.

            Like :class:`UpdatePermissions`, this shape is **not** replace-style: the
            client submits a list of additive/subtractive changes rather than a full
            desired state. This makes multi-writer workflows safe — two clients
            editing disjoint key sets do not clobber each other's tags — and matches
            the Databricks ``UpdateTags`` wire shape. See ``DIVERGENCES.md`` and
            ADR-0010 for the over-the-spec rationale.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TagList]
    """

    kwargs = _get_kwargs(
        securable_type=securable_type,
        full_name=full_name,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    securable_type: UpdateTagsTagsSecurableTypeFullNamePatchSecurableType,
    full_name: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateTags,
) -> HTTPValidationError | TagList | None:
    """Update tags for securable

     Apply an additive batch of set/remove changes to a securable's tags.

    The shape is not replace-style: the client submits set/remove
    operations and the service applies them transactionally. Overlapping
    operations within a single batch resolve as *set wins*
    (``remove key`` followed by ``set key`` ends with the key present) to
    keep multi-writer workflows safe. See
    :func:`soyuz_catalog.services.tags_service.update_tags` for the full
    semantics and ``DIVERGENCES.md`` for the over-the-spec notes.

    Args:
        securable_type: One of ``catalog``, ``schema``, ``table``, ``column``.
        full_name: Dotted address of the securable.
        payload: The batch of changes to apply.
        db: Database session dependency.

    Returns:
        TagList: The full post-change tag set, sorted by key.

    Args:
        securable_type (UpdateTagsTagsSecurableTypeFullNamePatchSecurableType):
        full_name (str):
        body (UpdateTags): Request body for ``PATCH /tags/{securable_type}/{full_name}``.

            Like :class:`UpdatePermissions`, this shape is **not** replace-style: the
            client submits a list of additive/subtractive changes rather than a full
            desired state. This makes multi-writer workflows safe — two clients
            editing disjoint key sets do not clobber each other's tags — and matches
            the Databricks ``UpdateTags`` wire shape. See ``DIVERGENCES.md`` and
            ADR-0010 for the over-the-spec rationale.

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
            body=body,
        )
    ).parsed
