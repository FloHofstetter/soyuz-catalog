"""Business logic for the Metastore summary endpoint.

The UC OpenAPI spec exposes only ``GET /metastore_summary`` for this
resource: no create, update, delete, or list. soyuz models the
metastore as a single-row table (:class:`soyuz_catalog.models.Metastore`)
and bootstraps that row **lazily** on the first summary call so that
in-memory test fixtures, fresh SQLite files, and freshly-migrated
Postgres deployments all converge on the same "one row, stable id"
invariant without a dedicated seed step. On the second and subsequent
calls the existing row is returned verbatim; the id never changes for
the lifetime of a database.

The divergence from UC Databricks-flavoured forks (which return a much
richer summary) is intentional — see ``DIVERGENCES.md``.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from soyuz_catalog.models import Metastore


def get_metastore_summary(session: Session) -> Metastore:
    """Return the singleton metastore row, creating it if absent.

    The first call on a fresh database inserts a row with a random
    UUID-hex id; every subsequent call returns that same row. The
    insert races benignly against a concurrent first call: both
    transactions attempt the same insert, one wins the primary-key
    conflict, the loser catches the ``IntegrityError``, rolls back,
    and re-reads the winning row. Either way the second SELECT is
    guaranteed to find exactly one row.

    Args:
        session: Active SQLAlchemy session.

    Returns:
        Metastore: The singleton metastore row. ``id`` is stable for
            the lifetime of the database.

    Raises:
        IntegrityError: If the row insert collides and the loser
            re-read still finds no row — unreachable in practice but
            re-raised rather than swallowed so a real bug surfaces.
    """
    row = session.scalar(select(Metastore))
    if row is not None:
        return row
    row = Metastore()
    session.add(row)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        row = session.scalar(select(Metastore))
        if row is None:
            raise
        return row
    session.refresh(row)
    return row
