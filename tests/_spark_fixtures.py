"""Shared pyspark fixtures for Spark integration tests.

This module is deliberately prefixed with an underscore so pytest does not
collect it as a test file, and deliberately **not** placed in
``conftest.py``: the fixtures here start a JVM via ``pyspark``, which takes
~20s to warm up and requires the ``spark`` optional extra. ``conftest.py``
is loaded unconditionally for every pytest run, so putting the fixtures
there would either break the default (no-pyspark) suite or pay the JVM
cost on every developer invocation.

Instead, the two Spark-facing test modules
(:mod:`tests.test_spark_roundtrip` for the must-pass external-Delta
gate, and :mod:`tests.test_spark_compatibility` for the parametrised
gap audit) each ``pytest.importorskip("pyspark")`` at module top
*before* importing from here. That keeps the default suite clean
while letting the two modules share a single module-scoped JVM and
live hypercorn server across parametrised cases — the ~20s warm-up
is paid exactly once per Spark-enabled pytest invocation.
"""

from __future__ import annotations

import asyncio
import socket
import threading
from collections.abc import Generator, Iterator

import pytest
from hypercorn.asyncio import serve
from hypercorn.config import Config as HypercornConfig
from pyspark.sql import SparkSession
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from soyuz_catalog.api.deps import get_db
from soyuz_catalog.api.main import create_app
from soyuz_catalog.models import Base
from tests._spark_helpers import CATALOG_NAME, CONNECTOR_PACKAGES


def free_port() -> int:
    """Return an unused TCP port on loopback."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture(scope="module")
def module_live_server(tmp_path_factory: pytest.TempPathFactory) -> Iterator[str]:
    """Module-scoped live **hypercorn** server for Spark-facing tests.

    Mirrors :func:`tests.conftest.live_server` but runs under hypercorn
    (not uvicorn) and is module-scoped so the JVM started by
    :func:`spark_session` can bind to a single stable base URL for the
    whole module.

    Why hypercorn instead of the conftest uvicorn fixture: the upstream
    JVM ``UCSingleCatalog`` connector uses Java ``HttpClient``, which
    defaults to HTTP/2 and advertises ``Upgrade: h2c`` on its first
    HTTP/1.1 request. uvicorn's httptools parser leaves its state machine
    stuck after the upgrade event, and the JVM client's pipelined
    follow-up request then hits the broken parser as raw bytes and gets
    rejected with a 400 "Invalid HTTP request received". hypercorn's
    ``h2c`` + HTTP/2 support handles the upgrade cleanly and keeps the
    same connection alive through the follow-up pipelined requests the
    JVM client actually sends in practice.

    Yields:
        str: Base URL like ``http://127.0.0.1:54321`` (no trailing slash).
    """
    work = tmp_path_factory.mktemp("live_server_module")
    db_path = work / "soyuz.db"
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

    port = free_port()
    config = HypercornConfig()
    config.bind = [f"127.0.0.1:{port}"]
    config.loglevel = "WARNING"
    config.accesslog = None
    config.h2_max_concurrent_streams = 100

    shutdown_event = asyncio.Event()
    loop_ready = threading.Event()
    loop_holder: dict[str, asyncio.AbstractEventLoop] = {}

    async def _serve() -> None:
        loop_holder["loop"] = asyncio.get_running_loop()
        loop_ready.set()
        await serve(app, config, shutdown_trigger=shutdown_event.wait)  # type: ignore[arg-type]

    def _run() -> None:
        asyncio.run(_serve())

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    loop_ready.wait(timeout=5.0)

    import time as _time

    deadline = _time.monotonic() + 5.0
    while _time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                break
        except OSError:
            _time.sleep(0.05)
    else:
        raise RuntimeError("hypercorn module_live_server failed to start within 5s")

    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        loop = loop_holder.get("loop")
        if loop is not None:
            loop.call_soon_threadsafe(shutdown_event.set)
        thread.join(timeout=5)
        engine.dispose()


@pytest.fixture(scope="module")
def spark_session(
    module_live_server: str,
    tmp_path_factory: pytest.TempPathFactory,
) -> Iterator[SparkSession]:
    """Build a SparkSession wired to the live soyuz server.

    Config matches upstream's own smoke recipe at
    ``unitycatalog/docs/integrations/unity-catalog-spark.md`` — Delta
    extensions on, ``UCSingleCatalog`` as the catalog plugin, the live
    server's base URL as the ``.uri``, and an **empty** ``.token``
    (soyuz has no auth; the connector treats an empty string as no-auth).
    ``spark.jars.packages`` pulls the connector + delta-spark from Maven
    Central into ``~/.ivy2/`` — on CI this is cached; locally it is a
    one-time cost.

    Module-scoped so the JVM is only started once per test module —
    ``pyspark`` on ``local[*]`` takes 20+ seconds to warm up. The
    compatibility sweep and the roundtrip test each get their own
    module-scoped session; pytest schedules them in separate module
    groups, so the JVM cost is paid twice in the worst case. If that
    ever becomes a bottleneck, lift the scope to ``"session"`` and
    add a reset hook — there is no state coupling between the two
    modules beyond the live server (which is already module-scoped).

    Args:
        module_live_server: The live-server base URL from the
            module-scoped hypercorn fixture.
        tmp_path_factory: Pytest factory for the Spark warehouse /
            derby-metastore paths.

    Yields:
        SparkSession: A configured SparkSession ready for SQL.
    """
    work = tmp_path_factory.mktemp("spark")
    warehouse = work / "warehouse"
    derby = work / "derby"
    warehouse.mkdir()
    derby.mkdir()

    uri = f"{module_live_server}/api/2.1/unity-catalog"
    spark = (
        SparkSession.builder.master("local[*]")
        .appName("soyuz-spark-fixtures")
        .config("spark.jars.packages", CONNECTOR_PACKAGES)
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config(
            "spark.sql.catalog.spark_catalog",
            "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        )
        .config(f"spark.sql.catalog.{CATALOG_NAME}", "io.unitycatalog.spark.UCSingleCatalog")
        .config(f"spark.sql.catalog.{CATALOG_NAME}.uri", uri)
        .config(f"spark.sql.catalog.{CATALOG_NAME}.token", "")
        .config("spark.sql.defaultCatalog", CATALOG_NAME)
        .config("spark.sql.warehouse.dir", str(warehouse))
        .config("spark.driver.extraJavaOptions", f"-Dderby.system.home={derby}")
        .getOrCreate()
    )
    try:
        yield spark
    finally:
        spark.stop()
