from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.report_metrics_request import ReportMetricsRequest
from ...types import UNSET, Response


def _get_kwargs(
    catalog: str,
    schema: str,
    table: str,
    *,
    body: ReportMetricsRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/2.1/unity-catalog/delta/v1/catalogs/{catalog}/schemas/{schema}/tables/{table}/metrics".format(
            catalog=quote(str(catalog), safe=""),
            schema=quote(str(schema), safe=""),
            table=quote(str(table), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | HTTPValidationError | None:
    if response.status_code == 204:
        response_204 = cast(Any, None)
        return response_204

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Any | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    catalog: str,
    schema: str,
    table: str,
    *,
    client: AuthenticatedClient | Client,
    body: ReportMetricsRequest,
) -> Response[Any | HTTPValidationError]:
    """Report Delta table metrics

     Accept a metrics report and discard it.

    soyuz has no metrics sink; rejecting these would make every
    Delta write log a client-side error over a non-feature. The
    body is still parsed (a malformed payload surfaces as 422)
    and the path is still probed (an unknown table surfaces as
    404) so well-behaved clients still get a useful error on a
    real bug. ADR-0009.

    Args:
        catalog: Catalog segment.
        schema: Schema segment.
        table: Table segment.
        payload: Validated metrics report body.
        db: Database session dependency.

    Returns:
        Response: Empty 204 body.

    Args:
        catalog (str):
        schema (str):
        table (str):
        body (ReportMetricsRequest): Request body for ``POST .../tables/{table}/metrics``.

            soyuz parses the body (so a malformed payload surfaces as 422)
            and then discards it — there is no metrics sink in the project.
            The 204 response is accept-and-discard; ADR-0009 explains why
            this beats 501 for Delta client compatibility.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        catalog=catalog,
        schema=schema,
        table=table,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    catalog: str,
    schema: str,
    table: str,
    *,
    client: AuthenticatedClient | Client,
    body: ReportMetricsRequest,
) -> Any | HTTPValidationError | None:
    """Report Delta table metrics

     Accept a metrics report and discard it.

    soyuz has no metrics sink; rejecting these would make every
    Delta write log a client-side error over a non-feature. The
    body is still parsed (a malformed payload surfaces as 422)
    and the path is still probed (an unknown table surfaces as
    404) so well-behaved clients still get a useful error on a
    real bug. ADR-0009.

    Args:
        catalog: Catalog segment.
        schema: Schema segment.
        table: Table segment.
        payload: Validated metrics report body.
        db: Database session dependency.

    Returns:
        Response: Empty 204 body.

    Args:
        catalog (str):
        schema (str):
        table (str):
        body (ReportMetricsRequest): Request body for ``POST .../tables/{table}/metrics``.

            soyuz parses the body (so a malformed payload surfaces as 422)
            and then discards it — there is no metrics sink in the project.
            The 204 response is accept-and-discard; ADR-0009 explains why
            this beats 501 for Delta client compatibility.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError
    """

    return sync_detailed(
        catalog=catalog,
        schema=schema,
        table=table,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    catalog: str,
    schema: str,
    table: str,
    *,
    client: AuthenticatedClient | Client,
    body: ReportMetricsRequest,
) -> Response[Any | HTTPValidationError]:
    """Report Delta table metrics

     Accept a metrics report and discard it.

    soyuz has no metrics sink; rejecting these would make every
    Delta write log a client-side error over a non-feature. The
    body is still parsed (a malformed payload surfaces as 422)
    and the path is still probed (an unknown table surfaces as
    404) so well-behaved clients still get a useful error on a
    real bug. ADR-0009.

    Args:
        catalog: Catalog segment.
        schema: Schema segment.
        table: Table segment.
        payload: Validated metrics report body.
        db: Database session dependency.

    Returns:
        Response: Empty 204 body.

    Args:
        catalog (str):
        schema (str):
        table (str):
        body (ReportMetricsRequest): Request body for ``POST .../tables/{table}/metrics``.

            soyuz parses the body (so a malformed payload surfaces as 422)
            and then discards it — there is no metrics sink in the project.
            The 204 response is accept-and-discard; ADR-0009 explains why
            this beats 501 for Delta client compatibility.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        catalog=catalog,
        schema=schema,
        table=table,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    catalog: str,
    schema: str,
    table: str,
    *,
    client: AuthenticatedClient | Client,
    body: ReportMetricsRequest,
) -> Any | HTTPValidationError | None:
    """Report Delta table metrics

     Accept a metrics report and discard it.

    soyuz has no metrics sink; rejecting these would make every
    Delta write log a client-side error over a non-feature. The
    body is still parsed (a malformed payload surfaces as 422)
    and the path is still probed (an unknown table surfaces as
    404) so well-behaved clients still get a useful error on a
    real bug. ADR-0009.

    Args:
        catalog: Catalog segment.
        schema: Schema segment.
        table: Table segment.
        payload: Validated metrics report body.
        db: Database session dependency.

    Returns:
        Response: Empty 204 body.

    Args:
        catalog (str):
        schema (str):
        table (str):
        body (ReportMetricsRequest): Request body for ``POST .../tables/{table}/metrics``.

            soyuz parses the body (so a malformed payload surfaces as 422)
            and then discards it — there is no metrics sink in the project.
            The 204 response is accept-and-discard; ADR-0009 explains why
            this beats 501 for Delta client compatibility.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            catalog=catalog,
            schema=schema,
            table=table,
            client=client,
            body=body,
        )
    ).parsed
