from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateStagingTableRequest")


@_attrs_define
class CreateStagingTableRequest:
    """Request body for ``POST .../staging-tables``.

    Single field: the leaf name of the staging-table allocation.
    The parent catalog and schema come from the path. soyuz reuses
    the existing
    :func:`soyuz_catalog.services.staging_table_service.create_staging_table`
    under the hood and augments the response with the Delta-specific
    protocol and credential fields.

        Attributes:
            name (str):
    """

    name: str

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        create_staging_table_request = cls(
            name=name,
        )

        return create_staging_table_request
