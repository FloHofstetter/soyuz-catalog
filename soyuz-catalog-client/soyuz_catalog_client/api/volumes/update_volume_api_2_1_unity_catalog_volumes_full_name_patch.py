from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.update_volume import UpdateVolume
from ...models.volume_info import VolumeInfo
from ...types import UNSET, Response


def _get_kwargs(
    full_name: str,
    *,
    body: UpdateVolume,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/api/2.1/unity-catalog/volumes/{full_name}".format(
            full_name=quote(str(full_name), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | VolumeInfo | None:
    if response.status_code == 200:
        response_200 = VolumeInfo.from_dict(response.json())

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
) -> Response[HTTPValidationError | VolumeInfo]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    full_name: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateVolume,
) -> Response[HTTPValidationError | VolumeInfo]:
    r"""Update volume

     Update an existing volume.

    The UC spec restricts volume updates to ``new_name`` and ``comment``
    only; the request schema's ``extra=\"forbid\"`` rejects any other
    field with HTTP 422.

    Args:
        full_name: Current ``catalog.schema.volume`` path parameter.
        payload: Patch body. Only fields explicitly present are applied.
        db: Database session dependency.

    Returns:
        VolumeInfo: The updated volume.

    Args:
        full_name (str):
        body (UpdateVolume): Request body for ``PATCH /volumes/{name}``.

            The UC spec is explicit that *only* ``new_name`` and ``comment`` may
            be updated on a volume — ``storage_location`` and ``volume_type`` are
            immutable (a managed volume cannot become external mid-life, and the
            underlying storage path cannot be moved without re-registering the
            volume). Volumes have no ``properties`` field on the wire, so there
            is no PATCH path for them either.

            ``extra="forbid"`` rejects unknown or read-only fields (including
            ``storage_location``, ``volume_type``, ``owner``, ``catalog_name``)
            with HTTP 422 instead of silently dropping them.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | VolumeInfo]
    """

    kwargs = _get_kwargs(
        full_name=full_name,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    full_name: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateVolume,
) -> HTTPValidationError | VolumeInfo | None:
    r"""Update volume

     Update an existing volume.

    The UC spec restricts volume updates to ``new_name`` and ``comment``
    only; the request schema's ``extra=\"forbid\"`` rejects any other
    field with HTTP 422.

    Args:
        full_name: Current ``catalog.schema.volume`` path parameter.
        payload: Patch body. Only fields explicitly present are applied.
        db: Database session dependency.

    Returns:
        VolumeInfo: The updated volume.

    Args:
        full_name (str):
        body (UpdateVolume): Request body for ``PATCH /volumes/{name}``.

            The UC spec is explicit that *only* ``new_name`` and ``comment`` may
            be updated on a volume — ``storage_location`` and ``volume_type`` are
            immutable (a managed volume cannot become external mid-life, and the
            underlying storage path cannot be moved without re-registering the
            volume). Volumes have no ``properties`` field on the wire, so there
            is no PATCH path for them either.

            ``extra="forbid"`` rejects unknown or read-only fields (including
            ``storage_location``, ``volume_type``, ``owner``, ``catalog_name``)
            with HTTP 422 instead of silently dropping them.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | VolumeInfo
    """

    return sync_detailed(
        full_name=full_name,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    full_name: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateVolume,
) -> Response[HTTPValidationError | VolumeInfo]:
    r"""Update volume

     Update an existing volume.

    The UC spec restricts volume updates to ``new_name`` and ``comment``
    only; the request schema's ``extra=\"forbid\"`` rejects any other
    field with HTTP 422.

    Args:
        full_name: Current ``catalog.schema.volume`` path parameter.
        payload: Patch body. Only fields explicitly present are applied.
        db: Database session dependency.

    Returns:
        VolumeInfo: The updated volume.

    Args:
        full_name (str):
        body (UpdateVolume): Request body for ``PATCH /volumes/{name}``.

            The UC spec is explicit that *only* ``new_name`` and ``comment`` may
            be updated on a volume — ``storage_location`` and ``volume_type`` are
            immutable (a managed volume cannot become external mid-life, and the
            underlying storage path cannot be moved without re-registering the
            volume). Volumes have no ``properties`` field on the wire, so there
            is no PATCH path for them either.

            ``extra="forbid"`` rejects unknown or read-only fields (including
            ``storage_location``, ``volume_type``, ``owner``, ``catalog_name``)
            with HTTP 422 instead of silently dropping them.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | VolumeInfo]
    """

    kwargs = _get_kwargs(
        full_name=full_name,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    full_name: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateVolume,
) -> HTTPValidationError | VolumeInfo | None:
    r"""Update volume

     Update an existing volume.

    The UC spec restricts volume updates to ``new_name`` and ``comment``
    only; the request schema's ``extra=\"forbid\"`` rejects any other
    field with HTTP 422.

    Args:
        full_name: Current ``catalog.schema.volume`` path parameter.
        payload: Patch body. Only fields explicitly present are applied.
        db: Database session dependency.

    Returns:
        VolumeInfo: The updated volume.

    Args:
        full_name (str):
        body (UpdateVolume): Request body for ``PATCH /volumes/{name}``.

            The UC spec is explicit that *only* ``new_name`` and ``comment`` may
            be updated on a volume — ``storage_location`` and ``volume_type`` are
            immutable (a managed volume cannot become external mid-life, and the
            underlying storage path cannot be moved without re-registering the
            volume). Volumes have no ``properties`` field on the wire, so there
            is no PATCH path for them either.

            ``extra="forbid"`` rejects unknown or read-only fields (including
            ``storage_location``, ``volume_type``, ``owner``, ``catalog_name``)
            with HTTP 422 instead of silently dropping them.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | VolumeInfo
    """

    return (
        await asyncio_detailed(
            full_name=full_name,
            client=client,
            body=body,
        )
    ).parsed
