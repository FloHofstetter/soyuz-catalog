"""HTTP middleware for soyuz-catalog."""

from __future__ import annotations

import logging
import uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from soyuz_catalog.api.error_envelope import envelope
from soyuz_catalog.api.request_context import (
    agent_run_id_var,
    client_ip_var,
    principal_var,
    request_id_var,
)

_HEADER = "X-Request-ID"
_PRINCIPAL_HEADER = "X-Principal"
_AGENT_RUN_ID_HEADER = "X-Agent-Run-Id"

_logger = logging.getLogger(__name__)


def _coerce_inbound(value: str | None) -> str:
    """Accept a caller-supplied ID only if it parses as a UUID.

    Silently-accept-garbage is the UC OSS bug class soyuz exists to fix
    (see ADR-0002). If a client sends ``X-Request-ID: ; DROP TABLE --``
    we mint a fresh ID rather than propagate that string into logs or
    downstream systems. The header is advisory — we do not return 400 —
    but we also do not trust it blindly.

    Args:
        value: The raw header value, or ``None`` if absent.

    Returns:
        str: A 32-character UUID hex. Either the client's original value
        (if well-formed) or a freshly minted one.
    """
    if value:
        try:
            return uuid.UUID(value).hex
        except ValueError:
            pass
    return uuid.uuid4().hex


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Assign and echo a correlation ID for every HTTP request.

    Three responsibilities in one dispatch:

    1. Mint (or accept) a UUID-hex request ID, expose it via the
       ``request_id_var`` ``ContextVar`` so exception handlers and the
       log filter can read it without plumbing a ``Request`` through
       every call site.
    2. Stamp the final ID onto every outgoing response as
       ``X-Request-ID`` so clients can quote it when reporting issues.
    3. Catch any exception escaping the route layer and return the soyuz
       error envelope for 500s. This belongs in the middleware rather
       than a FastAPI ``@app.exception_handler(Exception)`` because that
       handler runs in Starlette's ``ServerErrorMiddleware``, which sits
       *above* user middleware — responses built there never pass back
       through us and would lose their correlation header.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Run the stack, stamp the ID, and envelope any stray 500s.

        Args:
            request: The incoming Starlette request.
            call_next: The next handler in the middleware chain.

        Returns:
            Response: The downstream response with ``X-Request-ID`` set,
            or a 500 envelope if an exception escaped the route.
        """
        rid = _coerce_inbound(request.headers.get(_HEADER))
        token = request_id_var.set(rid)
        # Audit-context: capture X-Principal + X-Agent-Run-Id from the
        # inbound headers so :mod:`soyuz_catalog.services.audit` can
        # stamp every log_action() row without the routes having to
        # plumb a Request through every call site.  Garbage values are
        # tolerated (no validation) — the audit trail is best-effort
        # metadata, not a security gate.
        agent_run_id_raw = request.headers.get(_AGENT_RUN_ID_HEADER)
        agent_run_id = (
            agent_run_id_raw.strip()
            if isinstance(agent_run_id_raw, str) and agent_run_id_raw.strip()
            else None
        )
        principal_raw = request.headers.get(_PRINCIPAL_HEADER)
        principal = (
            principal_raw.strip()
            if isinstance(principal_raw, str) and principal_raw.strip()
            else None
        )
        client_ip = request.client.host if request.client else None
        principal_token = principal_var.set(principal)
        agent_run_id_token = agent_run_id_var.set(agent_run_id)
        client_ip_token = client_ip_var.set(client_ip)
        try:
            try:
                response = await call_next(request)
            except Exception as exc:
                _logger.error("unhandled exception", exc_info=exc)
                response = envelope(500, "INTERNAL", "Internal server error.")
            response.headers[_HEADER] = rid
            return response
        finally:
            client_ip_var.reset(client_ip_token)
            agent_run_id_var.reset(agent_run_id_token)
            principal_var.reset(principal_token)
            request_id_var.reset(token)
