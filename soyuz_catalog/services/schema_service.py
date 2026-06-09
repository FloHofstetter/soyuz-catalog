"""Business logic for the Schemas resource."""

from __future__ import annotations

import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from soyuz_catalog.api.schemas import CreateSchema, UpdateSchema
from soyuz_catalog.db import commit_or_conflict
from soyuz_catalog.exceptions import ConflictError, InvalidRequestError, NotFoundError
from soyuz_catalog.models import (
    Catalog,
    Function,
    RegisteredModel,
    Schema,
    Table,
    Volume,
    _now_ms,
)
from soyuz_catalog.pagination import apply_keyset, build_next_token
from soyuz_catalog.services.permissions_service import wipe_permissions_for
from soyuz_catalog.storage import derive_managed_location, parse_storage_uri


def parse_full_name(full_name: str) -> tuple[str, str]:
    """Split a Unity Catalog schema ``full_name`` into its two parts.

    The UC REST spec addresses schemas by ``"{catalog_name}.{schema_name}"``
    with a single dot separator. Any other shape — missing dot, empty halves,
    more than one dot — is a client bug and we surface it as a 400 so the
    caller learns about it immediately rather than getting a confusing 404.

    Args:
        full_name: The ``catalog.schema`` path parameter.

    Returns:
        tuple[str, str]: ``(catalog_name, schema_name)``.

    Raises:
        InvalidRequestError: If ``full_name`` is not exactly two dot-separated
            non-empty parts.
    """
    parts = full_name.split(".")
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise InvalidRequestError(
            f"Schema full_name '{full_name}' must be of the form 'catalog_name.schema_name'",
        )
    return parts[0], parts[1]


def _get_catalog_or_404(session: Session, catalog_name: str) -> Catalog:
    """Fetch the parent catalog or raise ``NotFoundError``.

    Args:
        session: Active SQLAlchemy session.
        catalog_name: Name of the parent catalog.

    Returns:
        Catalog: The matching catalog row.

    Raises:
        NotFoundError: If no catalog with ``catalog_name`` exists.
    """
    catalog = session.scalar(select(Catalog).where(Catalog.name == catalog_name))
    if catalog is None:
        raise NotFoundError(f"Catalog '{catalog_name}' does not exist")
    return catalog


def create_schema(session: Session, payload: CreateSchema) -> Schema:
    """Insert a new schema row under an existing catalog.

    The parent catalog is resolved by name to the opaque ``catalog_id`` used
    as the actual foreign key, so a later catalog rename leaves the
    relationship intact. Duplicate detection relies on the ``(catalog_id,
    name)`` unique constraint plus ``IntegrityError`` translation rather than
    a pre-check ``SELECT`` — same race-condition reasoning as
    :func:`soyuz_catalog.services.catalog_service.create_catalog`.

    When ``storage_root`` is present it is scheme-validated via
    :func:`soyuz_catalog.storage.parse_storage_uri`; absent (the common
    case for schemas under a managed catalog) is still allowed.

    ``storage_location`` is derived at create time via
    :func:`soyuz_catalog.storage.derive_managed_location` from the
    schema's own ``storage_root`` when supplied, falling back to the
    parent catalog's ``storage_root``. Both being absent yields
    ``None`` — matching the spec's *"if it is absent, managed securables
    under this schema will try to use storage_location of the parent
    catalog instead"* semantics. As with catalogs the derivation keys
    on the opaque ``schema_id`` so renaming the schema (or its parent
    catalog) must **not** recompute this field; ``update_schema``
    leaves it alone.

    Args:
        session: Active SQLAlchemy session.
        payload: Validated create request.

    Returns:
        Schema: The newly created schema.

    Raises:
        ConflictError: If a schema with the same name already exists under
            that catalog. (``InvalidRequestError`` may also propagate from
            :func:`soyuz_catalog.storage.parse_storage_uri` when a provided
            ``storage_root`` uses an unsupported scheme.)
    """
    catalog = _get_catalog_or_404(session, payload.catalog_name)
    if payload.storage_root is not None:
        parse_storage_uri(payload.storage_root)
    schema_id = uuid.uuid4().hex
    effective_root = payload.storage_root or catalog.storage_root
    schema = Schema(
        id=schema_id,
        name=payload.name,
        catalog_id=catalog.id,
        comment=payload.comment,
        properties=payload.properties or {},
        storage_root=payload.storage_root,
        storage_location=derive_managed_location(
            effective_root,
            "schemas",
            schema_id,
        ),
    )
    session.add(schema)
    with commit_or_conflict(
        session,
        f"Schema '{payload.catalog_name}.{payload.name}' already exists",
    ):
        pass
    session.refresh(schema)
    return schema


def get_schema(session: Session, full_name: str) -> Schema:
    """Fetch a schema by its ``catalog.schema`` full name.

    The lookup is two-step — resolve the catalog, then resolve the schema
    within that catalog — because schema names are only unique per catalog.
    A missing parent catalog and a missing schema both surface as 404; we do
    not distinguish them at the API layer because either way the full_name
    does not address a real resource.

    Args:
        session: Active SQLAlchemy session.
        full_name: ``catalog_name.schema_name`` path parameter.

    Returns:
        Schema: The matching schema row.

    Raises:
        NotFoundError: If either the catalog or the schema does not exist.
    """
    catalog_name, schema_name = parse_full_name(full_name)
    catalog = _get_catalog_or_404(session, catalog_name)
    schema = session.scalar(
        select(Schema).where(
            Schema.catalog_id == catalog.id,
            Schema.name == schema_name,
        ),
    )
    if schema is None:
        raise NotFoundError(f"Schema '{full_name}' does not exist")
    return schema


def list_schemas(
    session: Session,
    catalog_name: str,
    max_results: int | None = None,
    page_token: str | None = None,
) -> tuple[list[Schema], str | None]:
    """List schemas under a catalog with keyset pagination.

    If the parent catalog does not exist we surface 404 rather than an
    empty list — UC OSS does the same, and an empty result would
    silently mask typos in the ``catalog_name`` query parameter.
    Ordering is ``(created_at ASC, id ASC)`` — see
    :func:`soyuz_catalog.services.catalog_service.list_catalogs` for
    the rationale. ``InvalidRequestError`` may propagate from
    :func:`soyuz_catalog.pagination.apply_keyset` when ``max_results``
    is out of range or ``page_token`` fails to decode.

    Args:
        session: Active SQLAlchemy session.
        catalog_name: Parent catalog name (required query parameter).
        max_results: Spec-defined page size hint. Defaults to 100,
            capped at 1000.
        page_token: Spec-defined opaque page token from a previous
            call, or ``None`` for the first page.

    Returns:
        tuple[list[Schema], str | None]: One page of schemas under
            the catalog and the next page token (``None`` if last).
    """
    catalog = _get_catalog_or_404(session, catalog_name)
    stmt, limit = apply_keyset(
        select(Schema).where(Schema.catalog_id == catalog.id),
        Schema,
        page_token,
        max_results,
    )
    rows = list(session.scalars(stmt))
    return build_next_token(rows, limit)


def update_schema(
    session: Session,
    full_name: str,
    payload: UpdateSchema,
    fields_set: set[str],
) -> Schema:
    """Apply a PATCH to a schema.

    Same replace-style semantics as
    :func:`soyuz_catalog.services.catalog_service.update_catalog`: fields in
    ``fields_set`` are written through (including ``properties={}`` which
    clears all properties — the UC OSS bug fix), fields absent from the body
    are left untouched. A rename collides on the per-catalog unique
    constraint and surfaces as 409.

    Args:
        session: Active SQLAlchemy session.
        full_name: Current ``catalog.schema`` path parameter.
        payload: Validated update request.
        fields_set: Names of fields explicitly present in the request body.

    Returns:
        Schema: The updated schema row.

    Raises:
        ConflictError: If ``new_name`` collides with an existing schema under
            the same catalog.
    """
    schema = get_schema(session, full_name)

    if not fields_set:
        return schema

    if "new_name" in fields_set and payload.new_name is not None:
        schema.name = payload.new_name
    if "comment" in fields_set:
        schema.comment = payload.comment
    if "properties" in fields_set:
        schema.properties = payload.properties or {}

    schema.updated_at = _now_ms()

    with commit_or_conflict(
        session,
        f"Schema '{schema.catalog.name}.{payload.new_name}' already exists",
    ):
        pass
    session.refresh(schema)
    return schema


def delete_schema(session: Session, full_name: str, force: bool = False) -> None:
    """Delete a schema.

    If the schema has any child tables, volumes, functions, or
    registered models and ``force`` is false, the delete is rejected
    with :class:`ConflictError` (HTTP 409, ``FAILED_PRECONDITION``).
    With ``force=true``, all four child kinds are cascaded — tables
    and volumes via the ORM relationships' ``cascade="all,
    delete-orphan"``; functions and registered models (together with
    the latter's own versions) via explicit bulk DELETE statements
    because those classes do not have back-populating relationships
    on :class:`Schema`.

    Each child kind is checked independently so the rejection
    message can name whichever side(s) blocked the delete.

    Args:
        session: Active SQLAlchemy session.
        full_name: ``catalog.schema`` path parameter.
        force: When true, cascade-delete all child tables, volumes,
            functions, and registered models (and their sub-rows).
            When false, refuse the delete if any children exist.

    Raises:
        ConflictError: If the schema still has any child resources
            and ``force`` is false.
    """
    schema = get_schema(session, full_name)
    table_count = session.scalar(
        select(func.count()).select_from(Table).where(Table.schema_id == schema.id),
    )
    volume_count = session.scalar(
        select(func.count()).select_from(Volume).where(Volume.schema_id == schema.id),
    )
    function_count = session.scalar(
        select(func.count()).select_from(Function).where(Function.schema_id == schema.id),
    )
    model_count = session.scalar(
        select(func.count())
        .select_from(RegisteredModel)
        .where(RegisteredModel.schema_id == schema.id),
    )
    if (table_count or volume_count or function_count or model_count) and not force:
        blockers: list[str] = []
        if table_count:
            blockers.append("tables")
        if volume_count:
            blockers.append("volumes")
        if function_count:
            blockers.append("functions")
        if model_count:
            blockers.append("registered models")
        raise ConflictError(
            f"Cannot delete schema '{full_name}' because it still has "
            f"{' and '.join(blockers)}. Pass force=true to cascade.",
        )
    # Grants-cascade: collect the full descendant set (schema itself
    # plus every child table/volume/function/model) before the ORM
    # cascade fires on ``session.delete(schema)``. See
    # :func:`soyuz_catalog.services.catalog_service.delete_catalog`
    # for the rationale.
    pairs: list[tuple[str, str]] = [("schema", schema.id)]
    table_ids: list[str] = []
    for model_cls, label in (
        (Table, "table"),
        (Volume, "volume"),
        (Function, "function"),
        (RegisteredModel, "registered_model"),
    ):
        ids = list(
            session.scalars(select(model_cls.id).where(model_cls.schema_id == schema.id)),
        )
        if label == "table":
            table_ids = ids
        pairs.extend((label, rid) for rid in ids)
    wipe_permissions_for(session, pairs)
    # Declared-constraints cascade (ADR-0012): the ORM
    # cascade below drops the table rows, but their constraint rows
    # live FK-free on a side table and must be wiped explicitly —
    # exactly what ``delete_table`` does on the single-table path.
    from soyuz_catalog.services.constraints_service import delete_constraints_for_tables

    delete_constraints_for_tables(session, table_ids)
    if function_count:
        session.execute(delete(Function).where(Function.schema_id == schema.id))
    if model_count:
        # Fetch-then-delete so ModelVersion cascade via ORM relationship fires.
        models = list(
            session.scalars(
                select(RegisteredModel).where(RegisteredModel.schema_id == schema.id),
            ),
        )
        for model in models:
            session.delete(model)
    session.delete(schema)
    session.commit()
