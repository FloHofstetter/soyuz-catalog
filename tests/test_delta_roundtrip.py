"""End-to-end Delta-Lake round-trip against a live soyuz-catalog server.

The compat target is the *unmodified* ``unitycatalog`` Python SDK
(PyPI, Stainless-generated): create a catalog/schema/table via the
SDK, then read the table back with ``deltalake.DeltaTable`` from the
storage location the SDK returns. Any failure in this test is a bug
in soyuz, not in the test — the test exists precisely to surface
those bugs against a real client.

Marked `@pytest.mark.integration` so it is skipped from the default suite
(see ``pyproject.toml``: ``addopts = "-m 'not integration'"``); opt in with
``pytest -m integration``.
"""

from __future__ import annotations

import json

import httpx
import pytest

deltalake = pytest.importorskip("deltalake")
pa = pytest.importorskip("pyarrow")
unitycatalog = pytest.importorskip("unitycatalog")

from deltalake import DeltaTable, write_deltalake  # noqa: E402

from tests._sdk import make_uc_client  # noqa: E402

pytestmark = pytest.mark.integration


def test_live_server_healthz(live_server: str) -> None:
    response = httpx.get(f"{live_server}/healthz", timeout=5.0)
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_delta_read_round_trip(live_server: str, tmp_path) -> None:
    table_path = tmp_path / "round_trip"
    original = pa.table({"id": pa.array([1, 2, 3], type=pa.int64())})
    write_deltalake(str(table_path), original)

    client = make_uc_client(live_server)

    client.catalogs.create(name="main")
    client.schemas.create(catalog_name="main", name="default")

    type_json = json.dumps({"name": "id", "type": "long", "nullable": True, "metadata": {}})
    client.tables.create(
        name="round_trip",
        catalog_name="main",
        schema_name="default",
        table_type="EXTERNAL",
        data_source_format="DELTA",
        storage_location=f"file://{table_path}",
        columns=[
            {
                "name": "id",
                "type_text": "bigint",
                "type_json": type_json,
                "type_name": "LONG",
                "position": 0,
                "nullable": True,
            }
        ],
    )

    info = client.tables.retrieve("main.default.round_trip")
    assert info.storage_location == f"file://{table_path}"
    assert info.table_id is not None
    assert info.columns is not None and len(info.columns) == 1
    assert info.columns[0].name == "id"
    assert info.columns[0].type_name == "LONG"

    storage_location = info.storage_location
    assert storage_location is not None
    dt = DeltaTable(storage_location)
    round_tripped = dt.to_pyarrow_table()
    assert round_tripped.equals(original)


def test_delta_write_round_trip(live_server: str, tmp_path) -> None:
    """Create the catalog entry *before* the Delta files exist.

    The read round-trip test writes the Delta table first and then
    registers it. The write round-trip flips the order: register an
    EXTERNAL Delta table pointing at a not-yet-existent directory, then
    use the ``storage_location`` the server hands back to drive a
    subsequent ``write_deltalake`` call, then read it back through the
    same ``DeltaTable`` path the read test uses. This is the flow a
    Spark / Databricks notebook follows in practice — create the table
    in the catalog and only then materialise the data — and it is the
    thing that would break if soyuz silently rewrote ``storage_location``
    or rejected a missing directory at create time.
    """
    table_path = tmp_path / "write_trip"

    client = make_uc_client(live_server)

    client.catalogs.create(name="main")
    client.schemas.create(catalog_name="main", name="default")

    type_json = json.dumps({"name": "id", "type": "long", "nullable": True, "metadata": {}})
    client.tables.create(
        name="write_trip",
        catalog_name="main",
        schema_name="default",
        table_type="EXTERNAL",
        data_source_format="DELTA",
        storage_location=f"file://{table_path}",
        columns=[
            {
                "name": "id",
                "type_text": "bigint",
                "type_json": type_json,
                "type_name": "LONG",
                "position": 0,
                "nullable": True,
            }
        ],
    )

    info = client.tables.retrieve("main.default.write_trip")
    assert info.storage_location == f"file://{table_path}"
    assert info.table_id is not None

    original = pa.table({"id": pa.array([10, 20, 30], type=pa.int64())})
    assert info.storage_location is not None
    write_deltalake(info.storage_location.removeprefix("file://"), original)

    dt = DeltaTable(info.storage_location)
    round_tripped = dt.to_pyarrow_table()
    assert round_tripped.equals(original)


def test_temporary_table_credentials_stub_for_file_storage(
    live_server: str,
    tmp_path,
) -> None:
    """The credentials endpoint answers the table id a real client holds.

    The ``unitycatalog`` SDK does not call ``/temporary-table-credentials``
    for ``file://`` storage — its Delta code path goes straight to the
    local filesystem — so we have to hit the endpoint via plain httpx to
    verify the stub contract end-to-end against a live server.
    The shape assertion matches the unit tests: only ``expiration_time``
    on the wire, no cloud-specific fields, with an opt-in 400 on the
    ``UNKNOWN_TABLE_OPERATION`` sentinel so a real client that mis-wires
    its operation enum fails loudly.
    """
    table_path = tmp_path / "creds_stub"

    client = make_uc_client(live_server)
    client.catalogs.create(name="main")
    client.schemas.create(catalog_name="main", name="default")

    type_json = json.dumps({"name": "id", "type": "long", "nullable": True, "metadata": {}})
    client.tables.create(
        name="creds_stub",
        catalog_name="main",
        schema_name="default",
        table_type="EXTERNAL",
        data_source_format="DELTA",
        storage_location=f"file://{table_path}",
        columns=[
            {
                "name": "id",
                "type_text": "bigint",
                "type_json": type_json,
                "type_name": "LONG",
                "position": 0,
                "nullable": True,
            }
        ],
    )
    info = client.tables.retrieve("main.default.creds_stub")
    assert info.table_id is not None

    creds_url = f"{live_server}/api/2.1/unity-catalog/temporary-table-credentials"

    ok = httpx.post(
        creds_url,
        json={"table_id": info.table_id, "operation": "READ"},
        timeout=5.0,
    )
    assert ok.status_code == 200, ok.text
    body = ok.json()
    assert set(body.keys()) == {"expiration_time"}
    assert body["expiration_time"] > 0

    sentinel = httpx.post(
        creds_url,
        json={"table_id": info.table_id, "operation": "UNKNOWN_TABLE_OPERATION"},
        timeout=5.0,
    )
    assert sentinel.status_code == 400
    assert sentinel.json()["error_code"] == "INVALID_ARGUMENT"


def test_delta_get_commits_preview(live_server: str, tmp_path) -> None:
    """End-to-end check of GET / POST /delta/preview/commits against a live server.

    The ``unitycatalog`` Python SDK does not expose the DeltaCommits
    namespace at the pinned version, so this test drives the endpoint
    via raw ``httpx`` — same pattern other SDK-uncovered resources
    (credentials, external locations) use.

    Covers the four paths the unit suite pins against a FastAPI
    ``TestClient``: the empty-commits happy path on a ``file://``
    Delta table, the 400 ``table_uri`` mismatch, the 501 POST, and
    the 501 non-``file://`` scheme. Running them against a real
    uvicorn process is what catches bugs the in-process TestClient
    silently swallows — primarily anything to do with how ASGI
    middleware handles a GET-with-body request, which is the spec
    shape of this endpoint.
    """
    table_path = tmp_path / "commits_preview"
    original = pa.table({"id": pa.array([1, 2, 3], type=pa.int64())})
    write_deltalake(str(table_path), original)

    client = make_uc_client(live_server)
    client.catalogs.create(name="main")
    client.schemas.create(catalog_name="main", name="default")

    type_json = json.dumps({"name": "id", "type": "long", "nullable": True, "metadata": {}})
    registered_uri = f"file://{table_path}"
    client.tables.create(
        name="commits_preview",
        catalog_name="main",
        schema_name="default",
        table_type="EXTERNAL",
        data_source_format="DELTA",
        storage_location=registered_uri,
        columns=[
            {
                "name": "id",
                "type_text": "bigint",
                "type_json": type_json,
                "type_name": "LONG",
                "position": 0,
                "nullable": True,
            }
        ],
    )
    info = client.tables.retrieve("main.default.commits_preview")
    assert info.table_id is not None

    commits_url = f"{live_server}/api/2.1/unity-catalog/delta/preview/commits"

    # 1. happy path — GET with body, empty list, version 0
    ok = httpx.request(
        "GET",
        commits_url,
        json={
            "table_id": info.table_id,
            "table_uri": registered_uri,
            "start_version": 0,
        },
        timeout=5.0,
    )
    assert ok.status_code == 200, ok.text
    body = ok.json()
    assert body["commits"] == []
    assert body["latest_table_version"] == 0

    # 2. table_uri mismatch → 400
    mismatch = httpx.request(
        "GET",
        commits_url,
        json={
            "table_id": info.table_id,
            "table_uri": "file:///tmp/somewhere-else",
            "start_version": 0,
        },
        timeout=5.0,
    )
    assert mismatch.status_code == 400
    assert mismatch.json()["error_code"] == "INVALID_ARGUMENT"

    # 3. POST → 501 (soyuz has no commit coordinator)
    post = httpx.post(
        commits_url,
        json={
            "table_id": info.table_id,
            "table_uri": registered_uri,
            "latest_backfilled_version": 0,
        },
        timeout=5.0,
    )
    assert post.status_code == 501
    assert post.json()["error_code"] == "NOT_IMPLEMENTED"

    # 4. non-file:// scheme → 501 (cloud storage needs credential vending)
    client.tables.create(
        name="cloud_preview",
        catalog_name="main",
        schema_name="default",
        table_type="EXTERNAL",
        data_source_format="DELTA",
        storage_location="s3://bucket/cloud_preview",
        columns=[
            {
                "name": "id",
                "type_text": "bigint",
                "type_json": type_json,
                "type_name": "LONG",
                "position": 0,
                "nullable": True,
            }
        ],
    )
    cloud_info = client.tables.retrieve("main.default.cloud_preview")
    assert cloud_info.table_id is not None

    cloud = httpx.request(
        "GET",
        commits_url,
        json={
            "table_id": cloud_info.table_id,
            "table_uri": "s3://bucket/cloud_preview",
            "start_version": 0,
        },
        timeout=5.0,
    )
    assert cloud.status_code == 501
    cloud_body = cloud.json()
    assert cloud_body["error_code"] == "NOT_IMPLEMENTED"
    assert "file://" in cloud_body["message"]
