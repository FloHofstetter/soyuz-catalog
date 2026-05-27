from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.privilege_assignment import PrivilegeAssignment


T = TypeVar("T", bound="PermissionsList")


@_attrs_define
class PermissionsList:
    """Response shape for ``GET`` / ``PATCH /permissions/...``.

    Both endpoints return the same shape: ``GET`` returns the current
    state (optionally filtered by ``?principal=``), ``PATCH`` returns
    the state after the submitted changes have been applied. The
    optional ``?principal=`` filter applies only to ``GET``; ``PATCH``
    always returns the full current state to avoid the client having
    to re-fetch after every update.

        Attributes:
            privilege_assignments (list[PrivilegeAssignment]):
    """

    privilege_assignments: list[PrivilegeAssignment]

    def to_dict(self) -> dict[str, Any]:
        from ..models.privilege_assignment import PrivilegeAssignment

        privilege_assignments = []
        for privilege_assignments_item_data in self.privilege_assignments:
            privilege_assignments_item = privilege_assignments_item_data.to_dict()
            privilege_assignments.append(privilege_assignments_item)

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "privilege_assignments": privilege_assignments,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.privilege_assignment import PrivilegeAssignment

        d = dict(src_dict)
        privilege_assignments = []
        _privilege_assignments = d.pop("privilege_assignments")
        for privilege_assignments_item_data in _privilege_assignments:
            privilege_assignments_item = PrivilegeAssignment.from_dict(
                privilege_assignments_item_data
            )

            privilege_assignments.append(privilege_assignments_item)

        permissions_list = cls(
            privilege_assignments=privilege_assignments,
        )

        return permissions_list
