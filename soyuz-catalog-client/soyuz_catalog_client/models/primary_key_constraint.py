from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="PrimaryKeyConstraint")


@_attrs_define
class PrimaryKeyConstraint:
    """``PRIMARY KEY`` constraint payload (ADR-0012).

    A metadata-only declaration that the listed columns form the
    primary key of the table. soyuz does not enforce the declaration
    at write time — there is no query engine to check it against —
    but round-trips it verbatim so Spark / dbt / downstream catalog
    UIs that read declared constraints see the same metadata they
    would against Databricks.

    At most one :class:`PrimaryKeyConstraint` is allowed per table;
    adding a second one raises 409 ``ALREADY_EXISTS``. The spec does
    not pin this uniqueness rule but every SQL engine soyuz interoperates
    with does, so rejecting at write time is less confusing than a
    silent last-write-wins semantic.

        Attributes:
            child_columns (list[str]):
    """

    child_columns: list[str]

    def to_dict(self) -> dict[str, Any]:
        child_columns = self.child_columns

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "child_columns": child_columns,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        child_columns = cast(list[str], d.pop("child_columns"))

        primary_key_constraint = cls(
            child_columns=child_columns,
        )

        return primary_key_constraint
