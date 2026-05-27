"""Parse and validate ``storage_location`` / ``storage_root`` URIs.

UC OSS Java accepts any string for a storage location — including bare
paths, unknown URI schemes, and empty strings — and pushes the failure
down to whichever engine eventually tries to open the path. That is the
same *silently-accept-garbage* bug class that ``extra="forbid"`` and the
``UNKNOWN_*_OPERATION`` sentinel rejection are written to prevent.
soyuz-catalog therefore parses every storage location on the
write path and rejects schemes outside a small known-good set with
``400 INVALID_ARGUMENT``, so a typo surfaces at catalog-write time
instead of a confusing failure on first query.

Supported schemes are:

- ``file`` — local filesystem (used by the delta-rs integration tests).
- ``s3`` / ``s3a`` — AWS S3 (the ``s3a`` Hadoop variant is accepted
  because it is what the Spark-on-UC client emits).
- ``abfss`` — Azure Data Lake Storage Gen2.
- ``gs`` — Google Cloud Storage.

Read paths are deliberately not validated: rows written before this
sprint may have free-form values and must keep loading. Only
``create_*`` calls gate on the parser.
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit

from soyuz_catalog.exceptions import InvalidRequestError

SUPPORTED_SCHEMES: frozenset[str] = frozenset({"file", "s3", "s3a", "abfss", "gs"})


@dataclass(frozen=True, slots=True)
class StorageUri:
    """A parsed, scheme-validated storage URI.

    Attributes:
        scheme: Lower-cased URI scheme, guaranteed to be in
            :data:`SUPPORTED_SCHEMES`.
        raw: The original input string, trimmed of surrounding whitespace
            but otherwise unmodified. Services persist this verbatim so
            that a round-trip GET returns exactly what the client sent.
    """

    scheme: str
    raw: str


def parse_storage_uri(value: str) -> StorageUri:
    """Parse a storage URI and validate its scheme.

    The parser is deliberately narrow: it does not resolve bucket
    existence, does not touch the network, and does not normalise the
    path. It only checks that the value is a non-empty URI with a
    supported scheme and — for non-``file`` schemes — a non-empty
    authority. ``file://`` is allowed to have an empty authority so that
    ``file:///tmp/foo`` (the canonical local-file form used by delta-rs)
    parses cleanly.

    The error message lists the supported schemes so a client hitting
    this for the first time learns what to change without having to grep
    the server source.

    Args:
        value: The raw ``storage_location`` or ``storage_root`` string
            from a create request.

    Returns:
        StorageUri: The parsed, scheme-validated URI.

    Raises:
        InvalidRequestError: If the input is empty, missing a scheme, or
            has a scheme outside :data:`SUPPORTED_SCHEMES`, or if a
            non-``file`` scheme is missing its authority.
    """
    trimmed = value.strip() if value is not None else ""
    if not trimmed:
        raise InvalidRequestError(
            "storage location must not be empty; expected a URI with one of the "
            f"supported schemes: {_supported_schemes_display()}",
        )

    parts = urlsplit(trimmed)
    scheme = parts.scheme.lower()
    if not scheme:
        raise InvalidRequestError(
            f"storage location '{trimmed}' is missing a URI scheme; "
            f"expected one of: {_supported_schemes_display()}",
        )
    if scheme not in SUPPORTED_SCHEMES:
        raise InvalidRequestError(
            f"unsupported storage URI scheme '{scheme}'; "
            f"expected one of: {_supported_schemes_display()}",
        )
    if scheme != "file" and not parts.netloc:
        raise InvalidRequestError(
            f"storage location '{trimmed}' is missing an authority "
            f"(bucket / container) for scheme '{scheme}'",
        )

    return StorageUri(scheme=scheme, raw=trimmed)


def derive_managed_location(
    storage_root: str | None,
    kind: str,
    resource_id: str,
) -> str | None:
    """Return the UC managed-location path under ``storage_root``.

    The UC OpenAPI spec describes ``storage_location`` on
    ``CatalogInfo`` / ``SchemaInfo`` as *"an automatically generated
    unique path under storage_root"*, with the example
    ``s3://bucket/ucroot/__unitystorage/catalogs/{catalog_id}``. This
    helper encodes that layout in one place so every service that needs
    it (catalog, schema) produces a byte-identical string.

    The derivation is keyed by the opaque ``resource_id``, not the
    user-facing name: that is the whole point of the spec design, and
    the reason ``update_catalog`` / ``update_schema`` must never
    recompute this field. A rename leaves the managed path intact, so
    any child resource whose physical layout depends on it stays valid.

    No scheme validation happens here — the caller is expected to have
    already run ``parse_storage_uri`` on the write path. This keeps the
    helper safe to use from read paths that must tolerate legacy
    free-form ``storage_root`` values.

    Args:
        storage_root: The parent ``storage_root`` URI, or ``None``.
        kind: Resource kind used as the URL path segment — one of
            ``"catalogs"`` or ``"schemas"``. Chosen to match the spec
            example verbatim.
        resource_id: Opaque id (UUID hex) of the resource being created.

    Returns:
        str | None: ``f"{storage_root}/__unitystorage/{kind}/{resource_id}"``
            with any trailing slash on ``storage_root`` stripped, or
            ``None`` when ``storage_root`` is ``None``.
    """
    if storage_root is None:
        return None
    return f"{storage_root.rstrip('/')}/__unitystorage/{kind}/{resource_id}"


def _supported_schemes_display() -> str:
    """Return the supported-scheme set as a stable, sorted display string.

    Used only in error messages. ``frozenset`` iteration order is
    insertion-dependent in CPython but not part of the language
    contract, so we sort explicitly to keep error messages
    byte-stable — which matters for the regression tests that assert on
    substrings.

    Returns:
        str: Comma-separated list of supported schemes, sorted
            alphabetically and wrapped in backticks.
    """
    return ", ".join(f"`{s}`" for s in sorted(SUPPORTED_SCHEMES))
