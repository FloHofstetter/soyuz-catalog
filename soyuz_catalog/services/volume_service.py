"""Business logic for the Volumes resource."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from soyuz_catalog.api.schemas import CreateVolume, UpdateVolume
from soyuz_catalog.db import commit_or_conflict
from soyuz_catalog.exceptions import InvalidRequestError, NotFoundError
from soyuz_catalog.models import Catalog, Schema, Volume, _now_ms
from soyuz_catalog.pagination import apply_keyset, build_next_token
from soyuz_catalog.services.permissions_service import wipe_permissions_for
from soyuz_catalog.storage import parse_storage_uri


def parse_full_name(full_name: str) -> tuple[str, str, str]:
    """Split a Unity Catalog volume ``full_name`` into its three parts.

    The UC REST spec addresses volumes by
    ``"{catalog_name}.{schema_name}.{volume_name}"`` with two dot
    separators, identical in shape to a table full name. Any other
    layout — missing dot, empty parts, extra dots — is a client bug and
    we surface it as 400 ``INVALID_ARGUMENT`` so the caller learns
    immediately rather than getting a confusing 404.

    Args:
        full_name: The ``catalog.schema.volume`` path parameter.

    Returns:
        tuple[str, str, str]: ``(catalog_name, schema_name, volume_name)``.

    Raises:
        InvalidRequestError: If ``full_name`` is not exactly three
            dot-separated non-empty parts.
    """
    parts = full_name.split(".")
    if len(parts) != 3 or not all(parts):
        raise InvalidRequestError(
            f"Volume full_name '{full_name}' must be of the form "
            "'catalog_name.schema_name.volume_name'",
        )
    return parts[0], parts[1], parts[2]


def _get_schema_or_404(session: Session, catalog_name: str, schema_name: str) -> Schema:
    """Fetch the parent schema or raise ``NotFoundError``.

    Resolves catalog → schema in two queries. Either miss is surfaced as
    404; we do not distinguish "no such catalog" from "no such schema
    inside that catalog" at the API layer because from the client's
    perspective the parent address is simply invalid.

    Args:
        session: Active SQLAlchemy session.
        catalog_name: Name of the parent catalog.
        schema_name: Name of the parent schema, relative to its catalog.

    Returns:
        Schema: The matching schema row.

    Raises:
        NotFoundError: If either the catalog or the schema does not exist.
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


def create_volume(session: Session, payload: CreateVolume) -> Volume:
    """Insert a new volume row under an existing schema.

    The parent schema is resolved by ``(catalog_name, schema_name)`` to
    its opaque ``id``, and ``catalog_id`` is denormalised onto the row
    from the resolved schema so list queries can filter on both parents
    without a join — same shape as
    :func:`soyuz_catalog.services.table_service.create_table`. Duplicate
    detection relies on the ``(schema_id, name)`` unique constraint plus
    ``IntegrityError`` translation rather than a pre-check ``SELECT``,
    which would race with concurrent inserts.

    When ``storage_location`` is present it is scheme-validated via
    :func:`soyuz_catalog.storage.parse_storage_uri`. MANAGED volumes may
    still omit it entirely — the check only fires when the field was
    sent — which preserves the UC spec's optional-location contract.

    Args:
        session: Active SQLAlchemy session.
        payload: Validated create request.

    Returns:
        Volume: The newly created volume.

    Raises:
        ConflictError: If a volume with the same name already exists
            under that schema. (``NotFoundError`` may also propagate from
            :func:`_get_schema_or_404` when the parent catalog or schema
            does not exist, and ``InvalidRequestError`` from
            :func:`soyuz_catalog.storage.parse_storage_uri` when a
            provided ``storage_location`` uses an unsupported scheme.)
    """
    schema = _get_schema_or_404(session, payload.catalog_name, payload.schema_name)
    if payload.storage_location is not None:
        parse_storage_uri(payload.storage_location)
    volume = Volume(
        name=payload.name,
        schema_id=schema.id,
        catalog_id=schema.catalog_id,
        volume_type=payload.volume_type,
        storage_location=payload.storage_location,
        comment=payload.comment,
    )
    session.add(volume)
    with commit_or_conflict(
        session,
        f"Volume '{payload.catalog_name}.{payload.schema_name}.{payload.name}' already exists",
    ):
        pass
    session.refresh(volume)
    return volume


def get_volume(session: Session, full_name: str) -> Volume:
    """Fetch a volume by its ``catalog.schema.volume`` full name.

    The lookup walks catalog → schema → volume because volume names are
    only unique per schema. A missing catalog, schema, or volume all
    surface as 404 — the client's full_name address simply does not
    resolve to a real resource.

    Args:
        session: Active SQLAlchemy session.
        full_name: ``catalog_name.schema_name.volume_name`` path parameter.

    Returns:
        Volume: The matching volume row.

    Raises:
        NotFoundError: If any of catalog, schema, or volume is missing.
    """
    catalog_name, schema_name, volume_name = parse_full_name(full_name)
    schema = _get_schema_or_404(session, catalog_name, schema_name)
    volume = session.scalar(
        select(Volume).where(
            Volume.schema_id == schema.id,
            Volume.name == volume_name,
        ),
    )
    if volume is None:
        raise NotFoundError(f"Volume '{full_name}' does not exist")
    return volume


def get_volume_by_id(session: Session, volume_id: str) -> Volume:
    """Fetch a volume by its opaque ``id`` rather than by full name.

    Used by endpoints that address a volume by identity instead of by the
    catalog.schema.volume path — primarily
    ``/temporary-volume-credentials``, which must remain valid across a
    rename of either parent.

    Args:
        session: Active SQLAlchemy session.
        volume_id: Opaque volume identifier (the ``id`` column).

    Returns:
        Volume: The matching volume row.

    Raises:
        NotFoundError: If no volume with that id exists.
    """
    volume = session.scalar(select(Volume).where(Volume.id == volume_id))
    if volume is None:
        raise NotFoundError(f"Volume with id '{volume_id}' does not exist")
    return volume


def list_volumes(
    session: Session,
    catalog_name: str,
    schema_name: str,
    max_results: int | None = None,
    page_token: str | None = None,
) -> tuple[list[Volume], str | None]:
    """List volumes under a schema with keyset pagination.

    Both ``catalog_name`` and ``schema_name`` are required by the UC
    spec — volumes have no legitimate "list everything under this
    catalog" shape because a schema name is only meaningful inside
    its catalog. If the parent does not exist we surface 404 rather
    than an empty list so that typos in the query parameters are not
    silently masked. Ordering is ``(created_at ASC, id ASC)``.
    ``NotFoundError`` may propagate from :func:`_get_schema_or_404`,
    and ``InvalidRequestError`` from
    :func:`soyuz_catalog.pagination.apply_keyset` when
    ``max_results`` is out of range or ``page_token`` fails to
    decode.

    Args:
        session: Active SQLAlchemy session.
        catalog_name: Parent catalog name.
        schema_name: Parent schema name, relative to its catalog.
        max_results: Spec-defined page size hint. Defaults to 100,
            capped at 1000.
        page_token: Spec-defined opaque page token from a previous
            call, or ``None`` for the first page.

    Returns:
        tuple[list[Volume], str | None]: One page of volumes under
            the schema and the next page token (``None`` if last).
    """
    schema = _get_schema_or_404(session, catalog_name, schema_name)
    stmt, limit = apply_keyset(
        select(Volume).where(Volume.schema_id == schema.id),
        Volume,
        page_token,
        max_results,
    )
    rows = list(session.scalars(stmt))
    return build_next_token(rows, limit)


def update_volume(
    session: Session,
    full_name: str,
    payload: UpdateVolume,
    fields_set: set[str],
) -> Volume:
    """Apply a PATCH to a volume.

    The UC spec restricts volume updates to ``new_name`` and ``comment``
    only — ``storage_location`` and ``volume_type`` are immutable, and
    volumes have no ``properties`` map. The Pydantic layer enforces this
    via ``extra="forbid"``; the service layer uses ``fields_set`` from
    ``model_fields_set`` to distinguish "field omitted" from "field sent
    as null" so that ``{"comment": null}`` clears the comment while
    ``{}`` is a no-op (the latter is a regression test for the UC OSS
    Java behaviour of returning 500 on an empty PATCH body).

    A rename collides on the per-schema unique constraint and surfaces
    as 409, same shape as
    :func:`soyuz_catalog.services.schema_service.update_schema`.

    Args:
        session: Active SQLAlchemy session.
        full_name: Current ``catalog.schema.volume`` path parameter.
        payload: Validated update request.
        fields_set: Names of fields explicitly present in the request body.

    Returns:
        Volume: The updated volume row.

    Raises:
        ConflictError: If ``new_name`` collides with an existing volume
            under the same schema.
    """
    volume = get_volume(session, full_name)

    if not fields_set:
        return volume

    if "new_name" in fields_set and payload.new_name is not None:
        volume.name = payload.new_name
    if "comment" in fields_set:
        volume.comment = payload.comment

    volume.updated_at = _now_ms()

    with commit_or_conflict(
        session,
        f"Volume rename to '{payload.new_name}' collides with an existing volume",
    ):
        pass
    session.refresh(volume)
    return volume


def delete_volume(session: Session, full_name: str, force: bool = False) -> None:
    """Delete a volume.

    ``force`` is accepted for spec and route-signature stability but is
    currently a no-op: volumes have no child resources. The parameter is
    wired through now so the route signature is stable across sprints.

    ``NotFoundError`` may propagate from :func:`get_volume` when the
    volume does not exist.

    Args:
        session: Active SQLAlchemy session.
        full_name: ``catalog.schema.volume`` path parameter.
        force: Cascade flag — accepted but currently ignored.
    """
    del force
    volume = get_volume(session, full_name)
    wipe_permissions_for(session, [("volume", volume.id)])
    session.delete(volume)
    session.commit()
