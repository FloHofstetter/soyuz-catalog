"""Tests for the Functions CRUD resource."""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

CATALOGS = "/api/2.1/unity-catalog/catalogs"
SCHEMAS = "/api/2.1/unity-catalog/schemas"
FUNCTIONS = "/api/2.1/unity-catalog/functions"


def _make_catalog(client: TestClient, name: str = "main") -> None:
    assert client.post(CATALOGS, json={"name": name}).status_code == 200


def _make_schema(
    client: TestClient,
    catalog_name: str = "main",
    name: str = "s",
) -> None:
    assert (
        client.post(SCHEMAS, json={"name": name, "catalog_name": catalog_name}).status_code == 200
    )


def _function_info_body(
    name: str = "add_one",
    catalog_name: str = "main",
    schema_name: str = "s",
    routine_body: str = "SQL",
    sql_data_access: str = "CONTAINS_SQL",
    **overrides: Any,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "name": name,
        "catalog_name": catalog_name,
        "schema_name": schema_name,
        "input_params": {
            "parameters": [
                {
                    "name": "x",
                    "type_text": "int",
                    "type_json": '{"type":"int"}',
                    "type_name": "INT",
                    "position": 0,
                },
            ],
        },
        "data_type": "INT",
        "full_data_type": "INT",
        "return_params": {"parameters": []},
        "routine_body": routine_body,
        "routine_definition": "SELECT x + 1",
        "parameter_style": "S",
        "is_deterministic": True,
        "sql_data_access": sql_data_access,
        "is_null_call": False,
        "security_type": "DEFINER",
        "specific_name": name,
    }
    body.update(overrides)
    return {"function_info": body}


def _post_function(client: TestClient, name: str) -> None:
    assert client.post(FUNCTIONS, json=_function_info_body(name=name)).status_code == 200


def test_create_function_happy_path(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    r = client.post(FUNCTIONS, json=_function_info_body())
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["full_name"] == "main.s.add_one"
    assert body["routine_body"] == "SQL"
    assert body["input_params"]["parameters"][0]["name"] == "x"
    assert body["return_params"]["parameters"] == []
    assert body["function_id"]


def test_create_function_unknown_catalog_404(client: TestClient) -> None:
    r = client.post(FUNCTIONS, json=_function_info_body(catalog_name="nope"))
    assert r.status_code == 404


def test_create_function_unknown_schema_404(client: TestClient) -> None:
    _make_catalog(client)
    r = client.post(FUNCTIONS, json=_function_info_body(schema_name="nope"))
    assert r.status_code == 404


def test_create_function_duplicate_409(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    client.post(FUNCTIONS, json=_function_info_body())
    r = client.post(FUNCTIONS, json=_function_info_body())
    assert r.status_code == 409


def test_create_function_unknown_top_level_field_422(client: TestClient) -> None:
    """UC OSS bug fix: typos in the function_info body are rejected with 422."""
    _make_catalog(client)
    _make_schema(client)
    body = _function_info_body()
    body["function_info"]["bogus"] = 1
    r = client.post(FUNCTIONS, json=body)
    assert r.status_code == 422


def test_create_function_unknown_parameter_field_422(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    body = _function_info_body()
    body["function_info"]["input_params"]["parameters"][0]["bogus"] = "x"
    r = client.post(FUNCTIONS, json=body)
    assert r.status_code == 422


def test_create_function_invalid_routine_body_422(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    r = client.post(FUNCTIONS, json=_function_info_body(routine_body="PYTHON"))
    assert r.status_code == 422


def test_create_function_invalid_sql_data_access_422(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    r = client.post(FUNCTIONS, json=_function_info_body(sql_data_access="NONE"))
    assert r.status_code == 422


def test_create_function_empty_input_params(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    body = _function_info_body()
    body["function_info"]["input_params"]["parameters"] = []
    r = client.post(FUNCTIONS, json=body)
    assert r.status_code == 200
    assert r.json()["input_params"]["parameters"] == []


def test_create_function_missing_required_field_422(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    body = _function_info_body()
    del body["function_info"]["routine_definition"]
    assert client.post(FUNCTIONS, json=body).status_code == 422


def test_create_function_missing_wrapper_422(client: TestClient) -> None:
    """UC spec wraps the create body as {"function_info": ...}."""
    _make_catalog(client)
    _make_schema(client)
    flat = _function_info_body()["function_info"]
    r = client.post(FUNCTIONS, json=flat)
    assert r.status_code == 422


def test_same_function_name_in_two_schemas(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client, name="s1")
    _make_schema(client, name="s2")
    assert client.post(FUNCTIONS, json=_function_info_body(schema_name="s1")).status_code == 200
    assert client.post(FUNCTIONS, json=_function_info_body(schema_name="s2")).status_code == 200


def test_get_function_happy_path(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    client.post(FUNCTIONS, json=_function_info_body())
    r = client.get(f"{FUNCTIONS}/main.s.add_one")
    assert r.status_code == 200
    assert r.json()["full_name"] == "main.s.add_one"


def test_get_function_malformed_full_name_400(client: TestClient) -> None:
    r = client.get(f"{FUNCTIONS}/main.s")
    assert r.status_code == 400
    assert r.json()["error_code"] == "INVALID_ARGUMENT"


def test_get_function_404(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    r = client.get(f"{FUNCTIONS}/main.s.nope")
    assert r.status_code == 404


def test_list_functions_requires_parents(client: TestClient) -> None:
    r = client.get(FUNCTIONS)
    assert r.status_code == 422


def test_list_functions_empty(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    body = client.get(
        FUNCTIONS,
        params={"catalog_name": "main", "schema_name": "s"},
    ).json()
    assert body["functions"] == []
    assert body["next_page_token"] is None


def test_list_functions_insertion_order(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    _post_function(client, "b")
    _post_function(client, "a")
    body = client.get(
        FUNCTIONS,
        params={"catalog_name": "main", "schema_name": "s"},
    ).json()
    assert [f["name"] for f in body["functions"]] == ["b", "a"]


def test_list_functions_pagination_walk(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    for name in ("f0", "f1", "f2", "f3"):
        _post_function(client, name)
    base = {"catalog_name": "main", "schema_name": "s", "max_results": 2}
    p1 = client.get(FUNCTIONS, params=base).json()
    assert [f["name"] for f in p1["functions"]] == ["f0", "f1"]
    assert p1["next_page_token"]
    p2 = client.get(
        FUNCTIONS,
        params={**base, "page_token": p1["next_page_token"]},
    ).json()
    assert [f["name"] for f in p2["functions"]] == ["f2", "f3"]


def test_list_functions_parent_404(client: TestClient) -> None:
    r = client.get(
        FUNCTIONS,
        params={"catalog_name": "main", "schema_name": "s"},
    )
    assert r.status_code == 404


def test_delete_function_happy_path(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    client.post(FUNCTIONS, json=_function_info_body())
    r = client.delete(f"{FUNCTIONS}/main.s.add_one")
    assert r.status_code == 200
    assert client.get(f"{FUNCTIONS}/main.s.add_one").status_code == 404


def test_delete_function_404(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    r = client.delete(f"{FUNCTIONS}/main.s.nope")
    assert r.status_code == 404


def test_patch_function_returns_405(client: TestClient) -> None:
    """Spec-faithful divergence: UC defines no UpdateFunction → soyuz returns 405."""
    _make_catalog(client)
    _make_schema(client)
    client.post(FUNCTIONS, json=_function_info_body())
    r = client.patch(f"{FUNCTIONS}/main.s.add_one", json={})
    assert r.status_code == 405


def test_schema_delete_refuses_when_functions_exist(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    client.post(FUNCTIONS, json=_function_info_body())
    r = client.delete(f"{SCHEMAS}/main.s")
    assert r.status_code == 409
    assert "functions" in r.json()["message"]


def test_schema_delete_force_cascades_functions(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    client.post(FUNCTIONS, json=_function_info_body())
    r = client.delete(f"{SCHEMAS}/main.s", params={"force": "true"})
    assert r.status_code == 200


def test_catalog_rename_propagates_to_function_full_name(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    client.post(FUNCTIONS, json=_function_info_body())
    # Rename the parent catalog.
    assert client.patch(f"{CATALOGS}/main", json={"new_name": "prod"}).status_code == 200
    r = client.get(f"{FUNCTIONS}/prod.s.add_one")
    assert r.status_code == 200
    assert r.json()["full_name"] == "prod.s.add_one"
    assert r.json()["catalog_name"] == "prod"
