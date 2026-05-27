"""Database engine, session factory, and embedded Alembic migrations."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from alembic import command
from alembic.config import Config as AlembicConfig
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from soyuz_catalog.exceptions import ConflictError

logger = logging.getLogger(__name__)

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def _alembic_dir() -> str:
    """Return the path to the embedded alembic directory.

    Returns:
        str: Absolute path to the alembic directory inside the package.
    """
    return str(Path(__file__).parent / "alembic")


def _alembic_config(url: str) -> AlembicConfig:
    """Build a programmatic Alembic configuration.

    Args:
        url: SQLAlchemy database URL.

    Returns:
        AlembicConfig: Configured Alembic config instance.
    """
    cfg = AlembicConfig()
    cfg.set_main_option("script_location", _alembic_dir())
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg


def init_db(url: str) -> Engine:
    """Create the engine and the session factory.

    Called exactly once from the FastAPI lifespan. Stores the engine and
    sessionmaker at module level so request handlers can grab a session via
    :func:`get_session_factory` without threading a context object through
    every call site. SQLite gets a ``connect`` listener that sets WAL mode
    and ``foreign_keys=ON`` per connection — these are PRAGMAs, not engine
    options, so they have to be applied on each new DBAPI connection rather
    than once at engine creation.

    Args:
        url: SQLAlchemy database URL.

    Returns:
        Engine: The initialised SQLAlchemy engine.
    """
    global _engine, _session_factory  # noqa: PLW0603

    is_sqlite = url.startswith("sqlite")
    connect_args: dict[str, object] = {}
    if is_sqlite:
        connect_args["check_same_thread"] = False

    _engine = create_engine(url, connect_args=connect_args, pool_pre_ping=True)

    if is_sqlite:

        @event.listens_for(_engine, "connect")
        def _set_sqlite_pragma(dbapi_conn: Any, _record: Any) -> None:
            cursor = dbapi_conn.cursor()
            try:
                # ``journal_mode`` is a file-persistent SQLite setting,
                # so it only needs to be set once.  When the engine
                # spawns a new connection while other connections are
                # already mid-transaction (which happens routinely
                # under bursty fan-out — e.g. a UI sidebar that
                # issues N parallel list calls) calling
                # ``PRAGMA journal_mode=WAL`` racing with an active
                # writer raises ``sqlite3.OperationalError: disk I/O
                # error``.  Read the current mode first; only set it
                # if it is not already WAL.  busy_timeout, synchronous,
                # and foreign_keys are per-connection and stay on the
                # always-set path.
                cursor.execute("PRAGMA journal_mode")
                current = cursor.fetchone()
                current_mode = (current[0] if current else "").lower()
                if current_mode != "wal":
                    cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA busy_timeout=5000")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA foreign_keys=ON")
            finally:
                cursor.close()

    _session_factory = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False)
    logger.info("Database initialised (%s)", url.split("://")[0])
    return _engine


def run_migrations(url: str) -> None:
    """Run Alembic migrations to ``head``.

    For in-memory SQLite (``sqlite://`` / ``sqlite:///:memory:``) we bypass
    Alembic entirely and call ``Base.metadata.create_all`` instead. The
    migration history is irrelevant for a throwaway database, and Alembic's
    ``upgrade`` would open a fresh connection, breaking the StaticPool that
    the in-memory engine relies on to share state between sessions.

    Args:
        url: SQLAlchemy database URL.

    Raises:
        RuntimeError: If :func:`init_db` has not been called yet for an
            in-memory SQLite URL.
    """
    if url in {"sqlite:///:memory:", "sqlite://"}:
        from soyuz_catalog.models import Base

        if _engine is None:
            raise RuntimeError("init_db() must be called before run_migrations()")
        Base.metadata.create_all(_engine)
        return

    cfg = _alembic_config(url)
    command.upgrade(cfg, "head")


def get_engine() -> Engine:
    """Return the active engine.

    Returns:
        Engine: The active SQLAlchemy engine.

    Raises:
        RuntimeError: If :func:`init_db` has not been called.
    """
    if _engine is None:
        raise RuntimeError("Database not initialised — call init_db() first")
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    """Return the active session factory.

    Returns:
        sessionmaker[Session]: The configured session factory.

    Raises:
        RuntimeError: If :func:`init_db` has not been called.
    """
    if _session_factory is None:
        raise RuntimeError("Database not initialised — call init_db() first")
    return _session_factory


def reset_db_state() -> None:
    """Dispose the module-level engine and clear the session factory.

    The test suite rebuilds a fresh SQLite file (or Postgres schema)
    between fixtures and expects the next ``init_db`` to construct a
    brand-new ``Engine``; leaving the previous engine in place would
    pin stale connection-pool state to the old URL. Production code
    never calls this — the engine lives for the full process lifetime
    via the FastAPI lifespan.
    """
    global _engine, _session_factory  # noqa: PLW0603
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None


@contextmanager
def commit_or_conflict(session: Session, message: str) -> Iterator[None]:
    """Commit on success, translate IntegrityError to ConflictError.

    The single most common write pattern in the service layer is: add
    (or mutate) a row, commit, and on a uniqueness violation raise a
    409 with a resource-specific message. This wrapper collapses
    roughly a dozen lines of boilerplate (try/commit/except
    IntegrityError → rollback → raise ConflictError(...) from exc)
    into a one-line ``with`` so service functions read as one
    transaction per visible block. Other exceptions also trigger a
    rollback and re-raise unchanged.

    Args:
        session: Active SQLAlchemy session.
        message: Human-readable conflict message (e.g.
            ``"Catalog 'main' already exists"``). Passed verbatim into
            :class:`~soyuz_catalog.exceptions.ConflictError`, which
            the API layer renders as a 409 body.

    Yields:
        None: Control returns to the ``with`` body; commit runs on
            normal exit, rollback on any exception.

    Raises:
        ConflictError: When the wrapped commit raises ``IntegrityError``.
    """
    try:
        yield
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise ConflictError(message) from exc
    except Exception:
        session.rollback()
        raise


@contextmanager
def commit_or_raise(session: Session) -> Iterator[None]:
    """Commit on success, rollback and re-raise on any failure.

    Used by service functions that intentionally do **not** translate
    :class:`sqlalchemy.exc.IntegrityError` into a domain exception —
    the permissions service relies on IntegrityError bubbling out so
    a concurrent grant-creation race is signalled to the caller as
    the same exception type SQLAlchemy raised, rather than swallowed
    behind a 409.

    Args:
        session: Active SQLAlchemy session.

    Yields:
        None: Control returns to the ``with`` body; commit runs on
            normal exit, rollback on any exception.
    """
    try:
        yield
        session.commit()
    except Exception:
        session.rollback()
        raise
