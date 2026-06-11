from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.metric_view_info import MetricViewInfo
from ...models.update_metric_view import UpdateMetricView
from ...types import UNSET, Response


def _get_kwargs(
    full_name: str,
    *,
    body: UpdateMetricView,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/api/2.1/unity-catalog/metric-views/{full_name}".format(
            full_name=quote(str(full_name), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | MetricViewInfo | None:
    if response.status_code == 200:
        response_200 = MetricViewInfo.from_dict(response.json())

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
) -> Response[HTTPValidationError | MetricViewInfo]:
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
    body: UpdateMetricView,
) -> Response[HTTPValidationError | MetricViewInfo]:
    """Update metric view

     Update an existing metric view.

    Args:
        full_name: Current ``catalog.schema.metric_view`` full name.
        payload: Patch body. Only fields explicitly present are
            applied; ``spec`` replaces the whole stored definition.
        db: Database session dependency.

    Returns:
        MetricViewInfo: The updated metric view.

    Args:
        full_name (str):
        body (UpdateMetricView): Request body for ``PATCH /metric-views/{full_name}``.

            Replace-style PATCH semantics driven by ``model_fields_set`` in
            the service layer: ``spec`` replaces the whole stored definition
            (a per-dimension merge would have no predictable semantics), and
            an empty body is a no-op. ``new_name`` renames within the same
            schema — moving a metric view across schemas is a
            delete-and-recreate, same posture as every other child resource.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | MetricViewInfo]
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
    body: UpdateMetricView,
) -> HTTPValidationError | MetricViewInfo | None:
    """Update metric view

     Update an existing metric view.

    Args:
        full_name: Current ``catalog.schema.metric_view`` full name.
        payload: Patch body. Only fields explicitly present are
            applied; ``spec`` replaces the whole stored definition.
        db: Database session dependency.

    Returns:
        MetricViewInfo: The updated metric view.

    Args:
        full_name (str):
        body (UpdateMetricView): Request body for ``PATCH /metric-views/{full_name}``.

            Replace-style PATCH semantics driven by ``model_fields_set`` in
            the service layer: ``spec`` replaces the whole stored definition
            (a per-dimension merge would have no predictable semantics), and
            an empty body is a no-op. ``new_name`` renames within the same
            schema — moving a metric view across schemas is a
            delete-and-recreate, same posture as every other child resource.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | MetricViewInfo
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
    body: UpdateMetricView,
) -> Response[HTTPValidationError | MetricViewInfo]:
    """Update metric view

     Update an existing metric view.

    Args:
        full_name: Current ``catalog.schema.metric_view`` full name.
        payload: Patch body. Only fields explicitly present are
            applied; ``spec`` replaces the whole stored definition.
        db: Database session dependency.

    Returns:
        MetricViewInfo: The updated metric view.

    Args:
        full_name (str):
        body (UpdateMetricView): Request body for ``PATCH /metric-views/{full_name}``.

            Replace-style PATCH semantics driven by ``model_fields_set`` in
            the service layer: ``spec`` replaces the whole stored definition
            (a per-dimension merge would have no predictable semantics), and
            an empty body is a no-op. ``new_name`` renames within the same
            schema — moving a metric view across schemas is a
            delete-and-recreate, same posture as every other child resource.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | MetricViewInfo]
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
    body: UpdateMetricView,
) -> HTTPValidationError | MetricViewInfo | None:
    """Update metric view

     Update an existing metric view.

    Args:
        full_name: Current ``catalog.schema.metric_view`` full name.
        payload: Patch body. Only fields explicitly present are
            applied; ``spec`` replaces the whole stored definition.
        db: Database session dependency.

    Returns:
        MetricViewInfo: The updated metric view.

    Args:
        full_name (str):
        body (UpdateMetricView): Request body for ``PATCH /metric-views/{full_name}``.

            Replace-style PATCH semantics driven by ``model_fields_set`` in
            the service layer: ``spec`` replaces the whole stored definition
            (a per-dimension merge would have no predictable semantics), and
            an empty body is a no-op. ``new_name`` renames within the same
            schema — moving a metric view across schemas is a
            delete-and-recreate, same posture as every other child resource.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | MetricViewInfo
    """

    return (
        await asyncio_detailed(
            full_name=full_name,
            client=client,
            body=body,
        )
    ).parsed
