from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.permissions_change import PermissionsChange


T = TypeVar("T", bound="UpdatePermissions")


@_attrs_define
class UpdatePermissions:
    """Request body for ``PATCH /permissions/{securable_type}/{full_name}``.

    Unlike every other PATCH in this project, this shape is **not**
    replace-style: the client submits a list of additive/subtractive
    changes rather than a full desired state. This matches the
    upstream ``UpdatePermissions`` schema exactly — see
    ``DIVERGENCES.md`` for why the asymmetry with our catalog /
    schema / table PATCH routes is intentional.

        Attributes:
            changes (list[PermissionsChange]):
    """

    changes: list[PermissionsChange]

    def to_dict(self) -> dict[str, Any]:
        from ..models.permissions_change import PermissionsChange

        changes = []
        for changes_item_data in self.changes:
            changes_item = changes_item_data.to_dict()
            changes.append(changes_item)

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "changes": changes,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.permissions_change import PermissionsChange

        d = dict(src_dict)
        changes = []
        _changes = d.pop("changes")
        for changes_item_data in _changes:
            changes_item = PermissionsChange.from_dict(changes_item_data)

            changes.append(changes_item)

        update_permissions = cls(
            changes=changes,
        )

        return update_permissions
