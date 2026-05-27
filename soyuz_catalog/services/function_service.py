"""Business logic for the Functions resource."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from soyuz_catalog.api.schemas import CreateFunction
from soyuz_catalog.db import commit_or_conflict
from soyuz_catalog.exceptions import InvalidRequestError, NotFoundError
from soyuz_catalog.models import Catalog, Function, Schema
from soyuz_catalog.pagination import apply_keyset, build_next_token
from soyuz_catalog.services.permissions_service import wipe_permissions_for


def parse_full_name(full_name: str) -> tuple[str, str, str]:
    """Split a Unity Catalog function ``full_name`` into its three parts.

    The UC REST spec addresses functions by
    ``"{catalog_name}.{schema_name}.{function_name}"`` with two dot
    separators, identical in shape to a table or volume full name.
    Any other layout is surfaced as 400 ``INVALID_ARGUMENT`` so a
    client typo fails loudly instead of being routed to a surprising
    404.

    Args:
        full_name: The ``catalog.schema.function`` path parameter.

    Returns:
        tuple[str, str, str]: ``(catalog_name, schema_name, function_name)``.

    Raises:
        InvalidRequestError: If ``full_name`` is not exactly three
            dot-separated non-empty parts.
    """
    parts = full_name.split(".")
    if len(parts) != 3 or not all(parts):
        raise InvalidRequestError(
            f"Function full_name '{full_name}' must be of the form "
            "'catalog_name.schema_name.function_name'",
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


def create_function(session: Session, payload: CreateFunction) -> Function:
    """Insert a new function row under an existing schema.

    The parent schema is resolved by ``(catalog_name, schema_name)``
    to its opaque ``id``, and ``catalog_id`` is denormalised onto the
    row from the resolved schema so list queries can filter on both
    parents without a join — same shape as
    :func:`soyuz_catalog.services.volume_service.create_volume`.
    Duplicate detection relies on the ``(schema_id, name)`` unique
    constraint plus ``IntegrityError`` translation rather than a
    pre-check ``SELECT``.

    ``input_params`` and ``return_params`` are serialised into the
    single ``JSON`` columns as ``{"parameters": [...]}`` — see
    :class:`soyuz_catalog.models.Function` for why parameters are
    stored as blobs instead of child rows. ``routine_dependencies`` is
    passed through verbatim as a generic JSON object.

    Args:
        session: Active SQLAlchemy session.
        payload: Validated ``CreateFunction`` body (the inner payload
            unwrapped from ``CreateFunctionRequest`` at the route
            layer).

    Returns:
        Function: The newly created function row.

    Raises:
        ConflictError: If a function with the same name already
            exists under that schema. ``NotFoundError`` may propagate
            from :func:`_get_schema_or_404`.
    """
    schema = _get_schema_or_404(session, payload.catalog_name, payload.schema_name)
    return_params_dict: dict = {"parameters": []}
    if payload.return_params is not None:
        return_params_dict = payload.return_params.model_dump()
    function = Function(
        name=payload.name,
        schema_id=schema.id,
        catalog_id=schema.catalog_id,
        data_type=payload.data_type,
        full_data_type=payload.full_data_type,
        input_params=payload.input_params.model_dump(),
        return_params=return_params_dict,
        routine_body=payload.routine_body,
        routine_definition=payload.routine_definition,
        routine_dependencies=payload.routine_dependencies,
        parameter_style=payload.parameter_style,
        is_deterministic=payload.is_deterministic,
        sql_data_access=payload.sql_data_access,
        is_null_call=payload.is_null_call,
        security_type=payload.security_type,
        specific_name=payload.specific_name,
        external_language=payload.external_language,
        comment=payload.comment,
        properties=payload.properties,
    )
    session.add(function)
    with commit_or_conflict(
        session,
        f"Function '{payload.catalog_name}.{payload.schema_name}.{payload.name}' already exists",
    ):
        pass
    session.refresh(function)
    return function


def get_function(session: Session, full_name: str) -> Function:
    """Fetch a function by its ``catalog.schema.function`` full name.

    Walks catalog → schema → function; each miss surfaces as 404.

    Args:
        session: Active SQLAlchemy session.
        full_name: ``catalog_name.schema_name.function_name`` path parameter.

    Returns:
        Function: The matching function row.

    Raises:
        NotFoundError: If any of catalog, schema, or function is missing.
    """
    catalog_name, schema_name, function_name = parse_full_name(full_name)
    schema = _get_schema_or_404(session, catalog_name, schema_name)
    function = session.scalar(
        select(Function).where(
            Function.schema_id == schema.id,
            Function.name == function_name,
        ),
    )
    if function is None:
        raise NotFoundError(f"Function '{full_name}' does not exist")
    return function


def list_functions(
    session: Session,
    catalog_name: str,
    schema_name: str,
    max_results: int | None = None,
    page_token: str | None = None,
) -> tuple[list[Function], str | None]:
    """List functions under a schema with keyset pagination.

    Both parent filters are required by the UC spec. ``NotFoundError``
    propagates from :func:`_get_schema_or_404` when the parent does
    not exist so that typos in the query parameters are not silently
    masked by an empty result. ``InvalidRequestError`` may propagate
    from :func:`soyuz_catalog.pagination.apply_keyset` on malformed
    pagination parameters.

    Args:
        session: Active SQLAlchemy session.
        catalog_name: Parent catalog name.
        schema_name: Parent schema name, relative to its catalog.
        max_results: Spec-defined page size hint (1..1000).
        page_token: Opaque pagination cursor, or ``None``.

    Returns:
        tuple[list[Function], str | None]: One page of functions plus
            the next page token.
    """
    schema = _get_schema_or_404(session, catalog_name, schema_name)
    stmt, limit = apply_keyset(
        select(Function).where(Function.schema_id == schema.id),
        Function,
        page_token,
        max_results,
    )
    rows = list(session.scalars(stmt))
    return build_next_token(rows, limit)


def delete_function(session: Session, full_name: str) -> None:
    """Delete a function.

    Functions have no child resources, so there is no ``force``
    parameter on the route and no cascade. ``NotFoundError`` may
    propagate from :func:`get_function`.

    Args:
        session: Active SQLAlchemy session.
        full_name: ``catalog.schema.function`` path parameter.
    """
    function = get_function(session, full_name)
    wipe_permissions_for(session, [("function", function.id)])
    session.delete(function)
    session.commit()
