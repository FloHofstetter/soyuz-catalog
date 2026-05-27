"""Domain exceptions mapped to HTTP responses by the API layer."""

from __future__ import annotations


class SoyuzError(Exception):
    """Base class for soyuz-catalog domain errors.

    Args:
        message: Human-readable error description.
    """

    error_code: str = "INTERNAL_ERROR"
    status_code: int = 500

    def __init__(self, message: str) -> None:  # noqa: D107
        super().__init__(message)
        self.message = message


class NotFoundError(SoyuzError):
    """Raised when a requested resource does not exist.

    Maps to HTTP 404 with ``error_code = "NOT_FOUND"``. Services raise
    this for every "address does not resolve" case — missing catalog,
    schema, table, volume, or any of their ``*_by_id`` lookups — without
    distinguishing which level of the hierarchy is missing. From the
    client's perspective the distinction is meaningless: the full_name
    or id they sent simply does not point at a real row.
    """

    error_code = "NOT_FOUND"
    status_code = 404


class ConflictError(SoyuzError):
    """Raised when a uniqueness constraint or delete-gate fails.

    Maps to HTTP 409 with ``error_code = "ALREADY_EXISTS"``. Used for
    both shapes of conflict in the service layer: duplicate-name
    collisions on create/rename (translated from
    ``IntegrityError`` after the DB-level unique constraint fires, not
    from a pre-check SELECT, so it is race-safe) and the
    ``FAILED_PRECONDITION``-shaped delete rejection when a parent still
    owns children and ``force=true`` was not supplied. Both cases share
    the 409 status even though UC OSS uses different internal error
    codes, because the HTTP envelope in this project only exposes one
    409 code.
    """

    error_code = "ALREADY_EXISTS"
    status_code = 409


class NotImplementedError(SoyuzError):  # noqa: A001 - deliberate shadow of builtin
    """Raised when a spec-defined endpoint is intentionally not implemented.

    Maps to HTTP 501 with ``error_code = "NOT_IMPLEMENTED"``. The spec
    itself lists ``501`` as a valid response for
    ``POST /delta/preview/commits``, so returning it is *not* a
    divergence — it is the documented out. Two call sites use it
    today: the cloud-scheme fallthrough in ``get_commits`` (non-
    ``file://`` URIs would require a credential-vending layer that
    does not exist), and the missing-``delta``-extra case where the
    feature is gated behind an optional dependency.

    The class name deliberately shadows the builtin ``NotImplementedError``
    inside the ``soyuz_catalog.exceptions`` module: every other domain
    error in this project is imported qualified as
    ``exceptions.FooError``, and making the new one an exception to that
    rule would be the surprise. Call sites always use the qualified
    form, so the shadow never leaks into generic Python code paths.

    Per ADR-0011 the primary ``POST /delta/preview/commits`` endpoint
    is a real, backing-storage-touching coordinator and no longer
    returns 501 in the happy path. The dedicated
    :class:`CommitCoordinatorUnsupportedError` sibling below is
    narrower in scope — it applies only to the Delta REST Kernel
    surface at ``/delta/v1/`` (ADR-0009, ADR-0011) where the
    corresponding ``UpdateTable`` coordinator actions are still
    intentionally unimplemented.
    """

    error_code = "NOT_IMPLEMENTED"
    status_code = 501


class CommitCoordinatorUnsupportedError(SoyuzError):
    """Raised when the Delta REST Kernel ``UpdateTable`` asks for a coordinator action.

    Maps to HTTP 501 with ``error_code = "COMMIT_COORDINATOR_UNSUPPORTED"``.
    Narrow in scope: applies only to the Delta REST Kernel surface at
    ``/delta/v1/`` (ADR-0009), which exposes a parallel set of
    coordinator actions through the ``UpdateTable`` discriminated
    union — ``add-commit``, ``set-latest-backfilled-version``,
    ``update-metadata-snapshot-version``. Per ADR-0011 the primary
    ``POST /delta/preview/commits`` coordinator at ``/delta/preview/``
    is a real passthrough, but the parallel ``/delta/v1/`` actions
    are not yet wired to the same :class:`DeltaUnbackfilledCommit`
    storage. Spark does not reach the ``/delta/v1/`` surface today,
    so the open gap has no real consumer; the dedicated error code
    exists so a future unification can retire this exception without
    breaking the wire contract, and so clients can tell "Delta REST
    Kernel coordinator actions still TODO" apart from "this endpoint
    is not yet wired up".
    """

    error_code = "COMMIT_COORDINATOR_UNSUPPORTED"
    status_code = 501


class InvalidRequestError(SoyuzError):
    """Raised when the request payload is semantically invalid.

    Maps to HTTP 400 with ``error_code = "INVALID_ARGUMENT"``. Pydantic
    validation failures (unknown fields under ``extra="forbid"``, type
    mismatches, missing required fields) surface as 422 through
    FastAPI's own handler and do *not* flow through this exception —
    this class is reserved for the semantic rejections that only the
    service layer can make: malformed ``full_name`` path parameters,
    unsupported storage URI schemes, and the
    ``UNKNOWN_*_OPERATION`` sentinels on temporary credentials. Every
    raise site is the place where soyuz-catalog diverges from UC OSS
    Java's silently-accept-garbage behaviour (see ``DIVERGENCES.md``).
    """

    error_code = "INVALID_ARGUMENT"
    status_code = 400


class TooManyRequestsError(SoyuzError):
    """Raised when a resource has hit a per-entity cap.

    Maps to HTTP 429 with ``error_code = "TOO_MANY_REQUESTS"``. The sole
    consumer (per ADR-0011) is the Delta commit coordinator: each
    Delta table is capped at 10 concurrently-unbackfilled commits
    (matching the upstream
    ``io.unitycatalog.server.persist.DeltaCommitRepository.MAX_NUM_COMMITS_PER_TABLE``
    constant), and a ``POST /delta/preview/commits`` that would push
    the row count above the cap is rejected with this exception so the
    client knows to publish existing staged commits before adding more.
    This is a back-pressure signal, not a rate limit — hitting it means
    the client is not backfilling on its own schedule, which Delta
    Kernel clients always do.
    """

    error_code = "TOO_MANY_REQUESTS"
    status_code = 429
