from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ForeignKeyConstraint")


@_attrs_define
class ForeignKeyConstraint:
    """``FOREIGN KEY`` constraint payload (ADR-0012).

    A metadata-only declaration that the ``child_columns`` on the
    owning table reference ``parent_columns`` on ``parent_table``.
    ``parent_table`` is a three-part dotted full_name on the wire
    and is resolved to an opaque ``parent_table_id`` at write time
    so a rename of *either* side leaves the declaration intact —
    the same rename-invariance trick permissions / tags / lineage
    use. On response the opaque id is reconstructed back into a
    live three-part name.

    soyuz does not enforce referential integrity — there is no
    query engine — but the presence of the declaration is enough
    for catalog UIs and query planners that do.

        Attributes:
            child_columns (list[str]):
            parent_columns (list[str]):
            parent_table (str):
    """

    child_columns: list[str]
    parent_columns: list[str]
    parent_table: str

    def to_dict(self) -> dict[str, Any]:
        child_columns = self.child_columns

        parent_columns = self.parent_columns

        parent_table = self.parent_table

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "child_columns": child_columns,
                "parent_columns": parent_columns,
                "parent_table": parent_table,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        child_columns = cast(list[str], d.pop("child_columns"))

        parent_columns = cast(list[str], d.pop("parent_columns"))

        parent_table = d.pop("parent_table")

        foreign_key_constraint = cls(
            child_columns=child_columns,
            parent_columns=parent_columns,
            parent_table=parent_table,
        )

        return foreign_key_constraint
