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

T = TypeVar("T", bound="DropConstraintUpdate")


@_attrs_define
class DropConstraintUpdate:
    """``drop-constraint`` variant of :data:`TableUpdate` (ADR-0012).

    Drops the constraint with the given ``name`` from the target
    table. With ``if_exists=False`` (the default) a missing
    constraint raises 404 ``NOT_FOUND``; with ``if_exists=True``
    the call is a no-op. Matches the Delta spec's tri-state
    ``NOT_FOUND | found | noop`` pattern for idempotent DDL and
    aligns with ``RemovePropertiesUpdate``'s silent-ignore posture
    on missing keys.

        Attributes:
            action (Literal['drop-constraint']):
            name (str):
            if_exists (bool | Unset):  Default: False.
    """

    action: Literal["drop-constraint"]
    name: str
    if_exists: bool | Unset = False

    def to_dict(self) -> dict[str, Any]:
        action = self.action

        name = self.name

        if_exists = self.if_exists

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "action": action,
                "name": name,
            }
        )
        if if_exists is not UNSET:
            field_dict["if-exists"] = if_exists

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        action = cast(Literal["drop-constraint"], d.pop("action"))
        if action != "drop-constraint":
            raise ValueError(
                f"action must match const 'drop-constraint', got '{action}'"
            )

        name = d.pop("name")

        if_exists = d.pop("if-exists", UNSET)

        drop_constraint_update = cls(
            action=action,
            name=name,
            if_exists=if_exists,
        )

        return drop_constraint_update
