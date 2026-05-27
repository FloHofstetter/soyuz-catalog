"""Tests for the volume file-IO routes."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

CATALOGS = "/api/2.1/unity-catalog/catalogs"
SCHEMAS = "/api/2.1/unity-catalog/schemas"
VOLUMES = "/api/2.1/unity-catalog/volumes"


def _create_local_volume(client: TestClient, tmp_path: Path) -> str:
    """Build a fresh file:// volume and return its full_name."""
    r = client.post(CATALOGS, json={"name": "main"})
    assert r.status_code == 200, r.text
    r = client.post(SCHEMAS, json={"name": "ops", "catalog_name": "main"})
    assert r.status_code == 200, r.text
    storage = f"file://{tmp_path.resolve()}"
    r = client.post(
        VOLUMES,
        json={
            "name": "uploads",
            "catalog_name": "main",
            "schema_name": "ops",
            "volume_type": "EXTERNAL",
            "storage_location": storage,
        },
    )
    assert r.status_code == 200, r.text
    return "main.ops.uploads"


def test_volume_file_upload_browse_download_delete_round_trip(
    client: TestClient, tmp_path: Path
) -> None:
    full_name = _create_local_volume(client, tmp_path)

    # Upload a small file.
    files = {"upload": ("hello.csv", b"a,b\n1,2\n", "text/csv")}
    upload = client.post(
        f"{VOLUMES}/{full_name}/files",
        params={"path": "hello.csv"},
        files=files,
    )
    assert upload.status_code == 200, upload.text
    entry = upload.json()["file"]
    assert entry["path"] == "hello.csv"
    assert entry["size_bytes"] == len("a,b\n1,2\n")

    # Browse returns the entry.
    browse = client.get(f"{VOLUMES}/{full_name}/files")
    assert browse.status_code == 200
    names = [e["path"] for e in browse.json()["files"]]
    assert "hello.csv" in names

    # Download streams the bytes back.
    dl = client.get(f"{VOLUMES}/{full_name}/files/hello.csv")
    assert dl.status_code == 200
    assert dl.content == b"a,b\n1,2\n"

    # Delete removes it.
    rm = client.delete(f"{VOLUMES}/{full_name}/files/hello.csv")
    assert rm.status_code == 200
    assert rm.json() == {"deleted": True}
    after = client.get(f"{VOLUMES}/{full_name}/files")
    assert [e["path"] for e in after.json()["files"]] == []


def test_volume_file_rejects_path_traversal(client: TestClient, tmp_path: Path) -> None:
    full_name = _create_local_volume(client, tmp_path)
    files = {"upload": ("evil.txt", b"nope", "text/plain")}
    response = client.post(
        f"{VOLUMES}/{full_name}/files",
        params={"path": "../escaped.txt"},
        files=files,
    )
    # Path traversal is rejected with 400 INVALID_ARGUMENT via the
    # InvalidRequestError path.
    assert response.status_code == 400
    assert "invalid" in response.text.lower() or "escape" in response.text.lower()
