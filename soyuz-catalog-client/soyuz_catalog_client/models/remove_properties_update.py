from __future__ import annotations

from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    BinaryIO,
    Generator,
    Literal,
    TextIO,
    TypeVar,
    cast,
)

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="RemovePropertiesUpdate")


@_attrs_define
class RemovePropertiesUpdate:
    """Remove the listed property keys from the table.

    Silently ignores keys that are not present, matching Delta's own
    ``unsetTableProperties`` semantics and every other idempotent
    delete path in soyuz.

        Attributes:
            action (Literal['remove-properties']):
            removals (list[str]):
    """

    action: Literal["remove-properties"]
    removals: list[str]

    def to_dict(self) -> dict[str, Any]:
        action = self.action

        removals = self.removals

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "action": action,
                "removals": removals,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        action = cast(Literal["remove-properties"], d.pop("action"))
        if action != "remove-properties":
            raise ValueError(
                f"action must match const 'remove-properties', got '{action}'"
            )

        removals = cast(list[str], d.pop("removals"))

        remove_properties_update = cls(
            action=action,
            removals=removals,
        )

        return remove_properties_update
