from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_metric_view import CreateMetricView
from ...models.http_validation_error import HTTPValidationError
from ...models.metric_view_info import MetricViewInfo
from ...types import UNSET, Response


def _get_kwargs(
    *,
    body: CreateMetricView,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/2.1/unity-catalog/metric-views",
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
    *,
    client: AuthenticatedClient | Client,
    body: CreateMetricView,
) -> Response[HTTPValidationError | MetricViewInfo]:
    """Create metric view

     Create a new metric view under an existing schema.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        MetricViewInfo: The created metric view.

    Args:
        body (CreateMetricView): Request body for ``POST /metric-views``.

            ``source_table_full_name`` must be a syntactically valid
            three-part name but is *not* resolved against the tables surface
            — a metric view may be authored before its source table is
            registered, exactly like a SQL view body referencing a yet-to-be
            created table. The parent catalog and schema, by contrast, must
            exist (404 otherwise). ``extra="forbid"`` rejects unknown fields
            with 422 instead of silently dropping them.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | MetricViewInfo]
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
    body: CreateMetricView,
) -> HTTPValidationError | MetricViewInfo | None:
    """Create metric view

     Create a new metric view under an existing schema.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        MetricViewInfo: The created metric view.

    Args:
        body (CreateMetricView): Request body for ``POST /metric-views``.

            ``source_table_full_name`` must be a syntactically valid
            three-part name but is *not* resolved against the tables surface
            — a metric view may be authored before its source table is
            registered, exactly like a SQL view body referencing a yet-to-be
            created table. The parent catalog and schema, by contrast, must
            exist (404 otherwise). ``extra="forbid"`` rejects unknown fields
            with 422 instead of silently dropping them.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | MetricViewInfo
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateMetricView,
) -> Response[HTTPValidationError | MetricViewInfo]:
    """Create metric view

     Create a new metric view under an existing schema.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        MetricViewInfo: The created metric view.

    Args:
        body (CreateMetricView): Request body for ``POST /metric-views``.

            ``source_table_full_name`` must be a syntactically valid
            three-part name but is *not* resolved against the tables surface
            — a metric view may be authored before its source table is
            registered, exactly like a SQL view body referencing a yet-to-be
            created table. The parent catalog and schema, by contrast, must
            exist (404 otherwise). ``extra="forbid"`` rejects unknown fields
            with 422 instead of silently dropping them.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | MetricViewInfo]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreateMetricView,
) -> HTTPValidationError | MetricViewInfo | None:
    """Create metric view

     Create a new metric view under an existing schema.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        MetricViewInfo: The created metric view.

    Args:
        body (CreateMetricView): Request body for ``POST /metric-views``.

            ``source_table_full_name`` must be a syntactically valid
            three-part name but is *not* resolved against the tables surface
            — a metric view may be authored before its source table is
            registered, exactly like a SQL view body referencing a yet-to-be
            created table. The parent catalog and schema, by contrast, must
            exist (404 otherwise). ``extra="forbid"`` rejects unknown fields
            with 422 instead of silently dropping them.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | MetricViewInfo
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
