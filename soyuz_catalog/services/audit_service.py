"""Audit-log persistence helper.

Single entry-point :func:`log_action` that route handlers call after
performing a successful mutation.  The helper reads
``X-Principal`` / ``X-Agent-Run-Id`` / source IP from the
``request_context`` ContextVars populated by ``RequestIDMiddleware``,
so callers do not pass them explicitly.

Best-effort: insert errors are caught and logged so a transient DB
hiccup never breaks the underlying mutation route.

Agent-driven clients that forward ``X-Agent-Run-Id`` on every call
get their mutations cross-indexed by run, so a per-run audit view
on the client side becomes a single query against the
``agent_run_id`` column.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from soyuz_catalog.api.request_context import get_agent_run_id, get_client_ip, get_principal
from soyuz_catalog.models import AuditLog

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def log_action(
    db: Session,
    *,
    action: str,
    target: str,
    detail: dict[str, Any] | None = None,
) -> int | None:
    """Persist one audit-log row for the in-flight request.

    The insert is committed here, in its own transaction: every
    mutation route calls this helper *after* its service function has
    already committed the actual mutation, and nothing downstream
    commits the request session again. A bare ``flush()`` (the
    previous behaviour) left the row in a transaction that
    ``get_db``'s ``session.close()`` rolled back at request teardown,
    silently dropping every audit row.

    Args:
        db: Live SQLAlchemy session (the same one the route used for
            the mutation it just performed; that mutation is already
            committed by the time this helper runs).
        action: Dotted action name (``table.created`` /
            ``schema.deleted`` / ``tag.updated`` / …).  Convention
            is ``<resource>.<verb>``.
        target: Dotted FQN (or other stable identifier) of the
            affected securable.
        detail: Optional JSON-serialisable mapping with
            action-specific extras (e.g. before/after owner, tag
            key/value, changes set).  ``None`` when the action +
            target line is enough.

    Returns:
        int | None: The new ``audit_log.id`` on success, or ``None``
        when the insert failed (logged and swallowed — the audit
        trail is best-effort metadata).
    """
    try:
        detail_text = json.dumps(detail, default=str) if detail else None
    except (TypeError, ValueError) as exc:
        logger.warning("audit_service: detail not JSON-serialisable for %r: %s", action, exc)
        detail_text = None
    row = AuditLog(
        action=action,
        target=target,
        principal=get_principal(),
        agent_run_id=get_agent_run_id(),
        client_ip=get_client_ip(),
        detail=detail_text,
    )
    try:
        db.add(row)
        db.commit()
        return row.id
    except Exception as exc:  # noqa: BLE001 — audit must not break the mutation
        logger.warning("audit_service: insert failed for %r %r: %s", action, target, exc)
        try:
            db.rollback()
        except Exception:  # noqa: BLE001 — best-effort
            logger.exception("audit_service: rollback after insert failure also raised")
        return None


def list_for_run(
    db: Session,
    agent_run_id: str,
    *,
    limit: int = 200,
) -> list[dict[str, Any]]:
    """Return audit rows attributed to one agent run.

    Args:
        db: Live SQLAlchemy session.
        agent_run_id: UUID-shape value the client forwarded as
            ``X-Agent-Run-Id`` on the mutating requests during the
            run.
        limit: Hard row cap.  ORDER BY ``created_at ASC`` so the
            sequence of UC mutations during the run reads top-to-
            bottom in time order.

    Returns:
        list[dict[str, Any]]: List of dicts ready for JSON
        serialisation, ordered oldest-first by ``created_at``.
    """
    from sqlalchemy import select

    stmt = (
        select(AuditLog)
        .where(AuditLog.agent_run_id == agent_run_id)
        .order_by(AuditLog.created_at.asc())
        .limit(limit)
    )
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
