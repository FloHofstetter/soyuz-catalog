from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.permissions_change_add_item import PermissionsChangeAddItem
from ..models.permissions_change_remove_item import PermissionsChangeRemoveItem
from ..types import UNSET, Unset

T = TypeVar("T", bound="PermissionsChange")


@_attrs_define
class PermissionsChange:
    """One element of an ``UpdatePermissions`` request body.

    ``add`` and ``remove`` are spec-required arrays: clients that want
    to only add must still send an empty ``remove`` list (and vice
    versa). Overlapping entries within a single change are handled by
    the service layer: removes are applied first, then adds, so if
    the same privilege appears in both lists the net effect is *add
    wins*. That tiebreaker is soyuz-specific and documented in
    ``DIVERGENCES.md``; the upstream spec does not pin a winner.

        Attributes:
            add (list[PermissionsChangeAddItem]):
            principal (str):
            remove (list[PermissionsChangeRemoveItem]):
    """

    add: list[PermissionsChangeAddItem]
    principal: str
    remove: list[PermissionsChangeRemoveItem]

    def to_dict(self) -> dict[str, Any]:
        add = []
        for add_item_data in self.add:
            add_item = add_item_data.value
            add.append(add_item)

        principal = self.principal

        remove = []
        for remove_item_data in self.remove:
            remove_item = remove_item_data.value
            remove.append(remove_item)

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "add": add,
                "principal": principal,
                "remove": remove,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        add = []
        _add = d.pop("add")
        for add_item_data in _add:
            add_item = PermissionsChangeAddItem(add_item_data)

            add.append(add_item)

        principal = d.pop("principal")

        remove = []
        _remove = d.pop("remove")
        for remove_item_data in _remove:
            remove_item = PermissionsChangeRemoveItem(remove_item_data)

            remove.append(remove_item)

        permissions_change = cls(
            add=add,
            principal=principal,
            remove=remove,
        )

        return permissions_change
