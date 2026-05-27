"""Application settings loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Repository root — derived from the location of this module so the
# default SQLite path and the default model-artifact root resolve to
# stable absolute locations regardless of which CWD the server was
# launched from.  ``settings.py`` lives at
# ``<repo>/soyuz_catalog/settings.py`` so two ``parent`` walks
# yield the repo root.  Operators who want the legacy CWD-relative
# behaviour can still override every default via the matching env
# var.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Top-level configuration for soyuz-catalog.

    Attributes:
        database_url: SQLAlchemy database URL. Defaults to a local SQLite file.
        api_prefix: URL prefix under which the Unity Catalog REST routes are mounted.
            Matches the path used by UC OSS (``/api/2.1/unity-catalog``) so existing
            clients work without configuration.
        log_level: Python logging level name.
        structured_logging: If true, emit one JSON object per log line
            via ``logging_config.JsonFormatter`` instead of the default
            text format. Gated on a flag rather than always-on because
            the existing text output is still the nicer DX for local
            development; structured mode exists for containerised
            deployments where a log shipper consumes stdout.
        openapi_enabled: If true, FastAPI serves ``/openapi.json`` and
            ``/docs``. Default is ``True`` because soyuz has no auth
            layer (the README punts authentication to a front proxy),
            so an operator who can reach ``/openapi.json`` can also
            reach every CRUD endpoint anyway — information-disclosure
            is not a meaningful threat, and the polish value of the
            generated documentation outweighs it. Paranoid operators
            can still flip the flag off via ``SOYUZ_OPENAPI_ENABLED=0``.
        model_artifact_root: Base path (file URL or filesystem path) under
            which model-version artifacts are stored. ``create_model_version``
            populates ``ModelVersion.storage_location`` as
            ``{model_artifact_root}/{model_id}/{version}``. The MLflow
            UC-OSS client uploads artifacts to that URL before calling
            ``finalizeModelVersion`` to flip status from
            ``PENDING_REGISTRATION`` to ``READY``. The default is a
            cwd-relative ``model_artifacts`` folder; deployments using
            persistent storage should override via
            ``SOYUZ_MODEL_ARTIFACT_ROOT``.
    """

    model_config = SettingsConfigDict(env_prefix="SOYUZ_", env_file=None, extra="ignore")

    # Anchored to the repo root so the default DB location is stable
    # no matter which CWD the server was started from.  Override via
    # ``SOYUZ_DATABASE_URL`` when a different location is needed.
    database_url: str = f"sqlite:///{_PROJECT_ROOT / 'soyuz.db'}"
    api_prefix: str = "/api/2.1/unity-catalog"
    log_level: str = "INFO"
    structured_logging: bool = False
    openapi_enabled: bool = True
    # Same anchor for the artifact root so MLflow uploads land next
    # to ``soyuz.db`` regardless of CWD.
    model_artifact_root: str = str(_PROJECT_ROOT / "model_artifacts")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached application settings.

    Returns:
        Settings: The cached settings instance.
    """
    return Settings()


def reset_settings_cache() -> None:
    """Clear the ``get_settings`` LRU cache.

    Tests that manipulate ``SOYUZ_*`` environment variables with
    ``monkeypatch.setenv`` need the next ``get_settings()`` call to
    observe the new value rather than the cached ``Settings`` instance
    built at process start. Production code never calls this — the
    cache is load-bearing for handler performance.
    """
    get_settings.cache_clear()
