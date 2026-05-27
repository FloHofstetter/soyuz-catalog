from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="TagEntry")


@_attrs_define
class TagEntry:
    """A single ``(key, value)`` tag on a securable.

    ``value`` is optional because Databricks supports valueless tags (flag
    semantics, e.g. ``pii``). Timestamps are exposed as epoch milliseconds to
    match every other resource response in the project.

        Attributes:
            created_at (int):
            key (str):
            updated_at (int):
            value (None | str | Unset):
    """

    created_at: int
    key: str
    updated_at: int
    value: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        created_at = self.created_at

        key = self.key

        updated_at = self.updated_at

        value: None | str | Unset
        if isinstance(self.value, Unset):
            value = UNSET
        else:
            value = self.value

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "created_at": created_at,
                "key": key,
                "updated_at": updated_at,
            }
        )
        if value is not UNSET:
            field_dict["value"] = value

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        created_at = d.pop("created_at")

        key = d.pop("key")

        updated_at = d.pop("updated_at")

        def _parse_value(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        value = _parse_value(d.pop("value", UNSET))

        tag_entry = cls(
            created_at=created_at,
            key=key,
            updated_at=updated_at,
            value=value,
        )

        return tag_entry
