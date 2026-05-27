"""Business logic for the Tags resource.

Tags are a Databricks-only, over-the-spec extension (ADR-0010);
upstream Unity Catalog OSS and ``all.yaml`` have no tag concept. The service
mirrors the permissions posture: a flat table keyed on the opaque resource
id, a single resolver call at the boundary, and an additive (not
replace-style) PATCH shape.

The service exposes three public entry points:

* :func:`list_tags` — read the current tag set of a securable.
* :func:`update_tags` — apply a list of ``TagChange`` set/remove operations
  transactionally.
* :func:`resolve_tag_securable` — translate a ``(securable_type, full_name)``
  pair into the opaque row id stored on every ``tags`` row. Shared by both
  read and update paths. Extends the permissions resolver with 4-part
  ``catalog.schema.table.column`` handling.

Tags are append-only history in the same sense as lineage edges: there is
no delete-time cascade. When the underlying catalog / schema / table /
column is dropped, the tag rows stay behind as unreachable orphans (the
opaque ``securable_id`` is unique per creation, so a new resource with the
same full_name cannot inherit them). This keeps every ``delete_*`` service
unchanged and matches the lineage posture (ADR-0008).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import delete, select

from soyuz_catalog.api.schemas import TagChange, TagEntry, TagList
from soyuz_catalog.db import commit_or_raise
from soyuz_catalog.exceptions import InvalidRequestError, NotFoundError
from soyuz_catalog.models import Column, Tag, _now_ms
from soyuz_catalog.services import permissions_service

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


# The subset of securable types that tags are supported on in the MVP
# scope. Volume / function / registered_model are a non-breaking additive
# extension — the service is the only place that needs to change because
# the storage column is just a 32-char hex.
_SUPPORTED_TYPES = frozenset({"catalog", "schema", "table", "column"})


def resolve_tag_securable(session: Session, securable_type: str, full_name: str) -> str:
    """Translate a tag address into the opaque ``id`` to key the row on.

    Wraps :func:`permissions_service.resolve_securable` to add the 4-part
    ``catalog.schema.table.column`` case the permissions resolver does not
    know about. The returned id is the opaque row id of the leaf resource
    — a catalog id, schema id, table id, or column id — which is what
    :class:`soyuz_catalog.models.Tag` stores.

    Keying on the opaque id makes tags rename-invariant: renaming any parent
    in the chain leaves every tag attached, the same property permissions
    and lineage rely on.

    Args:
        session: Active SQLAlchemy session.
        securable_type: One of ``catalog``, ``schema``, ``table``, ``column``.
        full_name: Dotted address of the securable. Shape depends on type:
            1 segment for catalog, 2 for schema, 3 for table, 4 for column.

    Returns:
        str: The opaque ``id`` of the resolved row.

    Raises:
        InvalidRequestError: If the full_name segment count does not match
            the securable type, or if ``securable_type`` is not in the
            MVP supported set.
        NotFoundError: If any segment fails to resolve.
    """
    if securable_type not in _SUPPORTED_TYPES:
        raise InvalidRequestError(
            f"Tags are not supported on securable type '{securable_type}'. "
            f"MVP scope is {sorted(_SUPPORTED_TYPES)}; see ADR-0010.",
        )

    if securable_type == "column":
        parts = full_name.split(".")
        if len(parts) != 4 or not all(parts):
            raise InvalidRequestError(
                f"column full_name '{full_name}' must be 'catalog.schema.table.column'",
            )
        catalog_name, schema_name, table_name, column_name = parts
        table_id = permissions_service.resolve_securable(
            session,
            "table",
            f"{catalog_name}.{schema_name}.{table_name}",
        )
        column_id = session.scalar(
            select(Column.id).where(
                Column.table_id == table_id,
                Column.name == column_name,
            ),
        )
        if column_id is None:
            raise NotFoundError(f"Column '{full_name}' does not exist")
        return column_id

    return permissions_service.resolve_securable(session, securable_type, full_name)


def list_tags(session: Session, securable_type: str, full_name: str) -> TagList:
    """Return the current tag set of a securable.

    Resolves the address, queries every matching row, and returns the
    entries sorted by key so two calls against an unchanged state return
    byte-identical bodies. An empty result is ``{"tags": []}`` — the same
    shape as for securables that have no tags at all.

    ``NotFoundError`` may propagate from :func:`resolve_tag_securable` when
    any segment of the full name is wrong.

    Args:
        session: Active SQLAlchemy session.
        securable_type: One of ``catalog``, ``schema``, ``table``, ``column``.
        full_name: Spec-shaped dotted address.

    Returns:
        TagList: The current tag set, sorted by key.
    """
    securable_id = resolve_tag_securable(session, securable_type, full_name)
    rows = list(
        session.scalars(
            select(Tag)
            .where(
                Tag.securable_type == securable_type,
                Tag.securable_id == securable_id,
            )
            .order_by(Tag.key),
        ),
    )
    return _rows_to_list(rows)


def update_tags(
    session: Session,
    securable_type: str,
    full_name: str,
    changes: list[TagChange],
) -> TagList:
    """Apply a batch of set/remove changes to a securable's tags.

    Like permissions, the shape is additive rather than replace-style: the
    client submits set/remove operations and soyuz applies them
    transactionally. The flow is:

    1. Resolve the address once.
    2. Apply every ``remove`` first (bulk DELETE per key).
    3. Apply every ``set`` after that — upsert semantics: an existing row
       for the same key is UPDATEd in place (``value`` + ``updated_at``
       refreshed), a missing key is INSERTed.
    4. Commit once at the end, re-query the full state sorted by key, and
       return it so the caller does not need a follow-up GET.

    Overlapping operations within a single PATCH resolve as *set wins*:
    ``(remove key, set key)`` ends with the key present, which is the
    opposite of a naive "last operation wins" and matches the multi-writer
    invariant — two clients setting the same key after one client removed
    it should not leave a gap.

    An empty ``changes`` list is a valid no-op and returns the current
    state without opening a write transaction.

    Args:
        session: Active SQLAlchemy session.
        securable_type: One of ``catalog``, ``schema``, ``table``, ``column``.
        full_name: Spec-shaped dotted address.
        changes: The batch of changes to apply, in order.

    Returns:
        TagList: The full post-change state of the securable, sorted by key.

    ``InvalidRequestError`` and ``NotFoundError`` may also propagate
    from :func:`resolve_tag_securable` when the ``securable_type`` is
    outside the MVP set or the full_name does not resolve.

    Raises:
        IntegrityError: If a concurrent PATCH races past the pre-check
            SELECT and collides on the composite unique index. Re-raised
            after rolling back so the client can retry — same race
            strategy as ``update_permissions``.
    """
    securable_id = resolve_tag_securable(session, securable_type, full_name)

    if not changes:
        return list_tags(session, securable_type, full_name)

    remove_keys: set[str] = set()
    set_ops: dict[str, str | None] = {}
    for change in changes:
        if change.op == "remove":
            remove_keys.add(change.key)
        else:
            # set wins over a prior remove in the same batch
            remove_keys.discard(change.key)
            set_ops[change.key] = change.value

    if remove_keys:
        session.execute(
            delete(Tag).where(
                Tag.securable_type == securable_type,
                Tag.securable_id == securable_id,
                Tag.key.in_(sorted(remove_keys)),
            ),
        )

    if set_ops:
        existing = {
            row.key: row
            for row in session.scalars(
                select(Tag).where(
                    Tag.securable_type == securable_type,
                    Tag.securable_id == securable_id,
                    Tag.key.in_(sorted(set_ops.keys())),
                ),
            )
        }
        now = _now_ms()
        for key, value in set_ops.items():
            row = existing.get(key)
            if row is None:
                session.add(
                    Tag(
                        securable_type=securable_type,
                        securable_id=securable_id,
                        key=key,
                        value=value,
                        created_at=now,
                        updated_at=now,
                    ),
                )
            else:
                row.value = value
                row.updated_at = now

    # Two concurrent PATCHes could race on the unique index; the
    # pre-check above is advisory, not a lock. Let any IntegrityError
    # propagate so the client can retry — same race strategy as
    # ``update_permissions``.
    with commit_or_raise(session):
        pass

    rows = list(
        session.scalars(
            select(Tag)
            .where(
                Tag.securable_type == securable_type,
                Tag.securable_id == securable_id,
            )
            .order_by(Tag.key),
        ),
    )
    return _rows_to_list(rows)


def _rows_to_list(rows: list[Tag]) -> TagList:
    """Serialise ``Tag`` ORM rows into the wire-format response.

    Args:
        rows: The raw ``Tag`` rows for the securable, already filtered and
            sorted by key at query time.

    Returns:
        TagList: The serialised response body.
    """
    return TagList(
        tags=[
            TagEntry(
                key=row.key,
                value=row.value,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
            for row in rows
        ],
    )
