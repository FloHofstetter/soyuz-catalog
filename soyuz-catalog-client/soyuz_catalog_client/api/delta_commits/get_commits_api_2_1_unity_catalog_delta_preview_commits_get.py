from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.delta_get_commits import DeltaGetCommits
from ...models.delta_get_commits_response import DeltaGetCommitsResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response


def _get_kwargs(
    *,
    body: DeltaGetCommits,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/2.1/unity-catalog/delta/preview/commits",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DeltaGetCommitsResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = DeltaGetCommitsResponse.from_dict(response.json())

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
) -> Response[DeltaGetCommitsResponse | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: DeltaGetCommits,
) -> Response[DeltaGetCommitsResponse | HTTPValidationError]:
    """List unbackfilled Delta commits

     List unbackfilled Delta commits for a registered table.

    Args:
        payload: Request body with ``table_id``, ``table_uri``,
            ``start_version``, and optional ``end_version``.
        db: Database session dependency.

    Returns:
        DeltaGetCommitsResponse: The rows tracked by the coordinator
            in ``[start_version, end_version]`` plus the current
            ``latest_table_version``.

    Args:
        body (DeltaGetCommits): Request body for ``GET /delta/preview/commits``.

            The UC OpenAPI spec models this endpoint as a GET-with-body — unusual
            but unambiguous — so the request shape is a Pydantic model rather than
            query parameters. ``table_id`` and ``table_uri`` must both be present:
            the spec requires the server to reject a request whose ``table_uri``
            does not match the currently-registered storage location of
            ``table_id``, so sending one without the other is a client bug.
            ``start_version`` bounds the returned row set inclusively from below;
            ``end_version`` bounds it inclusively from above when present.

            Per ADR-0011 the coordinator tracks unbackfilled commits, so
            ``start_version`` and ``end_version`` carry a real filtering
            role. See :mod:`soyuz_catalog.services.delta_commits_service`
            for how the service applies them.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DeltaGetCommitsResponse | HTTPValidationError]
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
    body: DeltaGetCommits,
) -> DeltaGetCommitsResponse | HTTPValidationError | None:
    """List unbackfilled Delta commits

     List unbackfilled Delta commits for a registered table.

    Args:
        payload: Request body with ``table_id``, ``table_uri``,
            ``start_version``, and optional ``end_version``.
        db: Database session dependency.

    Returns:
        DeltaGetCommitsResponse: The rows tracked by the coordinator
            in ``[start_version, end_version]`` plus the current
            ``latest_table_version``.

    Args:
        body (DeltaGetCommits): Request body for ``GET /delta/preview/commits``.

            The UC OpenAPI spec models this endpoint as a GET-with-body — unusual
            but unambiguous — so the request shape is a Pydantic model rather than
            query parameters. ``table_id`` and ``table_uri`` must both be present:
            the spec requires the server to reject a request whose ``table_uri``
            does not match the currently-registered storage location of
            ``table_id``, so sending one without the other is a client bug.
            ``start_version`` bounds the returned row set inclusively from below;
            ``end_version`` bounds it inclusively from above when present.

            Per ADR-0011 the coordinator tracks unbackfilled commits, so
            ``start_version`` and ``end_version`` carry a real filtering
            role. See :mod:`soyuz_catalog.services.delta_commits_service`
            for how the service applies them.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DeltaGetCommitsResponse | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: DeltaGetCommits,
) -> Response[DeltaGetCommitsResponse | HTTPValidationError]:
    """List unbackfilled Delta commits

     List unbackfilled Delta commits for a registered table.

    Args:
        payload: Request body with ``table_id``, ``table_uri``,
            ``start_version``, and optional ``end_version``.
        db: Database session dependency.

    Returns:
        DeltaGetCommitsResponse: The rows tracked by the coordinator
            in ``[start_version, end_version]`` plus the current
            ``latest_table_version``.

    Args:
        body (DeltaGetCommits): Request body for ``GET /delta/preview/commits``.

            The UC OpenAPI spec models this endpoint as a GET-with-body — unusual
            but unambiguous — so the request shape is a Pydantic model rather than
            query parameters. ``table_id`` and ``table_uri`` must both be present:
            the spec requires the server to reject a request whose ``table_uri``
            does not match the currently-registered storage location of
            ``table_id``, so sending one without the other is a client bug.
            ``start_version`` bounds the returned row set inclusively from below;
            ``end_version`` bounds it inclusively from above when present.

            Per ADR-0011 the coordinator tracks unbackfilled commits, so
            ``start_version`` and ``end_version`` carry a real filtering
            role. See :mod:`soyuz_catalog.services.delta_commits_service`
            for how the service applies them.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DeltaGetCommitsResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: DeltaGetCommits,
) -> DeltaGetCommitsResponse | HTTPValidationError | None:
    """List unbackfilled Delta commits

     List unbackfilled Delta commits for a registered table.

    Args:
        payload: Request body with ``table_id``, ``table_uri``,
            ``start_version``, and optional ``end_version``.
        db: Database session dependency.

    Returns:
        DeltaGetCommitsResponse: The rows tracked by the coordinator
            in ``[start_version, end_version]`` plus the current
            ``latest_table_version``.

    Args:
        body (DeltaGetCommits): Request body for ``GET /delta/preview/commits``.

            The UC OpenAPI spec models this endpoint as a GET-with-body — unusual
            but unambiguous — so the request shape is a Pydantic model rather than
            query parameters. ``table_id`` and ``table_uri`` must both be present:
            the spec requires the server to reject a request whose ``table_uri``
            does not match the currently-registered storage location of
            ``table_id``, so sending one without the other is a client bug.
            ``start_version`` bounds the returned row set inclusively from below;
            ``end_version`` bounds it inclusively from above when present.

            Per ADR-0011 the coordinator tracks unbackfilled commits, so
            ``start_version`` and ``end_version`` carry a real filtering
            role. See :mod:`soyuz_catalog.services.delta_commits_service`
            for how the service applies them.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DeltaGetCommitsResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
