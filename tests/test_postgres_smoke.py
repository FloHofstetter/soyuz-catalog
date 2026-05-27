"""Postgres backend smoke tests (ADR-0004).

Marked ``@pytest.mark.postgres`` and deselected by default. These are the
canary tests proving that the Alembic migration path builds a valid schema
on a real Postgres database and that an HTTP catalog create / read cycle
succeeds against it. The broader suite is re-run against Postgres via
``pytest --db-backend=postgres -m "not integration"`` (which
re-parametrizes every ``session_factory``-based test).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect, text

from soyuz_catalog.models import Base

pytestmark = pytest.mark.postgres

PREFIX = "/api/2.1/unity-catalog/catalogs"


def test_alembic_migrations_create_every_orm_table(postgres_engine) -> None:
    engine, _factory = postgres_engine
    inspector = inspect(engine)
    actual = set(inspector.get_table_names(schema="public"))
    expected = {t.name for t in Base.metadata.sorted_tables}
    assert expected.issubset(actual), f"missing tables on postgres: {expected - actual}"


def test_postgres_reports_bigint_timestamps(postgres_engine) -> None:
    """ms-epoch does not fit in int4 past 2038 — the migration must ship BIGINT.

    This is the one dialect-specific hazard worth pinning explicitly:
    the ORM models declare ``Mapped[int]`` (which defaults to ``Integer``)
    but the Alembic migrations explicitly use ``BigInteger``. On SQLite the
    difference is invisible; on Postgres, an ``integer`` column would
    silently corrupt ms-epoch writes after 2038. Lock the migration
    behaviour down so nobody ever "simplifies" it.
    """
    engine, _factory = postgres_engine
    with engine.connect() as conn:
        row = conn.execute(
            text(
                "SELECT data_type FROM information_schema.columns "
                "WHERE table_name = 'catalogs' AND column_name = 'created_at'"
            )
        ).scalar_one()
    assert row == "bigint"


@pytest.mark.parametrize("table", ["credentials", "external_locations"])
def test_postgres_reports_bigint_timestamps_on_storage_credentials_tables(
    postgres_engine,
    table: str,
) -> None:
    """Same BIGINT trap, same lock-down, on the storage-credential tables.

    Alembic revision 006 creates ``credentials`` and
    ``external_locations``. Pin ``created_at`` as ``bigint`` on both so
    nobody "simplifies" the migration later.
    """
    engine, _factory = postgres_engine
    with engine.connect() as conn:
        row = conn.execute(
            text(
                "SELECT data_type FROM information_schema.columns "
                "WHERE table_name = :t AND column_name = 'created_at'"
            ),
            {"t": table},
        ).scalar_one()
    assert row == "bigint"


def test_catalog_round_trip_over_http_on_postgres(client: TestClient) -> None:
    r = client.post(PREFIX, json={"name": "cat_pg_smoke", "comment": "hello postgres"})
    assert r.status_code == 200, r.text
    assert r.json()["name"] == "cat_pg_smoke"

    r = client.get(f"{PREFIX}/cat_pg_smoke")
    assert r.status_code == 200, r.text
    assert r.json()["comment"] == "hello postgres"
