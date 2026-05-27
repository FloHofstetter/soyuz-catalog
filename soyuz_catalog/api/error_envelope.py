"""Shared builders for the soyuz error response body.

Centralised so that both the FastAPI exception handlers in
:mod:`soyuz_catalog.api.main` and the middleware fallback in
:mod:`soyuz_catalog.api.middleware` produce exactly the same shape. The
middleware owns the uncaught-exception path because ``@app.exception_
handler(Exception)`` in FastAPI is wired to Starlette's
``ServerErrorMiddleware``, which sits *above* user middleware — so a
response produced there would never pass back through our Request-ID
middleware and would lose its ``X-Request-ID`` header.
"""

from __future__ import annotations

from typing import Any

from fastapi.responses import JSONResponse

from soyuz_catalog.api.request_context import get_request_id


def envelope(
    status_code: int,
    error_code: str,
    message: str,
    *,
    details: Any | None = None,
) -> JSONResponse:
    """Build the standard soyuz error response.

    Also stamps ``X-Request-ID`` on the response itself so clients that
    short-circuit on non-200 bodies still see the correlation ID even if
    some future middleware ordering change moves the header-writing
    middleware out of the path.

    Args:
        status_code: HTTP status to return.
        error_code: Machine-readable soyuz error code.
        message: Human-readable description.
        details: Optional structured payload. Only the validation handler
            uses this today (to preserve the raw pydantic ``errors()``
            list alongside the flattened ``message``).

    Returns:
        JSONResponse: The response with body and ``X-Request-ID`` header
        set when a request scope is active.
    """
    body: dict[str, Any] = {
        "error_code": error_code,
        "message": message,
        "request_id": get_request_id(),
    }
    if details is not None:
        body["details"] = details
    response = JSONResponse(status_code=status_code, content=body)
    rid = get_request_id()
    if rid is not None:
        response.headers["X-Request-ID"] = rid
    return response


def flatten_validation_message(errors: list[dict[str, Any]]) -> str:
    """Render a pydantic ``errors()`` list as a single summary string.

    The raw per-error dicts are still available under ``details`` in the
    response body — this is only the one-line summary shoved into
    ``message`` so a client that just prints ``message`` to the user gets
    something useful.

    Args:
        errors: The list returned by ``RequestValidationError.errors()``.

    Returns:
        str: A ``"; "``-joined rendering, or a generic fallback if the
        list is empty (which should not happen in practice).
    """
    if not errors:
        return "Request validation failed."
    parts: list[str] = []
    for err in errors:
        loc = ".".join(str(p) for p in err.get("loc", ()))
        msg = err.get("msg", "invalid")
        parts.append(f"{loc}: {msg}" if loc else msg)
    return "; ".join(parts)
