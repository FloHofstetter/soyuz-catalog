from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.privilege_assignment_privileges_item import (
    PrivilegeAssignmentPrivilegesItem,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="PrivilegeAssignment")


@_attrs_define
class PrivilegeAssignment:
    """A single principal's privileges on one securable.

    The wire shape pivots the flat ``permissions`` rows onto the
    per-principal view the UC spec defines: instead of ``N`` rows of
    ``(principal, privilege)``, the response groups by principal and
    carries the privilege list inline. The service layer does the
    grouping and stable sorting; the route just serialises the
    result.

        Attributes:
            principal (str):
            privileges (list[PrivilegeAssignmentPrivilegesItem]):
    """

    principal: str
    privileges: list[PrivilegeAssignmentPrivilegesItem]

    def to_dict(self) -> dict[str, Any]:
        principal = self.principal

        privileges = []
        for privileges_item_data in self.privileges:
            privileges_item = privileges_item_data.value
            privileges.append(privileges_item)

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "principal": principal,
                "privileges": privileges,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        principal = d.pop("principal")

        privileges = []
        _privileges = d.pop("privileges")
        for privileges_item_data in _privileges:
            privileges_item = PrivilegeAssignmentPrivilegesItem(privileges_item_data)

            privileges.append(privileges_item)

        privilege_assignment = cls(
            principal=principal,
            privileges=privileges,
        )

        return privilege_assignment
