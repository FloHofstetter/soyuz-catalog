"""Storage-location utilities.

This subpackage owns everything that looks at the *shape* of a storage
URI — scheme validation today, credential routing once that sprint
lands. It deliberately has no SQLAlchemy or FastAPI imports so it can be
used from services, schemas, and (eventually) the credentials vending
layer without introducing a dependency cycle.
"""

from __future__ import annotations

from soyuz_catalog.storage.uri import (
    SUPPORTED_SCHEMES,
    StorageUri,
    derive_managed_location,
    parse_storage_uri,
)

__all__ = [
    "SUPPORTED_SCHEMES",
    "StorageUri",
    "derive_managed_location",
    "parse_storage_uri",
]
