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
    from ..models.delta_column import DeltaColumn


T = TypeVar("T", bound="SetSchemaUpdate")


@_attrs_define
class SetSchemaUpdate:
    """Replace the table's column list in full.

    The ``columns`` array is applied as a full replacement; the
    existing :class:`soyuz_catalog.models.Column` rows are dropped
    and re-inserted by the service layer in the order given. This
    matches Delta's own schema-evolution wire shape (the client
    always sends the full post-state) and avoids soyuz having to
    model per-column diffs.

        Attributes:
            action (Literal['set-columns']):
            columns (list[DeltaColumn]):
    """

    action: Literal["set-columns"]
    columns: list[DeltaColumn]

    def to_dict(self) -> dict[str, Any]:
        from ..models.delta_column import DeltaColumn

        action = self.action

        columns = []
        for columns_item_data in self.columns:
            columns_item = columns_item_data.to_dict()
            columns.append(columns_item)

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "action": action,
                "columns": columns,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.delta_column import DeltaColumn

        d = dict(src_dict)
        action = cast(Literal["set-columns"], d.pop("action"))
        if action != "set-columns":
            raise ValueError(f"action must match const 'set-columns', got '{action}'")

        columns = []
        _columns = d.pop("columns")
        for columns_item_data in _columns:
            columns_item = DeltaColumn.from_dict(columns_item_data)

            columns.append(columns_item)

        set_schema_update = cls(
            action=action,
            columns=columns,
        )

        return set_schema_update
