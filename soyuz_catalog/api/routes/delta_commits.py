"""HTTP routes for the DeltaCommits resource (ADR-0011).

Two sibling endpoints at ``/delta/preview/commits``:

- ``GET`` — the spec-defined ``getCommits`` operation. The request
  shape is a body (unusual for GET, but unambiguous in the upstream
  OpenAPI document), so FastAPI receives it via ``Body(...)``. Routed
  through :func:`soyuz_catalog.services.delta_commits_service.get_commits`.
- ``POST`` — the spec-defined ``commit`` operation. ADR-0011 supersedes
  ADR-0006's "no coordinator" posture with a passthrough Delta commit
  coordinator, so this route persists commits (and/or acknowledges
  backfills) via
  :func:`soyuz_catalog.services.delta_commits_service.commit` and
  returns a spec-shaped empty :class:`DeltaCommitResponse` on success.
  The error envelope covers 400 (version gap / precondition), 409
  (version already exists, either pre-check or race-lost to the
  database unique constraint), 429 (per-table cap), and 501 (cloud
  storage scheme — still out of scope pending credential vending).

See ADR-0011 for the design rationale, including why soyuz's optimistic-
concurrency story reduces to a single unique constraint and why there
is no background backfill watchdog.
"""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from soyuz_catalog.api.deps import get_db
from soyuz_catalog.api.schemas import (
    DeltaCommit,
    DeltaCommitResponse,
    DeltaGetCommits,
    DeltaGetCommitsResponse,
)
from soyuz_catalog.services import delta_commits_service

router = APIRouter(tags=["delta-commits"])


@router.get(
    "/delta/preview/commits",
    response_model=DeltaGetCommitsResponse,
    response_model_exclude_none=True,
    summary="List unbackfilled Delta commits",
)
def get_commits(
    payload: DeltaGetCommits = Body(...),
    db: Session = Depends(get_db),
) -> DeltaGetCommitsResponse:
    """List unbackfilled Delta commits for a registered table.

    Args:
        payload: Request body with ``table_id``, ``table_uri``,
            ``start_version``, and optional ``end_version``.
        db: Database session dependency.

    Returns:
        DeltaGetCommitsResponse: The rows tracked by the coordinator
            in ``[start_version, end_version]`` plus the current
            ``latest_table_version``.
    """
    return delta_commits_service.get_commits(db, payload)


@router.post(
    "/delta/preview/commits",
    response_model=DeltaCommitResponse,
    response_model_exclude_none=True,
    summary="Register Delta commit or acknowledge backfill",
)
def commit(
    payload: DeltaCommit = Body(...),
    db: Session = Depends(get_db),
) -> DeltaCommitResponse:
    """Register an unbackfilled Delta commit and/or acknowledge a backfill.

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
    """
    delta_commits_service.commit(db, payload)
    return DeltaCommitResponse()
