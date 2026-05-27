from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.connection_info import ConnectionInfo
from ...models.create_connection import CreateConnection
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response


def _get_kwargs(
    *,
    body: CreateConnection,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/2.1/unity-catalog/connections",
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
    *,
    client: AuthenticatedClient | Client,
    body: CreateConnection,
) -> Response[ConnectionInfo | HTTPValidationError]:
    """Create connection

     Create a new federation connection.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        ConnectionInfo: The created connection.

    Args:
        body (CreateConnection): Request body for ``POST /connections``.

            ``name``, ``connection_type``, and ``options`` are required;
            everything else is optional. ``extra="forbid"`` rejects unknown
            fields (including ``id``, ``created_at``, …) with 422 instead of
            silently dropping them — the same bug class soyuz exists to fix.

            ``connection_type`` is a ``Literal`` pinned to the common connector
            set so typos (``POSTGRES`` vs ``POSTGRESQL``) surface at the
            pydantic layer. The DB column is stored as a free string for
            future extensibility — see
            :class:`soyuz_catalog.models.Connection` for the rationale and
            ``DIVERGENCES.md`` for the soyuz-vs-Databricks difference.

            ``options`` is a free-form ``dict[str, str]`` passthrough. soyuz
            does **not** validate per-connector option sets (there is no query
            side to enforce them against) and **does not** encrypt sensitive
            values (``password``, ``token``, …); both postures are documented
            in ``DIVERGENCES.md``.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ConnectionInfo | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: CreateConnection,
) -> ConnectionInfo | HTTPValidationError | None:
    """Create connection

     Create a new federation connection.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        ConnectionInfo: The created connection.

    Args:
        body (CreateConnection): Request body for ``POST /connections``.

            ``name``, ``connection_type``, and ``options`` are required;
            everything else is optional. ``extra="forbid"`` rejects unknown
            fields (including ``id``, ``created_at``, …) with 422 instead of
            silently dropping them — the same bug class soyuz exists to fix.

            ``connection_type`` is a ``Literal`` pinned to the common connector
            set so typos (``POSTGRES`` vs ``POSTGRESQL``) surface at the
            pydantic layer. The DB column is stored as a free string for
            future extensibility — see
            :class:`soyuz_catalog.models.Connection` for the rationale and
            ``DIVERGENCES.md`` for the soyuz-vs-Databricks difference.

            ``options`` is a free-form ``dict[str, str]`` passthrough. soyuz
            does **not** validate per-connector option sets (there is no query
            side to enforce them against) and **does not** encrypt sensitive
            values (``password``, ``token``, …); both postures are documented
            in ``DIVERGENCES.md``.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ConnectionInfo | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateConnection,
) -> Response[ConnectionInfo | HTTPValidationError]:
    """Create connection

     Create a new federation connection.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        ConnectionInfo: The created connection.

    Args:
        body (CreateConnection): Request body for ``POST /connections``.

            ``name``, ``connection_type``, and ``options`` are required;
            everything else is optional. ``extra="forbid"`` rejects unknown
            fields (including ``id``, ``created_at``, …) with 422 instead of
            silently dropping them — the same bug class soyuz exists to fix.

            ``connection_type`` is a ``Literal`` pinned to the common connector
            set so typos (``POSTGRES`` vs ``POSTGRESQL``) surface at the
            pydantic layer. The DB column is stored as a free string for
            future extensibility — see
            :class:`soyuz_catalog.models.Connection` for the rationale and
            ``DIVERGENCES.md`` for the soyuz-vs-Databricks difference.

            ``options`` is a free-form ``dict[str, str]`` passthrough. soyuz
            does **not** validate per-connector option sets (there is no query
            side to enforce them against) and **does not** encrypt sensitive
            values (``password``, ``token``, …); both postures are documented
            in ``DIVERGENCES.md``.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ConnectionInfo | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreateConnection,
) -> ConnectionInfo | HTTPValidationError | None:
    """Create connection

     Create a new federation connection.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        ConnectionInfo: The created connection.

    Args:
        body (CreateConnection): Request body for ``POST /connections``.

            ``name``, ``connection_type``, and ``options`` are required;
            everything else is optional. ``extra="forbid"`` rejects unknown
            fields (including ``id``, ``created_at``, …) with 422 instead of
            silently dropping them — the same bug class soyuz exists to fix.

            ``connection_type`` is a ``Literal`` pinned to the common connector
            set so typos (``POSTGRES`` vs ``POSTGRESQL``) surface at the
            pydantic layer. The DB column is stored as a free string for
            future extensibility — see
            :class:`soyuz_catalog.models.Connection` for the rationale and
            ``DIVERGENCES.md`` for the soyuz-vs-Databricks difference.

            ``options`` is a free-form ``dict[str, str]`` passthrough. soyuz
            does **not** validate per-connector option sets (there is no query
            side to enforce them against) and **does not** encrypt sensitive
            values (``password``, ``token``, …); both postures are documented
            in ``DIVERGENCES.md``.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ConnectionInfo | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
