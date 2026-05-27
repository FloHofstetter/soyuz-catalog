"""Audit-log read API.

Cross-reference surface for agent-driven clients.  A client that
queries ``?agent_run_id=<uuid>`` gets every mutation that the
matching run made through soyuz — set_tag, create_table, set_owner,
etc. — so a per-run audit view on the client side is one round-trip
rather than N.

Read-only.  Writes happen via :func:`soyuz_catalog.services.audit_service.log_action`
called from the mutation routes.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from soyuz_catalog.api.deps import get_db
from soyuz_catalog.services import audit_service

router = APIRouter(prefix="/audit-log", tags=["audit"])


@router.get("", summary="List audit log entries")
def list_audit_log(
    agent_run_id: str | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """Return audit rows, optionally scoped to one agent run.

    Args:
        agent_run_id: Optional ``X-Agent-Run-Id`` filter.  When
            ``None`` returns the most recent ``limit`` rows across
            all runs (operator-style view).
        limit: Hard row cap (1-1000, default 200).
        db: Database session dependency.

    Returns:
        list[dict[str, Any]]: List of dicts — one per ``audit_log``
        row, ordered most-recent first when no ``agent_run_id``
        filter is set, oldest-first inside a single run.
    """
    if agent_run_id:
        return audit_service.list_for_run(db, agent_run_id.strip(), limit=limit)

    from sqlalchemy import select

    from soyuz_catalog.models import AuditLog

    stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    rows = db.scalars(stmt).all()
    return [
        {
            "id": r.id,
            "action": r.action,
            "target": r.target,
            "principal": r.principal,
            "agent_run_id": r.agent_run_id,
            "client_ip": r.client_ip,
            "detail": r.detail,
            "created_at": r.created_at,
        }
        for r in rows
    ]
