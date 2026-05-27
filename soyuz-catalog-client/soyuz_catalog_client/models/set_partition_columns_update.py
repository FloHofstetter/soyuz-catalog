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

T = TypeVar("T", bound="SetPartitionColumnsUpdate")


@_attrs_define
class SetPartitionColumnsUpdate:
    """Replace the set of partition-column names.

    soyuz stores this information on the child
    :class:`soyuz_catalog.models.Column` rows via ``partition_index``
    rather than as a separate array; the service layer rebuilds
    ``partition_index`` for every column on each update so the two
    representations stay in sync.

        Attributes:
            action (Literal['set-partition-columns']):
            partition_columns (list[str]):
    """

    action: Literal["set-partition-columns"]
    partition_columns: list[str]

    def to_dict(self) -> dict[str, Any]:
        action = self.action

        partition_columns = self.partition_columns

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "action": action,
                "partition-columns": partition_columns,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        action = cast(Literal["set-partition-columns"], d.pop("action"))
        if action != "set-partition-columns":
            raise ValueError(
                f"action must match const 'set-partition-columns', got '{action}'"
            )

        partition_columns = cast(list[str], d.pop("partition-columns"))

        set_partition_columns_update = cls(
            action=action,
            partition_columns=partition_columns,
        )

        return set_partition_columns_update
