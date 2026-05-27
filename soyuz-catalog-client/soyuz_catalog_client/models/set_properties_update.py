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

if TYPE_CHECKING:
    from ..models.updates import Updates


T = TypeVar("T", bound="SetPropertiesUpdate")


@_attrs_define
class SetPropertiesUpdate:
    """Merge the given ``updates`` dict into the table's ``properties``.

    Semantics match Delta's own ``setTableProperties``: keys in
    ``updates`` overwrite existing entries; keys absent from
    ``updates`` are left untouched (it is **not** a replace of the
    full properties map — use the combination
    ``remove-properties`` + ``set-properties`` for that).

        Attributes:
            action (Literal['set-properties']):
            updates (Updates):
    """

    action: Literal["set-properties"]
    updates: Updates

    def to_dict(self) -> dict[str, Any]:
        from ..models.updates import Updates

        action = self.action

        updates = self.updates.to_dict()

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "action": action,
                "updates": updates,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.updates import Updates

        d = dict(src_dict)
        action = cast(Literal["set-properties"], d.pop("action"))
        if action != "set-properties":
            raise ValueError(
                f"action must match const 'set-properties', got '{action}'"
            )

        updates = Updates.from_dict(d.pop("updates"))

        set_properties_update = cls(
            action=action,
            updates=updates,
        )

        return set_properties_update
