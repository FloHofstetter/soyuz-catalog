"""Business logic for the DeltaCommits resource (ADR-0011).

soyuz acts as a **passthrough Delta commit coordinator** for Delta
tables that live on local-filesystem storage (``file://``). The
``/delta/preview/commits`` endpoint pair exposes two operations the
Delta Kernel client calls during managed-Delta writes and reads:

- ``POST`` (:func:`commit`) — register an unbackfilled commit and/or
  acknowledge a completed client-side publish. The client has already
  written a staged commit file to ``_delta_log/.tmp/<uuid>.json`` at
  this point; soyuz records the file metadata and the commit version,
  and the client then publishes the staged file to
  ``_delta_log/NNNNN.json`` on receipt of the 200. On a subsequent
  ``POST`` the client may pass ``latest_backfilled_version`` to signal
  that everything up to version ``K`` has been published, at which
  point soyuz prunes rows at earlier versions and marks the row at
  ``commit_version == K`` with ``is_backfilled_latest_commit = True``
  so :func:`get_commits` can still report an accurate
  ``latest_table_version`` after cleanup. Both operations are
  idempotent in the sense that clients freely retry them; racing
  ``POST`` calls at the same version serialise through the
  ``UniqueConstraint("table_id", "commit_version")`` on the
  :class:`soyuz_catalog.models.DeltaUnbackfilledCommit` table and the
  losing writer observes a 409.

- ``GET`` (:func:`get_commits`) — return the unbackfilled rows for a
  table within the requested ``[start_version, end_version]`` window
  plus the current ``latest_table_version`` (max over **all** live
  rows, including the ``is_backfilled_latest_commit`` anchor, falling
  back to :py:meth:`deltalake.DeltaTable.version` on the on-disk log
  when the coordinator has no rows for the table so freshly-attached
  tables still report a valid version).

Both operations share the same preconditions: the table must exist,
``table_uri`` must match the registered ``storage_location`` (per the
upstream spec), and the storage scheme must be ``file://``. Cloud
schemes return 501 via :class:`soyuz_catalog.exceptions.NotImplementedError`
because cloud-side disk access would need the out-of-scope credential-
vending layer — this is a documented "not yet" rather than a
permanent posture.

The entire optimistic-concurrency story is the unique constraint: two
writers racing on version ``N`` hit the database together, one
succeeds, the other's :class:`sqlalchemy.exc.IntegrityError` translates
to :class:`soyuz_catalog.exceptions.ConflictError` and the client
retries at ``N+1``. There is no lock manager, no version vector, and
no background backfill watchdog — Delta Kernel readers apply
unbackfilled rows in-memory via ``snapshotBuilder.withLogData(...)``,
so a crash between the commit call and the client-side publish is a
read-path concern that heals itself on the next snapshot. See ADR-0011
for the full rationale and the reference to the upstream Java
implementation at ``DeltaCommitRepository.java`` lines 236-414 that
this module tracks.
"""

from __future__ import annotations

import logging

from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from soyuz_catalog.api.schemas import (
    DeltaCommit,
    DeltaCommitInfo,
    DeltaGetCommits,
    DeltaGetCommitsResponse,
)
from soyuz_catalog.exceptions import (
    ConflictError,
    InvalidRequestError,
    NotImplementedError,
    TooManyRequestsError,
)
from soyuz_catalog.models import DeltaUnbackfilledCommit, Table
from soyuz_catalog.services import table_service
from soyuz_catalog.storage import parse_storage_uri

_logger = logging.getLogger(__name__)

MAX_UNBACKFILLED_COMMITS_PER_TABLE = 10
"""Per-table cap on concurrently-tracked unbackfilled commits.

Matches the upstream
``io.unitycatalog.server.persist.DeltaCommitRepository.MAX_NUM_COMMITS_PER_TABLE``
constant. Exceeding the cap yields 429 ``TOO_MANY_REQUESTS`` — a
back-pressure signal, not a rate limit. Delta Kernel clients publish
staged commits on their own schedule and will not organically hit the
cap; a client that does is misbehaving and the 429 is the right
diagnosis.
"""


def _resolve_table(session: Session, payload_table_id: str, payload_table_uri: str) -> Table:
    """Resolve and validate the table referenced by a DeltaCommits payload.

    Shared between :func:`get_commits` and :func:`commit`: looks up the
    table by opaque ``table_id`` (404 propagates from
    :func:`table_service.get_table_by_id`), checks the registered
    ``storage_location`` against the payload's ``table_uri`` (400 on
    mismatch — the upstream spec explicitly calls this out as a
    rejection case), and asserts the stored location is non-empty.

    Args:
        session: Active SQLAlchemy session.
        payload_table_id: ``table_id`` from the request body.
        payload_table_uri: ``table_uri`` from the request body.

    Returns:
        Table: The validated table row.

    Raises:
        InvalidRequestError: If ``table_uri`` does not match the stored
            ``storage_location``, or if the stored location is missing
            or empty (a materialised Delta table is required for this
            endpoint). ``NotFoundError`` may also propagate when
            ``payload_table_id`` does not resolve.
    """
    table = table_service.get_table_by_id(session, payload_table_id)
    stored = table.storage_location
    if stored is None or not stored.strip():
        raise InvalidRequestError(
            f"table '{table.id}' has no registered storage_location; "
            "delta commits requires a materialised table",
        )
    if payload_table_uri != stored:
        raise InvalidRequestError(
            f"table_uri '{payload_table_uri}' does not match the registered "
            f"storage_location for table '{table.id}'",
        )
    return table


def _gate_file_scheme(storage_location: str) -> None:
    """Reject non-``file://`` storage schemes with a 501.

    Cloud Delta tables would require server-side credential vending to
    open the remote ``_delta_log``; that layer is explicitly out of
    scope (metadata-only design, README design principle 3). The
    gate lives here rather than at the route so both ``commit`` and
    ``get_commits`` enforce it identically and the service-layer
    tests can cover the rejection path without a running HTTP server.

    Args:
        storage_location: The table's registered ``storage_location``.

    Raises:
        NotImplementedError: If the scheme is not ``file``.
    """
    parsed = parse_storage_uri(storage_location)
    if parsed.scheme != "file":
        raise NotImplementedError(
            f"delta commits is only supported for file:// storage "
            f"in this build; got scheme '{parsed.scheme}'. Cloud URIs "
            "require the credential-vending layer, which is "
            "explicitly out of scope.",
        )


def _coordinator_latest_version(session: Session, table_id: str) -> int | None:
    """Return the highest commit version the coordinator has seen for a table.

    The max is taken over **all** live rows — including the row marked
    ``is_backfilled_latest_commit = True`` — because that marker is the
    whole point of the prune path: it preserves the highest-known
    version as an anchor after the earlier rows have been cleaned up.
    Returns ``None`` if the coordinator has never seen a commit for
    the table, in which case callers fall back to reading
    :py:meth:`deltalake.DeltaTable.version` off the on-disk log.

    Args:
        session: Active SQLAlchemy session.
        table_id: Opaque table id to query.

    Returns:
        int | None: The max ``commit_version`` or ``None`` if no rows
            exist for this table.
    """
    stmt = select(func.max(DeltaUnbackfilledCommit.commit_version)).where(
        DeltaUnbackfilledCommit.table_id == table_id,
    )
    return session.execute(stmt).scalar_one_or_none()


def _effective_latest(session: Session, table_id: str, storage_location: str) -> int:
    """Return the effective ``latest_table_version`` for a table.

    The coordinator's own max commit version wins when it has rows;
    otherwise the service falls back to the on-disk log via
    :py:meth:`deltalake.DeltaTable.version`. This matches the
    natural onboarding story for a table that was previously written
    through the path-based Delta writer: the Delta Kernel client
    reads the on-disk version itself and starts sending coordinator
    commits at ``on-disk + 1``, and the coordinator's write-path
    gap check needs to be consistent with that or every
    first-coordinator-commit would be rejected as a gap. A
    brand-new (coordinator-empty, log-empty) table has on-disk
    version ``-1`` by the convention
    :func:`_ondisk_latest_version_or_minus_one` returns.

    Args:
        session: Active SQLAlchemy session.
        table_id: Opaque table id.
        storage_location: The table's ``file://`` storage location,
            used for the on-disk fallback.

    Returns:
        int: The effective latest version. ``-1`` means "no commits
            at all", so the next expected commit is version ``0``.
    """
    coordinator = _coordinator_latest_version(session, table_id)
    if coordinator is not None:
        return coordinator
    return _ondisk_latest_version_or_minus_one(storage_location)


def _ondisk_latest_version_or_minus_one(storage_location: str) -> int:
    """Read the on-disk Delta log version, returning ``-1`` for empty tables.

    :py:class:`deltalake.DeltaTable` raises when the log directory is
    missing entirely, which is the natural state of a freshly-created
    coordinator-managed table. Catch that specific path and map it to
    ``-1`` so the caller can treat the "no commits anywhere" case and
    the "version 0 is on disk" case uniformly: the next expected
    coordinator commit is always ``effective_latest + 1``.

    Args:
        storage_location: The table's ``file://`` storage location.

    Returns:
        int: The on-disk version, or ``-1`` if the Delta log does not
            exist yet.

    Raises:
        NotImplementedError: If the ``delta`` optional extra is not
            installed.
    """
    try:
        from deltalake import DeltaTable  # noqa: PLC0415
        from deltalake.exceptions import TableNotFoundError  # noqa: PLC0415
    except ImportError as exc:  # pragma: no cover
        raise NotImplementedError(
            "the 'delta' optional extra is not installed; reinstall with "
            "'pip install soyuz-catalog[delta]' to enable "
            "/delta/preview/commits",
        ) from exc
    local_path = parse_storage_uri(storage_location).raw.removeprefix("file://")
    try:
        return int(DeltaTable(local_path).version())
    except TableNotFoundError:
        return -1


def get_commits(session: Session, payload: DeltaGetCommits) -> DeltaGetCommitsResponse:
    """Return the unbackfilled commits tracked for a registered Delta table.

    Resolves ``payload.table_id``, validates ``payload.table_uri`` against
    the stored ``storage_location``, gates on the ``file://`` scheme, and
    queries :class:`soyuz_catalog.models.DeltaUnbackfilledCommit` for the
    live rows in ``[start_version, end_version]`` excluding the
    ``is_backfilled_latest_commit`` anchor (the anchor is internal state
    that preserves the latest-version high-water mark after a prune —
    returning it would confuse the Delta Kernel reader which expects
    only rows it has not yet applied). ``latest_table_version`` is the
    max commit version across all live rows for the table, falling
    back to :func:`_ondisk_latest_version` when the coordinator has no
    rows (the read-path for tables that have only ever been written
    via external Delta with an explicit ``LOCATION``).

    Args:
        session: Active SQLAlchemy session.
        payload: Validated request body.

    Returns:
        DeltaGetCommitsResponse: The matched commits plus the current
            ``latest_table_version``. ``InvalidRequestError``
            (``table_uri`` mismatch) may propagate from
            :func:`_resolve_table`, and
            :class:`soyuz_catalog.exceptions.NotImplementedError` may
            propagate from :func:`_gate_file_scheme` or the on-disk
            fallback helper when the ``delta`` extra is missing.
    """
    table = _resolve_table(session, payload.table_id, payload.table_uri)
    _gate_file_scheme(table.storage_location or "")

    conditions = [
        DeltaUnbackfilledCommit.table_id == table.id,
        DeltaUnbackfilledCommit.commit_version >= payload.start_version,
        DeltaUnbackfilledCommit.is_backfilled_latest_commit.is_(False),
    ]
    if payload.end_version is not None:
        conditions.append(DeltaUnbackfilledCommit.commit_version <= payload.end_version)

    rows = (
        session.execute(
            select(DeltaUnbackfilledCommit)
            .where(*conditions)
            .order_by(DeltaUnbackfilledCommit.commit_version.asc())
        )
        .scalars()
        .all()
    )

    latest_effective = _effective_latest(session, table.id, table.storage_location or "")
    # GET reports 0 for a brand-new table whose log does not exist yet:
    # callers treat ``latest_table_version`` as an absolute version
    # counter and a freshly-attached coordinator table without any
    # commits yet is externally indistinguishable from a table at
    # version 0.
    latest = max(latest_effective, 0)

    _logger.debug(
        "delta commits GET: table_id=%s rows=%d latest_table_version=%d",
        table.id,
        len(rows),
        latest,
    )

    return DeltaGetCommitsResponse(
        commits=[
            DeltaCommitInfo(
                version=row.commit_version,
                timestamp=row.commit_timestamp,
                file_name=row.file_name,
                file_size=row.file_size,
                file_modification_timestamp=row.file_modification_timestamp,
            )
            for row in rows
        ],
        latest_table_version=latest,
    )


def commit(session: Session, payload: DeltaCommit) -> None:
    """Register a new unbackfilled commit and/or acknowledge a backfill.

    The DeltaCommit request fuses two operations that may appear
    together on a single ``POST``: registering a freshly-staged commit
    (``commit_info`` set) and acknowledging that the client has
    published everything up to a given version (``latest_backfilled_version``
    set). The write path runs first so the new row's persistence does
    not depend on the prune — a client that sends both fields in one
    call expects version ``N`` to appear in ``get_commits`` output if
    the prune then fails for any reason (it cannot in practice, but
    the ordering is documented contract).

    Write path (``commit_info`` set):

    - ``commit_info.version <= current latest`` → 409
      ``ALREADY_EXISTS``. Matches the upstream
      ``DeltaCommitRepository.java`` line 380 ``lastCommitVersion``
      check.
    - ``commit_info.version > current latest + 1`` → 400 "version gap"
      (upstream ``INVALID_ARGUMENT``, line 383-388).
    - The unbackfilled row count for the table already at the
      :data:`MAX_UNBACKFILLED_COMMITS_PER_TABLE` cap → 429
      ``TOO_MANY_REQUESTS``. The cap is a back-pressure signal telling
      the client to publish existing commits before adding more.
    - The row is inserted. ``session.flush()`` is wrapped in a
      ``try/except IntegrityError`` so a **race** between two writers
      at the same version — where both passed the pre-check — still
      surfaces as 409 from the database-level unique constraint. This
      is the belt-and-braces for the entire optimistic-concurrency
      story.

    Prune path (``latest_backfilled_version`` set):

    - ``latest_backfilled_version > current latest`` → 400 (cannot
      acknowledge a publish past the highest version the coordinator
      has seen; upstream line 330-336).
    - Rows with ``commit_version < latest_backfilled_version`` are
      deleted; the row at ``commit_version == latest_backfilled_version``
      is flagged ``is_backfilled_latest_commit = True`` so it remains
      as the version anchor without leaking into ``get_commits``
      output. Idempotent: repeated prunes with the same
      ``latest_backfilled_version`` settle to the same state.

    Args:
        session: Active SQLAlchemy session.
        payload: Validated request body. Either ``commit_info`` or
            ``latest_backfilled_version`` (or both) must be present —
            enforced at the schema layer and re-checked defensively
            here.

    Raises:
        InvalidRequestError: Version gap, acknowledgement past the
            current latest, or neither action field set (defensive
            re-check of the schema-level validator). Also propagates
            from :func:`_resolve_table` on ``table_uri`` mismatch.
        ConflictError: Commit version already exists (pre-check or
            race), translated from the ``UniqueConstraint`` on
            ``(table_id, commit_version)``.
        TooManyRequestsError: Cap of
            :data:`MAX_UNBACKFILLED_COMMITS_PER_TABLE` rows per table
            would be exceeded. :class:`soyuz_catalog.exceptions.NotImplementedError`
            may also propagate from :func:`_gate_file_scheme` for
            non-``file://`` storage schemes.
    """
    if payload.commit_info is None and payload.latest_backfilled_version is None:
        raise InvalidRequestError(
            "DeltaCommit must carry at least one of 'commit_info' or 'latest_backfilled_version'",
        )

    table = _resolve_table(session, payload.table_id, payload.table_uri)
    _gate_file_scheme(table.storage_location or "")

    effective_latest = _effective_latest(session, table.id, table.storage_location or "")

    if payload.commit_info is not None:
        info = payload.commit_info
        if info.version <= effective_latest:
            raise ConflictError(
                f"commit version {info.version} already exists for table "
                f"'{table.id}' (current latest_table_version={effective_latest})",
            )
        if info.version > effective_latest + 1:
            raise InvalidRequestError(
                f"commit version {info.version} leaves a gap: the next "
                f"expected version is {effective_latest + 1}",
            )

        row_count = session.execute(
            select(func.count())
            .select_from(DeltaUnbackfilledCommit)
            .where(DeltaUnbackfilledCommit.table_id == table.id)
        ).scalar_one()
        if row_count >= MAX_UNBACKFILLED_COMMITS_PER_TABLE:
            raise TooManyRequestsError(
                f"table '{table.id}' already has {row_count} unbackfilled "
                f"commits (cap={MAX_UNBACKFILLED_COMMITS_PER_TABLE}); "
                "publish existing staged commits before adding more",
            )

        row = DeltaUnbackfilledCommit(
            table_id=table.id,
            commit_version=info.version,
            commit_timestamp=info.timestamp,
            file_name=info.file_name,
            file_size=info.file_size,
            file_modification_timestamp=info.file_modification_timestamp,
            is_backfilled_latest_commit=False,
        )
        session.add(row)
        try:
            session.flush()
        except IntegrityError as exc:
            session.rollback()
            raise ConflictError(
                f"commit version {info.version} already exists for table "
                f"'{table.id}' (race lost to a concurrent writer)",
            ) from exc

        effective_latest = info.version

    if payload.latest_backfilled_version is not None:
        lbv = payload.latest_backfilled_version
        if lbv > effective_latest:
            raise InvalidRequestError(
                f"latest_backfilled_version {lbv} exceeds the current "
                f"latest_table_version {effective_latest}",
            )

        # Delete everything strictly below the anchor.
        session.execute(
            delete(DeltaUnbackfilledCommit).where(
                DeltaUnbackfilledCommit.table_id == table.id,
                DeltaUnbackfilledCommit.commit_version < lbv,
            )
        )

        # Mark the anchor row. Idempotent: if the anchor was already
        # marked from a previous prune the UPDATE is a no-op.
        session.execute(
            update(DeltaUnbackfilledCommit)
            .where(
                DeltaUnbackfilledCommit.table_id == table.id,
                DeltaUnbackfilledCommit.commit_version == lbv,
            )
            .values(is_backfilled_latest_commit=True)
        )
        session.flush()

    session.commit()

    _logger.debug(
        "delta commits POST: table_id=%s committed=%s backfilled=%s",
        table.id,
        payload.commit_info.version if payload.commit_info else None,
        payload.latest_backfilled_version,
    )
