from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ShareObjectInfo")


@_attrs_define
class ShareObjectInfo:
    """One table placed inside a share, as returned on ``ShareInfo``.

    ``added_at`` is the wire name for the row's creation timestamp —
    a share object is immutable after creation (remove + re-add is
    the only edit), so there is no ``updated_at``.

        Attributes:
            table_full_name (str):
            added_at (int | None | Unset):
            shared_as (None | str | Unset):
    """

    table_full_name: str
    added_at: int | None | Unset = UNSET
    shared_as: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        table_full_name = self.table_full_name

        added_at: int | None | Unset
        if isinstance(self.added_at, Unset):
            added_at = UNSET
        else:
            added_at = self.added_at

        shared_as: None | str | Unset
        if isinstance(self.shared_as, Unset):
            shared_as = UNSET
        else:
            shared_as = self.shared_as

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "table_full_name": table_full_name,
            }
        )
        if added_at is not UNSET:
            field_dict["added_at"] = added_at
        if shared_as is not UNSET:
            field_dict["shared_as"] = shared_as

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        table_full_name = d.pop("table_full_name")

        def _parse_added_at(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        added_at = _parse_added_at(d.pop("added_at", UNSET))

        def _parse_shared_as(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        shared_as = _parse_shared_as(d.pop("shared_as", UNSET))

        share_object_info = cls(
            table_full_name=table_full_name,
            added_at=added_at,
            shared_as=shared_as,
        )

        share_object_info.additional_properties = d
        return share_object_info

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
