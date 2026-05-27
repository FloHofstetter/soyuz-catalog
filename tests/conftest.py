"""Shared pytest fixtures."""

from __future__ import annotations

import os
import socket
import tempfile
import threading
import time
from collections.abc import Generator, Iterator
from pathlib import Path

import pytest
import uvicorn
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import soyuz_catalog.db as db_module
from soyuz_catalog.api.deps import get_db
from soyuz_catalog.api.main import create_app
from soyuz_catalog.models import Base
from soyuz_catalog.settings import reset_settings_cache

# ---------------------------------------------------------------------------
# Multi-backend support (ADR-0004)
#
# ``--db-backend=sqlite`` (the default) runs every ``session_factory``-based
# test against an in-memory SQLite engine. Passing
# ``--db-backend=postgres`` re-points the fixture at a real Postgres engine
# built once per session from ``SOYUZ_TEST_POSTGRES_URL`` (see
# ``docker-compose.yml`` for the default creds). Tests themselves are
# unchanged: they only depend on ``session_factory``, and the fixture below
# decides which backend to serve.
#
# Postgres-only test state is handled by dropping + recreating the ``public``
# schema once per session (which forces a fresh Alembic upgrade through
# ``db.run_migrations``), then ``TRUNCATE ... RESTART IDENTITY CASCADE`` on
# every table between tests. That is faster than a drop/recreate per test
# while still giving complete isolation.
# ---------------------------------------------------------------------------


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--db-backend",
        action="store",
        default="sqlite",
        choices=("sqlite", "postgres"),
        help="Which database backend the session_factory fixture should point at.",
    )


def _default_pg_url() -> str:
    return os.environ.get(
        "SOYUZ_TEST_POSTGRES_URL",
        "postgresql+psycopg://soyuz:soyuz@localhost:5432/soyuz",  # pragma: allowlist secret
    )


@pytest.fixture(scope="session")
def postgres_engine() -> Iterator[tuple[Engine, sessionmaker[Session]]]:
    """Session-scoped Postgres engine with a fresh schema + Alembic upgrade.

    Skips cleanly when the target URL is unreachable, so local dev without
    docker keeps working. The drop-and-recreate of the ``public`` schema
    guarantees every test session exercises the real Alembic migration
    path from zero, not ``Base.metadata.create_all`` — which is the whole
    point of the Postgres validation sprint.

    The fixture is intentionally decoupled from the module-level engine
    managed by :mod:`soyuz_catalog.db`. Tests that need a FastAPI app
    override ``get_db`` onto the sessionmaker returned here, so nothing in
    the per-test reset flow can dispose the engine out from under a
    running test.

    Yields:
        tuple[Engine, sessionmaker[Session]]: The engine and its bound
            sessionmaker; both stay alive for the whole pytest session.
    """
    url = _default_pg_url()
    try:
        engine = create_engine(url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except OperationalError as exc:
        pytest.skip(f"Postgres not reachable at {url}: {exc}")

    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))

    # run_migrations opens its own Alembic connection for non-in-memory
    # URLs; it does not touch db_module._engine, so our session-scoped
    # engine is safe from the per-test reset_db_state().
    db_module.run_migrations(url)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    try:
        yield engine, factory
    finally:
        engine.dispose()


def _truncate_all(engine: Engine) -> None:
    """TRUNCATE every table tracked by ``Base.metadata`` on Postgres.

    Args:
        engine: Engine bound to the Postgres database under test.
    """
    tables = ", ".join(f'"{t.name}"' for t in Base.metadata.sorted_tables)
    if not tables:
        return
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))


@pytest.fixture(autouse=True)
def _reset_state(request: pytest.FixtureRequest) -> Iterator[None]:
    # Integration tests own their own engine via the live_server fixture;
    # tearing down the module-level state in the middle would dispose the
    # engine the background uvicorn thread is still using.
    if "integration" in request.keywords:
        yield
        return
    backend = request.config.getoption("--db-backend")
    use_postgres = backend == "postgres" or "postgres" in request.keywords
    if use_postgres:
        engine, _factory = request.getfixturevalue("postgres_engine")
        _truncate_all(engine)
        reset_settings_cache()
        # db_module's module-level engine is untouched by postgres_engine,
        # but we still reset so any stray init_db() from a prior test
        # run doesn't leak.
        db_module.reset_db_state()
        yield
        _truncate_all(engine)
        reset_settings_cache()
        return
    reset_settings_cache()
    db_module.reset_db_state()
    yield
    db_module.reset_db_state()
    reset_settings_cache()


@pytest.fixture(autouse=True)
def deterministic_clock(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Replace ``models._base._epoch_ms`` with a monotonic ms counter.

    Production code reads the wall clock through
    :func:`soyuz_catalog.models._base._now_ms`, which delegates to
    :func:`_epoch_ms`. SQLAlchemy ``default=_now_ms`` columns capture
    the function reference at table-definition time, so a direct patch
    on ``_now_ms`` is bypassed — patching ``_epoch_ms`` via the module
    namespace works because ``_now_ms``'s body resolves ``_epoch_ms``
    through ``__globals__`` on every call.

    The counter starts at the real wall clock so any code that
    subtracts two timestamps (e.g. duration logging) still produces
    sane values, and increments by 1 ms per call. Autouse because the
    tick is purely monotonic — no test asserts an absolute timestamp
    against the wall clock; the existing tests assert order or
    ``>=`` between two reads, both of which a monotonic counter
    satisfies by construction. The fixture lets us drop the
    ``time.sleep(0.002)`` calls that previously disambiguated rows
    landing in the same millisecond.

    Args:
        monkeypatch: Pytest fixture used to swap the module attribute.

    Yields:
        None: Cleanup happens automatically when monkeypatch unwinds.
    """
    from soyuz_catalog.models import _base

    tick = [int(time.time() * 1000)]

    def fake_epoch_ms() -> int:
        tick[0] += 1
        return tick[0]

    monkeypatch.setattr(_base, "_epoch_ms", fake_epoch_ms)
    yield


def _sqlite_factory() -> sessionmaker[Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture
def session_factory(request: pytest.FixtureRequest) -> sessionmaker[Session]:
    """Return a sessionmaker bound to the requested backend.

    ``--db-backend=sqlite`` (default) returns a fresh per-test in-memory
    SQLite engine; ``--db-backend=postgres`` returns the session-scoped
    Postgres factory built by :func:`postgres_engine`. Tests marked
    ``@pytest.mark.postgres`` always use Postgres regardless of the CLI
    flag, so you can target a single test without flipping the whole suite.

    Args:
        request: Pytest request, used to read ``--db-backend`` and detect
            the ``postgres`` marker.

    Returns:
        sessionmaker[Session]: A session factory ready to hand to the
        service layer.
    """
    backend = request.config.getoption("--db-backend")
    if backend == "postgres" or "postgres" in request.keywords:
        _engine, factory = request.getfixturevalue("postgres_engine")
        return factory
    return _sqlite_factory()


@pytest.fixture
def client(session_factory: sessionmaker[Session]) -> TestClient:
    app = create_app()

    def _override_get_db() -> Generator[Session]:
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _override_get_db

    # Skip the lifespan (which would try to init the real DB); we already
    # have an in-memory engine wired via the dependency override.
    return TestClient(app, raise_server_exceptions=True)


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture
def live_server() -> Iterator[str]:
    """Spin up the FastAPI app under uvicorn on a free port for HTTP tests.

    Used by integration tests that need a real socket — the unitycatalog
    Python SDK and similar third-party clients go through httpx/reqwest and
    cannot use FastAPI's in-process TestClient. The server runs in a daemon
    thread so teardown does not block test exit. A tempfile-backed SQLite DB
    is shared between the request thread and the background uvicorn worker
    (in-memory + StaticPool would not survive the cross-thread access pattern
    that the live request handlers introduce).

    Yields:
        str: Base URL like ``http://127.0.0.1:54321`` (no trailing slash).
    """
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    db_path = Path(tmp.name)
    db_url = f"sqlite:///{db_path}"

    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def _override_get_db() -> Generator[Session]:
        session = factory()
        try:
            yield session
        finally:
            session.close()

    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db

    port = _free_port()
    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=port,
        log_level="warning",
        lifespan="off",
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    deadline = time.monotonic() + 5.0
    while not server.started:
        if time.monotonic() > deadline:
            server.should_exit = True
            thread.join(timeout=2)
            raise RuntimeError("uvicorn live_server failed to start within 5s")
        time.sleep(0.02)

    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.should_exit = True
        thread.join(timeout=5)
        engine.dispose()
        db_path.unlink(missing_ok=True)
