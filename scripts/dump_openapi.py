"""Dump the FastAPI OpenAPI document to stdout.

Used by the ``just regen-client`` flow and the ``client-drift`` CI job.
Calls ``app.openapi()`` directly rather than booting uvicorn and scraping
``/openapi.json`` — deterministic, no ports, no lifespan side effects
(``init_db`` / migrations do not run because we never enter the ASGI
lifespan).

ADR-0007 records why the generated client exists in the first place; this
script is the source-of-truth producer for every regeneration.
"""

from __future__ import annotations

import json
import sys

from soyuz_catalog.api.main import create_app


def main() -> int:
    """Write the OpenAPI document as JSON to stdout.

    Returns:
        int: Process exit code. Always ``0`` on success; exceptions bubble
            up and the interpreter returns non-zero.
    """
    app = create_app()
    json.dump(app.openapi(), sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
