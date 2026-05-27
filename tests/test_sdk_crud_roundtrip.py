"""Full CRUD verb matrix against a live soyuz-catalog via the unitycatalog SDK.

[tests/test_delta_roundtrip.py](test_delta_roundtrip.py) covers the
create + retrieve side of the ``unitycatalog`` Python SDK against a
real soyuz process. This module extends that coverage to every CRUD
verb the SDK exposes on every implemented resource (catalog, schema,
table, volume). Unit tests assert against soyuz's own response shapes
and miss the "field renamed / field omitted" bug class the SDK
catches for free: the SDK deserialises every response into its own
dataclass, so a drift surfaces as a ``TypeError`` / validation error
rather than silently staying green.

``tables.update`` is absent from the SDK surface on purpose — the UC
OpenAPI spec defines no ``UpdateTable``, and the Stainless-generated
client does not even expose the method. We verify the absence here
as a regression guard for the spec-conformant divergence (see
``DIVERGENCES.md``), so a future SDK revision that *adds* the method
will fail this test and prompt a spec re-check.

Extended resources beyond the core CRUD set (credentials, external
locations, functions, registered models, metastore, staging tables,
path credentials, permissions) are **not** covered by the upstream
``unitycatalog`` SDK; they are exercised in
[test_generated_client_roundtrip.py](test_generated_client_roundtrip.py)
against the generated ``soyuz-catalog-client``. This module covers
only the upstream-SDK path.
"""

from __future__ import annotations

import json
import uuid

import pytest

pytest.importorskip("unitycatalog")

from unitycatalog.types.table_create_params import Column  # noqa: E402

from tests._sdk import make_uc_client  # noqa: E402

pytestmark = pytest.mark.integration


_COLUMN_TYPE_JSON = json.dumps(
    {"name": "id", "type": "long", "nullable": True, "metadata": {}},
)
_COLUMNS: list[Column] = [
    {
        "name": "id",
        "type_text": "bigint",
        "type_json": _COLUMN_TYPE_JSON,
        "type_name": "LONG",
        "position": 0,
        "nullable": True,
    },
]


def _fresh_names() -> tuple[str, str]:
    """Return a ``(catalog, schema)`` name pair unique to the caller.

    ``live_server`` is a fresh SQLite file per test so strictly speaking
    collisions cannot happen, but the unique suffix makes failure
    output self-identifying when two tests fail in the same run.
    """
    suffix = uuid.uuid4().hex[:8]
    return f"cat_{suffix}", f"sch_{suffix}"


# ---------------------------------------------------------------------------
# Catalogs
# ---------------------------------------------------------------------------


def test_sdk_catalog_full_crud(live_server: str) -> None:
    client = make_uc_client(live_server)
    cat, _ = _fresh_names()

    created = client.catalogs.create(name=cat, comment="initial")
    assert created.name == cat
    assert created.comment == "initial"

    got = client.catalogs.retrieve(cat)
    assert got.name == cat
    assert got.id == created.id

    listed = client.catalogs.list()
    assert listed.catalogs is not None
    assert any(c.name == cat for c in listed.catalogs)

    updated = client.catalogs.update(cat, comment="edited")
    assert updated.comment == "edited"
    assert updated.id == created.id

    client.catalogs.delete(cat)
    with pytest.raises(Exception):  # noqa: BLE001 — any SDK error type counts as "gone"
        client.catalogs.retrieve(cat)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


def test_sdk_schema_full_crud(live_server: str) -> None:
    client = make_uc_client(live_server)
    cat, sch = _fresh_names()
    client.catalogs.create(name=cat)

    created = client.schemas.create(catalog_name=cat, name=sch, comment="initial")
    assert created.name == sch
    assert created.catalog_name == cat
    assert created.full_name == f"{cat}.{sch}"

    got = client.schemas.retrieve(f"{cat}.{sch}")
    assert got.schema_id == created.schema_id

    listed = client.schemas.list(catalog_name=cat)
    assert listed.schemas is not None
    assert any(s.name == sch for s in listed.schemas)

    updated = client.schemas.update(f"{cat}.{sch}", comment="edited")
    assert updated.comment == "edited"
    assert updated.schema_id == created.schema_id

    client.schemas.delete(f"{cat}.{sch}")
    with pytest.raises(Exception):  # noqa: BLE001
        client.schemas.retrieve(f"{cat}.{sch}")


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------


def test_sdk_table_crud_without_update(live_server: str, tmp_path) -> None:
    client = make_uc_client(live_server)
    cat, sch = _fresh_names()
    client.catalogs.create(name=cat)
    client.schemas.create(catalog_name=cat, name=sch)

    table_path = tmp_path / "t"
    created = client.tables.create(
        name="t",
        catalog_name=cat,
        schema_name=sch,
        table_type="EXTERNAL",
        data_source_format="DELTA",
        storage_location=f"file://{table_path}",
        columns=_COLUMNS,
    )
    assert created.name == "t"
    assert created.storage_location == f"file://{table_path}"

    got = client.tables.retrieve(f"{cat}.{sch}.t")
    assert got.table_id == created.table_id
    assert got.columns is not None and len(got.columns) == 1
    assert got.columns[0].name == "id"

    listed = client.tables.list(catalog_name=cat, schema_name=sch)
    assert listed.tables is not None
    assert any(t.name == "t" for t in listed.tables)

    client.tables.delete(f"{cat}.{sch}.t")
    with pytest.raises(Exception):  # noqa: BLE001
        client.tables.retrieve(f"{cat}.{sch}.t")


def test_sdk_tables_namespace_has_no_update(live_server: str) -> None:
    """Regression guard for the "no ``PATCH /tables``" divergence.

    The spec defines no ``UpdateTable`` and the Stainless-generated SDK
    omits the method entirely. If a future SDK revision *adds* it, the
    soyuz route returns 405 and the assertion below catches the drift
    before a real client reaches that 405 by accident.
    """
    client = make_uc_client(live_server)
    assert not hasattr(client.tables, "update")


# ---------------------------------------------------------------------------
# Volumes
# ---------------------------------------------------------------------------


def test_sdk_volume_full_crud(live_server: str, tmp_path) -> None:
    client = make_uc_client(live_server)
    cat, sch = _fresh_names()
    client.catalogs.create(name=cat)
    client.schemas.create(catalog_name=cat, name=sch)

    vol_path = tmp_path / "v"
    vol_path.mkdir()
    created = client.volumes.create(
        catalog_name=cat,
        schema_name=sch,
        name="v",
        volume_type="EXTERNAL",
        storage_location=f"file://{vol_path}",
        comment="initial",
    )
    assert created.name == "v"
    assert created.storage_location == f"file://{vol_path}"

    got = client.volumes.retrieve(f"{cat}.{sch}.v")
    assert got.volume_id == created.volume_id

    listed = client.volumes.list(catalog_name=cat, schema_name=sch)
    assert listed.volumes is not None
    assert any(v.name == "v" for v in listed.volumes)

    updated = client.volumes.update(f"{cat}.{sch}.v", comment="edited")
    assert updated.comment == "edited"
    assert updated.volume_id == created.volume_id

    client.volumes.delete(f"{cat}.{sch}.v")
    with pytest.raises(Exception):  # noqa: BLE001
        client.volumes.retrieve(f"{cat}.{sch}.v")
