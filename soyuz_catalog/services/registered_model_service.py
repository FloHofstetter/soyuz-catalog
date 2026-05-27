"""Business logic for the Registered Models resource."""

from __future__ import annotations

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from soyuz_catalog.api.schemas import CreateRegisteredModel, UpdateRegisteredModel
from soyuz_catalog.db import commit_or_conflict
from soyuz_catalog.exceptions import ConflictError, InvalidRequestError, NotFoundError
from soyuz_catalog.models import Catalog, ModelVersion, RegisteredModel, Schema, _now_ms
from soyuz_catalog.pagination import apply_keyset, build_next_token
from soyuz_catalog.services.permissions_service import wipe_permissions_for


def parse_full_name(full_name: str) -> tuple[str, str, str]:
    """Split a Unity Catalog registered-model ``full_name`` into its three parts.

    Same three-part layout as tables, volumes, and functions. Any
    other shape surfaces as 400 ``INVALID_ARGUMENT``.

    Args:
        full_name: The ``catalog.schema.model`` path parameter.

    Returns:
        tuple[str, str, str]: ``(catalog_name, schema_name, model_name)``.

    Raises:
        InvalidRequestError: If ``full_name`` is not exactly three
            dot-separated non-empty parts.
    """
    parts = full_name.split(".")
    if len(parts) != 3 or not all(parts):
        raise InvalidRequestError(
            f"Registered model full_name '{full_name}' must be of the form "
            "'catalog_name.schema_name.model_name'",
        )
    return parts[0], parts[1], parts[2]


def _get_schema_or_404(session: Session, catalog_name: str, schema_name: str) -> Schema:
    """Fetch the parent schema or raise ``NotFoundError``.

    Args:
        session: Active SQLAlchemy session.
        catalog_name: Name of the parent catalog.
        schema_name: Name of the parent schema, relative to its catalog.

    Returns:
        Schema: The matching schema row.

    Raises:
        NotFoundError: If either parent does not exist.
    """
    catalog = session.scalar(select(Catalog).where(Catalog.name == catalog_name))
    if catalog is None:
        raise NotFoundError(f"Catalog '{catalog_name}' does not exist")
    schema = session.scalar(
        select(Schema).where(
            Schema.catalog_id == catalog.id,
            Schema.name == schema_name,
        ),
    )
    if schema is None:
        raise NotFoundError(f"Schema '{catalog_name}.{schema_name}' does not exist")
    return schema


def create_registered_model(
    session: Session,
    payload: CreateRegisteredModel,
) -> RegisteredModel:
    """Insert a new registered model row under an existing schema.

    Same shape as :func:`soyuz_catalog.services.volume_service.create_volume`:
    parent resolved by ``(catalog_name, schema_name)``, ``catalog_id``
    denormalised onto the row, duplicate detection via ``IntegrityError``
    on the ``(schema_id, name)`` unique constraint.

    ``storage_location`` is deliberately **not** derived on create —
    the UC ``CreateRegisteredModel`` schema does not carry a
    ``storage_root`` and the upstream spec leaves the field as a
    server-owned optional. Any real consumer that needs it can be
    added in a follow-up sprint.

    Args:
        session: Active SQLAlchemy session.
        payload: Validated create request.

    Returns:
        RegisteredModel: The newly created row.

    Raises:
        ConflictError: If a registered model with the same name
            already exists under that schema.
    """
    schema = _get_schema_or_404(session, payload.catalog_name, payload.schema_name)
    model = RegisteredModel(
        name=payload.name,
        schema_id=schema.id,
        catalog_id=schema.catalog_id,
        comment=payload.comment,
    )
    session.add(model)
    with commit_or_conflict(
        session,
        f"Registered model '{payload.catalog_name}.{payload.schema_name}."
        f"{payload.name}' already exists",
    ):
        pass
    session.refresh(model)
    return model


def get_registered_model(session: Session, full_name: str) -> RegisteredModel:
    """Fetch a registered model by its ``catalog.schema.model`` full name.

    Args:
        session: Active SQLAlchemy session.
        full_name: ``catalog_name.schema_name.model_name`` path parameter.

    Returns:
        RegisteredModel: The matching row.

    Raises:
        NotFoundError: If any of catalog, schema, or model is missing.
    """
    catalog_name, schema_name, model_name = parse_full_name(full_name)
    schema = _get_schema_or_404(session, catalog_name, schema_name)
    model = session.scalar(
        select(RegisteredModel).where(
            RegisteredModel.schema_id == schema.id,
            RegisteredModel.name == model_name,
        ),
    )
    if model is None:
        raise NotFoundError(f"Registered model '{full_name}' does not exist")
    return model


def list_registered_models(
    session: Session,
    catalog_name: str | None = None,
    schema_name: str | None = None,
    max_results: int | None = None,
    page_token: str | None = None,
) -> tuple[list[RegisteredModel], str | None]:
    """List registered models with optional parent filters.

    Both ``catalog_name`` and ``schema_name`` are **optional** on this
    endpoint — the UC spec allows a metastore-wide listing. If only
    ``catalog_name`` is provided we filter on the denormalised
    ``catalog_id`` column; if both are provided we resolve to a
    single ``schema_id``; if neither, we list every row. Providing
    ``schema_name`` without ``catalog_name`` is rejected as 400 since
    schema names are not metastore-unique.

    Args:
        session: Active SQLAlchemy session.
        catalog_name: Optional parent catalog filter.
        schema_name: Optional parent schema filter (requires ``catalog_name``).
        max_results: Spec-defined page size hint.
        page_token: Opaque pagination cursor.

    Returns:
        tuple[list[RegisteredModel], str | None]: One page of rows
            plus the next page token.

    Raises:
        InvalidRequestError: If ``schema_name`` is set without
            ``catalog_name``, or if pagination parameters are
            malformed (from :func:`apply_keyset`).
        NotFoundError: If a provided parent does not exist.
    """
    if schema_name is not None and catalog_name is None:
        raise InvalidRequestError(
            "schema_name requires catalog_name because schema names are not metastore-unique",
        )
    stmt = select(RegisteredModel)
    if catalog_name is not None and schema_name is not None:
        schema = _get_schema_or_404(session, catalog_name, schema_name)
        stmt = stmt.where(RegisteredModel.schema_id == schema.id)
    elif catalog_name is not None:
        catalog = session.scalar(select(Catalog).where(Catalog.name == catalog_name))
        if catalog is None:
            raise NotFoundError(f"Catalog '{catalog_name}' does not exist")
        stmt = stmt.where(RegisteredModel.catalog_id == catalog.id)
    stmt, limit = apply_keyset(stmt, RegisteredModel, page_token, max_results)
    rows = list(session.scalars(stmt))
    return build_next_token(rows, limit)


def update_registered_model(
    session: Session,
    full_name: str,
    payload: UpdateRegisteredModel,
    fields_set: set[str],
) -> RegisteredModel:
    """Apply a PATCH to a registered model.

    Replace-style PATCH semantics driven by ``fields_set`` from
    ``model_fields_set`` so ``{"comment": null}`` clears the comment
    while ``{}`` is a no-op, same contract as every other update
    service in this project.

    A rename collides on the per-schema unique constraint and
    surfaces as 409.

    Args:
        session: Active SQLAlchemy session.
        full_name: Current ``catalog.schema.model`` path parameter.
        payload: Validated update request.
        fields_set: Names of fields explicitly present in the body.

    Returns:
        RegisteredModel: The updated row.

    Raises:
        ConflictError: If ``new_name`` collides with an existing
            registered model under the same schema.
    """
    model = get_registered_model(session, full_name)

    if not fields_set:
        return model

    if "new_name" in fields_set and payload.new_name is not None:
        model.name = payload.new_name
    if "comment" in fields_set:
        model.comment = payload.comment

    model.updated_at = _now_ms()

    with commit_or_conflict(
        session,
        f"Registered model rename to '{payload.new_name}' collides with an existing model",
    ):
        pass
    session.refresh(model)
    return model


def delete_registered_model(
    session: Session,
    full_name: str,
    force: bool = False,
) -> None:
    """Delete a registered model.

    If the model has any child :class:`ModelVersion` rows and
    ``force`` is false, the delete is rejected with 409 — same
    gate-and-cascade policy as every other parent resource in this
    project. With ``force=true`` the service deletes every child
    version first and then removes the model row, all in one
    transaction (the ORM relationship's ``cascade="all,
    delete-orphan"`` handles the sub-row deletion when we
    ``session.delete`` the parent).

    Args:
        session: Active SQLAlchemy session.
        full_name: ``catalog.schema.model`` path parameter.
        force: Cascade flag. Without ``force``, any surviving model
            version causes a 409; with ``force=true`` all versions
            are deleted alongside the model.

    Raises:
        ConflictError: If versions exist and ``force`` is false.
    """
    model = get_registered_model(session, full_name)
    version_count = session.scalar(
        select(func.count())
        .select_from(ModelVersion)
        .where(ModelVersion.registered_model_id == model.id),
    )
    if version_count and not force:
        raise ConflictError(
            f"Cannot delete registered model '{full_name}' because it still "
            f"has {version_count} version(s). Pass force=true to cascade.",
        )
    if version_count:
        session.execute(
            delete(ModelVersion).where(ModelVersion.registered_model_id == model.id),
        )
    wipe_permissions_for(session, [("registered_model", model.id)])
    session.delete(model)
    session.commit()
