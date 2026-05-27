"""Business logic for declared table constraints (ADR-0012).

Table constraints are a Databricks-supported, UC OSS missing,
over-the-spec extension. soyuz stores ``PRIMARY KEY``, ``FOREIGN
KEY``, ``CHECK``, and named ``NOT NULL`` declarations as flat rows
on a dedicated ``table_constraints`` table keyed on the opaque
``Table.id``. The feature is **metadata-only**: soyuz runs no query
engine and therefore does not enforce declarations at write time.
The value is interoperability with Spark / dbt / downstream
catalog UIs that read declared constraints to display schema
documentation or pick join strategies.

The service exposes four public entry points:

* :func:`list_constraints` — rebuild the wire-format list for a
  table from the live rows, used by ``TableInfo`` response builders.
* :func:`add_constraint` — insert one validated declaration row.
* :func:`drop_constraint` — remove a declaration by ``name``.
* :func:`delete_constraints_for_table` — cascade hook for
  ``delete_table``.

All mutations ride on the Delta REST ``UpdateTable`` discriminated
union (``add-constraint`` / ``drop-constraint`` actions, ADR-0009)
— the main UC REST surface has no ``PATCH /tables`` (the spec
returns 405; constraint declarations deliberately do not reopen
that invariant). Reads surface on the main UC REST ``GET /tables``
via the ``table_constraints`` field on :class:`TableInfo`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from soyuz_catalog.api.schemas import (
    CheckConstraint,
    ForeignKeyConstraint,
    NotNullConstraint,
    PrimaryKeyConstraint,
)
from soyuz_catalog.api.schemas import (
    TableConstraint as TableConstraintPayload,
)
from soyuz_catalog.exceptions import (
    ConflictError,
    InvalidRequestError,
    NotFoundError,
)
from soyuz_catalog.models import Column, Table, TableConstraint, _now_ms
from soyuz_catalog.services import table_service

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


_VALID_TYPES = frozenset({"PRIMARY_KEY", "FOREIGN_KEY", "CHECK", "NOT_NULL"})


def _column_names(session: Session, table_id: str) -> set[str]:
    """Return the set of column names on a table.

    Args:
        session: Active SQLAlchemy session.
        table_id: Opaque table id.

    Returns:
        set[str]: The column names currently attached to ``table_id``.
    """
    return set(
        session.scalars(select(Column.name).where(Column.table_id == table_id)),
    )


def _classify(payload: TableConstraintPayload) -> str:
    """Return the constraint type for a wire payload.

    Exactly one of the four per-type fields on the envelope must be
    populated; zero or more than one is a client bug that surfaces
    as 400 ``INVALID_ARGUMENT``. This helper encapsulates the check
    so the per-type branches below do not each have to re-verify it.

    Args:
        payload: The validated :class:`TableConstraintPayload` from
            the request body.

    Returns:
        str: One of ``PRIMARY_KEY`` / ``FOREIGN_KEY`` / ``CHECK`` /
            ``NOT_NULL``.

    Raises:
        InvalidRequestError: If zero or more than one per-type
            field is populated on the envelope.
    """
    populated = [
        name
        for name, value in (
            ("primary_key_constraint", payload.primary_key_constraint),
            ("foreign_key_constraint", payload.foreign_key_constraint),
            ("check_constraint", payload.check_constraint),
            ("named_table_constraint", payload.named_table_constraint),
        )
        if value is not None
    ]
    if len(populated) != 1:
        raise InvalidRequestError(
            "TableConstraint must populate exactly one of "
            "primary_key_constraint / foreign_key_constraint / "
            f"check_constraint / named_table_constraint; got {populated or 'none'}",
        )
    mapping = {
        "primary_key_constraint": "PRIMARY_KEY",
        "foreign_key_constraint": "FOREIGN_KEY",
        "check_constraint": "CHECK",
        "named_table_constraint": "NOT_NULL",
    }
    return mapping[populated[0]]


def _validate_columns_exist(names: list[str], available: set[str], label: str) -> None:
    """Raise ``InvalidRequestError`` if any name is not in ``available``.

    Args:
        names: The column names referenced by a constraint payload.
        available: The set of column names that exist on the target table.
        label: Human-readable label used in the error message
            (``"PRIMARY KEY"``, ``"FOREIGN KEY child"``, …).

    Raises:
        InvalidRequestError: If any referenced name is missing.
    """
    missing = [n for n in names if n not in available]
    if missing:
        raise InvalidRequestError(
            f"{label} references unknown column(s): {sorted(missing)}",
        )


def _resolve_parent_table(session: Session, parent_full_name: str) -> Table:
    """Resolve a three-part ``parent_table`` reference to a live row.

    Wraps :func:`table_service.get_table` so the 400 / 404 contract
    for foreign keys matches the contract every other address-resolving
    endpoint in the project uses.

    ``InvalidRequestError`` (malformed three-part name) and
    ``NotFoundError`` (missing parent) may propagate from
    :func:`table_service.get_table`.

    Args:
        session: Active SQLAlchemy session.
        parent_full_name: ``catalog.schema.table`` from the wire.

    Returns:
        Table: The parent table row.
    """
    return table_service.get_table(session, parent_full_name)


def _build_definition(
    session: Session,
    table: Table,
    payload: TableConstraintPayload,
    constraint_type: str,
) -> dict:
    """Validate and assemble the JSON ``definition`` for a constraint row.

    Per-type validation rules:

    * ``PRIMARY_KEY`` — every listed column must exist on the
      target table, and at most one PK is allowed per table. A
      second PK raises 409 ``ALREADY_EXISTS``.
    * ``FOREIGN_KEY`` — child columns must exist on the target
      table; ``parent_table`` must resolve via
      :func:`_resolve_parent_table`; ``parent_columns`` must exist
      on the resolved parent. The resolved parent's opaque ``id``
      is stored as ``parent_table_id`` so a rename of either side
      leaves the declaration intact.
    * ``CHECK`` — ``sql_text`` is stored verbatim; ``child_columns``
      is informational and not validated against the table.
    * ``NOT_NULL`` — ``child_column`` must exist on the target
      table; the column's ``nullable`` flag is deliberately not
      flipped (orthogonal representation — see ADR-0012).

    Args:
        session: Active SQLAlchemy session.
        table: The target table.
        payload: Validated wire payload.
        constraint_type: The type classified by :func:`_classify`.

    Returns:
        dict: The JSON ``definition`` blob to persist on the row.

    ``InvalidRequestError`` may propagate from
    :func:`_validate_columns_exist` (unknown column) and
    :func:`_resolve_parent_table` (malformed three-part FK
    ``parent_table``). ``NotFoundError`` may propagate from
    :func:`_resolve_parent_table` when the FK parent does not
    exist.

    Raises:
        ConflictError: On a second PK declaration for the same table.
    """
    columns = _column_names(session, table.id)

    if constraint_type == "PRIMARY_KEY":
        assert isinstance(payload.primary_key_constraint, PrimaryKeyConstraint)
        pk = payload.primary_key_constraint
        _validate_columns_exist(pk.child_columns, columns, "PRIMARY KEY")
        existing_pk = session.scalar(
            select(TableConstraint.id).where(
                TableConstraint.table_id == table.id,
                TableConstraint.constraint_type == "PRIMARY_KEY",
            ),
        )
        if existing_pk is not None:
            raise ConflictError(
                f"Table '{table.id}' already has a PRIMARY KEY constraint",
            )
        return {"child_columns": list(pk.child_columns)}

    if constraint_type == "FOREIGN_KEY":
        assert isinstance(payload.foreign_key_constraint, ForeignKeyConstraint)
        fk = payload.foreign_key_constraint
        _validate_columns_exist(fk.child_columns, columns, "FOREIGN KEY child")
        parent = _resolve_parent_table(session, fk.parent_table)
        parent_columns = _column_names(session, parent.id)
        _validate_columns_exist(fk.parent_columns, parent_columns, "FOREIGN KEY parent")
        return {
            "child_columns": list(fk.child_columns),
            "parent_table_id": parent.id,
            "parent_columns": list(fk.parent_columns),
        }

    if constraint_type == "CHECK":
        assert isinstance(payload.check_constraint, CheckConstraint)
        ck = payload.check_constraint
        return {
            "child_columns": list(ck.child_columns),
            "sql_text": ck.sql_text,
        }

    # NOT_NULL
    assert isinstance(payload.named_table_constraint, NotNullConstraint)
    nn = payload.named_table_constraint
    _validate_columns_exist([nn.child_column], columns, "NOT NULL")
    return {"child_column": nn.child_column}


def _rehydrate(session: Session, row: TableConstraint) -> TableConstraintPayload:
    """Rebuild a wire-format :class:`TableConstraintPayload` from a stored row.

    For foreign keys, the stored ``parent_table_id`` is re-resolved
    into a live three-part ``catalog.schema.table`` full_name. If
    the parent table has since been deleted (tables never delete
    constraint rows that *reference* them — see
    :func:`delete_constraints_for_table`) the parent name is
    rendered as the sentinel ``<deleted>.<deleted>.<deleted>`` so
    clients can still see the declaration shape.

    Args:
        session: Active SQLAlchemy session.
        row: The stored ORM row.

    Returns:
        TableConstraintPayload: The reconstructed wire payload.
    """
    definition = row.definition or {}
    if row.constraint_type == "PRIMARY_KEY":
        return TableConstraintPayload(
            name=row.name,
            primary_key_constraint=PrimaryKeyConstraint(
                child_columns=list(definition.get("child_columns", [])),
            ),
        )
    if row.constraint_type == "FOREIGN_KEY":
        parent_id = definition.get("parent_table_id")
        parent_full_name = "<deleted>.<deleted>.<deleted>"
        if parent_id:
            parent = session.get(Table, parent_id)
            if parent is not None:
                parent_full_name = (
                    f"{parent.schema.catalog.name}.{parent.schema.name}.{parent.name}"
                )
        return TableConstraintPayload(
            name=row.name,
            foreign_key_constraint=ForeignKeyConstraint(
                child_columns=list(definition.get("child_columns", [])),
                parent_table=parent_full_name,
                parent_columns=list(definition.get("parent_columns", [])),
            ),
        )
    if row.constraint_type == "CHECK":
        return TableConstraintPayload(
            name=row.name,
            check_constraint=CheckConstraint(
                child_columns=list(definition.get("child_columns", [])),
                sql_text=str(definition.get("sql_text", "")),
            ),
        )
    return TableConstraintPayload(
        name=row.name,
        named_table_constraint=NotNullConstraint(
            child_column=str(definition.get("child_column", "")),
        ),
    )


def list_constraints(
    session: Session,
    table_id: str,
) -> list[TableConstraintPayload]:
    """Return the declared constraints for a table, ordered by creation.

    Two calls against an unchanged state return a byte-identical
    list because rows are ordered by ``(created_at, id)`` — same
    stable-ordering posture used by every other list helper in
    the service layer.

    Args:
        session: Active SQLAlchemy session.
        table_id: Opaque table id whose constraints to fetch.

    Returns:
        list[TableConstraintPayload]: The rehydrated wire list.
            Empty when the table has no declared constraints.
    """
    rows = list(
        session.scalars(
            select(TableConstraint)
            .where(TableConstraint.table_id == table_id)
            .order_by(TableConstraint.created_at, TableConstraint.id),
        ),
    )
    return [_rehydrate(session, row) for row in rows]


def add_constraint(
    session: Session,
    table: Table,
    payload: TableConstraintPayload,
) -> TableConstraint:
    """Validate and insert one declared constraint on a table.

    Flow:

    1. Classify the envelope into one of the four concrete types.
    2. Run per-type validation — column existence, PK uniqueness,
       FK parent resolution — via :func:`_build_definition`. A
       validation failure raises 400 ``INVALID_ARGUMENT`` or 409
       ``ALREADY_EXISTS`` (PK duplicate) **before any write**.
    3. Insert the row. The ``(table_id, name)`` unique constraint
       catches duplicate names race-safely — same pattern as every
       other create path in the project.

    The caller is responsible for committing the session;
    ``update_delta_table`` does this once at the end of the batch
    so multiple ``add-constraint`` actions in a single ``UpdateTable``
    request apply transactionally.

    Args:
        session: Active SQLAlchemy session.
        table: The target table row (already resolved by the caller).
        payload: Validated wire payload.

    Returns:
        TableConstraint: The freshly inserted ORM row.

    ``NotFoundError`` may propagate from :func:`_build_definition`
    when a foreign-key parent table does not resolve.

    Raises:
        InvalidRequestError: On a mis-shaped envelope (zero or
            multiple populated per-type fields) or on a defensive
            internal classification miss. Other validation-layer
            ``InvalidRequestError`` raises are emitted from
            :func:`_build_definition` / :func:`_validate_columns_exist`
            and propagate through this function unchanged.
        ConflictError: On a second PK for the same table (raised
            by :func:`_build_definition`), or on a duplicate
            constraint name detected via the unique constraint.
    """
    constraint_type = _classify(payload)
    if constraint_type not in _VALID_TYPES:  # pragma: no cover - defensive
        raise InvalidRequestError(f"Unknown constraint type '{constraint_type}'")
    definition = _build_definition(session, table, payload, constraint_type)
    row = TableConstraint(
        table_id=table.id,
        name=payload.name,
        constraint_type=constraint_type,
        definition=definition,
        created_at=_now_ms(),
    )
    session.add(row)
    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        raise ConflictError(
            f"Constraint '{payload.name}' already exists on this table",
        ) from exc
    return row


def drop_constraint(
    session: Session,
    table: Table,
    name: str,
    if_exists: bool = False,
) -> None:
    """Remove a declared constraint from a table by name.

    With ``if_exists=False`` (the default) a missing constraint
    raises 404 ``NOT_FOUND``; with ``if_exists=True`` the call is a
    no-op. Matches the Delta spec's tri-state ``NOT_FOUND | found |
    noop`` pattern for idempotent DDL.

    Args:
        session: Active SQLAlchemy session. The caller commits.
        table: The target table row.
        name: Constraint name to drop.
        if_exists: Idempotent-delete flag.

    Raises:
        NotFoundError: If the constraint does not exist and
            ``if_exists`` is false.
    """
    row = session.scalar(
        select(TableConstraint).where(
            TableConstraint.table_id == table.id,
            TableConstraint.name == name,
        ),
    )
    if row is None:
        if if_exists:
            return
        raise NotFoundError(
            f"Constraint '{name}' does not exist on table '{table.id}'",
        )
    session.delete(row)


def delete_constraints_for_table(session: Session, table_id: str) -> None:
    """Cascade hook: wipe every constraint attached to a table.

    Called from :func:`soyuz_catalog.services.table_service.delete_table`
    so dropping a table also drops its declared constraints in the
    same transaction. Constraints on *other* tables that reference
    this one as a foreign key parent are **not** cascaded — the row
    stays and rehydration renders ``parent_table`` as a
    ``<deleted>`` sentinel, which keeps the simpler single-table
    drop path free of cross-table fan-out. A future sprint can
    tighten this to 409-unless-force if a consumer asks.

    Args:
        session: Active SQLAlchemy session. The caller commits.
        table_id: Opaque id of the table being deleted.
    """
    session.execute(
        delete(TableConstraint).where(TableConstraint.table_id == table_id),
    )
