"""Tests for GET/POST /delta/preview/commits.

The DeltaCommits preview endpoints implement the spec's passthrough
commit-coordinator contract (ADR-0011 supersedes ADR-0006's "no
coordinator" posture). ``POST`` persists commits to
:class:`soyuz_catalog.models.DeltaUnbackfilledCommit`, enforces
``commit_version == latest + 1``, catches duplicate races via the
database unique constraint, and prunes on
``latest_backfilled_version``. ``GET`` returns the coordinator's
live row set for the requested window plus the max-over-live-rows
``latest_table_version`` (falling back to the on-disk reader when
the coordinator has no rows for the table — the read-path for
freshly-attached tables that never staged a commit through soyuz).

These tests lock down the contract against a FastAPI ``TestClient``:

- file-URI GET happy path: empty list + on-disk version when no rows
- 400 on ``table_uri`` mismatch
- 404 on unknown ``table_id``
- 501 on non-``file://`` storage schemes (generic ``NOT_IMPLEMENTED``)
- 422 on ``extra="forbid"`` violations, missing required fields, and
  empty POST (no ``commit_info`` and no ``latest_backfilled_version``)
- POST happy path: 200 with empty body, follow-up GET returns the row
- POST 409 on duplicate version (pre-check)
- POST 400 on version gap
- POST 429 on per-table cap
- POST backfill prune: earlier rows disappear from GET, anchor row
  preserves ``latest_table_version``
- POST combined commit + backfill in a single call
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

deltalake = pytest.importorskip("deltalake")
pa = pytest.importorskip("pyarrow")

from deltalake import write_deltalake  # noqa: E402

CATALOGS = "/api/2.1/unity-catalog/catalogs"
SCHEMAS = "/api/2.1/unity-catalog/schemas"
TABLES = "/api/2.1/unity-catalog/tables"
COMMITS = "/api/2.1/unity-catalog/delta/preview/commits"


def _bootstrap_schema(client: TestClient) -> None:
    assert client.post(CATALOGS, json={"name": "main"}).status_code == 200
    assert client.post(SCHEMAS, json={"name": "s", "catalog_name": "main"}).status_code == 200


def _create_table(
    client: TestClient,
    name: str,
    storage_location: str,
) -> str:
    type_json = json.dumps({"name": "id", "type": "long", "nullable": True, "metadata": {}})
    body: dict[str, Any] = {
        "name": name,
        "catalog_name": "main",
        "schema_name": "s",
        "table_type": "EXTERNAL",
        "data_source_format": "DELTA",
        "storage_location": storage_location,
        "columns": [
            {
                "name": "id",
                "type_text": "bigint",
                "type_json": type_json,
                "type_name": "LONG",
                "position": 0,
                "nullable": True,
            }
        ],
    }
    r = client.post(TABLES, json=body)
    assert r.status_code == 200, r.text
    return r.json()["table_id"]


def _write_delta(tmp_path: Path, name: str) -> Path:
    table_path = tmp_path / name
    write_deltalake(str(table_path), pa.table({"id": pa.array([1, 2, 3], type=pa.int64())}))
    return table_path


def _commit_info(version: int, file_name: str = "00000000000000000001.json") -> dict[str, Any]:
    """Build a ``DeltaCommitInfo`` dict with filler metadata for tests.

    The Delta Kernel client sends real file metadata from a staged
    commit file on disk; these tests only need a payload that passes
    Pydantic validation, so we populate every required field with
    arbitrary but plausible scalars.
    """
    return {
        "version": version,
        "timestamp": 1_700_000_000_000 + version,
        "file_name": file_name,
        "file_size": 123,
        "file_modification_timestamp": 1_700_000_000_000 + version,
    }


def test_get_commits_file_scheme_returns_empty_list_and_ondisk_version(
    client: TestClient,
    tmp_path: Path,
) -> None:
    """GET on a coordinator-empty table falls back to the on-disk reader."""
    _bootstrap_schema(client)
    table_path = _write_delta(tmp_path, "t0")
    uri = f"file://{table_path}"
    table_id = _create_table(client, "t0", uri)

    r = client.request(
        "GET",
        COMMITS,
        json={"table_id": table_id, "table_uri": uri, "start_version": 0},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["commits"] == []
    assert body["latest_table_version"] == 0


def test_get_commits_accepts_optional_end_version(
    client: TestClient,
    tmp_path: Path,
) -> None:
    _bootstrap_schema(client)
    table_path = _write_delta(tmp_path, "t1")
    uri = f"file://{table_path}"
    table_id = _create_table(client, "t1", uri)

    r = client.request(
        "GET",
        COMMITS,
        json={
            "table_id": table_id,
            "table_uri": uri,
            "start_version": 0,
            "end_version": 5,
        },
    )
    assert r.status_code == 200, r.text
    assert r.json()["commits"] == []


def test_get_commits_400_on_table_uri_mismatch(
    client: TestClient,
    tmp_path: Path,
) -> None:
    _bootstrap_schema(client)
    table_path = _write_delta(tmp_path, "t2")
    uri = f"file://{table_path}"
    table_id = _create_table(client, "t2", uri)

    r = client.request(
        "GET",
        COMMITS,
        json={
            "table_id": table_id,
            "table_uri": "file:///tmp/not-the-registered-path",
            "start_version": 0,
        },
    )
    assert r.status_code == 400
    body = r.json()
    assert body["error_code"] == "INVALID_ARGUMENT"
    assert "does not match" in body["message"]


def test_get_commits_404_on_unknown_table_id(client: TestClient) -> None:
    r = client.request(
        "GET",
        COMMITS,
        json={
            "table_id": "00000000000000000000000000000000",
            "table_uri": "file:///tmp/nope",
            "start_version": 0,
        },
    )
    assert r.status_code == 404
    assert r.json()["error_code"] == "NOT_FOUND"


@pytest.mark.parametrize(
    "storage_location",
    [
        "s3://bucket/t",
        "s3a://bucket/t",
        "abfss://container@acct.dfs.core.windows.net/t",
        "gs://bucket/t",
    ],
)
def test_get_commits_501_on_non_file_scheme(
    client: TestClient,
    storage_location: str,
) -> None:
    _bootstrap_schema(client)
    table_id = _create_table(client, "cloud", storage_location)

    r = client.request(
        "GET",
        COMMITS,
        json={
            "table_id": table_id,
            "table_uri": storage_location,
            "start_version": 0,
        },
    )
    assert r.status_code == 501
    body = r.json()
    assert body["error_code"] == "NOT_IMPLEMENTED"
    assert "file://" in body["message"]


def test_get_commits_rejects_extra_field(client: TestClient) -> None:
    _bootstrap_schema(client)
    table_id = _create_table(client, "t3", "file:///tmp/t3")
    r = client.request(
        "GET",
        COMMITS,
        json={
            "table_id": table_id,
            "table_uri": "file:///tmp/t3",
            "start_version": 0,
            "bogus": 1,
        },
    )
    assert r.status_code == 422


def test_get_commits_rejects_missing_required_fields(client: TestClient) -> None:
    r = client.request("GET", COMMITS, json={"table_id": "x"})
    assert r.status_code == 422


def test_post_commit_happy_path_round_trip(
    client: TestClient,
    tmp_path: Path,
) -> None:
    """POST a commit, then GET it back through the same endpoint."""
    _bootstrap_schema(client)
    table_path = _write_delta(tmp_path, "t_post")
    uri = f"file://{table_path}"
    table_id = _create_table(client, "t_post", uri)

    r = client.post(
        COMMITS,
        json={
            "table_id": table_id,
            "table_uri": uri,
            "commit_info": _commit_info(version=1),
        },
    )
    assert r.status_code == 200, r.text
    assert r.json() == {}

    r = client.request(
        "GET",
        COMMITS,
        json={"table_id": table_id, "table_uri": uri, "start_version": 0},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body["commits"]) == 1
    assert body["commits"][0]["version"] == 1
    assert body["latest_table_version"] == 1


def test_post_commit_409_on_duplicate_version(
    client: TestClient,
    tmp_path: Path,
) -> None:
    _bootstrap_schema(client)
    table_path = _write_delta(tmp_path, "t_dup")
    uri = f"file://{table_path}"
    table_id = _create_table(client, "t_dup", uri)

    first = client.post(
        COMMITS,
        json={
            "table_id": table_id,
            "table_uri": uri,
            "commit_info": _commit_info(version=1),
        },
    )
    assert first.status_code == 200, first.text

    second = client.post(
        COMMITS,
        json={
            "table_id": table_id,
            "table_uri": uri,
            "commit_info": _commit_info(version=1, file_name="00000000000000000001-dup.json"),
        },
    )
    assert second.status_code == 409
    body = second.json()
    assert body["error_code"] == "ALREADY_EXISTS"
    assert "already exists" in body["message"]


def test_post_commit_400_on_version_gap(
    client: TestClient,
    tmp_path: Path,
) -> None:
    _bootstrap_schema(client)
    table_path = _write_delta(tmp_path, "t_gap")
    uri = f"file://{table_path}"
    table_id = _create_table(client, "t_gap", uri)

    r = client.post(
        COMMITS,
        json={
            "table_id": table_id,
            "table_uri": uri,
            "commit_info": _commit_info(version=5),
        },
    )
    assert r.status_code == 400
    body = r.json()
    assert body["error_code"] == "INVALID_ARGUMENT"
    assert "gap" in body["message"]


def test_post_commit_429_on_per_table_cap(
    client: TestClient,
    tmp_path: Path,
) -> None:
    """The 11th unbackfilled commit on a single table is rejected."""
    _bootstrap_schema(client)
    table_path = _write_delta(tmp_path, "t_cap")
    uri = f"file://{table_path}"
    table_id = _create_table(client, "t_cap", uri)

    for version in range(1, 11):
        r = client.post(
            COMMITS,
            json={
                "table_id": table_id,
                "table_uri": uri,
                "commit_info": _commit_info(version=version),
            },
        )
        assert r.status_code == 200, (version, r.text)

    overflow = client.post(
        COMMITS,
        json={
            "table_id": table_id,
            "table_uri": uri,
            "commit_info": _commit_info(version=11),
        },
    )
    assert overflow.status_code == 429
    body = overflow.json()
    assert body["error_code"] == "TOO_MANY_REQUESTS"
    assert "cap=10" in body["message"]


def test_post_backfill_prunes_earlier_rows_and_preserves_latest(
    client: TestClient,
    tmp_path: Path,
) -> None:
    """A follow-up POST with ``latest_backfilled_version`` prunes the row set."""
    _bootstrap_schema(client)
    table_path = _write_delta(tmp_path, "t_prune")
    uri = f"file://{table_path}"
    table_id = _create_table(client, "t_prune", uri)

    for version in range(1, 6):
        r = client.post(
            COMMITS,
            json={
                "table_id": table_id,
                "table_uri": uri,
                "commit_info": _commit_info(version=version),
            },
        )
        assert r.status_code == 200, (version, r.text)

    prune = client.post(
        COMMITS,
        json={
            "table_id": table_id,
            "table_uri": uri,
            "latest_backfilled_version": 4,
        },
    )
    assert prune.status_code == 200, prune.text

    r = client.request(
        "GET",
        COMMITS,
        json={"table_id": table_id, "table_uri": uri, "start_version": 0},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    versions = [c["version"] for c in body["commits"]]
    assert versions == [5]
    assert body["latest_table_version"] == 5


def test_post_combined_commit_and_backfill(
    client: TestClient,
    tmp_path: Path,
) -> None:
    """A single POST may carry both a new commit and a backfill ack."""
    _bootstrap_schema(client)
    table_path = _write_delta(tmp_path, "t_combo")
    uri = f"file://{table_path}"
    table_id = _create_table(client, "t_combo", uri)

    for version in range(1, 4):
        assert (
            client.post(
                COMMITS,
                json={
                    "table_id": table_id,
                    "table_uri": uri,
                    "commit_info": _commit_info(version=version),
                },
            ).status_code
            == 200
        )

    combo = client.post(
        COMMITS,
        json={
            "table_id": table_id,
            "table_uri": uri,
            "commit_info": _commit_info(version=4),
            "latest_backfilled_version": 3,
        },
    )
    assert combo.status_code == 200, combo.text

    r = client.request(
        "GET",
        COMMITS,
        json={"table_id": table_id, "table_uri": uri, "start_version": 0},
    )
    body = r.json()
    versions = [c["version"] for c in body["commits"]]
    assert versions == [4]
    assert body["latest_table_version"] == 4


def test_post_rejects_empty_body(client: TestClient, tmp_path: Path) -> None:
    """A POST with neither commit_info nor latest_backfilled_version is 422."""
    _bootstrap_schema(client)
    table_path = _write_delta(tmp_path, "t_empty")
    uri = f"file://{table_path}"
    table_id = _create_table(client, "t_empty", uri)

    r = client.post(
        COMMITS,
        json={"table_id": table_id, "table_uri": uri},
    )
    assert r.status_code == 422


def test_post_rejects_extra_field(client: TestClient, tmp_path: Path) -> None:
    _bootstrap_schema(client)
    table_path = _write_delta(tmp_path, "t_extra")
    uri = f"file://{table_path}"
    table_id = _create_table(client, "t_extra", uri)

    r = client.post(
        COMMITS,
        json={
            "table_id": table_id,
            "table_uri": uri,
            "latest_backfilled_version": 0,
            "bogus": 1,
        },
    )
    assert r.status_code == 422


def test_post_accepts_opaque_metadata_and_uniform(
    client: TestClient,
    tmp_path: Path,
) -> None:
    """``metadata`` and ``uniform`` pass-through fields are accepted as dicts."""
    _bootstrap_schema(client)
    table_path = _write_delta(tmp_path, "t_meta")
    uri = f"file://{table_path}"
    table_id = _create_table(client, "t_meta", uri)

    r = client.post(
        COMMITS,
        json={
            "table_id": table_id,
            "table_uri": uri,
            "commit_info": _commit_info(version=1),
            "metadata": {"arbitrary": "kernel-side-thing"},
            "uniform": {"iceberg_compat_version": 2},
        },
    )
    assert r.status_code == 200, r.text
