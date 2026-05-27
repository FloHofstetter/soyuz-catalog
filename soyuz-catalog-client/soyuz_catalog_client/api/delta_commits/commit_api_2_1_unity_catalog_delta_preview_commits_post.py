from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.delta_commit import DeltaCommit
from ...models.delta_commit_response import DeltaCommitResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response


def _get_kwargs(
    *,
    body: DeltaCommit,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/2.1/unity-catalog/delta/preview/commits",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DeltaCommitResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = DeltaCommitResponse.from_dict(response.json())

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
) -> Response[DeltaCommitResponse | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: DeltaCommit,
) -> Response[DeltaCommitResponse | HTTPValidationError]:
    """Register Delta commit or acknowledge backfill

     Register an unbackfilled Delta commit and/or acknowledge a backfill.

    The request body may carry a ``commit_info`` (new commit
    registration), a ``latest_backfilled_version`` (acknowledgement
    that the client has published everything up to that version), or
    both in a single call. At least one must be present — the schema-
    level validator on :class:`DeltaCommit` rejects an empty request
    with a 422 before the service is invoked. Full semantics live in
    :func:`soyuz_catalog.services.delta_commits_service.commit` and
    ADR-0011.

    Args:
        payload: Validated request body.
        db: Database session dependency.

    Returns:
        DeltaCommitResponse: The spec-mandated empty object. Success
            is communicated entirely through the HTTP status.

    Args:
        body (DeltaCommit): Request body for ``POST /delta/preview/commits``.

            Request shape for the passthrough Delta commit coordinator
            (ADR-0011). The request fuses two conceptually
            independent operations the Delta Kernel client may send in a
            single call: a **commit** registration (``commit_info`` set,
            carrying the metadata of a freshly-staged ``_delta_log/.tmp/``
            file) and a **backfill acknowledgement** (``latest_backfilled_version``
            set, signalling that the client has published everything up to
            that version and the coordinator can prune). Either field, or
            both, may be present — the spec's ``oneOf-ish`` requirement is
            enforced by :meth:`_require_at_least_one_action` below and
            re-checked defensively in
            :func:`soyuz_catalog.services.delta_commits_service.commit`.

            ``metadata`` and ``uniform`` are accepted as opaque pass-through
            dicts: the upstream protocol forwards them to downstream Delta
            Kernel consumers (protocol upgrades, Iceberg conversion hints)
            and soyuz stores neither. Their shapes are not pinned on this
            side because doing so would couple soyuz to a Kernel-side
            contract that evolves independently and does not participate in
            the `all.yaml` conformance test.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DeltaCommitResponse | HTTPValidationError]
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
    body: DeltaCommit,
) -> DeltaCommitResponse | HTTPValidationError | None:
    """Register Delta commit or acknowledge backfill

     Register an unbackfilled Delta commit and/or acknowledge a backfill.

    The request body may carry a ``commit_info`` (new commit
    registration), a ``latest_backfilled_version`` (acknowledgement
    that the client has published everything up to that version), or
    both in a single call. At least one must be present — the schema-
    level validator on :class:`DeltaCommit` rejects an empty request
    with a 422 before the service is invoked. Full semantics live in
    :func:`soyuz_catalog.services.delta_commits_service.commit` and
    ADR-0011.

    Args:
        payload: Validated request body.
        db: Database session dependency.

    Returns:
        DeltaCommitResponse: The spec-mandated empty object. Success
            is communicated entirely through the HTTP status.

    Args:
        body (DeltaCommit): Request body for ``POST /delta/preview/commits``.

            Request shape for the passthrough Delta commit coordinator
            (ADR-0011). The request fuses two conceptually
            independent operations the Delta Kernel client may send in a
            single call: a **commit** registration (``commit_info`` set,
            carrying the metadata of a freshly-staged ``_delta_log/.tmp/``
            file) and a **backfill acknowledgement** (``latest_backfilled_version``
            set, signalling that the client has published everything up to
            that version and the coordinator can prune). Either field, or
            both, may be present — the spec's ``oneOf-ish`` requirement is
            enforced by :meth:`_require_at_least_one_action` below and
            re-checked defensively in
            :func:`soyuz_catalog.services.delta_commits_service.commit`.

            ``metadata`` and ``uniform`` are accepted as opaque pass-through
            dicts: the upstream protocol forwards them to downstream Delta
            Kernel consumers (protocol upgrades, Iceberg conversion hints)
            and soyuz stores neither. Their shapes are not pinned on this
            side because doing so would couple soyuz to a Kernel-side
            contract that evolves independently and does not participate in
            the `all.yaml` conformance test.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DeltaCommitResponse | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: DeltaCommit,
) -> Response[DeltaCommitResponse | HTTPValidationError]:
    """Register Delta commit or acknowledge backfill

     Register an unbackfilled Delta commit and/or acknowledge a backfill.

    The request body may carry a ``commit_info`` (new commit
    registration), a ``latest_backfilled_version`` (acknowledgement
    that the client has published everything up to that version), or
    both in a single call. At least one must be present — the schema-
    level validator on :class:`DeltaCommit` rejects an empty request
    with a 422 before the service is invoked. Full semantics live in
    :func:`soyuz_catalog.services.delta_commits_service.commit` and
    ADR-0011.

    Args:
        payload: Validated request body.
        db: Database session dependency.

    Returns:
        DeltaCommitResponse: The spec-mandated empty object. Success
            is communicated entirely through the HTTP status.

    Args:
        body (DeltaCommit): Request body for ``POST /delta/preview/commits``.

            Request shape for the passthrough Delta commit coordinator
            (ADR-0011). The request fuses two conceptually
            independent operations the Delta Kernel client may send in a
            single call: a **commit** registration (``commit_info`` set,
            carrying the metadata of a freshly-staged ``_delta_log/.tmp/``
            file) and a **backfill acknowledgement** (``latest_backfilled_version``
            set, signalling that the client has published everything up to
            that version and the coordinator can prune). Either field, or
            both, may be present — the spec's ``oneOf-ish`` requirement is
            enforced by :meth:`_require_at_least_one_action` below and
            re-checked defensively in
            :func:`soyuz_catalog.services.delta_commits_service.commit`.

            ``metadata`` and ``uniform`` are accepted as opaque pass-through
            dicts: the upstream protocol forwards them to downstream Delta
            Kernel consumers (protocol upgrades, Iceberg conversion hints)
            and soyuz stores neither. Their shapes are not pinned on this
            side because doing so would couple soyuz to a Kernel-side
            contract that evolves independently and does not participate in
            the `all.yaml` conformance test.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DeltaCommitResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: DeltaCommit,
) -> DeltaCommitResponse | HTTPValidationError | None:
    """Register Delta commit or acknowledge backfill

     Register an unbackfilled Delta commit and/or acknowledge a backfill.

    The request body may carry a ``commit_info`` (new commit
    registration), a ``latest_backfilled_version`` (acknowledgement
    that the client has published everything up to that version), or
    both in a single call. At least one must be present — the schema-
    level validator on :class:`DeltaCommit` rejects an empty request
    with a 422 before the service is invoked. Full semantics live in
    :func:`soyuz_catalog.services.delta_commits_service.commit` and
    ADR-0011.

    Args:
        payload: Validated request body.
        db: Database session dependency.

    Returns:
        DeltaCommitResponse: The spec-mandated empty object. Success
            is communicated entirely through the HTTP status.

    Args:
        body (DeltaCommit): Request body for ``POST /delta/preview/commits``.

            Request shape for the passthrough Delta commit coordinator
            (ADR-0011). The request fuses two conceptually
            independent operations the Delta Kernel client may send in a
            single call: a **commit** registration (``commit_info`` set,
            carrying the metadata of a freshly-staged ``_delta_log/.tmp/``
            file) and a **backfill acknowledgement** (``latest_backfilled_version``
            set, signalling that the client has published everything up to
            that version and the coordinator can prune). Either field, or
            both, may be present — the spec's ``oneOf-ish`` requirement is
            enforced by :meth:`_require_at_least_one_action` below and
            re-checked defensively in
            :func:`soyuz_catalog.services.delta_commits_service.commit`.

            ``metadata`` and ``uniform`` are accepted as opaque pass-through
            dicts: the upstream protocol forwards them to downstream Delta
            Kernel consumers (protocol upgrades, Iceberg conversion hints)
            and soyuz stores neither. Their shapes are not pinned on this
            side because doing so would couple soyuz to a Kernel-side
            contract that evolves independently and does not participate in
            the `all.yaml` conformance test.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DeltaCommitResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
