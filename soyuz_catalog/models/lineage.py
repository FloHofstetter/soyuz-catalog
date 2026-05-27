"""OpenLineage ingestion models (ADR-0008).

Over-the-spec extension: upstream Unity Catalog OSS has no lineage at
all. Each :class:`LineageRun` is one OpenLineage run (one job
execution); :class:`LineageEdge` and :class:`LineageColumnEdge`
capture the table- and column-level dataflow respectively;
:class:`LineageValueChange` ingests a producer-defined per-cell diff
facet. The three edge tables share the same posture: opaque securable
ids, no foreign keys to the underlying resource tables, append-only
history (so a table delete leaves its edges intact for historical
queries), and ``ON DELETE CASCADE`` only on ``run_id``.
"""

from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from soyuz_catalog.models._base import Base, _new_id, _now_ms


class LineageRun(Base):
    """A single OpenLineage run (one execution of a job).

    soyuz-catalog accepts OpenLineage events as an over-the-spec extension
    (ADR-0008); upstream UC OSS has no lineage at all. Each run
    is identified by the OpenLineage ``runId`` with hyphens stripped so it
    fits soyuz' 32-char-hex convention for primary keys, and the ORM row is
    upserted as the run transitions through OpenLineage lifecycle states
    (``START`` → ``RUNNING`` → ``COMPLETE`` / ``FAIL`` / ``ABORT``).

    The ``state`` column is last-write-wins: OpenLineage producers may
    redeliver events or emit out-of-order transitions, and a monotonic
    state machine here would reject legitimate retries. Downstream
    consumers that care about strict ordering can look at ``started_at``
    and ``ended_at`` to reconstruct the timeline.

    ``lineage_edges`` rows FK into this table with ``ON DELETE CASCADE``
    because deleting a run logically drops its attached graph contribution.
    Edges referencing tables that were later deleted, however, are **not**
    cascade-cleaned — lineage is append-only history; see :class:`LineageEdge`.
    """

    __tablename__ = "lineage_runs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    job_namespace: Mapped[str] = mapped_column(String(255), nullable=False)
    job_name: Mapped[str] = mapped_column(String(512), nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False)
    started_at: Mapped[int] = mapped_column(BigInteger, nullable=False)
    ended_at: Mapped[int | None] = mapped_column(BigInteger, nullable=True)


class LineageEdge(Base):
    """A directed lineage edge: one source securable produced one target.

    Each row captures that a specific :class:`LineageRun` read
    ``source_securable_id`` and wrote ``target_securable_id``. The cross
    product of (resolved inputs × resolved outputs) on a single OpenLineage
    event yields as many rows as there are pairs; the unique constraint on
    ``(run_id, source_securable_id, target_securable_id)`` makes event
    redelivery idempotent without a pre-check SELECT — the same race
    strategy used by every other ``create_*`` in the service layer.

    ``source_securable_id`` and ``target_securable_id`` are **opaque row
    ids** from the underlying resource table (tables only in the MVP —
    volumes and models are a non-breaking extension because the column is
    just a 32-char hex). There is deliberately **no foreign key** on
    either column: the target varies by row, and a partial FK per resource
    would not buy anything the query-time ``LEFT JOIN`` already buys.
    Lineage is append-only history: when a table is deleted its edges
    stay, and the query layer renders them with ``full_name = null`` so
    clients can still see the shape of the historical graph.

    ``operation`` is the OpenLineage ``job.name`` captured verbatim. It is
    the closest 1:1 analogue of "what transformation ran" across
    producers; richer facets exist in OpenLineage but vary by emitter and
    would pin soyuz to one producer's conventions. See ADR-0008.
    """

    __tablename__ = "lineage_edges"
    __table_args__ = (
        UniqueConstraint(
            "run_id",
            "source_securable_id",
            "target_securable_id",
            name="uq_lineage_edges_run_source_target",
        ),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    run_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("lineage_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_securable_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    target_securable_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    operation: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False, default=_now_ms)


class LineageColumnEdge(Base):
    """One per-column lineage edge inside a :class:`LineageRun`.

    Extends the table-level :class:`LineageEdge` graph with column-
    level resolution.  Each row pairs one
    ``(source_securable_id, source_column)`` to one
    ``(target_securable_id, target_column)`` for a specific run.

    ``transformation_type`` carries the OpenLineage 1.x
    ``columnLineage`` facet's transformation type
    (``IDENTITY`` / ``RENAME`` / ``DERIVED`` / ...) verbatim or
    ``None`` when the producer omitted it.  The column is a free-
    form ``Text`` rather than a CHECK-constrained enum so non-spec
    transformation kinds — e.g. ``aggregate``, ``unknown_origin`` —
    round-trip from upstream producers without fixing soyuz's
    vocabulary in stone.

    Same posture as :class:`LineageEdge`: opaque securable ids, no
    FK, append-only history, ``ON DELETE CASCADE`` on ``run_id``
    only.  The unique constraint makes redelivery idempotent.
    """

    __tablename__ = "lineage_column_edges"
    __table_args__ = (
        UniqueConstraint(
            "run_id",
            "source_securable_id",
            "source_column",
            "target_securable_id",
            "target_column",
            name="uq_lineage_column_edges_run_quad",
        ),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    run_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("lineage_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_securable_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    source_column: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    target_securable_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    target_column: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    transformation_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False, default=_now_ms)


class LineageValueChange(Base):
    """One per-cell value diff inside a :class:`LineageRun`.

    Ingests a producer-defined ``valueChange`` facet — non-
    OpenLineage-spec, namespaced via ``_producer`` URI on the facet
    payload.  Each row captures the before/after values for one
    cell change.

    Any OpenLineage producer can emit the facet, but its field shape
    is not part of OpenLineage 1.x — consumers should treat the
    schema as producer-defined.  soyuz stores whatever the producer
    sent verbatim; it does no redaction or hashing of its own and
    expects producers that handle PII to redact upstream.

    No unique constraint: redeliveries by the same producer are
    expected to be rare, and the cost of a duplicate row is
    bounded by the producer's `track_value_changes` cap.
    """

    __tablename__ = "lineage_value_changes"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    run_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("lineage_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_securable_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    target_row_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    target_column: Mapped[str] = mapped_column(String(255), nullable=False)
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False, default=_now_ms)
