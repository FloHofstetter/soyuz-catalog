"""Business logic for the Permissions (grants) resource.

soyuz-catalog treats permissions as a **storage backend for an auth
proxy**, not an enforcement layer. The catalog server persists grants
and returns them on demand, but never consults them when deciding
whether to honour an unrelated endpoint — that is the auth proxy's
job. See ADR-0005 and ``DIVERGENCES.md`` for the full rationale.

The service exposes three public entry points plus the cascade hook:

* :func:`get_permissions` — read the current state of a securable,
  optionally filtered by principal.
* :func:`update_permissions` — apply a list of ``PermissionsChange``
  add/remove operations transactionally.
* :func:`resolve_securable` — translate a ``(securable_type,
  full_name)`` pair into the opaque row id stored on every
  ``permissions`` row. Shared by both read and update paths.
* :func:`wipe_permissions_for` — bulk-delete every grant attached to
  a given ``(type, id)`` pair. Called from every resource's
  ``delete_*`` service so grants do not survive their parent.

The per-type privilege **allow-set** lives in this module as a flat
dict. UC OSS Java accepts any privilege on any type at API time and
defers rejection to an enforcement layer that does not exist in OSS;
soyuz rejects at write time as part of the same silent-accept-garbage
divergence class that motivates ``extra="forbid"`` on every request
body. The set itself is soyuz-specific — see the ``Permissions``
section of ``DIVERGENCES.md``.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from sqlalchemy import delete, select, tuple_

from soyuz_catalog.api.schemas import (
    PermissionsChange,
    PermissionsList,
    PrivilegeAssignment,
)
from soyuz_catalog.db import commit_or_raise
from soyuz_catalog.exceptions import InvalidRequestError, NotFoundError
from soyuz_catalog.models import (
    Catalog,
    Credential,
    ExternalLocation,
    Function,
    Permission,
    RegisteredModel,
    Schema,
    Table,
    Volume,
)
from soyuz_catalog.services import metastore_service

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


# ---------------------------------------------------------------------------
# Per-securable-type privilege allow-set.
#
# Mapping of ``securable_type`` to the set of ``Privilege`` values soyuz
# considers valid on that type. UC OSS Java has no such check — any
# privilege may be granted on any securable at API time, and the
# enforcement layer (which OSS does not ship) is expected to reject
# later. soyuz rejects at write time with 400 ``INVALID_ARGUMENT`` so
# the silent-accept-garbage class that motivates ``extra="forbid"`` is
# consistent across every write path. The allow-set is hand-curated
# from the ``x-enum-descriptions`` of the upstream ``Privilege`` enum
# in ``unitycatalog/api/all.yaml`` and documented verbatim in
# ``DIVERGENCES.md``.
# ---------------------------------------------------------------------------
_ALLOWED_PRIVILEGES: dict[str, frozenset[str]] = {
    "metastore": frozenset(
        {
            "CREATE CATALOG",
            "CREATE EXTERNAL LOCATION",
            "CREATE STORAGE CREDENTIAL",
        },
    ),
    "catalog": frozenset({"USE CATALOG", "CREATE SCHEMA"}),
    "schema": frozenset(
        {
            "USE SCHEMA",
            "CREATE TABLE",
            "CREATE FUNCTION",
            "CREATE VOLUME",
            "CREATE MODEL",
        },
    ),
    "table": frozenset({"SELECT", "MODIFY"}),
    "function": frozenset({"EXECUTE"}),
    "volume": frozenset({"READ VOLUME"}),
    "registered_model": frozenset({"EXECUTE"}),
    "external_location": frozenset(
        {
            "READ FILES",
            "WRITE FILES",
            "CREATE EXTERNAL TABLE",
            "CREATE EXTERNAL VOLUME",
            "CREATE MANAGED STORAGE",
        },
    ),
    "credential": frozenset({"CREATE EXTERNAL LOCATION"}),
}


# Securable types whose full_name is exactly one dotted segment.
_ONE_PART_TYPES = frozenset({"catalog", "credential", "external_location"})
# Securable types whose full_name is exactly two dotted segments.
_TWO_PART_TYPES = frozenset({"schema"})
# Securable types whose full_name is exactly three dotted segments.
_THREE_PART_TYPES = frozenset({"table", "volume", "function", "registered_model"})


def resolve_securable(session: Session, securable_type: str, full_name: str) -> str:
    """Translate a securable address into the opaque ``id`` to key grants on.

    The caller passes the spec-shaped ``(securable_type, full_name)``
    pair; this helper walks whichever resource table corresponds to
    the type, verifies every segment of the full name resolves, and
    returns the leaf row's ``id`` column. That id is what
    :class:`soyuz_catalog.models.Permission` stores, so the returned
    value is rename-invariant — a later rename of any parent leaves
    every existing grant attached.

    The segment count is enforced strictly: a 2-part name passed with
    a 3-part type (or vice versa) raises :class:`InvalidRequestError`
    with a 400. soyuz rejects at the boundary rather than silently
    treating "nearly right" as "right" — same rule as every other
    write path in the project.

    ``metastore`` is a special case: the upstream spec treats the
    metastore as a named singleton, so the expected ``full_name`` is
    the live ``metastore_id`` from
    :func:`soyuz_catalog.services.metastore_service.get_metastore_summary`.
    Any other string surfaces as 404 so typos do not silently
    accumulate grants against a nonexistent id.

    Args:
        session: Active SQLAlchemy session.
        securable_type: One of the nine ``SecurableType`` enum values.
        full_name: Dotted address of the securable. Shape depends on
            type: 1 segment for catalog / credential / external
            location, 2 for schema, 3 for table / volume / function /
            registered model, and the live ``metastore_id`` for
            metastore.

    Returns:
        str: The opaque ``id`` of the resolved row — the value to
            store on every :class:`Permission` row for this securable.

    Raises:
        InvalidRequestError: If the full_name segment count does not
            match the securable type.
        NotFoundError: If any segment of the full_name fails to
            resolve to a real row.
    """
    parts = full_name.split(".")
    if securable_type == "metastore":
        metastore = metastore_service.get_metastore_summary(session)
        if full_name != metastore.id:
            raise NotFoundError(
                f"Metastore '{full_name}' does not exist (expected the live metastore id)",
            )
        return metastore.id

    if securable_type in _ONE_PART_TYPES:
        if len(parts) != 1 or not parts[0]:
            raise InvalidRequestError(
                f"{securable_type} full_name '{full_name}' must be a single segment",
            )
        return _resolve_one_part(session, securable_type, parts[0])

    if securable_type in _TWO_PART_TYPES:
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise InvalidRequestError(
                f"schema full_name '{full_name}' must be 'catalog.schema'",
            )
        return _resolve_schema(session, parts[0], parts[1])

    if securable_type in _THREE_PART_TYPES:
        if len(parts) != 3 or not all(parts):
            raise InvalidRequestError(
                f"{securable_type} full_name '{full_name}' must be 'catalog.schema.<name>'",
            )
        return _resolve_three_part(session, securable_type, parts[0], parts[1], parts[2])

    # Pydantic routes filter unknown types at the FastAPI boundary,
    # so reaching here means an internal caller misused the API.
    raise InvalidRequestError(f"Unknown securable_type '{securable_type}'")


def _resolve_one_part(session: Session, securable_type: str, name: str) -> str:
    """Resolve a 1-part name to an opaque row id.

    Args:
        session: Active SQLAlchemy session.
        securable_type: ``catalog``, ``credential``, or ``external_location``.
        name: The single segment of the full name.

    Returns:
        str: The resolved row's ``id``.

    Raises:
        NotFoundError: If the row does not exist.
    """
    if securable_type == "catalog":
        row = session.scalar(select(Catalog).where(Catalog.name == name))
        if row is None:
            raise NotFoundError(f"Catalog '{name}' does not exist")
        return row.id
    if securable_type == "credential":
        row = session.scalar(select(Credential).where(Credential.name == name))
        if row is None:
            raise NotFoundError(f"Credential '{name}' does not exist")
        return row.id
    row = session.scalar(select(ExternalLocation).where(ExternalLocation.name == name))
    if row is None:
        raise NotFoundError(f"External location '{name}' does not exist")
    return row.id


def _resolve_schema(session: Session, catalog_name: str, schema_name: str) -> str:
    """Resolve ``catalog.schema`` to a schema row id.

    Args:
        session: Active SQLAlchemy session.
        catalog_name: Parent catalog name.
        schema_name: Schema name under that catalog.

    Returns:
        str: The resolved schema's ``id``.

    Raises:
        NotFoundError: If either catalog or schema is missing.
    """
    catalog = session.scalar(select(Catalog).where(Catalog.name == catalog_name))
    if catalog is None:
        raise NotFoundError(f"Catalog '{catalog_name}' does not exist")
    schema = session.scalar(
        select(Schema).where(Schema.catalog_id == catalog.id, Schema.name == schema_name),
    )
    if schema is None:
        raise NotFoundError(f"Schema '{catalog_name}.{schema_name}' does not exist")
    return schema.id


def _resolve_three_part(
    session: Session,
    securable_type: str,
    catalog_name: str,
    schema_name: str,
    leaf_name: str,
) -> str:
    """Resolve ``catalog.schema.<name>`` to a table/volume/function/model id.

    Args:
        session: Active SQLAlchemy session.
        securable_type: One of ``table``, ``volume``, ``function``,
            ``registered_model``.
        catalog_name: Parent catalog name.
        schema_name: Parent schema name.
        leaf_name: Innermost resource name.

    Returns:
        str: The resolved leaf row's ``id``.

    Raises:
        NotFoundError: If any segment fails to resolve.
    """
    schema_id = _resolve_schema(session, catalog_name, schema_name)
    full_name = f"{catalog_name}.{schema_name}.{leaf_name}"
    model_map = {
        "table": Table,
        "volume": Volume,
        "function": Function,
        "registered_model": RegisteredModel,
    }
    model_cls = model_map[securable_type]
    row = session.scalar(
        select(model_cls).where(model_cls.schema_id == schema_id, model_cls.name == leaf_name),
    )
    if row is None:
        raise NotFoundError(f"{securable_type} '{full_name}' does not exist")
    return row.id


def get_permissions(
    session: Session,
    securable_type: str,
    full_name: str,
    principal: str | None = None,
) -> PermissionsList:
    """Return the current permission state of a securable.

    Resolves the address, queries every matching row, pivots the flat
    ``(principal, privilege)`` rows into the per-principal shape the
    spec defines, and returns the result. Assignments are sorted by
    principal so the response is stable across calls; each
    principal's privilege list is sorted too, for the same reason.
    An empty result is ``{"privilege_assignments": []}`` — the same
    shape as for securables that have no grants at all.

    ``NotFoundError`` may propagate from :func:`resolve_securable`
    when any segment of the full name is wrong.

    Args:
        session: Active SQLAlchemy session.
        securable_type: One of the nine ``SecurableType`` values.
        full_name: Spec-shaped dotted address.
        principal: Optional filter. When set, only that principal's
            assignment appears in the response (or none, if the
            principal has no grants).

    Returns:
        PermissionsList: The current state of the securable, filtered
            if ``principal`` is provided.
    """
    securable_id = resolve_securable(session, securable_type, full_name)
    stmt = select(Permission).where(
        Permission.securable_type == securable_type,
        Permission.securable_id == securable_id,
    )
    if principal is not None:
        stmt = stmt.where(Permission.principal == principal)
    rows = list(session.scalars(stmt))
    return _pivot_to_assignments(rows)


def update_permissions(
    session: Session,
    securable_type: str,
    full_name: str,
    changes: list[PermissionsChange],
) -> PermissionsList:
    """Apply a batch of add/remove changes to a securable's grants.

    Unlike the other PATCH routes in this project, permissions are
    *not* replace-style: the client submits additive and subtractive
    operations, and soyuz applies them transactionally. The flow is:

    1. Resolve the address once.
    2. Validate every ``add`` privilege against the per-type
       :data:`_ALLOWED_PRIVILEGES` **before any write** — a single
       disallowed privilege anywhere in the batch rejects the whole
       request with 400 and no state change.
    3. For each change, apply ``remove`` first (bulk DELETE), then
       ``add`` (idempotent insert via ``INSERT ... ON CONFLICT
       DO NOTHING``-style pre-filter). Overlapping entries within a
       single change therefore resolve as *add wins* — a tiebreaker
       the upstream spec does not pin; see ``DIVERGENCES.md``.
    4. Commit once at the end, re-query the full state, and return
       it (no ``principal`` filter — the caller gets the whole
       post-state to avoid a follow-up GET).

    ``remove`` entries are **not** gated by the allow-set: removing a
    privilege that was never allowed on this type is harmless (no row
    to delete) and makes cleanup after an allow-set tightening
    possible.

    An empty ``changes`` list is a valid no-op and returns the
    current state without opening a write transaction.

    Args:
        session: Active SQLAlchemy session.
        securable_type: One of the nine ``SecurableType`` values.
        full_name: Spec-shaped dotted address.
        changes: The batch of changes to apply, in order.

    Returns:
        PermissionsList: The full post-change state of the securable.

    Raises:
        InvalidRequestError: If any ``add`` privilege is not in the
            per-type allow-set. Raised before any DB write.
            ``NotFoundError`` may also propagate from
            :func:`resolve_securable` when the address is wrong.
        IntegrityError: If a concurrent PATCH races past the
            pre-check SELECT and collides on the composite unique
            index. Re-raised after rolling back so the client can
            retry — same race strategy as every other ``create_*``
            in the service layer.
    """
    securable_id = resolve_securable(session, securable_type, full_name)

    allowed = _ALLOWED_PRIVILEGES.get(securable_type, frozenset())
    for change in changes:
        for priv in change.add:
            if priv not in allowed:
                raise InvalidRequestError(
                    f"Privilege '{priv}' is not valid on securable type "
                    f"'{securable_type}'. See DIVERGENCES.md for the per-type allow-set.",
                )

    if not changes:
        rows = list(
            session.scalars(
                select(Permission).where(
                    Permission.securable_type == securable_type,
                    Permission.securable_id == securable_id,
                ),
            ),
        )
        return _pivot_to_assignments(rows)

    for change in changes:
        if change.remove:
            session.execute(
                delete(Permission).where(
                    Permission.securable_type == securable_type,
                    Permission.securable_id == securable_id,
                    Permission.principal == change.principal,
                    Permission.privilege.in_(list(change.remove)),
                ),
            )
        # Pre-check the existing set for this principal on this
        # securable so duplicate adds are silently skipped without
        # triggering an ``IntegrityError`` rollback — the rollback
        # would discard every change earlier in the batch. Duplicates
        # within the same ``add`` list are deduped via the set too,
        # matching the spec's *"set of privileges"* wording.
        if change.add:
            already = set(
                session.scalars(
                    select(Permission.privilege).where(
                        Permission.securable_type == securable_type,
                        Permission.securable_id == securable_id,
                        Permission.principal == change.principal,
                    ),
                ),
            )
            for priv in set(change.add):
                if priv in already:
                    continue
                session.add(
                    Permission(
                        securable_type=securable_type,
                        securable_id=securable_id,
                        principal=change.principal,
                        privilege=priv,
                    ),
                )
                already.add(priv)

    # Two concurrent PATCHes could race on the unique index; the
    # pre-check above is advisory, not a lock. Let any IntegrityError
    # propagate so the client can retry — same race strategy as every
    # other create_* in the service layer.
    with commit_or_raise(session):
        pass

    rows = list(
        session.scalars(
            select(Permission).where(
                Permission.securable_type == securable_type,
                Permission.securable_id == securable_id,
            ),
        ),
    )
    return _pivot_to_assignments(rows)


def wipe_permissions_for(
    session: Session,
    pairs: Iterable[tuple[str, str]],
) -> None:
    """Bulk-delete every grant attached to the given securables.

    Called from every resource's ``delete_*`` service so that when a
    catalog / schema / table / etc. is dropped, its grants disappear
    in the same transaction. The cascade runs unconditionally — it is
    not gated by ``force=true`` because grants are not first-class
    children the way tables or volumes are. Without this hook, a
    renamed-and-recreated resource would inherit stale grants from
    the previous incarnation, which would be a real privilege bug.

    The caller is responsible for collecting the full set of
    descendant ids before invoking the helper (e.g. catalog delete
    must pass ``[("catalog", cid), ("schema", sid), ...]``).

    Args:
        session: Active SQLAlchemy session. The delete is executed on
            the session but *not* committed — the caller's own
            ``session.commit()`` at the end of ``delete_*`` flushes it.
        pairs: Iterable of ``(securable_type, securable_id)`` tuples
            to wipe. An empty iterable is a no-op.
    """
    items = list(pairs)
    if not items:
        return
    # Group by type so we issue one DELETE per type, minimising round-trips.
    by_type: dict[str, list[str]] = {}
    for stype, sid in items:
        by_type.setdefault(stype, []).append(sid)
    for stype, ids in by_type.items():
        session.execute(
            delete(Permission).where(
                Permission.securable_type == stype,
                Permission.securable_id.in_(ids),
            ),
        )


def _ancestor_chain(
    session: Session,
    securable_type: str,
    securable_id: str,
) -> list[tuple[str, str]]:
    """Return the ordered ancestor chain for a resolved leaf securable.

    Walks upward from ``(securable_type, securable_id)`` through the
    owning relationships encoded in the ORM and returns the full
    chain of ``(type, id)`` pairs starting with the leaf itself and
    ending with the metastore. Every entry in the returned list is a
    pair the :class:`Permission` table can be queried with directly,
    so :func:`get_effective_permissions` can union grants across the
    full chain with a single SELECT.

    The walk uses the denormalised ``catalog_id`` / ``schema_id``
    columns on Table / Volume / Function / RegisteredModel so the
    chain for a 3-part leaf requires one row-lookup plus one
    metastore-summary call — four
    round-trips in the worst case, the same fan-out the direct
    :func:`get_permissions` path already pays. No new index is
    required: the leaf row is fetched by primary key, then two
    scalar FK reads, then the single-row metastore.

    ``ExternalLocation`` and ``Credential`` are metastore-level
    resources (no owning catalog/schema), so their chain is
    ``[(type, id), ("metastore", mid)]``. ``catalog`` is
    ``[("catalog", cid), ("metastore", mid)]``. ``schema`` is
    ``[("schema", sid), ("catalog", cid), ("metastore", mid)]``.
    ``metastore`` is a singleton — chain is just ``[("metastore", mid)]``.

    Args:
        session: Active SQLAlchemy session.
        securable_type: A resolved securable type (must already be
            validated by :func:`resolve_securable` — this helper
            does not re-check segment counts).
        securable_id: Opaque id of the leaf row, as returned by
            :func:`resolve_securable`.

    Returns:
        list[tuple[str, str]]: ``[(type, id), …]`` leaf-to-root.
            Every entry queryable against
            :class:`Permission.securable_type` /
            :class:`Permission.securable_id`.

    Raises:
        NotFoundError: If a parent referenced by a denormalised FK
            has been deleted out from under the caller (should be
            impossible in practice because the cascade in
            ``delete_*`` wipes grants in the same transaction — but
            raised explicitly so a stale ``securable_id`` from a
            long-lived transaction cannot silently truncate the
            chain).
        InvalidRequestError: If ``securable_type`` is an unknown
            3-part leaf type — only reachable if an internal caller
            bypasses :func:`resolve_securable` (the FastAPI routing
            layer rejects unknown types at 422 before the service
            is ever invoked).
    """
    metastore_id = metastore_service.get_metastore_summary(session).id

    if securable_type == "metastore":
        return [("metastore", metastore_id)]

    if securable_type == "catalog":
        return [("catalog", securable_id), ("metastore", metastore_id)]

    if securable_type in ("external_location", "credential"):
        return [(securable_type, securable_id), ("metastore", metastore_id)]

    if securable_type == "schema":
        schema_row = session.get(Schema, securable_id)
        if schema_row is None:
            raise NotFoundError(f"Schema '{securable_id}' no longer exists")
        return [
            ("schema", securable_id),
            ("catalog", schema_row.catalog_id),
            ("metastore", metastore_id),
        ]

    # Three-part leaves: table / volume / function / registered_model.
    # Every one carries denormalised ``schema_id`` and ``catalog_id``.
    model_map: dict[str, type] = {
        "table": Table,
        "volume": Volume,
        "function": Function,
        "registered_model": RegisteredModel,
    }
    model_cls = model_map.get(securable_type)
    if model_cls is None:
        # Unknown type reaching this helper means an internal caller
        # bypassed ``resolve_securable`` — raise so the bug surfaces
        # at development time rather than silently returning a short
        # chain that skips inheritance.
        raise InvalidRequestError(f"Unknown securable_type '{securable_type}'")
    leaf_row = session.get(model_cls, securable_id)
    if leaf_row is None:
        raise NotFoundError(f"{securable_type} '{securable_id}' no longer exists")
    return [
        (securable_type, securable_id),
        ("schema", leaf_row.schema_id),
        ("catalog", leaf_row.catalog_id),
        ("metastore", metastore_id),
    ]


def get_effective_permissions(
    session: Session,
    securable_type: str,
    full_name: str,
    principal: str | None = None,
) -> PermissionsList:
    """Return the effective (inherited) grant set for a securable.

    Computes the **union** of privileges granted to each principal
    at any level of the securable's ownership chain: table gets
    table-level, schema-level, catalog-level, and metastore-level
    grants all merged together. UC grants are additive (no deny
    rows), so set-union is the only honest aggregation — the
    :func:`_pivot_to_assignments` helper already handles overlap
    correctly because it builds a per-principal set.

    This is a pure computation over existing ``Permission`` rows;
    no new storage, no cached materialisation. The single SELECT
    uses a ``(securable_type, securable_id) IN (…)`` tuple match
    against the full chain, so a leaf at four levels deep pulls
    every relevant grant in one round-trip.

    The endpoint is deliberately over-the-spec: upstream ``all.yaml``
    defines only the direct-grant ``GET /permissions/{type}/{name}``
    form, leaving effective computation to client code that has to
    walk the chain itself. soyuz moves the computation server-side
    so every client gets the same answer. See ``DIVERGENCES.md``
    under "Permissions: effective computation" for the rule and
    the conformance-test skip.

    Args:
        session: Active SQLAlchemy session.
        securable_type: One of the nine UC ``SecurableType`` values.
        full_name: Spec-shaped dotted address of the leaf.
        principal: Optional filter. When present, only that
            principal's assignment appears in the response. Useful
            for "does P have X on L" queries that do not want the
            whole grant matrix over the wire.

    Returns:
        PermissionsList: The effective grants, shape-identical to
            :func:`get_permissions`. Callers can swap endpoints with
            no code change beyond the URL.
            :class:`InvalidRequestError` (wrong segment count /
            unknown type) and :class:`NotFoundError` (missing row
            anywhere in the chain) may propagate from
            :func:`resolve_securable` or :func:`_ancestor_chain`.
    """
    securable_id = resolve_securable(session, securable_type, full_name)
    chain = _ancestor_chain(session, securable_type, securable_id)

    stmt = select(Permission).where(
        tuple_(Permission.securable_type, Permission.securable_id).in_(chain),
    )
    if principal is not None:
        stmt = stmt.where(Permission.principal == principal)
    rows = list(session.scalars(stmt))
    return _pivot_to_assignments(rows)


def _pivot_to_assignments(rows: list[Permission]) -> PermissionsList:
    """Group flat permission rows into ``PrivilegeAssignment`` response shape.

    The output is sorted by principal, and each principal's privilege
    list is also sorted, so two calls against an unchanged state
    return byte-identical bodies — a property tests rely on and a
    convenience for clients that diff responses.

    Args:
        rows: The raw ``Permission`` rows for the securable (already
            filtered by type + id at query time).

    Returns:
        PermissionsList: The pivoted wire-format response.
    """
    by_principal: dict[str, set[str]] = {}
    for row in rows:
        by_principal.setdefault(row.principal, set()).add(row.privilege)
    assignments = [
        PrivilegeAssignment(
            principal=principal,
            privileges=sorted(privs),  # type: ignore[arg-type]
        )
        for principal, privs in sorted(by_principal.items())
    ]
    return PermissionsList(privilege_assignments=assignments)
