"""Per-request context shared between middleware, handlers, and logging.

The Request-ID middleware mints a UUID hex per incoming request and stores
it here; exception handlers read it to stamp the error body, and the
logging filter reads it to attach ``request_id`` to every log record. A
single module-level ``ContextVar`` is the right tool because the value has
to be reachable from *outside* a route function (the log filter runs on
arbitrary records, not just ones emitted from handler code), and
``request.state`` is only accessible where a ``Request`` object is in
scope.
"""

from __future__ import annotations

from contextvars import ContextVar

request_id_var: ContextVar[str | None] = ContextVar("soyuz_request_id", default=None)

# Audit-context vars populated by ``AuditContextMiddleware`` from the
# ``X-Principal`` and ``X-Agent-Run-Id`` headers.  Both default to
# ``None`` so non-agent / unauthenticated traffic does not raise when
# the audit helper reads them outside a request scope.
principal_var: ContextVar[str | None] = ContextVar("soyuz_principal", default=None)
agent_run_id_var: ContextVar[str | None] = ContextVar("soyuz_agent_run_id", default=None)
client_ip_var: ContextVar[str | None] = ContextVar("soyuz_client_ip", default=None)


def get_request_id() -> str | None:
    """Return the current request's correlation ID, if one is set.

    Returns:
        str | None: The UUID hex assigned by ``RequestIDMiddleware`` for
        the in-flight request, or ``None`` when called outside a request
        scope (e.g. during app startup or in a unit test that bypasses
        the middleware).
    """
    return request_id_var.get()


def get_principal() -> str | None:
    """Return the current request's ``X-Principal`` value, if any.

    Returns:
        str | None: The header value or ``None`` outside a request
        scope.
    """
    return principal_var.get()


def get_agent_run_id() -> str | None:
    """Return the current request's ``X-Agent-Run-Id`` value, if any.

    Returns:
        str | None: The header value (UUID-shape) or ``None`` outside
        a request scope or when the caller did not forward an
        ``X-Agent-Run-Id`` header.
    """
    return agent_run_id_var.get()


def get_client_ip() -> str | None:
    """Return the best-effort source IP of the current request.

    Returns:
        str | None: The IP string (``request.client.host`` value) or
        ``None`` outside a request scope.
    """
    return client_ip_var.get()
