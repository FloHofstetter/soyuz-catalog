"""Shared SQLAlchemy plumbing for the models package.

Holds the declarative ``Base`` plus the two id/timestamp helpers every
domain submodule uses. Lives in a private ``_base`` module so it is
clear at the import that nothing here is part of the public API — the
top-level ``soyuz_catalog.models`` re-exports everything callers should
reach for.

The two-step clock indirection (:func:`_epoch_ms` called by
:func:`_now_ms`) is the seam the pytest deterministic-clock fixture
hooks into. SQLAlchemy captures ``default=_now_ms`` callable references
at table-definition time, so monkeypatching ``_now_ms`` itself has no
effect — patching ``_epoch_ms`` does, because ``_now_ms``'s body
resolves ``_epoch_ms`` through ``__globals__`` on every call.
"""

from __future__ import annotations

import time
import uuid

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """SQLAlchemy 2.0 declarative base for every soyuz-catalog ORM model.

    Everything that backs a REST resource (catalogs, schemas, tables,
    columns, volumes) inherits from this class so that ``Base.metadata``
    is the single source of truth for Alembic autogenerate and the
    ``Base.metadata.create_all`` shortcut used by the test fixtures.
    Kept intentionally empty — no shared columns, no mixins — because
    the system-field conventions (``id``, ``created_at`` / ``updated_at``,
    ``properties``) are deliberately re-declared on each model so the
    differences between resources (e.g. volumes have no ``properties``)
    stay visible at the class level instead of being hidden in a mixin.
    """


def _epoch_ms() -> int:
    """Read the wall clock as an epoch-millisecond integer.

    Sole real-time call site in the models package. Lives behind
    :func:`_now_ms` so the pytest deterministic-clock fixture can
    monkeypatch just this function and intercept every ``created_at``
    / ``updated_at`` write — both Column defaults and service-layer
    manual writes — via the module-global lookup that happens at call
    time.

    Returns:
        int: Current Unix time in milliseconds.
    """
    return int(time.time() * 1000)


def _now_ms() -> int:
    """Return the current time in epoch milliseconds.

    Used as the ``default=`` factory for ``created_at`` / ``updated_at``
    columns and by service-layer code that bumps ``updated_at`` on
    PATCH. Delegates to :func:`_epoch_ms` so a single test fixture can
    intercept every clock read.

    Returns:
        int: Current Unix time in milliseconds.
    """
    return _epoch_ms()


def _new_id() -> str:
    """Generate a new opaque resource identifier.

    Returns:
        str: A random UUID4 hex string.
    """
    return uuid.uuid4().hex
