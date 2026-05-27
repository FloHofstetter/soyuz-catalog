"""Tests for the default-path anchoring of ``Settings``.

``Settings.database_url`` and ``model_artifact_root`` default to
locations under the repo root rather than CWD-relative strings, so
starting the server from a different directory does not produce
parallel SQLite files / scattered artefact directories. Env vars
(``SOYUZ_DATABASE_URL`` etc.) still override exactly as before.
"""

from __future__ import annotations

import os

import soyuz_catalog.settings as settings_mod
from soyuz_catalog.settings import Settings


def test_database_url_default_is_absolute_project_anchor(tmp_path, monkeypatch) -> None:
    """``settings.database_url`` resolves to ``<repo>/soyuz.db`` from any cwd."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("SOYUZ_DATABASE_URL", raising=False)

    s = Settings()
    expected = settings_mod._PROJECT_ROOT / "soyuz.db"
    assert s.database_url == f"sqlite:///{expected}"
    # Path inside the URL must be absolute.
    assert os.path.isabs(s.database_url.removeprefix("sqlite:///"))


def test_database_url_env_override_still_wins(tmp_path, monkeypatch) -> None:
    """``SOYUZ_DATABASE_URL`` overrides the anchored default verbatim."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SOYUZ_DATABASE_URL", "sqlite:///./caller-override.db")

    s = Settings()
    assert s.database_url == "sqlite:///./caller-override.db"


def test_model_artifact_root_default_is_absolute(tmp_path, monkeypatch) -> None:
    """``settings.model_artifact_root`` resolves to ``<repo>/model_artifacts``."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("SOYUZ_MODEL_ARTIFACT_ROOT", raising=False)

    s = Settings()
    expected = settings_mod._PROJECT_ROOT / "model_artifacts"
    assert s.model_artifact_root == str(expected)
    assert os.path.isabs(s.model_artifact_root)


def test_project_root_constant_points_at_repo() -> None:
    """``_PROJECT_ROOT`` resolves to the repository checkout root."""
    assert (settings_mod._PROJECT_ROOT / "pyproject.toml").is_file()
