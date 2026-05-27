"""FastAPI dependency providers."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.orm import Session

from soyuz_catalog.db import get_session_factory


def get_db() -> Generator[Session]:
    """Yield a SQLAlchemy session for the duration of a request.

    Yields:
        Generator[Session]: An open SQLAlchemy session, closed when the request ends.
    """
    factory = get_session_factory()
    session = factory()
    try:
        yield session
    finally:
        session.close()
