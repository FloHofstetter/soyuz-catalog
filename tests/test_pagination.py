"""Unit tests for the shared keyset-pagination helpers."""

from __future__ import annotations

import base64
import json

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from soyuz_catalog.exceptions import InvalidRequestError
from soyuz_catalog.models import Catalog
from soyuz_catalog.pagination import (
    DEFAULT_MAX_RESULTS,
    MAX_MAX_RESULTS,
    apply_keyset,
    build_next_token,
    decode_page_token,
    encode_page_token,
)


def test_encode_decode_round_trip() -> None:
    token = encode_page_token(1_700_000_000_000, "abc123")
    assert decode_page_token(token) == (1_700_000_000_000, "abc123")


def test_encode_produces_url_safe_unpadded_token() -> None:
    token = encode_page_token(1, "x")
    assert "=" not in token
    assert "+" not in token
    assert "/" not in token


def test_decode_rejects_non_base64() -> None:
    with pytest.raises(InvalidRequestError, match="not a valid token"):
        decode_page_token("not!!!base64!!!")


def test_decode_rejects_non_json_payload() -> None:
    bogus = base64.urlsafe_b64encode(b"not-json").rstrip(b"=").decode("ascii")
    with pytest.raises(InvalidRequestError, match="not a valid token"):
        decode_page_token(bogus)


def test_decode_rejects_wrong_shape() -> None:
    bogus = (
        base64.urlsafe_b64encode(
            json.dumps({"c": 1, "i": "x", "extra": 2}).encode("utf-8"),
        )
        .rstrip(b"=")
        .decode("ascii")
    )
    with pytest.raises(InvalidRequestError, match="unexpected shape"):
        decode_page_token(bogus)


def test_decode_rejects_missing_key() -> None:
    bogus = (
        base64.urlsafe_b64encode(
            json.dumps({"c": 1}).encode("utf-8"),
        )
        .rstrip(b"=")
        .decode("ascii")
    )
    with pytest.raises(InvalidRequestError, match="unexpected shape"):
        decode_page_token(bogus)


def test_decode_rejects_wrong_value_types() -> None:
    bad_c = (
        base64.urlsafe_b64encode(
            json.dumps({"c": "nope", "i": "x"}).encode("utf-8"),
        )
        .rstrip(b"=")
        .decode("ascii")
    )
    with pytest.raises(InvalidRequestError, match="'c' field must be int"):
        decode_page_token(bad_c)

    bad_i = (
        base64.urlsafe_b64encode(
            json.dumps({"c": 1, "i": 42}).encode("utf-8"),
        )
        .rstrip(b"=")
        .decode("ascii")
    )
    with pytest.raises(InvalidRequestError, match="'i' field must be str"):
        decode_page_token(bad_i)


def test_decode_rejects_bool_as_int() -> None:
    # Python's bool is a subclass of int — guard against it explicitly so a
    # tampered token can't smuggle True/False past the int check.
    bogus = (
        base64.urlsafe_b64encode(
            json.dumps({"c": True, "i": "x"}).encode("utf-8"),
        )
        .rstrip(b"=")
        .decode("ascii")
    )
    with pytest.raises(InvalidRequestError, match="'c' field must be int"):
        decode_page_token(bogus)


def _make_catalogs(session: Session, count: int) -> list[Catalog]:
    rows: list[Catalog] = []
    for n in range(count):
        c = Catalog(
            name=f"c{n}",
            properties={},
            created_at=1_000 + n,
            updated_at=1_000 + n,
        )
        session.add(c)
        rows.append(c)
    session.commit()
    for c in rows:
        session.refresh(c)
    return rows


def test_apply_keyset_defaults_and_orders(session_factory: sessionmaker[Session]) -> None:
    with session_factory() as session:
        _make_catalogs(session, 3)
        stmt, limit = apply_keyset(select(Catalog), Catalog, None, None)
        assert limit == DEFAULT_MAX_RESULTS
        rows = list(session.scalars(stmt))
        assert [r.name for r in rows] == ["c0", "c1", "c2"]


def test_apply_keyset_rejects_out_of_range_max_results() -> None:
    with pytest.raises(InvalidRequestError, match="max_results must be between"):
        apply_keyset(select(Catalog), Catalog, None, MAX_MAX_RESULTS + 1)
    with pytest.raises(InvalidRequestError, match="max_results must be between"):
        apply_keyset(select(Catalog), Catalog, None, -5)


def test_apply_keyset_accepts_zero_as_default(
    session_factory: sessionmaker[Session],
) -> None:
    """``max_results=0`` routes through to the server default.

    The upstream JVM ``UCSingleCatalog`` connector sends
    ``max_results=0`` when it wants the server-side default —
    rejecting 0 with 422 would break every ``listTables`` call from
    it, so we pin the "use the default" semantic.
    """
    with session_factory() as session:
        _make_catalogs(session, 3)
        stmt, limit = apply_keyset(select(Catalog), Catalog, None, 0)
        from soyuz_catalog.pagination import DEFAULT_MAX_RESULTS

        assert limit == DEFAULT_MAX_RESULTS
        rows = list(session.scalars(stmt))
        assert [r.name for r in rows] == ["c0", "c1", "c2"]


def test_paginate_walks_multi_page(session_factory: sessionmaker[Session]) -> None:
    with session_factory() as session:
        _make_catalogs(session, 5)

        stmt, limit = apply_keyset(select(Catalog), Catalog, None, 2)
        page1, token1 = build_next_token(list(session.scalars(stmt)), limit)
        assert [r.name for r in page1] == ["c0", "c1"]
        assert token1 is not None

        stmt, limit = apply_keyset(select(Catalog), Catalog, token1, 2)
        page2, token2 = build_next_token(list(session.scalars(stmt)), limit)
        assert [r.name for r in page2] == ["c2", "c3"]
        assert token2 is not None

        stmt, limit = apply_keyset(select(Catalog), Catalog, token2, 2)
        page3, token3 = build_next_token(list(session.scalars(stmt)), limit)
        assert [r.name for r in page3] == ["c4"]
        assert token3 is None


def test_paginate_boundary_exactly_one_page(session_factory: sessionmaker[Session]) -> None:
    """When the last page has exactly ``max_results`` rows, no phantom page."""
    with session_factory() as session:
        _make_catalogs(session, 2)
        stmt, limit = apply_keyset(select(Catalog), Catalog, None, 2)
        page1, token1 = build_next_token(list(session.scalars(stmt)), limit)
        assert [r.name for r in page1] == ["c0", "c1"]
        assert token1 is None


def test_paginate_empty_result(session_factory: sessionmaker[Session]) -> None:
    with session_factory() as session:
        stmt, limit = apply_keyset(select(Catalog), Catalog, None, 10)
        page, token = build_next_token(list(session.scalars(stmt)), limit)
        assert page == []
        assert token is None


def test_id_tiebreaker_on_duplicate_created_at(
    session_factory: sessionmaker[Session],
) -> None:
    """Rows sharing a ``created_at`` ms still walk deterministically."""
    with session_factory() as session:
        # Three rows with the same created_at; the (created_at, id) tuple
        # must still form a stable total order and the keyset walk must
        # not skip or repeat any row.
        for name in ("a", "b", "c"):
            session.add(Catalog(name=name, properties={}, created_at=42, updated_at=42))
        session.commit()

        seen: list[str] = []
        token: str | None = None
        while True:
            stmt, limit = apply_keyset(select(Catalog), Catalog, token, 1)
            rows = list(session.scalars(stmt))
            page, token = build_next_token(rows, limit)
            seen.extend(r.name for r in page)
            if token is None:
                break
        assert sorted(seen) == ["a", "b", "c"]
        assert len(seen) == 3
