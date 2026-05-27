"""Business logic for lineage ingestion and graph traversal.

Lineage is a genuine over-the-spec extension: upstream Unity Catalog
OSS has no lineage at all. soyuz-catalog accepts
OpenLineage events at ``POST /lineage/v1/events`` and exposes
upstream/downstream graph queries keyed on opaque securable ids so
that lineage edges survive parent renames — the same rename-invariance
trick every other resource uses, applied to a brand-new resource that
the spec does not define. See ADR-0008 for the full rationale.

Public entry points:

* :func:`ingest_event` — validate an OpenLineage event, upsert the run
  row, and insert one idempotent edge per (resolved input × resolved
  output) pair.
* :func:`traverse` — walk the edge table in either direction starting
  from a root opaque id, capped at ``depth`` hops. Dialect-aware:
  Postgres uses a recursive CTE, SQLite falls back to an iterative BFS
  in Python.

The MVP intentionally limits the securable types that can appear in a
lineage edge to **tables only**. Volumes, functions, and registered
models all have opaque row ids of the same shape, so extending the
ingestor to accept them is a non-breaking change that will land in a
dedicated sprint when there is a concrete consumer asking.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal

from sqlalchemy import select, text

from soyuz_catalog.api.schemas import (
    LineageEdgeOut,
    LineageGraphResponse,
    LineageIngestResponse,
    LineageNode,
    OpenLineageDataset,
    OpenLineageEvent,
)
from soyuz_catalog.db import commit_or_raise
from soyuz_catalog.exceptions import InvalidRequestError, NotFoundError
from soyuz_catalog.models import (
    Catalog,
    LineageColumnEdge,
    LineageEdge,
    LineageRun,
    LineageValueChange,
    Schema,
    Table,
)
from soyuz_catalog.services import permissions_service

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


# Hard upper bound on traversal depth. Keeps an accidentally-cyclic
# graph or a pathologically deep chain from turning a single GET into
# a full-table scan. Chosen generously — ten hops is well beyond what
# any real pipeline emits — but small enough that the recursive CTE
# stays cheap.
MAX_DEPTH = 10

# OpenLineage lifecycle states soyuz considers *terminal* — i.e. the
# ones that should populate ``ended_at`` on the run row. ``RUNNING``
# and ``OTHER`` leave ``ended_at`` untouched because the run is still
# in flight from OpenLineage' perspective.
_TERMINAL_STATES = frozenset({"COMPLETE", "FAIL", "ABORT"})


def _iso_to_ms(iso: str) -> int:
    """Parse an ISO-8601 timestamp to epoch milliseconds.

    OpenLineage events carry ``eventTime`` as an ISO-8601 string,
    typically with a trailing ``Z`` for UTC. Python's
    :meth:`datetime.fromisoformat` accepts ``+00:00`` but not ``Z`` on
    versions before 3.11; soyuz targets 3.11+ but the ``Z`` rewrite
    here is cheap insurance and keeps the parse deterministic across
    producers.

    Args:
        iso: The ``eventTime`` value from an OpenLineage event.

    Returns:
        int: Unix milliseconds since epoch.

    Raises:
        InvalidRequestError: If the string is not parseable as ISO-8601.
    """
    try:
        normalised = iso.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalised)
    except ValueError as exc:
        raise InvalidRequestError(f"eventTime '{iso}' is not a valid ISO-8601 timestamp") from exc
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return int(dt.timestamp() * 1000)


def _strip_hyphens(run_id: str) -> str:
    """Normalise an OpenLineage ``runId`` to soyuz' 32-hex primary-key shape.

    OpenLineage producers usually emit runIds as canonical UUIDs with
    hyphens; soyuz stores every opaque id as a 32-character hex string
    (:func:`soyuz_catalog.models._new_id`) so the lineage run PK has
    the same shape as every other PK in the catalog.

    Accepts every standard UUID textual representation
    (canonical-with-hyphens, 32-hex unhyphenated, ``urn:uuid:…``,
    ``{…}``-braced) by delegating to :class:`uuid.UUID`.  Returns the
    32-hex normalised form so redeliveries of the same event hit the
    same row regardless of which form the producer used.

    v0.3.0rc2: replaced the old hand-rolled hex-strip+length-check
    with :class:`uuid.UUID`.  The old check rejected ``urn:uuid:…``
    and braced forms even though they are valid UUIDs per RFC 4122,
    and returned an error message that left producers guessing at
    the expected format.  The new implementation is a strict superset
    — non-UUID strings still reject with a clearer message.

    Args:
        run_id: The raw ``run.runId`` from the OpenLineage event.

    Returns:
        str: The 32-hex canonical form suitable for soyuz' PK shape.

    Raises:
        InvalidRequestError: If the value is not a valid UUID in any
            standard representation.
    """
    try:
        return uuid.UUID(run_id).hex
    except (ValueError, AttributeError, TypeError) as exc:
        raise InvalidRequestError(
            f"run.runId must be a valid UUID; received {run_id!r} "
            f"(expected canonical-with-hyphens or 32-hex form, "
            f"e.g. 8ac59c26-7dca-46cf-8281-78fc7e8c58f9)"
        ) from exc


def _resolve_dataset(session: Session, dataset: OpenLineageDataset) -> str | None:
    """Translate one OpenLineage dataset entry into a soyuz table id.

    Soyuz interprets the OpenLineage ``name`` field as a
    ``catalog.schema.table`` full_name and reuses
    :func:`permissions_service.resolve_securable` so that the
    same three-segment rules apply. Any resolution failure — unknown
    catalog, schema, or table, *or* a name that is not three segments
    at all — returns ``None`` instead of propagating. That turns a
    "this dataset is not in UC" event into a silent drop-and-count
    rather than an ingest-wide 400, which is the posture the ADR-0008
    calls out as the soyuz-as-OpenLineage-sink contract.

    ``dataset.namespace`` is intentionally ignored: OpenLineage
    producers use it for the physical storage namespace (``s3://``,
    ``hdfs://``, a JDBC URL, etc.), not for the UC namespace. Mapping
    it would require a second indirection that no producer currently
    supplies.

    Args:
        session: Active SQLAlchemy session, used for the lookup.
        dataset: One entry from ``event.inputs`` or ``event.outputs``.

    Returns:
        str | None: The opaque table id, or ``None`` if the dataset
            does not resolve to a soyuz table.
    """
    try:
        return permissions_service.resolve_securable(session, "table", dataset.name)
    # PEP 758 (Python 3.14+) parenthesis-free except-tuple. ruff-format
    # strips the parens on every run, so the canonical
    # ``except (NotFoundError, InvalidRequestError):`` form cannot be
    # preserved. The two exceptions are both caught — this is *not*
    # ``except A as B``, which is how a pre-3.14 reader might parse it.
    except NotFoundError, InvalidRequestError:
        return None


def ingest_event(session: Session, event: OpenLineageEvent) -> LineageIngestResponse:
    """Upsert a lineage run and insert its idempotent edges.

    The flow is deliberately single-pass so a redelivered event is
    cheap: one ``SELECT`` for the run, a small cross product of
    resolved dataset ids, and one ``INSERT`` per new edge guarded by
    the unique constraint on
    ``(run_id, source_securable_id, target_securable_id)``. Every
    state transition is last-write-wins: OpenLineage producers
    occasionally emit events out of order, and a strict monotonic
    state machine would reject legitimate retries from a restarted
    worker.

    Concretely, per event:

    1. Normalise ``run.runId`` to the soyuz 32-hex shape.
    2. Resolve every input and output dataset to an opaque table id;
       drop the ones that do not resolve and count them so the
       response tells the caller what soyuz ignored.
    3. Upsert the :class:`LineageRun` row. First event sets
       ``started_at`` from the event time; every event overwrites
       ``state``; terminal events also set ``ended_at``.
    4. Compute the cross product of (inputs × outputs), skip pairs
       that already exist for this run, and insert the rest. Duplicate
       events insert zero new rows — the unique constraint fires on
       the pre-check side only, no ``IntegrityError`` rollback needed.
    5. Commit and return a summary.

    An event with zero resolved inputs **or** zero resolved outputs
    still updates the run state (so ``COMPLETE`` without a payload
    still marks the run done) but inserts no edges. That matches the
    "state transitions are cheap" contract of OpenLineage lifecycle
    events.

    Args:
        session: Active SQLAlchemy session.
        event: The validated OpenLineage event body.

    Returns:
        LineageIngestResponse: A summary with the normalised
            ``run_id``, the current ``state``, the number of
            ``accepted_edges`` actually inserted on this call
            (redeliveries report ``0``), and the number of
            ``rejected_datasets`` whose names did not resolve.

    Raises:
        IntegrityError: If a concurrent ingest call races past the
            pre-check ``SELECT`` and collides on the unique
            constraint ``(run_id, source_securable_id,
            target_securable_id)``. Re-raised after rolling back so
            the client can redeliver — same race strategy as every
            other ``create_*`` in the service layer.
            ``InvalidRequestError`` may also propagate from
            :func:`_strip_hyphens` (malformed ``run.runId``) or
            :func:`_iso_to_ms` (unparseable ``eventTime``); both
            surface as 400 ``INVALID_ARGUMENT``.
    """
    run_id = _strip_hyphens(event.run.runId)
    event_ms = _iso_to_ms(event.eventTime)

    input_ids: list[str] = []
    output_ids: list[str] = []
    rejected = 0
    for ds in event.inputs:
        resolved = _resolve_dataset(session, ds)
        if resolved is None:
            rejected += 1
        else:
            input_ids.append(resolved)
    for ds in event.outputs:
        resolved = _resolve_dataset(session, ds)
        if resolved is None:
            rejected += 1
        else:
            output_ids.append(resolved)

    run = session.get(LineageRun, run_id)
    if run is None:
        run = LineageRun(
            id=run_id,
            job_namespace=event.job.namespace,
            job_name=event.job.name,
            state=event.eventType,
            started_at=event_ms,
            ended_at=event_ms if event.eventType in _TERMINAL_STATES else None,
        )
        session.add(run)
    else:
        run.state = event.eventType
        run.job_namespace = event.job.namespace
        run.job_name = event.job.name
        if event.eventType in _TERMINAL_STATES:
            run.ended_at = event_ms

    # Flush so the run row exists for the FK in the edges below and so
    # the pre-check SELECT sees any pre-existing edges from earlier
    # events on the same run id.
    session.flush()

    existing_pairs: set[tuple[str, str]] = {
        (row[0], row[1])
        for row in session.execute(
            select(LineageEdge.source_securable_id, LineageEdge.target_securable_id).where(
                LineageEdge.run_id == run_id,
            ),
        )
    }

    accepted = 0
    for src in input_ids:
        for tgt in output_ids:
            if src == tgt:
                # Self-edges are legal in OpenLineage (a job that
                # reads and writes the same table) but they turn
                # traversal into a cycle with no useful signal, so
                # soyuz drops them. This is documented in ADR-0008.
                continue
            if (src, tgt) in existing_pairs:
                continue
            session.add(
                LineageEdge(
                    run_id=run_id,
                    source_securable_id=src,
                    target_securable_id=tgt,
                    operation=event.job.name,
                ),
            )
            existing_pairs.add((src, tgt))
            accepted += 1

    column_accepted, value_accepted = _ingest_optional_facets(
        session,
        event=event,
        run_id=run_id,
        output_ids=output_ids,
    )

    # Two concurrent ingest calls could race past the pre-check
    # SELECT and collide on the unique constraint. The rollback
    # loses the in-flight edges from *this* call only; the client
    # can redeliver and the second attempt will skip everything.
    with commit_or_raise(session):
        pass

    return LineageIngestResponse(
        run_id=run_id,
        state=event.eventType,
        accepted_edges=accepted,
        rejected_datasets=rejected,
        accepted_column_edges=column_accepted,
        accepted_value_changes=value_accepted,
    )


def _stringify(value: object) -> str | None:
    """Coerce *value* to ``str`` for the value-change ``Text`` columns.

    Args:
        value: Anything the producer placed in ``oldValue`` /
            ``newValue``.  ``None`` round-trips as ``None`` (true SQL
            NULL); strings stay verbatim; other JSON scalars are
            stringified.

    Returns:
        str | None: ``None`` for null input, a ``str`` for everything else.
    """
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return str(value)


def _resolve_dataset_by_name(session: Session, name: str) -> str | None:
    """Resolve a dataset name (``catalog.schema.table``) to a securable id.

    Args:
        session: Active SQLAlchemy session.
        name: Dotted three-part UC name.

    Returns:
        str | None: The opaque table id, or ``None`` when the name
            does not resolve to a soyuz table.
    """
    try:
        return permissions_service.resolve_securable(session, "table", name)
    # PEP 758 — see :func:`_resolve_dataset` for the parens-free idiom.
    except NotFoundError, InvalidRequestError:
        return None


def _ingest_optional_facets(
    session: Session,
    *,
    event: OpenLineageEvent,
    run_id: str,
    output_ids: list[str],
) -> tuple[int, int]:
    """Walk the optional ``columnLineage`` + ``valueChange`` facets.

    Both facets are pulled from each output dataset's ``facets`` map
    via Pydantic's ``model_extra``.  The ``columnLineage`` facet is
    OpenLineage 1.x standard; the ``valueChange`` facet is a
    non-spec producer extension, identified by its ``_producer`` URI.

    Args:
        session: Active SQLAlchemy session.
        event: The validated OpenLineage event body.
        run_id: Normalised run id (already stripped + validated).
        output_ids: Securable ids for the resolved outputs, in
            ``event.outputs`` order.  Used to map per-output facets
            back to the correct target table without re-resolving.

    Returns:
        tuple[int, int]: ``(accepted_column_edges,
            accepted_value_changes)`` — the count of new rows
            actually inserted on this call.
    """
    accepted_columns = 0
    accepted_values = 0

    existing_columns: set[tuple[str, str, str, str]] = {
        (row[0], row[1], row[2], row[3])
        for row in session.execute(
            select(
                LineageColumnEdge.source_securable_id,
                LineageColumnEdge.source_column,
                LineageColumnEdge.target_securable_id,
                LineageColumnEdge.target_column,
            ).where(LineageColumnEdge.run_id == run_id),
        )
    }

    output_index = 0
    for ds in event.outputs:
        resolved = _resolve_dataset(session, ds)
        if resolved is None:
            continue
        target_id = resolved
        output_index = output_ids.index(target_id) if target_id in output_ids else -1
        del output_index  # value not needed; the loop tracks ds → target_id

        extra = (ds.model_extra or {}) if hasattr(ds, "model_extra") else {}
        facets = extra.get("facets") if isinstance(extra, dict) else None
        if not isinstance(facets, dict):
            continue

        column_facet = facets.get("columnLineage")
        if isinstance(column_facet, dict):
            fields = column_facet.get("fields")
            if isinstance(fields, dict):
                for target_column, payload in fields.items():
                    if not isinstance(payload, dict):
                        continue
                    input_fields = payload.get("inputFields")
                    if not isinstance(input_fields, list):
                        continue
                    for input_ref in input_fields:
                        if not isinstance(input_ref, dict):
                            continue
                        source_name = input_ref.get("name")
                        source_column = input_ref.get("field")
                        if not isinstance(source_name, str) or not isinstance(source_column, str):
                            continue
                        source_id = _resolve_dataset_by_name(session, source_name)
                        if source_id is None:
                            continue
                        transforms = input_ref.get("transformations")
                        transform_type: str | None = None
                        if isinstance(transforms, list) and transforms:
                            first = transforms[0]
                            if isinstance(first, dict):
                                t = first.get("type")
                                if isinstance(t, str):
                                    transform_type = t
                        key = (source_id, source_column, target_id, str(target_column))
                        if key in existing_columns:
                            continue
                        session.add(
                            LineageColumnEdge(
                                run_id=run_id,
                                source_securable_id=source_id,
                                source_column=source_column,
                                target_securable_id=target_id,
                                target_column=str(target_column),
                                transformation_type=transform_type,
                            )
                        )
                        existing_columns.add(key)
                        accepted_columns += 1

        value_facet = facets.get("valueChange")
        if isinstance(value_facet, dict):
            changes = value_facet.get("changes")
            if isinstance(changes, list):
                for change in changes:
                    if not isinstance(change, dict):
                        continue
                    row_id_raw = change.get("rowId")
                    column_raw = change.get("column")
                    if not isinstance(row_id_raw, str) or not isinstance(column_raw, str):
                        continue
                    old_value = change.get("oldValue")
                    new_value = change.get("newValue")
                    session.add(
                        LineageValueChange(
                            run_id=run_id,
                            target_securable_id=target_id,
                            target_row_id=row_id_raw,
                            target_column=column_raw,
                            old_value=_stringify(old_value),
                            new_value=_stringify(new_value),
                        )
                    )
                    accepted_values += 1

    return accepted_columns, accepted_values


def _reconstruct_full_names(session: Session, ids: set[str]) -> dict[str, str]:
    """Reverse-map opaque table ids to live ``catalog.schema.table`` strings.

    Edge traversal stores only opaque ids so that parent renames
    propagate for free. At response time we join
    :class:`Table` → :class:`Schema` → :class:`Catalog` to reconstruct
    the current full_name for every id still resolvable. Ids that
    have no matching row — because the underlying table was deleted
    after its edges were recorded — are simply absent from the
    returned map, and the response layer renders them as ``null``.

    Args:
        session: Active SQLAlchemy session.
        ids: The set of opaque table ids to look up. Empty input
            returns an empty map without opening a query.

    Returns:
        dict[str, str]: Mapping from opaque id to ``catalog.schema.table``.
    """
    if not ids:
        return {}
    rows = session.execute(
        select(Table.id, Catalog.name, Schema.name, Table.name)
        .join(Schema, Table.schema_id == Schema.id)
        .join(Catalog, Schema.catalog_id == Catalog.id)
        .where(Table.id.in_(ids)),
    ).all()
    return {tid: f"{cname}.{sname}.{tname}" for tid, cname, sname, tname in rows}


def _traverse_postgres(
    session: Session,
    root_id: str,
    direction: Literal["upstream", "downstream"],
    depth: int,
) -> tuple[list[tuple[str, int]], list[tuple[str, str, str, str | None]]]:
    """Walk the lineage edge table with a Postgres recursive CTE.

    Two queries run back-to-back: first the node CTE (reachable
    securable ids with the minimum depth at which each was reached),
    then the edge CTE (every edge whose source *or* target is a
    reachable node, whichever end matches the walk direction). Both
    are bounded by the ``depth`` parameter to cap work.

    For ``upstream`` the walk follows edges from target back to
    source (who fed this table?); ``downstream`` follows source to
    target (what did this table feed?).

    Args:
        session: Active SQLAlchemy session bound to a Postgres engine.
        root_id: Opaque table id to start the walk from.
        direction: ``"upstream"`` or ``"downstream"``.
        depth: Maximum number of hops to traverse, ``>=1``.

    Returns:
        tuple[list[tuple[str, int]], list[tuple[str, str, str, str | None]]]:
            ``(nodes, edges)``. ``nodes`` is a list of
            ``(securable_id, depth)`` pairs including the root at
            depth 0. ``edges`` is a list of
            ``(source_id, target_id, run_id, operation)`` tuples.
    """
    # The CTE is almost identical in both directions — only the
    # join columns flip — so the direction parameter gets baked into
    # a small SQL fragment rather than a dynamic query builder.
    if direction == "upstream":
        next_col = "source_securable_id"
        match_col = "target_securable_id"
    else:
        next_col = "target_securable_id"
        match_col = "source_securable_id"

    # B608 false positive: next_col and match_col are chosen from the
    # two hard-coded literals above, never from caller input.
    # Column names cannot be parameterised through ``text()`` bind
    # parameters — only values can. The ``# nosec`` has to live on
    # the f-string line itself (not on the ``text()`` call above) —
    # bandit matches the suppression by the reported line number.
    # CAST(:root AS VARCHAR) keeps Postgres happy: without the cast, the
    # non-recursive term types the ``sid`` column as ``text`` (psycopg
    # infers a plain Python str that way), while the recursive term
    # supplies ``character varying`` from the lineage_edges columns, and
    # Postgres rejects the union with DatatypeMismatch. SQLite is
    # type-affinity-only so the cast is a no-op there.
    node_sql_str = (
        f"WITH RECURSIVE walk(sid, d) AS (SELECT CAST(:root AS VARCHAR), 0 UNION ALL "  # nosec B608
        f"SELECT e.{next_col}, walk.d + 1 FROM lineage_edges e "
        f"JOIN walk ON e.{match_col} = walk.sid WHERE walk.d < :depth) "
        f"SELECT sid, MIN(d) AS depth FROM walk GROUP BY sid"
    )
    node_sql = text(node_sql_str)
    nodes = [
        (row[0], row[1]) for row in session.execute(node_sql, {"root": root_id, "depth": depth})
    ]

    reachable_ids = {sid for sid, _ in nodes}
    if not reachable_ids:
        return nodes, []

    # Edges whose walk-anchoring endpoint is in the reachable set,
    # bounded to the same direction so we do not accidentally return
    # an unrelated edge that happens to share one endpoint.
    edge_rows = session.execute(
        select(
            LineageEdge.source_securable_id,
            LineageEdge.target_securable_id,
            LineageEdge.run_id,
            LineageEdge.operation,
        ).where(
            getattr(LineageEdge, match_col).in_(reachable_ids),
            getattr(LineageEdge, next_col).in_(reachable_ids),
        ),
    ).all()
    edges = [(r[0], r[1], r[2], r[3]) for r in edge_rows]
    return nodes, edges


def _traverse_iterative(
    session: Session,
    root_id: str,
    direction: Literal["upstream", "downstream"],
    depth: int,
) -> tuple[list[tuple[str, int]], list[tuple[str, str, str, str | None]]]:
    """BFS walk of the lineage edge table without a recursive CTE.

    SQLite does not support recursive CTEs in all build configurations,
    and keeping a pure-Python fallback makes the test matrix simpler
    (sqlite + postgres exercise the same code path for everything
    except the query engine). The BFS is bounded by ``depth`` and
    keeps a visited set so cycles terminate.

    Args:
        session: Active SQLAlchemy session.
        root_id: Opaque table id to start the walk from.
        direction: ``"upstream"`` or ``"downstream"``.
        depth: Maximum number of hops.

    Returns:
        tuple[list[tuple[str, int]], list[tuple[str, str, str, str | None]]]:
            Same shape as :func:`_traverse_postgres`.
    """
    upstream = direction == "upstream"
    match_attr = LineageEdge.target_securable_id if upstream else LineageEdge.source_securable_id

    node_depth: dict[str, int] = {root_id: 0}
    frontier: set[str] = {root_id}
    collected_edges: list[tuple[str, str, str, str | None]] = []
    seen_edges: set[tuple[str, str, str]] = set()

    for current_depth in range(depth):
        if not frontier:
            break
        rows = session.execute(
            select(
                LineageEdge.source_securable_id,
                LineageEdge.target_securable_id,
                LineageEdge.run_id,
                LineageEdge.operation,
            ).where(match_attr.in_(frontier)),
        ).all()
        new_frontier: set[str] = set()
        for src, tgt, run_id, operation in rows:
            key = (src, tgt, run_id)
            if key not in seen_edges:
                seen_edges.add(key)
                collected_edges.append((src, tgt, run_id, operation))
            next_id = src if upstream else tgt
            if next_id not in node_depth:
                node_depth[next_id] = current_depth + 1
                new_frontier.add(next_id)
        frontier = new_frontier

    nodes = sorted(node_depth.items(), key=lambda kv: (kv[1], kv[0]))
    return nodes, collected_edges


def traverse(
    session: Session,
    full_name: str,
    direction: Literal["upstream", "downstream"],
    depth: int,
) -> LineageGraphResponse:
    """Walk the lineage graph starting from a table and return the subgraph.

    The root is addressed by ``catalog.schema.table`` because that is
    the only shape clients already use to talk to soyuz. The function
    reuses :func:`permissions_service.resolve_securable` so a missing
    catalog / schema / table surfaces as a plain 404, consistent with
    every other endpoint. The returned graph includes the root as a
    depth-0 node even when it has no edges, so clients can render
    "this table has no recorded lineage" as a single-node graph
    rather than an error.

    On Postgres the walk runs as a recursive CTE for O(depth) SQL
    round-trips; on SQLite the fallback is a Python BFS, one SELECT
    per hop. Both paths respect the :data:`MAX_DEPTH` cap and reject
    requests above it with 400 so a client typo (``depth=100``) does
    not issue a full-table scan. ``depth=0`` returns only the root
    node with an empty edge list — this is a valid no-op that lets
    clients probe "does this table exist?" without actually walking.

    Args:
        session: Active SQLAlchemy session.
        full_name: ``catalog.schema.table`` address of the root.
        direction: ``"upstream"`` (walk from targets back to sources)
            or ``"downstream"`` (walk from sources forward to targets).
        depth: Maximum hops to walk. Must be in ``[0, MAX_DEPTH]``.

    Returns:
        LineageGraphResponse: Reachable nodes (with reconstructed
            full_names) and the edges traversed.

    Raises:
        InvalidRequestError: If ``depth`` is outside
            ``[0, MAX_DEPTH]``. ``NotFoundError`` may also propagate
            from :func:`permissions_service.resolve_securable` when
            ``full_name`` does not resolve to a table.
    """
    if depth < 0 or depth > MAX_DEPTH:
        raise InvalidRequestError(
            f"depth must be between 0 and {MAX_DEPTH} inclusive, got {depth}",
        )
    root_id = permissions_service.resolve_securable(session, "table", full_name)

    if depth == 0 or session.bind is None:
        node_rows: list[tuple[str, int]] = [(root_id, 0)]
        edge_rows: list[tuple[str, str, str, str | None]] = []
    else:
        dialect = session.bind.dialect.name
        if dialect == "postgresql":
            node_rows, edge_rows = _traverse_postgres(session, root_id, direction, depth)
        else:
            node_rows, edge_rows = _traverse_iterative(session, root_id, direction, depth)

    all_ids: set[str] = {nid for nid, _ in node_rows}
    for src, tgt, _rid, _op in edge_rows:
        all_ids.add(src)
        all_ids.add(tgt)
    name_map = _reconstruct_full_names(session, all_ids)

    nodes = [
        LineageNode(securable_id=nid, full_name=name_map.get(nid), depth=d)
        for nid, d in sorted(node_rows, key=lambda kv: (kv[1], kv[0]))
    ]
    edges = [
        LineageEdgeOut(
            source_securable_id=src,
            target_securable_id=tgt,
            source_full_name=name_map.get(src),
            target_full_name=name_map.get(tgt),
            run_id=rid,
            operation=op,
        )
        for src, tgt, rid, op in edge_rows
    ]
    return LineageGraphResponse(root=full_name, direction=direction, nodes=nodes, edges=edges)
