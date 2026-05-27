"""Alembic environment configuration for embedded migrations."""

from alembic import context
from sqlalchemy import engine_from_config, pool

from soyuz_catalog.models import Base

target_metadata = Base.metadata


def _is_sqlite(url: str | None) -> bool:
    """Return True if the SQLAlchemy URL points at SQLite.

    ``render_as_batch`` is a SQLite-only workaround for its missing ``ALTER
    TABLE`` semantics; Postgres handles column-level alters natively and
    enabling batch mode there produces unnecessary table rewrites on future
    migrations. Gating on the dialect keeps both backends happy.

    Args:
        url: SQLAlchemy URL string, or ``None`` in offline mode with no URL set.

    Returns:
        bool: ``True`` if ``url`` starts with ``sqlite``.
    """
    return url is not None and url.startswith("sqlite")


def run_migrations_offline() -> None:
    """Emit the migration SQL without connecting to a database.

    Offline mode is used by ``alembic upgrade --sql`` to print the DDL
    a migration *would* execute, for review or for feeding into a
    separate DBA workflow. No connection is opened; the URL is only
    used to pick the dialect (and, via :func:`_is_sqlite`, to decide
    whether to render ALTERs in batch mode).
    """
    url = context.config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        render_as_batch=_is_sqlite(url),
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Apply migrations against a live database connection.

    This is the path taken by the FastAPI lifespan on startup (via
    :func:`soyuz_catalog.db.run_migrations`) and by the pytest
    ``--db-backend=postgres`` fixture. A ``NullPool`` engine is used
    so the single short-lived connection does not fight the
    application pool for a slot, and ``render_as_batch`` is gated on
    the live dialect rather than the URL string so future runtime
    dialect overrides stay correct.
    """
    connectable = engine_from_config(
        context.config.get_section(context.config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=connection.dialect.name == "sqlite",
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
