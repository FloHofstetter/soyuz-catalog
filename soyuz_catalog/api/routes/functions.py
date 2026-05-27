"""HTTP routes for the Functions resource."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from soyuz_catalog.api.deps import get_db
from soyuz_catalog.api.schemas import (
    CreateFunctionRequest,
    FunctionInfo,
    FunctionParameterInfos,
    ListFunctionsResponse,
)
from soyuz_catalog.models import Function
from soyuz_catalog.services import function_service

router = APIRouter(prefix="/functions", tags=["functions"])


def _to_info(function: Function) -> FunctionInfo:
    """Assemble a :class:`FunctionInfo` response from an ORM row.

    ``full_name`` / ``catalog_name`` / ``schema_name`` are not columns
    on :class:`Function` — they are computed from the live parent
    schema and its catalog, so a rename of either parent propagates
    for free. ``input_params`` and ``return_params`` are reconstructed
    from the JSON blob columns through the Pydantic wrapper model so
    the wire shape is ``{"parameters": [...]}`` as the spec requires.

    Args:
        function: The function ORM row. Its ``schema`` relationship
            must be loadable — the session that fetched ``function``
            must still be active.

    Returns:
        FunctionInfo: The wire-format response.
    """
    schema = function.schema
    catalog_name = schema.catalog.name
    schema_name = schema.name
    return FunctionInfo(
        name=function.name,
        catalog_name=catalog_name,
        schema_name=schema_name,
        full_name=f"{catalog_name}.{schema_name}.{function.name}",
        input_params=FunctionParameterInfos.model_validate(function.input_params),
        data_type=function.data_type,
        full_data_type=function.full_data_type,
        return_params=FunctionParameterInfos.model_validate(function.return_params),
        routine_body=function.routine_body,  # type: ignore[arg-type]
        routine_definition=function.routine_definition,
        routine_dependencies=function.routine_dependencies,
        parameter_style=function.parameter_style,  # type: ignore[arg-type]
        is_deterministic=function.is_deterministic,
        sql_data_access=function.sql_data_access,  # type: ignore[arg-type]
        is_null_call=function.is_null_call,
        security_type=function.security_type,  # type: ignore[arg-type]
        specific_name=function.specific_name,
        external_language=function.external_language,
        comment=function.comment,
        properties=function.properties,
        owner=function.owner,
        created_at=function.created_at,
        created_by=function.created_by,
        updated_at=function.updated_at,
        updated_by=function.updated_by,
        function_id=function.id,
    )


@router.post(
    "",
    response_model=FunctionInfo,
    response_model_exclude_none=True,
    summary="Create function",
)
def create_function(
    payload: CreateFunctionRequest,
    db: Session = Depends(get_db),
) -> FunctionInfo:
    """Create a new function under an existing schema.

    The request body is the double-wrapped ``{"function_info": {...}}``
    shape from the UC spec — we unwrap the inner ``CreateFunction``
    before handing it to the service layer.

    Args:
        payload: Create request wrapper.
        db: Database session dependency.

    Returns:
        FunctionInfo: The created function.
    """
    function = function_service.create_function(db, payload.function_info)
    return _to_info(function)


@router.get("", response_model=ListFunctionsResponse, summary="List functions")
def list_functions(
    catalog_name: str,
    schema_name: str,
    max_results: int | None = Query(default=None, ge=0, le=1000),
    page_token: str | None = None,
    db: Session = Depends(get_db),
) -> ListFunctionsResponse:
    """List functions under a schema with keyset pagination.

    Args:
        catalog_name: Required query parameter — name of the parent catalog.
        schema_name: Required query parameter — name of the parent schema.
        max_results: Page size hint, 1..1000. Defaults to 100.
        page_token: Opaque cursor from a previous ``next_page_token``.
        db: Database session dependency.

    Returns:
        ListFunctionsResponse: One page of functions plus the next
            page token.
    """
    rows, next_token = function_service.list_functions(
        db,
        catalog_name,
        schema_name,
        max_results,
        page_token,
    )
    return ListFunctionsResponse(
        functions=[_to_info(r) for r in rows],
        next_page_token=next_token,
    )


@router.get(
    "/{full_name}",
    response_model=FunctionInfo,
    response_model_exclude_none=True,
    summary="Get function by full name",
)
def get_function(full_name: str, db: Session = Depends(get_db)) -> FunctionInfo:
    """Fetch a single function by full name.

    Args:
        full_name: ``catalog_name.schema_name.function_name`` path parameter.
        db: Database session dependency.

    Returns:
        FunctionInfo: The requested function.
    """
    function = function_service.get_function(db, full_name)
    return _to_info(function)


@router.delete("/{full_name}", summary="Delete function")
def delete_function(full_name: str, db: Session = Depends(get_db)) -> dict[str, str]:
    """Delete a function.

    The UC REST spec defines no ``UpdateFunction`` — soyuz does not
    register a PATCH handler and FastAPI returns 405 Method Not
    Allowed for that method, same shape as the tables resource.

    Args:
        full_name: ``catalog.schema.function`` path parameter.
        db: Database session dependency.

    Returns:
        dict[str, str]: Empty success payload.
    """
    function_service.delete_function(db, full_name)
    return {}
