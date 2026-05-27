from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.lineage_ingest_response import LineageIngestResponse
from ...models.open_lineage_event import OpenLineageEvent
from ...types import UNSET, Response


def _get_kwargs(
    *,
    body: OpenLineageEvent,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/lineage/v1/events",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | LineageIngestResponse | None:
    if response.status_code == 201:
        response_201 = LineageIngestResponse.from_dict(response.json())

        return response_201

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[HTTPValidationError | LineageIngestResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: OpenLineageEvent,
) -> Response[HTTPValidationError | LineageIngestResponse]:
    """Ingest OpenLineage event

     Ingest one OpenLineage ``RunEvent``.

    The body is validated permissively — OpenLineage facets evolve
    independently of soyuz and the endpoint must not crash producers
    when a new field ships. The service layer extracts the small set
    of fields soyuz actually stores (run id, job name, event time,
    input + output dataset names) and leaves everything else on the
    wire.

    Dataset names that do not resolve to a soyuz table are silently
    dropped and counted in the response — OpenLineage producers
    routinely emit events for tables outside UC and a 400 would make
    soyuz unusable as a drop-in sink.

    Args:
        event: The OpenLineage ``RunEvent`` body.
        db: Database session dependency.

    Returns:
        LineageIngestResponse: ``run_id``, current ``state``, number
            of edges actually inserted on this call, and number of
            dataset references that did not resolve.

    Args:
        body (OpenLineageEvent): An OpenLineage ``RunEvent`` body posted to
            ``/lineage/v1/events``.

            Permissively validated: unknown top-level fields and unknown
            sub-fields are accepted because OpenLineage evolves independently of
            soyuz and the endpoint must not crash producers when a new facet
            ships. The strict-``forbid`` policy still applies to every soyuz
            *response* shape and every spec-sourced request shape; this is the
            only documented exception. See ADR-0008.

            soyuz extracts a small fixed set of fields:

            * ``eventType`` drives the :class:`LineageRun.state` transition.
            * ``eventTime`` (ISO-8601) is parsed to epoch milliseconds and
              stored as ``started_at`` on the first event (``ended_at`` on the
              terminal event).
            * ``run.runId`` is the run primary key.
            * ``job.namespace`` / ``job.name`` populate the run's denormalised
              job columns and ``job.name`` also becomes each edge's
              ``operation`` label.
            * ``inputs`` × ``outputs`` cross product produces
              :class:`LineageEdge` rows, dropping datasets whose names do not
              resolve to an existing soyuz table.
            * Two additional facets are ingested when present on output
              datasets:

              * ``columnLineage`` — OpenLineage 1.x standard.  Each
                ``fields[target_column].inputFields`` entry produces one
                :class:`LineageColumnEdge` row.  ``transformations[0].type``
                (when present) populates ``transformation_type`` verbatim.
              * ``valueChange`` — **non-spec producer extension**, identified
                on the wire by its ``_producer`` URI on the facet payload.
                The body shape is ``{changes: [{rowId, column, oldValue,
                newValue}]}``; one :class:`LineageValueChange` row per
                entry.  soyuz stores the values verbatim and does no
                redaction of its own — producers handling PII are expected
                to redact upstream.  The shape is producer-defined, not
                part of OpenLineage 1.x.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | LineageIngestResponse]
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
    body: OpenLineageEvent,
) -> HTTPValidationError | LineageIngestResponse | None:
    """Ingest OpenLineage event

     Ingest one OpenLineage ``RunEvent``.

    The body is validated permissively — OpenLineage facets evolve
    independently of soyuz and the endpoint must not crash producers
    when a new field ships. The service layer extracts the small set
    of fields soyuz actually stores (run id, job name, event time,
    input + output dataset names) and leaves everything else on the
    wire.

    Dataset names that do not resolve to a soyuz table are silently
    dropped and counted in the response — OpenLineage producers
    routinely emit events for tables outside UC and a 400 would make
    soyuz unusable as a drop-in sink.

    Args:
        event: The OpenLineage ``RunEvent`` body.
        db: Database session dependency.

    Returns:
        LineageIngestResponse: ``run_id``, current ``state``, number
            of edges actually inserted on this call, and number of
            dataset references that did not resolve.

    Args:
        body (OpenLineageEvent): An OpenLineage ``RunEvent`` body posted to
            ``/lineage/v1/events``.

            Permissively validated: unknown top-level fields and unknown
            sub-fields are accepted because OpenLineage evolves independently of
            soyuz and the endpoint must not crash producers when a new facet
            ships. The strict-``forbid`` policy still applies to every soyuz
            *response* shape and every spec-sourced request shape; this is the
            only documented exception. See ADR-0008.

            soyuz extracts a small fixed set of fields:

            * ``eventType`` drives the :class:`LineageRun.state` transition.
            * ``eventTime`` (ISO-8601) is parsed to epoch milliseconds and
              stored as ``started_at`` on the first event (``ended_at`` on the
              terminal event).
            * ``run.runId`` is the run primary key.
            * ``job.namespace`` / ``job.name`` populate the run's denormalised
              job columns and ``job.name`` also becomes each edge's
              ``operation`` label.
            * ``inputs`` × ``outputs`` cross product produces
              :class:`LineageEdge` rows, dropping datasets whose names do not
              resolve to an existing soyuz table.
            * Two additional facets are ingested when present on output
              datasets:

              * ``columnLineage`` — OpenLineage 1.x standard.  Each
                ``fields[target_column].inputFields`` entry produces one
                :class:`LineageColumnEdge` row.  ``transformations[0].type``
                (when present) populates ``transformation_type`` verbatim.
              * ``valueChange`` — **non-spec producer extension**, identified
                on the wire by its ``_producer`` URI on the facet payload.
                The body shape is ``{changes: [{rowId, column, oldValue,
                newValue}]}``; one :class:`LineageValueChange` row per
                entry.  soyuz stores the values verbatim and does no
                redaction of its own — producers handling PII are expected
                to redact upstream.  The shape is producer-defined, not
                part of OpenLineage 1.x.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | LineageIngestResponse
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: OpenLineageEvent,
) -> Response[HTTPValidationError | LineageIngestResponse]:
    """Ingest OpenLineage event

     Ingest one OpenLineage ``RunEvent``.

    The body is validated permissively — OpenLineage facets evolve
    independently of soyuz and the endpoint must not crash producers
    when a new field ships. The service layer extracts the small set
    of fields soyuz actually stores (run id, job name, event time,
    input + output dataset names) and leaves everything else on the
    wire.

    Dataset names that do not resolve to a soyuz table are silently
    dropped and counted in the response — OpenLineage producers
    routinely emit events for tables outside UC and a 400 would make
    soyuz unusable as a drop-in sink.

    Args:
        event: The OpenLineage ``RunEvent`` body.
        db: Database session dependency.

    Returns:
        LineageIngestResponse: ``run_id``, current ``state``, number
            of edges actually inserted on this call, and number of
            dataset references that did not resolve.

    Args:
        body (OpenLineageEvent): An OpenLineage ``RunEvent`` body posted to
            ``/lineage/v1/events``.

            Permissively validated: unknown top-level fields and unknown
            sub-fields are accepted because OpenLineage evolves independently of
            soyuz and the endpoint must not crash producers when a new facet
            ships. The strict-``forbid`` policy still applies to every soyuz
            *response* shape and every spec-sourced request shape; this is the
            only documented exception. See ADR-0008.

            soyuz extracts a small fixed set of fields:

            * ``eventType`` drives the :class:`LineageRun.state` transition.
            * ``eventTime`` (ISO-8601) is parsed to epoch milliseconds and
              stored as ``started_at`` on the first event (``ended_at`` on the
              terminal event).
            * ``run.runId`` is the run primary key.
            * ``job.namespace`` / ``job.name`` populate the run's denormalised
              job columns and ``job.name`` also becomes each edge's
              ``operation`` label.
            * ``inputs`` × ``outputs`` cross product produces
              :class:`LineageEdge` rows, dropping datasets whose names do not
              resolve to an existing soyuz table.
            * Two additional facets are ingested when present on output
              datasets:

              * ``columnLineage`` — OpenLineage 1.x standard.  Each
                ``fields[target_column].inputFields`` entry produces one
                :class:`LineageColumnEdge` row.  ``transformations[0].type``
                (when present) populates ``transformation_type`` verbatim.
              * ``valueChange`` — **non-spec producer extension**, identified
                on the wire by its ``_producer`` URI on the facet payload.
                The body shape is ``{changes: [{rowId, column, oldValue,
                newValue}]}``; one :class:`LineageValueChange` row per
                entry.  soyuz stores the values verbatim and does no
                redaction of its own — producers handling PII are expected
                to redact upstream.  The shape is producer-defined, not
                part of OpenLineage 1.x.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | LineageIngestResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: OpenLineageEvent,
) -> HTTPValidationError | LineageIngestResponse | None:
    """Ingest OpenLineage event

     Ingest one OpenLineage ``RunEvent``.

    The body is validated permissively — OpenLineage facets evolve
    independently of soyuz and the endpoint must not crash producers
    when a new field ships. The service layer extracts the small set
    of fields soyuz actually stores (run id, job name, event time,
    input + output dataset names) and leaves everything else on the
    wire.

    Dataset names that do not resolve to a soyuz table are silently
    dropped and counted in the response — OpenLineage producers
    routinely emit events for tables outside UC and a 400 would make
    soyuz unusable as a drop-in sink.

    Args:
        event: The OpenLineage ``RunEvent`` body.
        db: Database session dependency.

    Returns:
        LineageIngestResponse: ``run_id``, current ``state``, number
            of edges actually inserted on this call, and number of
            dataset references that did not resolve.

    Args:
        body (OpenLineageEvent): An OpenLineage ``RunEvent`` body posted to
            ``/lineage/v1/events``.

            Permissively validated: unknown top-level fields and unknown
            sub-fields are accepted because OpenLineage evolves independently of
            soyuz and the endpoint must not crash producers when a new facet
            ships. The strict-``forbid`` policy still applies to every soyuz
            *response* shape and every spec-sourced request shape; this is the
            only documented exception. See ADR-0008.

            soyuz extracts a small fixed set of fields:

            * ``eventType`` drives the :class:`LineageRun.state` transition.
            * ``eventTime`` (ISO-8601) is parsed to epoch milliseconds and
              stored as ``started_at`` on the first event (``ended_at`` on the
              terminal event).
            * ``run.runId`` is the run primary key.
            * ``job.namespace`` / ``job.name`` populate the run's denormalised
              job columns and ``job.name`` also becomes each edge's
              ``operation`` label.
            * ``inputs`` × ``outputs`` cross product produces
              :class:`LineageEdge` rows, dropping datasets whose names do not
              resolve to an existing soyuz table.
            * Two additional facets are ingested when present on output
              datasets:

              * ``columnLineage`` — OpenLineage 1.x standard.  Each
                ``fields[target_column].inputFields`` entry produces one
                :class:`LineageColumnEdge` row.  ``transformations[0].type``
                (when present) populates ``transformation_type`` verbatim.
              * ``valueChange`` — **non-spec producer extension**, identified
                on the wire by its ``_producer`` URI on the facet payload.
                The body shape is ``{changes: [{rowId, column, oldValue,
                newValue}]}``; one :class:`LineageValueChange` row per
                entry.  soyuz stores the values verbatim and does no
                redaction of its own — producers handling PII are expected
                to redact upstream.  The shape is producer-defined, not
                part of OpenLineage 1.x.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | LineageIngestResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
