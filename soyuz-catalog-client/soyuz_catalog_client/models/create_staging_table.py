from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateStagingTable")


@_attrs_define
class CreateStagingTable:
    """Request body for ``POST /staging-tables``.

    The UC spec marks every field as required: a staging table is
    addressed by ``(catalog_name, schema_name, name)`` and has no
    other client-supplied inputs. ``extra="forbid"`` rejects unknown
    fields — notably including ``storage_location`` and ``id``, which
    are server-derived on the response and must not be accepted on
    create.

        Attributes:
            catalog_name (str):
            name (str):
            schema_name (str):
    """

    catalog_name: str
    name: str
    schema_name: str

    def to_dict(self) -> dict[str, Any]:
        catalog_name = self.catalog_name

        name = self.name

        schema_name = self.schema_name

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "catalog_name": catalog_name,
                "name": name,
                "schema_name": schema_name,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        catalog_name = d.pop("catalog_name")

        name = d.pop("name")

        schema_name = d.pop("schema_name")

        create_staging_table = cls(
            catalog_name=catalog_name,
            name=name,
            schema_name=schema_name,
        )

        return create_staging_table
