"""Unit tests for the spec-drift checker (``scripts/check_spec_drift.py``).

These tests run fully offline: they construct tiny in-memory OpenAPI
documents and baselines, hand them to ``check_spec_drift`` via ``tmp_path``,
and assert on exit codes, stdout, and the written-back baseline. No network,
no upstream clone, no FastAPI app instantiation — the checker lives in the
``scripts/`` tree precisely so it stays testable without the full runtime.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import check_spec_drift  # type: ignore[import-not-found]  # noqa: E402


def _write_spec(path: Path, spec: dict) -> None:
    path.write_text(yaml.safe_dump(spec))


def _baseline(paths: list[list[str]], schemas: list[str]) -> dict:
    return {
        "source": "https://example/all.yaml",
        "captured_at": "2026-04-15",
        "paths": paths,
        "schemas": schemas,
    }


SPEC_BASE = {
    "paths": {
        "/catalogs": {"get": {}, "post": {}},
        "/catalogs/{name}": {"get": {}, "delete": {}},
    },
    "components": {"schemas": {"CatalogInfo": {}, "CreateCatalog": {}}},
}


def test_extract_snapshot_normalises_parameters() -> None:
    snap = check_spec_drift.extract_snapshot(SPEC_BASE)
    assert ["/catalogs/{}", "get"] in snap["paths"]
    assert snap["schemas"] == ["CatalogInfo", "CreateCatalog"]


def test_no_drift_exits_zero(tmp_path: Path) -> None:
    spec = tmp_path / "all.yaml"
    baseline = tmp_path / "baseline.json"
    _write_spec(spec, SPEC_BASE)
    baseline.write_text(
        json.dumps(
            _baseline(
                paths=[
                    ["/catalogs", "get"],
                    ["/catalogs", "post"],
                    ["/catalogs/{}", "delete"],
                    ["/catalogs/{}", "get"],
                ],
                schemas=["CatalogInfo", "CreateCatalog"],
            )
        )
    )
    rc = check_spec_drift.main(["--spec", str(spec), "--baseline", str(baseline)])
    assert rc == 0


def test_drift_reports_additions(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    spec_with_extra = {
        "paths": {
            **SPEC_BASE["paths"],
            "/functions": {"post": {}},
        },
        "components": {"schemas": {**SPEC_BASE["components"]["schemas"], "FunctionInfo": {}}},
    }
    spec = tmp_path / "all.yaml"
    baseline = tmp_path / "baseline.json"
    _write_spec(spec, spec_with_extra)
    baseline.write_text(
        json.dumps(
            _baseline(
                paths=[
                    ["/catalogs", "get"],
                    ["/catalogs", "post"],
                    ["/catalogs/{}", "delete"],
                    ["/catalogs/{}", "get"],
                ],
                schemas=["CatalogInfo", "CreateCatalog"],
            )
        )
    )
    rc = check_spec_drift.main(["--spec", str(spec), "--baseline", str(baseline)])
    assert rc == 1
    out = capsys.readouterr().out
    assert "Upstream spec drift detected" in out
    assert "`POST /functions`" in out
    assert "`FunctionInfo`" in out
    assert "Removed paths" not in out


def test_write_baseline_creates_file(tmp_path: Path) -> None:
    spec = tmp_path / "all.yaml"
    baseline = tmp_path / "nested" / "baseline.json"
    _write_spec(spec, SPEC_BASE)
    rc = check_spec_drift.main(
        [
            "--spec",
            str(spec),
            "--baseline",
            str(baseline),
            "--source",
            "https://example/all.yaml",
            "--write-baseline",
        ]
    )
    assert rc == 0
    payload = json.loads(baseline.read_text())
    assert payload["source"] == "https://example/all.yaml"
    assert payload["schemas"] == ["CatalogInfo", "CreateCatalog"]
    assert ["/catalogs", "post"] in payload["paths"]


def test_missing_spec_exits_two(tmp_path: Path) -> None:
    rc = check_spec_drift.main(
        ["--spec", str(tmp_path / "missing.yaml"), "--baseline", str(tmp_path / "b.json")]
    )
    assert rc == 2


def test_missing_baseline_exits_two(tmp_path: Path) -> None:
    spec = tmp_path / "all.yaml"
    _write_spec(spec, SPEC_BASE)
    rc = check_spec_drift.main(["--spec", str(spec), "--baseline", str(tmp_path / "missing.json")])
    assert rc == 2
