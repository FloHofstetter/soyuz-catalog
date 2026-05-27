from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.body_upload_volume_file_api_21_unity_catalog_volumes_full_name_files_post import (
    BodyUploadVolumeFileApi21UnityCatalogVolumesFullNameFilesPost,
)
from ...models.http_validation_error import HTTPValidationError
from ...models.response_upload_volume_file_api_21_unity_catalog_volumes_full_name_files_post import (
    ResponseUploadVolumeFileApi21UnityCatalogVolumesFullNameFilesPost,
)
from ...types import UNSET, Response


def _get_kwargs(
    full_name: str,
    *,
    body: BodyUploadVolumeFileApi21UnityCatalogVolumesFullNameFilesPost,
    path: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    params: dict[str, Any] = {}

    params["path"] = path

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/2.1/unity-catalog/volumes/{full_name}/files".format(
            full_name=quote(str(full_name), safe=""),
        ),
        "params": params,
    }

    _kwargs["files"] = body.to_multipart()

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    HTTPValidationError
    | ResponseUploadVolumeFileApi21UnityCatalogVolumesFullNameFilesPost
    | None
):
    if response.status_code == 200:
        response_200 = (
            ResponseUploadVolumeFileApi21UnityCatalogVolumesFullNameFilesPost.from_dict(
                response.json()
            )
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
    | ResponseUploadVolumeFileApi21UnityCatalogVolumesFullNameFilesPost
]:
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
    body: BodyUploadVolumeFileApi21UnityCatalogVolumesFullNameFilesPost,
    path: str,
) -> Response[
    HTTPValidationError
    | ResponseUploadVolumeFileApi21UnityCatalogVolumesFullNameFilesPost
]:
    """Upload file to volume

     Stream *upload* into the volume at *path*.

    Args:
        full_name: Dotted ``catalog.schema.volume`` identifier.
        path: Volume-relative destination path; enforced to stay
            inside the volume root.
        upload: The ``multipart/form-data`` body carrying the file.
        db: DB session dependency.

    Returns:
        dict[str, object]: Single ``file`` key with the resulting
            entry's JSON shape.

    Args:
        full_name (str):
        path (str): Volume-relative destination path.
        body (BodyUploadVolumeFileApi21UnityCatalogVolumesFullNameFilesPost):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ResponseUploadVolumeFileApi21UnityCatalogVolumesFullNameFilesPost]
    """

    kwargs = _get_kwargs(
        full_name=full_name,
        body=body,
        path=path,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    full_name: str,
    *,
    client: AuthenticatedClient | Client,
    body: BodyUploadVolumeFileApi21UnityCatalogVolumesFullNameFilesPost,
    path: str,
) -> (
    HTTPValidationError
    | ResponseUploadVolumeFileApi21UnityCatalogVolumesFullNameFilesPost
    | None
):
    """Upload file to volume

     Stream *upload* into the volume at *path*.

    Args:
        full_name: Dotted ``catalog.schema.volume`` identifier.
        path: Volume-relative destination path; enforced to stay
            inside the volume root.
        upload: The ``multipart/form-data`` body carrying the file.
        db: DB session dependency.

    Returns:
        dict[str, object]: Single ``file`` key with the resulting
            entry's JSON shape.

    Args:
        full_name (str):
        path (str): Volume-relative destination path.
        body (BodyUploadVolumeFileApi21UnityCatalogVolumesFullNameFilesPost):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ResponseUploadVolumeFileApi21UnityCatalogVolumesFullNameFilesPost
    """

    return sync_detailed(
        full_name=full_name,
        client=client,
        body=body,
        path=path,
    ).parsed


async def asyncio_detailed(
    full_name: str,
    *,
    client: AuthenticatedClient | Client,
    body: BodyUploadVolumeFileApi21UnityCatalogVolumesFullNameFilesPost,
    path: str,
) -> Response[
    HTTPValidationError
    | ResponseUploadVolumeFileApi21UnityCatalogVolumesFullNameFilesPost
]:
    """Upload file to volume

     Stream *upload* into the volume at *path*.

    Args:
        full_name: Dotted ``catalog.schema.volume`` identifier.
        path: Volume-relative destination path; enforced to stay
            inside the volume root.
        upload: The ``multipart/form-data`` body carrying the file.
        db: DB session dependency.

    Returns:
        dict[str, object]: Single ``file`` key with the resulting
            entry's JSON shape.

    Args:
        full_name (str):
        path (str): Volume-relative destination path.
        body (BodyUploadVolumeFileApi21UnityCatalogVolumesFullNameFilesPost):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ResponseUploadVolumeFileApi21UnityCatalogVolumesFullNameFilesPost]
    """

    kwargs = _get_kwargs(
        full_name=full_name,
        body=body,
        path=path,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    full_name: str,
    *,
    client: AuthenticatedClient | Client,
    body: BodyUploadVolumeFileApi21UnityCatalogVolumesFullNameFilesPost,
    path: str,
) -> (
    HTTPValidationError
    | ResponseUploadVolumeFileApi21UnityCatalogVolumesFullNameFilesPost
    | None
):
    """Upload file to volume

     Stream *upload* into the volume at *path*.

    Args:
        full_name: Dotted ``catalog.schema.volume`` identifier.
        path: Volume-relative destination path; enforced to stay
            inside the volume root.
        upload: The ``multipart/form-data`` body carrying the file.
        db: DB session dependency.

    Returns:
        dict[str, object]: Single ``file`` key with the resulting
            entry's JSON shape.

    Args:
        full_name (str):
        path (str): Volume-relative destination path.
        body (BodyUploadVolumeFileApi21UnityCatalogVolumesFullNameFilesPost):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ResponseUploadVolumeFileApi21UnityCatalogVolumesFullNameFilesPost
    """

    return (
        await asyncio_detailed(
            full_name=full_name,
            client=client,
            body=body,
            path=path,
        )
    ).parsed
