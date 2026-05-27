from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.update_table_request import UpdateTableRequest
from ...types import UNSET, Response


def _get_kwargs(
    catalog: str,
    schema: str,
    table: str,
    *,
    body: UpdateTableRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/2.1/unity-catalog/delta/v1/catalogs/{catalog}/schemas/{schema}/tables/{table}".format(
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
) -> HTTPValidationError | None:
    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[HTTPValidationError]:
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
    body: UpdateTableRequest,
) -> Response[HTTPValidationError]:
    """Update Delta table

     Apply a batch of updates to a table.

    Args:
        catalog: Catalog segment.
        schema: Schema segment.
        table: Table segment.
        payload: Validated update request body. Requirements run
            first and a failure short-circuits with 409; updates
            are applied in order and commit-coordinator actions
            surface as 501.
        db: Database session dependency.

    Returns:
        LoadTableResponse: Post-update state with the bumped etag.

    Args:
        catalog (str):
        schema (str):
        table (str):
        body (UpdateTableRequest): Request body for ``POST .../tables/{table}``.

            Pre-conditions in ``requirements`` are validated first and a
            failure on any of them short-circuits the whole batch with 409
            before any mutation runs. Updates in ``updates`` are applied in
            order; a 501 on a commit-coordinator action (``add-commit`` et
            al.) happens at the very first such entry, leaving earlier
            entries in place — consistent with Delta's own
            "append-only commit" story for the parts that are applied and
            soyuz' "fail fast on unsupported" posture everywhere else.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError]
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
    body: UpdateTableRequest,
) -> HTTPValidationError | None:
    """Update Delta table

     Apply a batch of updates to a table.

    Args:
        catalog: Catalog segment.
        schema: Schema segment.
        table: Table segment.
        payload: Validated update request body. Requirements run
            first and a failure short-circuits with 409; updates
            are applied in order and commit-coordinator actions
            surface as 501.
        db: Database session dependency.

    Returns:
        LoadTableResponse: Post-update state with the bumped etag.

    Args:
        catalog (str):
        schema (str):
        table (str):
        body (UpdateTableRequest): Request body for ``POST .../tables/{table}``.

            Pre-conditions in ``requirements`` are validated first and a
            failure on any of them short-circuits the whole batch with 409
            before any mutation runs. Updates in ``updates`` are applied in
            order; a 501 on a commit-coordinator action (``add-commit`` et
            al.) happens at the very first such entry, leaving earlier
            entries in place — consistent with Delta's own
            "append-only commit" story for the parts that are applied and
            soyuz' "fail fast on unsupported" posture everywhere else.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError
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
    body: UpdateTableRequest,
) -> Response[HTTPValidationError]:
    """Update Delta table

     Apply a batch of updates to a table.

    Args:
        catalog: Catalog segment.
        schema: Schema segment.
        table: Table segment.
        payload: Validated update request body. Requirements run
            first and a failure short-circuits with 409; updates
            are applied in order and commit-coordinator actions
            surface as 501.
        db: Database session dependency.

    Returns:
        LoadTableResponse: Post-update state with the bumped etag.

    Args:
        catalog (str):
        schema (str):
        table (str):
        body (UpdateTableRequest): Request body for ``POST .../tables/{table}``.

            Pre-conditions in ``requirements`` are validated first and a
            failure on any of them short-circuits the whole batch with 409
            before any mutation runs. Updates in ``updates`` are applied in
            order; a 501 on a commit-coordinator action (``add-commit`` et
            al.) happens at the very first such entry, leaving earlier
            entries in place — consistent with Delta's own
            "append-only commit" story for the parts that are applied and
            soyuz' "fail fast on unsupported" posture everywhere else.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError]
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
    body: UpdateTableRequest,
) -> HTTPValidationError | None:
    """Update Delta table

     Apply a batch of updates to a table.

    Args:
        catalog: Catalog segment.
        schema: Schema segment.
        table: Table segment.
        payload: Validated update request body. Requirements run
            first and a failure short-circuits with 409; updates
            are applied in order and commit-coordinator actions
            surface as 501.
        db: Database session dependency.

    Returns:
        LoadTableResponse: Post-update state with the bumped etag.

    Args:
        catalog (str):
        schema (str):
        table (str):
        body (UpdateTableRequest): Request body for ``POST .../tables/{table}``.

            Pre-conditions in ``requirements`` are validated first and a
            failure on any of them short-circuits the whole batch with 409
            before any mutation runs. Updates in ``updates`` are applied in
            order; a 501 on a commit-coordinator action (``add-commit`` et
            al.) happens at the very first such entry, leaving earlier
            entries in place — consistent with Delta's own
            "append-only commit" story for the parts that are applied and
            soyuz' "fail fast on unsupported" posture everywhere else.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError
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
