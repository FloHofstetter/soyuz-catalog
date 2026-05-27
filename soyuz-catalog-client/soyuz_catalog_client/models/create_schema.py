from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.create_schema_properties_type_0 import CreateSchemaPropertiesType0


T = TypeVar("T", bound="CreateSchema")


@_attrs_define
class CreateSchema:
    """Request body for ``POST /schemas``.

    ``name`` and ``catalog_name`` are both required — a schema cannot exist
    without knowing which catalog it lives under, and the spec addresses
    schemas by relative name. ``extra="forbid"`` rejects unknown fields, same
    policy as :class:`CreateCatalog`.

        Attributes:
            catalog_name (str):
            name (str):
            comment (None | str | Unset):
            properties (CreateSchemaPropertiesType0 | None | Unset):
            storage_root (None | str | Unset):
    """

    catalog_name: str
    name: str
    comment: None | str | Unset = UNSET
    properties: CreateSchemaPropertiesType0 | None | Unset = UNSET
    storage_root: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.create_schema_properties_type_0 import CreateSchemaPropertiesType0

        catalog_name = self.catalog_name

        name = self.name

        comment: None | str | Unset
        if isinstance(self.comment, Unset):
            comment = UNSET
        else:
            comment = self.comment

        properties: dict[str, Any] | None | Unset
        if isinstance(self.properties, Unset):
            properties = UNSET
        elif isinstance(self.properties, CreateSchemaPropertiesType0):
            properties = self.properties.to_dict()
        else:
            properties = self.properties

        storage_root: None | str | Unset
        if isinstance(self.storage_root, Unset):
            storage_root = UNSET
        else:
            storage_root = self.storage_root

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "catalog_name": catalog_name,
                "name": name,
            }
        )
        if comment is not UNSET:
            field_dict["comment"] = comment
        if properties is not UNSET:
            field_dict["properties"] = properties
        if storage_root is not UNSET:
            field_dict["storage_root"] = storage_root

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.create_schema_properties_type_0 import CreateSchemaPropertiesType0

        d = dict(src_dict)
        catalog_name = d.pop("catalog_name")

        name = d.pop("name")

        def _parse_comment(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        comment = _parse_comment(d.pop("comment", UNSET))

        def _parse_properties(
            data: object,
        ) -> CreateSchemaPropertiesType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                properties_type_0 = CreateSchemaPropertiesType0.from_dict(data)

                return properties_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(CreateSchemaPropertiesType0 | None | Unset, data)

        properties = _parse_properties(d.pop("properties", UNSET))

        def _parse_storage_root(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        storage_root = _parse_storage_root(d.pop("storage_root", UNSET))

        create_schema = cls(
            catalog_name=catalog_name,
            name=name,
            comment=comment,
            properties=properties,
            storage_root=storage_root,
        )

        return create_schema
