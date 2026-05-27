from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.list_audit_log_audit_log_get_response_200_item import (
    ListAuditLogAuditLogGetResponse200Item,
)
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    agent_run_id: None | str | Unset = UNSET,
    limit: int | Unset = 200,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    json_agent_run_id: None | str | Unset
    if isinstance(agent_run_id, Unset):
        json_agent_run_id = UNSET
    else:
        json_agent_run_id = agent_run_id
    params["agent_run_id"] = json_agent_run_id

    params["limit"] = limit

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/audit-log",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | list[ListAuditLogAuditLogGetResponse200Item] | None:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = ListAuditLogAuditLogGetResponse200Item.from_dict(
                response_200_item_data
            )

            response_200.append(response_200_item)

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
) -> Response[HTTPValidationError | list[ListAuditLogAuditLogGetResponse200Item]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    agent_run_id: None | str | Unset = UNSET,
    limit: int | Unset = 200,
) -> Response[HTTPValidationError | list[ListAuditLogAuditLogGetResponse200Item]]:
    """List audit log entries

     Return audit rows, optionally scoped to one agent run.

    Args:
        agent_run_id: Optional ``X-Agent-Run-Id`` filter.  When
            ``None`` returns the most recent ``limit`` rows across
            all runs (operator-style view).
        limit: Hard row cap (1-1000, default 200).
        db: Database session dependency.

    Returns:
        list[dict[str, Any]]: List of dicts — one per ``audit_log``
        row, ordered most-recent first when no ``agent_run_id``
        filter is set, oldest-first inside a single run.

    Args:
        agent_run_id (None | str | Unset):
        limit (int | Unset):  Default: 200.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | list[ListAuditLogAuditLogGetResponse200Item]]
    """

    kwargs = _get_kwargs(
        agent_run_id=agent_run_id,
        limit=limit,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    agent_run_id: None | str | Unset = UNSET,
    limit: int | Unset = 200,
) -> HTTPValidationError | list[ListAuditLogAuditLogGetResponse200Item] | None:
    """List audit log entries

     Return audit rows, optionally scoped to one agent run.

    Args:
        agent_run_id: Optional ``X-Agent-Run-Id`` filter.  When
            ``None`` returns the most recent ``limit`` rows across
            all runs (operator-style view).
        limit: Hard row cap (1-1000, default 200).
        db: Database session dependency.

    Returns:
        list[dict[str, Any]]: List of dicts — one per ``audit_log``
        row, ordered most-recent first when no ``agent_run_id``
        filter is set, oldest-first inside a single run.

    Args:
        agent_run_id (None | str | Unset):
        limit (int | Unset):  Default: 200.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | list[ListAuditLogAuditLogGetResponse200Item]
    """

    return sync_detailed(
        client=client,
        agent_run_id=agent_run_id,
        limit=limit,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    agent_run_id: None | str | Unset = UNSET,
    limit: int | Unset = 200,
) -> Response[HTTPValidationError | list[ListAuditLogAuditLogGetResponse200Item]]:
    """List audit log entries

     Return audit rows, optionally scoped to one agent run.

    Args:
        agent_run_id: Optional ``X-Agent-Run-Id`` filter.  When
            ``None`` returns the most recent ``limit`` rows across
            all runs (operator-style view).
        limit: Hard row cap (1-1000, default 200).
        db: Database session dependency.

    Returns:
        list[dict[str, Any]]: List of dicts — one per ``audit_log``
        row, ordered most-recent first when no ``agent_run_id``
        filter is set, oldest-first inside a single run.

    Args:
        agent_run_id (None | str | Unset):
        limit (int | Unset):  Default: 200.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | list[ListAuditLogAuditLogGetResponse200Item]]
    """

    kwargs = _get_kwargs(
        agent_run_id=agent_run_id,
        limit=limit,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    agent_run_id: None | str | Unset = UNSET,
    limit: int | Unset = 200,
) -> HTTPValidationError | list[ListAuditLogAuditLogGetResponse200Item] | None:
    """List audit log entries

     Return audit rows, optionally scoped to one agent run.

    Args:
        agent_run_id: Optional ``X-Agent-Run-Id`` filter.  When
            ``None`` returns the most recent ``limit`` rows across
            all runs (operator-style view).
        limit: Hard row cap (1-1000, default 200).
        db: Database session dependency.

    Returns:
        list[dict[str, Any]]: List of dicts — one per ``audit_log``
        row, ordered most-recent first when no ``agent_run_id``
        filter is set, oldest-first inside a single run.

    Args:
        agent_run_id (None | str | Unset):
        limit (int | Unset):  Default: 200.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | list[ListAuditLogAuditLogGetResponse200Item]
    """

    return (
        await asyncio_detailed(
            client=client,
            agent_run_id=agent_run_id,
            limit=limit,
        )
    ).parsed
