from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="TableIdentifierWithDataSourceFormat")


@_attrs_define
class TableIdentifierWithDataSourceFormat:
    """One entry in a ``listTables`` response.

    Only the leaf name and the data-source-format are exposed — the
    parent catalog and schema are implicit from the request path, so
    echoing them would be redundant with the URL.

        Attributes:
            data_source_format (str):
            name (str):
    """

    data_source_format: str
    name: str

    def to_dict(self) -> dict[str, Any]:
        data_source_format = self.data_source_format

        name = self.name

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "data-source-format": data_source_format,
                "name": name,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        data_source_format = d.pop("data-source-format")

        name = d.pop("name")

        table_identifier_with_data_source_format = cls(
            data_source_format=data_source_format,
            name=name,
        )

        return table_identifier_with_data_source_format
