"""Tests for the recipient-facing Delta Sharing protocol surface (ADR-0015).

Exercises the wire contract from PROTOCOL.md against real Delta
tables fabricated with ``deltalake.write_deltalake`` on ``tmp_path``:
bearer-token auth, the derived share/schema/table namespace
(including ``shared_as`` aliasing), the ``Delta-Table-Version``
header, the NDJSON metadata/query shapes, version pinning, the
pre-signed file download round-trip (parquet bytes verified), and
every protocol-error path — all in the protocol's own
``{"errorCode", "message"}`` envelope, never the soyuz one.
"""

from __future__ import annotations

import io
import json
import time
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

deltalake = pytest.importorskip("deltalake")
pa = pytest.importorskip("pyarrow")

import pyarrow.parquet as pq  # noqa: E402
from deltalake import write_deltalake  # noqa: E402

CATALOGS = "/api/2.1/unity-catalog/catalogs"
SCHEMAS = "/api/2.1/unity-catalog/schemas"
TABLES = "/api/2.1/unity-catalog/tables"
SHARES = "/api/2.1/unity-catalog/shares"
RECIPIENTS = "/api/2.1/unity-catalog/recipients"
DS = "/delta-sharing"


def _register_table(client: TestClient, storage_location: str, name: str = "orders") -> None:
    """Register a table row pointing at *storage_location*."""
    if client.get(f"{CATALOGS}/main").status_code == 404:
        assert client.post(CATALOGS, json={"name": "main"}).status_code == 200
        assert client.post(SCHEMAS, json={"name": "s", "catalog_name": "main"}).status_code == 200
    body: dict[str, Any] = {
        "name": name,
        "catalog_name": "main",
        "schema_name": "s",
        "table_type": "EXTERNAL",
        "data_source_format": "DELTA",
        "storage_location": storage_location,
        "columns": [
            {"name": "id", "type_name": "LONG", "type_text": "bigint", "type_json": "{}"},
        ],
    }
    assert client.post(TABLES, json=body).status_code == 200


def _write_delta_table(path: Path) -> Any:
    """Write a small partitioned Delta table and return its data."""
    data = pa.table(
        {
            "id": pa.array([1, 2, 3], type=pa.int64()),
            "part": pa.array(["a", "a", "b"]),
        },
    )
    write_deltalake(str(path), data, partition_by=["part"])
    return data


def _share_table(
    client: TestClient,
    tmp_path: Path,
    shared_as: str | None = None,
) -> str:
    """Create table + share + recipient + grant; return the bearer token."""
    table_path = tmp_path / "orders"
    _write_delta_table(table_path)
    _register_table(client, f"file://{table_path}")
    assert client.post(SHARES, json={"name": "sh"}).status_code == 200
    body: dict[str, Any] = {"table_full_name": "main.s.orders"}
    if shared_as is not None:
        body["shared_as"] = shared_as
    assert client.post(f"{SHARES}/sh/objects", json=body).status_code == 200
    token = client.post(RECIPIENTS, json={"name": "r1"}).json()["token"]
    assert client.put(f"{SHARES}/sh/recipients/r1").status_code == 200
    return token


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _ndjson(text: str) -> list[dict[str, Any]]:
    return [json.loads(line) for line in text.strip().split("\n")]


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------


def test_missing_token_401_protocol_envelope(client: TestClient) -> None:
    r = client.get(f"{DS}/shares")
    assert r.status_code == 401
    body = r.json()
    # The protocol pins its own error envelope — camelCase errorCode,
    # no soyuz request_id / error_code fields.
    assert body["errorCode"] == "UNAUTHENTICATED"
    assert "message" in body
    assert "error_code" not in body
    assert "request_id" not in body


def test_unknown_token_401(client: TestClient) -> None:
    r = client.get(f"{DS}/shares", headers=_auth("not-a-real-token"))
    assert r.status_code == 401


def test_non_bearer_scheme_401(client: TestClient) -> None:
    r = client.get(f"{DS}/shares", headers={"Authorization": "Basic dXNlcjpwdw=="})
    assert r.status_code == 401


def test_rotated_token_invalidates_old(client: TestClient, tmp_path: Path) -> None:
    token = _share_table(client, tmp_path)
    fresh = client.post(f"{RECIPIENTS}/r1/rotate-token").json()["token"]
    assert client.get(f"{DS}/shares", headers=_auth(token)).status_code == 401
    r = client.get(f"{DS}/shares", headers=_auth(fresh))
    assert r.status_code == 200
    assert [s["name"] for s in r.json()["items"]] == ["sh"]


def test_all_protocol_routes_require_token(client: TestClient) -> None:
    paths = [
        f"{DS}/shares",
        f"{DS}/shares/sh",
        f"{DS}/shares/sh/schemas",
        f"{DS}/shares/sh/schemas/s/tables",
        f"{DS}/shares/sh/all-tables",
        f"{DS}/shares/sh/schemas/s/tables/orders/version",
        f"{DS}/shares/sh/schemas/s/tables/orders/metadata",
    ]
    for path in paths:
        assert client.get(path).status_code == 401, path
    assert client.post(f"{DS}/shares/sh/schemas/s/tables/orders/query", json={}).status_code == 401


# ---------------------------------------------------------------------------
# Listing endpoints
# ---------------------------------------------------------------------------


def test_list_shares_only_granted(client: TestClient, tmp_path: Path) -> None:
    token = _share_table(client, tmp_path)
    # A second share the recipient has no grant on must stay invisible.
    assert client.post(SHARES, json={"name": "hidden"}).status_code == 200
    r = client.get(f"{DS}/shares", headers=_auth(token))
    assert r.status_code == 200
    assert [s["name"] for s in r.json()["items"]] == ["sh"]
    assert "nextPageToken" not in r.json()
    # Direct access to the ungranted share is indistinguishable from
    # a missing one.
    assert client.get(f"{DS}/shares/hidden", headers=_auth(token)).status_code == 404


def test_get_share_shape(client: TestClient, tmp_path: Path) -> None:
    token = _share_table(client, tmp_path)
    r = client.get(f"{DS}/shares/sh", headers=_auth(token))
    assert r.status_code == 200
    body = r.json()
    assert body["share"]["name"] == "sh"
    assert body["share"]["id"]


def test_list_schemas_derived_from_objects(client: TestClient, tmp_path: Path) -> None:
    token = _share_table(client, tmp_path)
    r = client.get(f"{DS}/shares/sh/schemas", headers=_auth(token))
    assert r.status_code == 200
    assert r.json()["items"] == [{"name": "s", "share": "sh"}]


def test_shared_as_rehomes_table(client: TestClient, tmp_path: Path) -> None:
    token = _share_table(client, tmp_path, shared_as="public.orders_v1")
    headers = _auth(token)
    r = client.get(f"{DS}/shares/sh/schemas", headers=headers)
    assert r.json()["items"] == [{"name": "public", "share": "sh"}]
    r = client.get(f"{DS}/shares/sh/schemas/public/tables", headers=headers)
    items = r.json()["items"]
    assert len(items) == 1
    assert items[0]["name"] == "orders_v1"
    assert items[0]["schema"] == "public"
    assert items[0]["share"] == "sh"
    # The original placement does not exist on the protocol surface.
    assert client.get(f"{DS}/shares/sh/schemas/s/tables", headers=headers).status_code == 404
    # But the aliased address serves data.
    r = client.get(
        f"{DS}/shares/sh/schemas/public/tables/orders_v1/version",
        headers=headers,
    )
    assert r.status_code == 200
    assert r.headers["Delta-Table-Version"] == "0"


def test_list_tables_shape(client: TestClient, tmp_path: Path) -> None:
    token = _share_table(client, tmp_path)
    r = client.get(f"{DS}/shares/sh/schemas/s/tables", headers=_auth(token))
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) == 1
    assert items[0]["name"] == "orders"
    assert items[0]["schema"] == "s"
    assert items[0]["share"] == "sh"
    assert items[0]["shareId"]
    assert items[0]["id"]


def test_all_tables(client: TestClient, tmp_path: Path) -> None:
    token = _share_table(client, tmp_path)
    second = tmp_path / "events"
    _write_delta_table(second)
    _register_table(client, f"file://{second}", name="events")
    assert (
        client.post(
            f"{SHARES}/sh/objects",
            json={"table_full_name": "main.s.events", "shared_as": "other.events"},
        ).status_code
        == 200
    )
    r = client.get(f"{DS}/shares/sh/all-tables", headers=_auth(token))
    assert r.status_code == 200
    addresses = [(t["schema"], t["name"]) for t in r.json()["items"]]
    assert addresses == [("other", "events"), ("s", "orders")]


def test_protocol_pagination(client: TestClient, tmp_path: Path) -> None:
    token = _share_table(client, tmp_path)
    for name in ("t1", "t2"):
        path = tmp_path / name
        _write_delta_table(path)
        _register_table(client, f"file://{path}", name=name)
        assert (
            client.post(
                f"{SHARES}/sh/objects",
                json={"table_full_name": f"main.s.{name}"},
            ).status_code
            == 200
        )
    headers = _auth(token)
    r1 = client.get(
        f"{DS}/shares/sh/schemas/s/tables",
        params={"maxResults": 2},
        headers=headers,
    )
    body1 = r1.json()
    assert [t["name"] for t in body1["items"]] == ["orders", "t1"]
    assert body1["nextPageToken"]
    r2 = client.get(
        f"{DS}/shares/sh/schemas/s/tables",
        params={"pageToken": body1["nextPageToken"]},
        headers=headers,
    )
    body2 = r2.json()
    assert [t["name"] for t in body2["items"]] == ["t2"]
    assert "nextPageToken" not in body2


def test_protocol_bad_page_token_400(client: TestClient, tmp_path: Path) -> None:
    token = _share_table(client, tmp_path)
    r = client.get(
        f"{DS}/shares",
        params={"pageToken": "garbage!!"},
        headers=_auth(token),
    )
    assert r.status_code == 400
    assert r.json()["errorCode"] == "INVALID_PARAMETER_VALUE"


def test_protocol_bad_max_results_400(client: TestClient, tmp_path: Path) -> None:
    token = _share_table(client, tmp_path)
    r = client.get(f"{DS}/shares", params={"maxResults": -1}, headers=_auth(token))
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# Version / metadata
# ---------------------------------------------------------------------------


def test_version_header_empty_body(client: TestClient, tmp_path: Path) -> None:
    token = _share_table(client, tmp_path)
    r = client.get(f"{DS}/shares/sh/schemas/s/tables/orders/version", headers=_auth(token))
    assert r.status_code == 200
    assert r.headers["Delta-Table-Version"] == "0"
    assert r.content == b""


def test_version_starting_timestamp_501(client: TestClient, tmp_path: Path) -> None:
    token = _share_table(client, tmp_path)
    r = client.get(
        f"{DS}/shares/sh/schemas/s/tables/orders/version",
        params={"startingTimestamp": "2026-01-01T00:00:00Z"},
        headers=_auth(token),
    )
    assert r.status_code == 501
    assert r.json()["errorCode"] == "NOT_IMPLEMENTED"


def test_metadata_ndjson_shape(client: TestClient, tmp_path: Path) -> None:
    token = _share_table(client, tmp_path)
    r = client.get(f"{DS}/shares/sh/schemas/s/tables/orders/metadata", headers=_auth(token))
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/x-ndjson")
    assert r.headers["Delta-Table-Version"] == "0"
    lines = _ndjson(r.text)
    assert len(lines) == 2
    assert lines[0] == {"protocol": {"minReaderVersion": 1}}
    meta = lines[1]["metaData"]
    assert meta["format"] == {"provider": "parquet"}
    assert meta["partitionColumns"] == ["part"]
    assert meta["configuration"] == {}
    assert meta["id"]
    schema = json.loads(meta["schemaString"])
    assert schema["type"] == "struct"
    assert [f["name"] for f in schema["fields"]] == ["id", "part"]


def test_table_not_in_share_404(client: TestClient, tmp_path: Path) -> None:
    token = _share_table(client, tmp_path)
    r = client.get(f"{DS}/shares/sh/schemas/s/tables/missing/metadata", headers=_auth(token))
    assert r.status_code == 404
    assert r.json()["errorCode"] == "RESOURCE_DOES_NOT_EXIST"


def test_dropped_table_yields_protocol_404(client: TestClient, tmp_path: Path) -> None:
    """The share binds by name; a dropped table 404s at read time."""
    token = _share_table(client, tmp_path)
    assert client.delete(f"{TABLES}/main.s.orders").status_code == 200
    r = client.get(f"{DS}/shares/sh/schemas/s/tables/orders/version", headers=_auth(token))
    assert r.status_code == 404
    assert r.json()["errorCode"] == "RESOURCE_DOES_NOT_EXIST"


# ---------------------------------------------------------------------------
# Query + file download (the full protocol round-trip)
# ---------------------------------------------------------------------------


def test_query_and_download_roundtrip(client: TestClient, tmp_path: Path) -> None:
    """Share a real Delta table, query it, download every file URL,
    and verify the parquet bytes reassemble the original rows."""
    token = _share_table(client, tmp_path)
    r = client.post(
        f"{DS}/shares/sh/schemas/s/tables/orders/query",
        json={"predicateHints": ["part = 'a'"], "limitHint": 100},
        headers=_auth(token),
    )
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/x-ndjson")
    assert r.headers["Delta-Table-Version"] == "0"
    lines = _ndjson(r.text)
    assert lines[0] == {"protocol": {"minReaderVersion": 1}}
    assert "metaData" in lines[1]
    files = [line["file"] for line in lines[2:]]
    # Two partitions → two parquet files; hints are non-binding so
    # the full file list comes back.
    assert len(files) == 2
    seen: dict[int, int] = {}
    for action in files:
        assert action["id"]
        assert action["size"] > 0
        assert set(action["partitionValues"].keys()) == {"part"}
        assert json.loads(action["stats"])["numRecords"] in (1, 2)
        assert action["expirationTimestamp"] > int(time.time() * 1000)
        url = action["url"]
        assert "/delta-sharing/files/" in url
        # Download without any bearer token — the signed handle is
        # the authorisation, like a cloud pre-signed URL.
        fr = client.get(url.replace("http://testserver", ""))
        assert fr.status_code == 200
        table = pq.read_table(io.BytesIO(fr.content))
        assert len(fr.content) == action["size"]
        for value in table.column("id").to_pylist():
            seen[value] = seen.get(value, 0) + 1
    assert seen == {1: 1, 2: 1, 3: 1}


def test_query_empty_body_ok(client: TestClient, tmp_path: Path) -> None:
    token = _share_table(client, tmp_path)
    r = client.post(
        f"{DS}/shares/sh/schemas/s/tables/orders/query",
        headers=_auth(token),
    )
    assert r.status_code == 200


def test_query_tolerates_unknown_future_fields(client: TestClient, tmp_path: Path) -> None:
    """The protocol evolves independently — newer clients must not 422."""
    token = _share_table(client, tmp_path)
    r = client.post(
        f"{DS}/shares/sh/schemas/s/tables/orders/query",
        json={"maxFiles": 10, "includeRefreshToken": True},
        headers=_auth(token),
    )
    assert r.status_code == 200


def test_query_version_pinning(client: TestClient, tmp_path: Path) -> None:
    token = _share_table(client, tmp_path)
    table_path = tmp_path / "orders"
    write_deltalake(
        str(table_path),
        pa.table({"id": pa.array([4], type=pa.int64()), "part": pa.array(["b"])}),
        partition_by=["part"],
        mode="append",
    )
    headers = _auth(token)
    # Latest is version 1 with three files.
    r = client.get(f"{DS}/shares/sh/schemas/s/tables/orders/version", headers=headers)
    assert r.headers["Delta-Table-Version"] == "1"
    r = client.post(
        f"{DS}/shares/sh/schemas/s/tables/orders/query",
        json={"version": 0},
        headers=headers,
    )
    assert r.status_code == 200
    assert r.headers["Delta-Table-Version"] == "0"
    files = [line["file"] for line in _ndjson(r.text)[2:]]
    assert len(files) == 2  # the appended file is not in version 0
    r = client.post(
        f"{DS}/shares/sh/schemas/s/tables/orders/query",
        json={},
        headers=headers,
    )
    assert len(_ndjson(r.text)[2:]) == 3


def test_query_nonexistent_version_400(client: TestClient, tmp_path: Path) -> None:
    token = _share_table(client, tmp_path)
    r = client.post(
        f"{DS}/shares/sh/schemas/s/tables/orders/query",
        json={"version": 99},
        headers=_auth(token),
    )
    assert r.status_code == 400
    assert r.json()["errorCode"] == "INVALID_PARAMETER_VALUE"


def test_query_cdf_style_params_501(client: TestClient, tmp_path: Path) -> None:
    token = _share_table(client, tmp_path)
    for body in ({"timestamp": "2026-01-01T00:00:00Z"}, {"startingVersion": 0}):
        r = client.post(
            f"{DS}/shares/sh/schemas/s/tables/orders/query",
            json=body,
            headers=_auth(token),
        )
        assert r.status_code == 501, body
        assert r.json()["errorCode"] == "NOT_IMPLEMENTED"


def test_unsupported_reader_features_rejected(client: TestClient, tmp_path: Path) -> None:
    """Tables whose protocol demands reader features beyond plain
    parquet must be refused, not served wrong."""
    table_path = tmp_path / "dv_table"
    write_deltalake(
        str(table_path),
        pa.table({"id": pa.array([1], type=pa.int64())}),
        configuration={"delta.enableDeletionVectors": "true"},
    )
    _register_table(client, f"file://{table_path}", name="dv_table")
    assert client.post(SHARES, json={"name": "sh"}).status_code == 200
    assert (
        client.post(f"{SHARES}/sh/objects", json={"table_full_name": "main.s.dv_table"}).status_code
        == 200
    )
    token = client.post(RECIPIENTS, json={"name": "r1"}).json()["token"]
    assert client.put(f"{SHARES}/sh/recipients/r1").status_code == 200
    r = client.post(
        f"{DS}/shares/sh/schemas/s/tables/dv_table/query",
        json={},
        headers=_auth(token),
    )
    assert r.status_code == 400
    body = r.json()
    assert body["errorCode"] == "UNSUPPORTED_TABLE_FEATURES"
    assert "deletionVectors" in body["message"]


def test_cloud_scheme_501(client: TestClient) -> None:
    _register_table(client, "s3://bucket/prefix/orders")
    assert client.post(SHARES, json={"name": "sh"}).status_code == 200
    assert (
        client.post(f"{SHARES}/sh/objects", json={"table_full_name": "main.s.orders"}).status_code
        == 200
    )
    token = client.post(RECIPIENTS, json={"name": "r1"}).json()["token"]
    assert client.put(f"{SHARES}/sh/recipients/r1").status_code == 200
    r = client.get(
        f"{DS}/shares/sh/schemas/s/tables/orders/version",
        headers=_auth(token),
    )
    assert r.status_code == 501
    assert r.json()["errorCode"] == "NOT_IMPLEMENTED"


# ---------------------------------------------------------------------------
# Signed file handles
# ---------------------------------------------------------------------------


def _first_file_url(client: TestClient, token: str) -> str:
    r = client.post(
        f"{DS}/shares/sh/schemas/s/tables/orders/query",
        json={},
        headers=_auth(token),
    )
    return _ndjson(r.text)[2]["file"]["url"].replace("http://testserver", "")


def test_tampered_file_token_403(client: TestClient, tmp_path: Path) -> None:
    token = _share_table(client, tmp_path)
    url = _first_file_url(client, token)
    assert client.get(url + "AA").status_code == 403
    assert client.get(url.split("?")[0], params={"token": "forged"}).status_code == 403


def test_file_token_bound_to_file_id(client: TestClient, tmp_path: Path) -> None:
    """A handle signed for one file must not download another."""
    token = _share_table(client, tmp_path)
    url = _first_file_url(client, token)
    path_part, _, query = url.partition("?")
    swapped = path_part.rsplit("/", 1)[0] + "/" + "0" * 32 + "?" + query
    assert client.get(swapped).status_code == 403


def test_expired_file_token_403(client: TestClient, tmp_path: Path) -> None:
    from soyuz_catalog.storage.signed_urls import sign_file_handle

    table_path = tmp_path / "orders"
    _write_delta_table(table_path)
    parquet = next(table_path.rglob("*.parquet"))
    expired = sign_file_handle(parquet, "f" * 32, int(time.time() * 1000) - 1)
    r = client.get(f"{DS}/files/{'f' * 32}", params={"token": expired})
    assert r.status_code == 403
    assert r.json()["errorCode"] == "PERMISSION_DENIED"


def test_valid_handle_for_vanished_file_404(client: TestClient, tmp_path: Path) -> None:
    token = _share_table(client, tmp_path)
    url = _first_file_url(client, token)
    for parquet in (tmp_path / "orders").rglob("*.parquet"):
        parquet.unlink()
    r = client.get(url)
    assert r.status_code == 404
    assert r.json()["errorCode"] == "RESOURCE_DOES_NOT_EXIST"
