"""Tests for ``GET /metastore_summary``.

The endpoint exposes exactly one field (``metastore_id``) and the
backing row is bootstrapped lazily on first call — see
:mod:`soyuz_catalog.services.metastore_service`. These tests lock
down the contract surface plus the lazy-bootstrap invariant.
"""

from __future__ import annotations

import re

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker

from soyuz_catalog.models import Metastore

METASTORE = "/api/2.1/unity-catalog/metastore_summary"

_HEX32 = re.compile(r"^[0-9a-f]{32}$")


def test_metastore_summary_bootstraps_lazily(client: TestClient) -> None:
    r = client.get(METASTORE)
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body.keys()) == {"metastore_id"}
    assert _HEX32.match(body["metastore_id"]), body["metastore_id"]


def test_metastore_summary_is_stable_across_calls(client: TestClient) -> None:
    first = client.get(METASTORE).json()["metastore_id"]
    second = client.get(METASTORE).json()["metastore_id"]
    third = client.get(METASTORE).json()["metastore_id"]
    assert first == second == third


def test_metastore_summary_creates_exactly_one_row(
    client: TestClient,
    session_factory: sessionmaker,
) -> None:
    # Several concurrent-looking hits shouldn't produce multiple rows.
    for _ in range(5):
        assert client.get(METASTORE).status_code == 200
    with session_factory() as session:
        count = session.scalar(select(func.count()).select_from(Metastore))
    assert count == 1
