from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="RenameTableRequest")


@_attrs_define
class RenameTableRequest:
    """Request body for ``POST .../tables/{table}/rename``.

    The spec is minimal — a single ``new-name`` field. soyuz surfaces
    an empty string as 400 ``INVALID_ARGUMENT`` at the service layer
    rather than relying on pydantic's ``min_length`` so the error
    message matches the rest of the service's 400 envelope shape.

        Attributes:
            new_name (str):
    """

    new_name: str

    def to_dict(self) -> dict[str, Any]:
        new_name = self.new_name

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "new-name": new_name,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        new_name = d.pop("new-name")

        rename_table_request = cls(
            new_name=new_name,
        )

        return rename_table_request
