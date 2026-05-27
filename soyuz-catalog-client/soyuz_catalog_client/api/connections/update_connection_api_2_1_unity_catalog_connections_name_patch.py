from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.connection_info import ConnectionInfo
from ...models.http_validation_error import HTTPValidationError
from ...models.update_connection import UpdateConnection
from ...types import UNSET, Response


def _get_kwargs(
    name: str,
    *,
    body: UpdateConnection,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/api/2.1/unity-catalog/connections/{name}".format(
            name=quote(str(name), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ConnectionInfo | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = ConnectionInfo.from_dict(response.json())

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
) -> Response[ConnectionInfo | HTTPValidationError]:
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
    body: UpdateConnection,
) -> Response[ConnectionInfo | HTTPValidationError]:
    """Update connection

     Update an existing connection.

    Args:
        name: Current connection name.
        payload: Patch body. Only fields explicitly present are applied;
            ``options={}`` clears the options dict.
        db: Database session dependency.

    Returns:
        ConnectionInfo: The updated connection.

    Args:
        name (str):
        body (UpdateConnection): Request body for ``PATCH /connections/{name}``.

            Replace-style PATCH semantics driven by ``model_fields_set`` in
            the service layer. ``connection_type`` is **not** exposed: flipping
            a live connection from Postgres to Snowflake would orphan every
            bound foreign catalog's ``options`` dictionary, so it is frozen at
            create time. ``new_name`` renames propagate to every bound foreign
            catalog automatically because the catalog row stores
            ``connection_id`` and reconstructs ``connection_name`` at response
            time.

            ``extra="forbid"`` rejects read-only fields (``id``, ``created_at``,
            …) with 422.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ConnectionInfo | HTTPValidationError]
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
    body: UpdateConnection,
) -> ConnectionInfo | HTTPValidationError | None:
    """Update connection

     Update an existing connection.

    Args:
        name: Current connection name.
        payload: Patch body. Only fields explicitly present are applied;
            ``options={}`` clears the options dict.
        db: Database session dependency.

    Returns:
        ConnectionInfo: The updated connection.

    Args:
        name (str):
        body (UpdateConnection): Request body for ``PATCH /connections/{name}``.

            Replace-style PATCH semantics driven by ``model_fields_set`` in
            the service layer. ``connection_type`` is **not** exposed: flipping
            a live connection from Postgres to Snowflake would orphan every
            bound foreign catalog's ``options`` dictionary, so it is frozen at
            create time. ``new_name`` renames propagate to every bound foreign
            catalog automatically because the catalog row stores
            ``connection_id`` and reconstructs ``connection_name`` at response
            time.

            ``extra="forbid"`` rejects read-only fields (``id``, ``created_at``,
            …) with 422.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ConnectionInfo | HTTPValidationError
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
    body: UpdateConnection,
) -> Response[ConnectionInfo | HTTPValidationError]:
    """Update connection

     Update an existing connection.

    Args:
        name: Current connection name.
        payload: Patch body. Only fields explicitly present are applied;
            ``options={}`` clears the options dict.
        db: Database session dependency.

    Returns:
        ConnectionInfo: The updated connection.

    Args:
        name (str):
        body (UpdateConnection): Request body for ``PATCH /connections/{name}``.

            Replace-style PATCH semantics driven by ``model_fields_set`` in
            the service layer. ``connection_type`` is **not** exposed: flipping
            a live connection from Postgres to Snowflake would orphan every
            bound foreign catalog's ``options`` dictionary, so it is frozen at
            create time. ``new_name`` renames propagate to every bound foreign
            catalog automatically because the catalog row stores
            ``connection_id`` and reconstructs ``connection_name`` at response
            time.

            ``extra="forbid"`` rejects read-only fields (``id``, ``created_at``,
            …) with 422.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ConnectionInfo | HTTPValidationError]
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
    body: UpdateConnection,
) -> ConnectionInfo | HTTPValidationError | None:
    """Update connection

     Update an existing connection.

    Args:
        name: Current connection name.
        payload: Patch body. Only fields explicitly present are applied;
            ``options={}`` clears the options dict.
        db: Database session dependency.

    Returns:
        ConnectionInfo: The updated connection.

    Args:
        name (str):
        body (UpdateConnection): Request body for ``PATCH /connections/{name}``.

            Replace-style PATCH semantics driven by ``model_fields_set`` in
            the service layer. ``connection_type`` is **not** exposed: flipping
            a live connection from Postgres to Snowflake would orphan every
            bound foreign catalog's ``options`` dictionary, so it is frozen at
            create time. ``new_name`` renames propagate to every bound foreign
            catalog automatically because the catalog row stores
            ``connection_id`` and reconstructs ``connection_name`` at response
            time.

            ``extra="forbid"`` rejects read-only fields (``id``, ``created_at``,
            …) with 422.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ConnectionInfo | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
            body=body,
        )
    ).parsed
