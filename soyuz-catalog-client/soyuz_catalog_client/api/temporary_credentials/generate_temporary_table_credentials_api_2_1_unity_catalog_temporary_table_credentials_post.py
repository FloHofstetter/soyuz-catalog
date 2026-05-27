from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.generate_temporary_table_credential import (
    GenerateTemporaryTableCredential,
)
from ...models.http_validation_error import HTTPValidationError
from ...models.temporary_credentials import TemporaryCredentials
from ...types import UNSET, Response


def _get_kwargs(
    *,
    body: GenerateTemporaryTableCredential,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/2.1/unity-catalog/temporary-table-credentials",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | TemporaryCredentials | None:
    if response.status_code == 200:
        response_200 = TemporaryCredentials.from_dict(response.json())

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
) -> Response[HTTPValidationError | TemporaryCredentials]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: GenerateTemporaryTableCredential,
) -> Response[HTTPValidationError | TemporaryCredentials]:
    """Vend temporary table credentials

     Generate temporary credentials for a table.

    Args:
        payload: Request body with ``table_id`` and ``operation``.
        db: Database session dependency.

    Returns:
        TemporaryCredentials: Stub response with only ``expiration_time``
            populated. See ``DIVERGENCES.md`` for why cloud-specific
            fields are never populated (metadata-only design).

    Args:
        body (GenerateTemporaryTableCredential): Request body for ``POST /temporary-table-
            credentials``.

            The UC spec addresses the table by its opaque ``table_id`` rather than
            its ``full_name`` because credentials are scoped to the physical
            storage identity, not the namespace path: a rename of the parent
            catalog or schema must not invalidate an outstanding credential.

            ``operation`` is a tri-state enum in the spec
            (``UNKNOWN_TABLE_OPERATION``, ``READ``, ``READ_WRITE``). We accept the
            two real values via :class:`typing.Literal` so a typo surfaces as 422
            at the Pydantic layer and reject ``UNKNOWN_TABLE_OPERATION`` at the
            service layer as an invalid request — the sentinel exists in the spec
            only as a protobuf default and accepting it here would reproduce the
            same silently-accept-garbage behaviour that ``extra="forbid"`` is
            everywhere else written to prevent (see ``DIVERGENCES.md``).

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TemporaryCredentials]
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
    body: GenerateTemporaryTableCredential,
) -> HTTPValidationError | TemporaryCredentials | None:
    """Vend temporary table credentials

     Generate temporary credentials for a table.

    Args:
        payload: Request body with ``table_id`` and ``operation``.
        db: Database session dependency.

    Returns:
        TemporaryCredentials: Stub response with only ``expiration_time``
            populated. See ``DIVERGENCES.md`` for why cloud-specific
            fields are never populated (metadata-only design).

    Args:
        body (GenerateTemporaryTableCredential): Request body for ``POST /temporary-table-
            credentials``.

            The UC spec addresses the table by its opaque ``table_id`` rather than
            its ``full_name`` because credentials are scoped to the physical
            storage identity, not the namespace path: a rename of the parent
            catalog or schema must not invalidate an outstanding credential.

            ``operation`` is a tri-state enum in the spec
            (``UNKNOWN_TABLE_OPERATION``, ``READ``, ``READ_WRITE``). We accept the
            two real values via :class:`typing.Literal` so a typo surfaces as 422
            at the Pydantic layer and reject ``UNKNOWN_TABLE_OPERATION`` at the
            service layer as an invalid request — the sentinel exists in the spec
            only as a protobuf default and accepting it here would reproduce the
            same silently-accept-garbage behaviour that ``extra="forbid"`` is
            everywhere else written to prevent (see ``DIVERGENCES.md``).

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TemporaryCredentials
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: GenerateTemporaryTableCredential,
) -> Response[HTTPValidationError | TemporaryCredentials]:
    """Vend temporary table credentials

     Generate temporary credentials for a table.

    Args:
        payload: Request body with ``table_id`` and ``operation``.
        db: Database session dependency.

    Returns:
        TemporaryCredentials: Stub response with only ``expiration_time``
            populated. See ``DIVERGENCES.md`` for why cloud-specific
            fields are never populated (metadata-only design).

    Args:
        body (GenerateTemporaryTableCredential): Request body for ``POST /temporary-table-
            credentials``.

            The UC spec addresses the table by its opaque ``table_id`` rather than
            its ``full_name`` because credentials are scoped to the physical
            storage identity, not the namespace path: a rename of the parent
            catalog or schema must not invalidate an outstanding credential.

            ``operation`` is a tri-state enum in the spec
            (``UNKNOWN_TABLE_OPERATION``, ``READ``, ``READ_WRITE``). We accept the
            two real values via :class:`typing.Literal` so a typo surfaces as 422
            at the Pydantic layer and reject ``UNKNOWN_TABLE_OPERATION`` at the
            service layer as an invalid request — the sentinel exists in the spec
            only as a protobuf default and accepting it here would reproduce the
            same silently-accept-garbage behaviour that ``extra="forbid"`` is
            everywhere else written to prevent (see ``DIVERGENCES.md``).

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TemporaryCredentials]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: GenerateTemporaryTableCredential,
) -> HTTPValidationError | TemporaryCredentials | None:
    """Vend temporary table credentials

     Generate temporary credentials for a table.

    Args:
        payload: Request body with ``table_id`` and ``operation``.
        db: Database session dependency.

    Returns:
        TemporaryCredentials: Stub response with only ``expiration_time``
            populated. See ``DIVERGENCES.md`` for why cloud-specific
            fields are never populated (metadata-only design).

    Args:
        body (GenerateTemporaryTableCredential): Request body for ``POST /temporary-table-
            credentials``.

            The UC spec addresses the table by its opaque ``table_id`` rather than
            its ``full_name`` because credentials are scoped to the physical
            storage identity, not the namespace path: a rename of the parent
            catalog or schema must not invalidate an outstanding credential.

            ``operation`` is a tri-state enum in the spec
            (``UNKNOWN_TABLE_OPERATION``, ``READ``, ``READ_WRITE``). We accept the
            two real values via :class:`typing.Literal` so a typo surfaces as 422
            at the Pydantic layer and reject ``UNKNOWN_TABLE_OPERATION`` at the
            service layer as an invalid request — the sentinel exists in the spec
            only as a protobuf default and accepting it here would reproduce the
            same silently-accept-garbage behaviour that ``extra="forbid"`` is
            everywhere else written to prevent (see ``DIVERGENCES.md``).

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TemporaryCredentials
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
