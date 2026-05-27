from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CheckConstraint")


@_attrs_define
class CheckConstraint:
    """``CHECK`` constraint payload (ADR-0012).

    A metadata-only declaration that ``sql_text`` should hold for
    every row of the table. soyuz does **not** parse the predicate
    — the string is stored verbatim and round-tripped unchanged —
    because the dialect of the predicate depends on the query
    engine that will eventually evaluate it (Spark SQL, Trino SQL,
    DuckDB SQL, …) and pinning a single parser here would reject
    perfectly valid predicates for other engines.

    ``child_columns`` is informational: clients that produce the
    constraint from an AST pre-computed the referenced column set
    and include it so readers do not have to re-parse the predicate.
    The list is not validated against the table's columns.

        Attributes:
            sql_text (str):
            child_columns (list[str] | Unset):
    """

    sql_text: str
    child_columns: list[str] | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        sql_text = self.sql_text

        child_columns: list[str] | Unset = UNSET
        if not isinstance(self.child_columns, Unset):
            child_columns = self.child_columns

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "sql_text": sql_text,
            }
        )
        if child_columns is not UNSET:
            field_dict["child_columns"] = child_columns

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        sql_text = d.pop("sql_text")

        child_columns = cast(list[str], d.pop("child_columns", UNSET))

        check_constraint = cls(
            sql_text=sql_text,
            child_columns=child_columns,
        )

        return check_constraint
