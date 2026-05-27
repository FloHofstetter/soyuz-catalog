from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.response_delete_registered_model_api_21_unity_catalog_models_full_name_delete import (
    ResponseDeleteRegisteredModelApi21UnityCatalogModelsFullNameDelete,
)
from ...types import UNSET, Response, Unset


def _get_kwargs(
    full_name: str,
    *,
    force: bool | Unset = False,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["force"] = force

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/api/2.1/unity-catalog/models/{full_name}".format(
            full_name=quote(str(full_name), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    HTTPValidationError
    | ResponseDeleteRegisteredModelApi21UnityCatalogModelsFullNameDelete
    | None
):
    if response.status_code == 200:
        response_200 = ResponseDeleteRegisteredModelApi21UnityCatalogModelsFullNameDelete.from_dict(
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
    | ResponseDeleteRegisteredModelApi21UnityCatalogModelsFullNameDelete
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
    force: bool | Unset = False,
) -> Response[
    HTTPValidationError
    | ResponseDeleteRegisteredModelApi21UnityCatalogModelsFullNameDelete
]:
    """Delete registered model

     Delete a registered model.

    Args:
        full_name: ``catalog.schema.model`` path parameter.
        force: Cascade flag. Without ``force``, child model versions
            cause a 409; with ``force=true`` every child version is
            deleted first.
        db: Database session dependency.

    Returns:
        dict[str, str]: Empty success payload.

    Args:
        full_name (str):
        force (bool | Unset):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ResponseDeleteRegisteredModelApi21UnityCatalogModelsFullNameDelete]
    """

    kwargs = _get_kwargs(
        full_name=full_name,
        force=force,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    full_name: str,
    *,
    client: AuthenticatedClient | Client,
    force: bool | Unset = False,
) -> (
    HTTPValidationError
    | ResponseDeleteRegisteredModelApi21UnityCatalogModelsFullNameDelete
    | None
):
    """Delete registered model

     Delete a registered model.

    Args:
        full_name: ``catalog.schema.model`` path parameter.
        force: Cascade flag. Without ``force``, child model versions
            cause a 409; with ``force=true`` every child version is
            deleted first.
        db: Database session dependency.

    Returns:
        dict[str, str]: Empty success payload.

    Args:
        full_name (str):
        force (bool | Unset):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ResponseDeleteRegisteredModelApi21UnityCatalogModelsFullNameDelete
    """

    return sync_detailed(
        full_name=full_name,
        client=client,
        force=force,
    ).parsed


async def asyncio_detailed(
    full_name: str,
    *,
    client: AuthenticatedClient | Client,
    force: bool | Unset = False,
) -> Response[
    HTTPValidationError
    | ResponseDeleteRegisteredModelApi21UnityCatalogModelsFullNameDelete
]:
    """Delete registered model

     Delete a registered model.

    Args:
        full_name: ``catalog.schema.model`` path parameter.
        force: Cascade flag. Without ``force``, child model versions
            cause a 409; with ``force=true`` every child version is
            deleted first.
        db: Database session dependency.

    Returns:
        dict[str, str]: Empty success payload.

    Args:
        full_name (str):
        force (bool | Unset):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ResponseDeleteRegisteredModelApi21UnityCatalogModelsFullNameDelete]
    """

    kwargs = _get_kwargs(
        full_name=full_name,
        force=force,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    full_name: str,
    *,
    client: AuthenticatedClient | Client,
    force: bool | Unset = False,
) -> (
    HTTPValidationError
    | ResponseDeleteRegisteredModelApi21UnityCatalogModelsFullNameDelete
    | None
):
    """Delete registered model

     Delete a registered model.

    Args:
        full_name: ``catalog.schema.model`` path parameter.
        force: Cascade flag. Without ``force``, child model versions
            cause a 409; with ``force=true`` every child version is
            deleted first.
        db: Database session dependency.

    Returns:
        dict[str, str]: Empty success payload.

    Args:
        full_name (str):
        force (bool | Unset):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ResponseDeleteRegisteredModelApi21UnityCatalogModelsFullNameDelete
    """

    return (
        await asyncio_detailed(
            full_name=full_name,
            client=client,
            force=force,
        )
    ).parsed
