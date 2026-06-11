from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AddShareObject")


@_attrs_define
class AddShareObject:
    """Request body for ``POST /shares/{name}/objects``.

    ``table_full_name`` must resolve to an existing table at add time
    (404 otherwise). ``shared_as`` optionally re-homes the table
    inside the share's namespace as a two-part ``schema.table`` alias;
    when absent the protocol placement derives from the table's own
    schema and table name segments.

        Attributes:
            table_full_name (str):
            shared_as (None | str | Unset):
    """

    table_full_name: str
    shared_as: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        table_full_name = self.table_full_name

        shared_as: None | str | Unset
        if isinstance(self.shared_as, Unset):
            shared_as = UNSET
        else:
            shared_as = self.shared_as

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "table_full_name": table_full_name,
            }
        )
        if shared_as is not UNSET:
            field_dict["shared_as"] = shared_as

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        table_full_name = d.pop("table_full_name")

        def _parse_shared_as(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        shared_as = _parse_shared_as(d.pop("shared_as", UNSET))

        add_share_object = cls(
            table_full_name=table_full_name,
            shared_as=shared_as,
        )

        return add_share_object
