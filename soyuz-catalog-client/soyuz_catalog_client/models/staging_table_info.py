from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="StagingTableInfo")


@_attrs_define
class StagingTableInfo:
    """Response shape for ``POST /staging-tables``.

    Returned directly from the create endpoint — there is no GET /
    LIST / DELETE route for staging tables in the spec, so this is
    the only shape the resource ever takes on the wire.
    ``staging_location`` is the server-derived URL the client should
    write data to before promoting the allocation to a real managed
    table.

        Attributes:
            catalog_name (None | str | Unset):
            id (None | str | Unset):
            name (None | str | Unset):
            schema_name (None | str | Unset):
            staging_location (None | str | Unset):
    """

    catalog_name: None | str | Unset = UNSET
    id: None | str | Unset = UNSET
    name: None | str | Unset = UNSET
    schema_name: None | str | Unset = UNSET
    staging_location: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        catalog_name: None | str | Unset
        if isinstance(self.catalog_name, Unset):
            catalog_name = UNSET
        else:
            catalog_name = self.catalog_name

        id: None | str | Unset
        if isinstance(self.id, Unset):
            id = UNSET
        else:
            id = self.id

        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        schema_name: None | str | Unset
        if isinstance(self.schema_name, Unset):
            schema_name = UNSET
        else:
            schema_name = self.schema_name

        staging_location: None | str | Unset
        if isinstance(self.staging_location, Unset):
            staging_location = UNSET
        else:
            staging_location = self.staging_location

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if catalog_name is not UNSET:
            field_dict["catalog_name"] = catalog_name
        if id is not UNSET:
            field_dict["id"] = id
        if name is not UNSET:
            field_dict["name"] = name
        if schema_name is not UNSET:
            field_dict["schema_name"] = schema_name
        if staging_location is not UNSET:
            field_dict["staging_location"] = staging_location

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_catalog_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        catalog_name = _parse_catalog_name(d.pop("catalog_name", UNSET))

        def _parse_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        id = _parse_id(d.pop("id", UNSET))

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_schema_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        schema_name = _parse_schema_name(d.pop("schema_name", UNSET))

        def _parse_staging_location(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        staging_location = _parse_staging_location(d.pop("staging_location", UNSET))

        staging_table_info = cls(
            catalog_name=catalog_name,
            id=id,
            name=name,
            schema_name=schema_name,
            staging_location=staging_location,
        )

        staging_table_info.additional_properties = d
        return staging_table_info

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
