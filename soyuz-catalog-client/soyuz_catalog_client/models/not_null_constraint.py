from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="NotNullConstraint")


@_attrs_define
class NotNullConstraint:
    """Named ``NOT NULL`` constraint payload (ADR-0012).

    Named NOT NULL constraints are a *second* concept alongside the
    unnamed :class:`soyuz_catalog.models.Column.nullable` flag, not
    a replacement: the column flag stays authoritative for the
    column's nullability, and adding / dropping this named
    constraint deliberately does *not* flip it. Databricks models
    them the same way — the two can disagree in practice, and
    soyuz does not second-guess that — and flipping the column
    flag as a side effect of adding a constraint would reintroduce
    the silent-side-effects class that the "no table PATCH"
    invariant (Tables resource has no update endpoint in the UC
    spec) was designed to prevent.

        Attributes:
            child_column (str):
    """

    child_column: str

    def to_dict(self) -> dict[str, Any]:
        child_column = self.child_column

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "child_column": child_column,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        child_column = d.pop("child_column")

        not_null_constraint = cls(
            child_column=child_column,
        )

        return not_null_constraint
