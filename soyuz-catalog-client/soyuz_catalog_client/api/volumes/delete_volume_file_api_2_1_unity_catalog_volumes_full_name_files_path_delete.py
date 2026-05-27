from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.response_delete_volume_file_api_21_unity_catalog_volumes_full_name_files_path_delete import (
    ResponseDeleteVolumeFileApi21UnityCatalogVolumesFullNameFilesPathDelete,
)
from ...types import UNSET, Response


def _get_kwargs(
    full_name: str,
    path: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/api/2.1/unity-catalog/volumes/{full_name}/files/{path}".format(
            full_name=quote(str(full_name), safe=""),
            path=quote(str(path), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    HTTPValidationError
    | ResponseDeleteVolumeFileApi21UnityCatalogVolumesFullNameFilesPathDelete
    | None
):
    if response.status_code == 200:
        response_200 = ResponseDeleteVolumeFileApi21UnityCatalogVolumesFullNameFilesPathDelete.from_dict(
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
    | ResponseDeleteVolumeFileApi21UnityCatalogVolumesFullNameFilesPathDelete
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    full_name: str,
    path: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    HTTPValidationError
    | ResponseDeleteVolumeFileApi21UnityCatalogVolumesFullNameFilesPathDelete
]:
    """Delete file from volume

     Remove a file from the volume.

    Args:
        full_name: Dotted UC identifier.
        path: Volume-relative path to remove.
        db: DB session dependency.

    Returns:
        dict[str, bool]: Dict with a single ``deleted`` boolean flag.

    Args:
        full_name (str):
        path (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ResponseDeleteVolumeFileApi21UnityCatalogVolumesFullNameFilesPathDelete]
    """

    kwargs = _get_kwargs(
        full_name=full_name,
        path=path,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    full_name: str,
    path: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    HTTPValidationError
    | ResponseDeleteVolumeFileApi21UnityCatalogVolumesFullNameFilesPathDelete
    | None
):
    """Delete file from volume

     Remove a file from the volume.

    Args:
        full_name: Dotted UC identifier.
        path: Volume-relative path to remove.
        db: DB session dependency.

    Returns:
        dict[str, bool]: Dict with a single ``deleted`` boolean flag.

    Args:
        full_name (str):
        path (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ResponseDeleteVolumeFileApi21UnityCatalogVolumesFullNameFilesPathDelete
    """

    return sync_detailed(
        full_name=full_name,
        path=path,
        client=client,
    ).parsed


async def asyncio_detailed(
    full_name: str,
    path: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    HTTPValidationError
    | ResponseDeleteVolumeFileApi21UnityCatalogVolumesFullNameFilesPathDelete
]:
    """Delete file from volume

     Remove a file from the volume.

    Args:
        full_name: Dotted UC identifier.
        path: Volume-relative path to remove.
        db: DB session dependency.

    Returns:
        dict[str, bool]: Dict with a single ``deleted`` boolean flag.

    Args:
        full_name (str):
        path (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ResponseDeleteVolumeFileApi21UnityCatalogVolumesFullNameFilesPathDelete]
    """

    kwargs = _get_kwargs(
        full_name=full_name,
        path=path,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    full_name: str,
    path: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    HTTPValidationError
    | ResponseDeleteVolumeFileApi21UnityCatalogVolumesFullNameFilesPathDelete
    | None
):
    """Delete file from volume

     Remove a file from the volume.

    Args:
        full_name: Dotted UC identifier.
        path: Volume-relative path to remove.
        db: DB session dependency.

    Returns:
        dict[str, bool]: Dict with a single ``deleted`` boolean flag.

    Args:
        full_name (str):
        path (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ResponseDeleteVolumeFileApi21UnityCatalogVolumesFullNameFilesPathDelete
    """

    return (
        await asyncio_detailed(
            full_name=full_name,
            path=path,
            client=client,
        )
    ).parsed
