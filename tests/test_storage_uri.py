"""Unit tests for :mod:`soyuz_catalog.storage.uri`.

These tests exercise the parser in isolation — no FastAPI, no database.
Regression coverage for the service wiring (Tables / Volumes / Schemas
rejecting unsupported schemes at the HTTP layer) lives in
``test_tables.py``, ``test_volumes.py``, and ``test_schemas.py``.
"""

from __future__ import annotations

import pytest

from soyuz_catalog.exceptions import InvalidRequestError
from soyuz_catalog.storage import SUPPORTED_SCHEMES, parse_storage_uri


def test_parse_file_uri_absolute() -> None:
    parsed = parse_storage_uri("file:///tmp/soyuz/t")
    assert parsed.scheme == "file"
    assert parsed.raw == "file:///tmp/soyuz/t"


def test_parse_s3_uri() -> None:
    parsed = parse_storage_uri("s3://bucket/key")
    assert parsed.scheme == "s3"


def test_parse_s3a_uri() -> None:
    parsed = parse_storage_uri("s3a://bucket/key")
    assert parsed.scheme == "s3a"


def test_parse_abfss_uri() -> None:
    parsed = parse_storage_uri(
        "abfss://container@account.dfs.core.windows.net/path",
    )
    assert parsed.scheme == "abfss"


def test_parse_gs_uri() -> None:
    parsed = parse_storage_uri("gs://bucket/path")
    assert parsed.scheme == "gs"


def test_parse_is_case_insensitive_on_scheme() -> None:
    parsed = parse_storage_uri("S3://bucket/key")
    assert parsed.scheme == "s3"


def test_parse_trims_surrounding_whitespace() -> None:
    parsed = parse_storage_uri("  s3://bucket/key  ")
    assert parsed.raw == "s3://bucket/key"


def test_parse_rejects_empty_string() -> None:
    with pytest.raises(InvalidRequestError, match="must not be empty"):
        parse_storage_uri("")


def test_parse_rejects_whitespace_only_string() -> None:
    with pytest.raises(InvalidRequestError, match="must not be empty"):
        parse_storage_uri("   ")


def test_parse_rejects_missing_scheme() -> None:
    with pytest.raises(InvalidRequestError, match="missing a URI scheme"):
        parse_storage_uri("/tmp/foo")


def test_parse_rejects_unknown_scheme_hdfs() -> None:
    with pytest.raises(InvalidRequestError, match="unsupported storage URI scheme"):
        parse_storage_uri("hdfs://namenode/path")


def test_parse_rejects_unknown_scheme_wasbs() -> None:
    with pytest.raises(InvalidRequestError, match="unsupported storage URI scheme"):
        parse_storage_uri("wasbs://container@account.blob.core.windows.net/path")


def test_parse_rejects_ftp_scheme() -> None:
    with pytest.raises(InvalidRequestError, match="unsupported storage URI scheme"):
        parse_storage_uri("ftp://host/path")


def test_parse_rejects_non_file_scheme_without_authority() -> None:
    with pytest.raises(InvalidRequestError, match="missing an authority"):
        parse_storage_uri("s3:///just/a/path")


def test_supported_schemes_constant_matches_expected_set() -> None:
    assert SUPPORTED_SCHEMES == frozenset({"file", "s3", "s3a", "abfss", "gs"})
