from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.schema_info_properties_type_0 import SchemaInfoPropertiesType0


T = TypeVar("T", bound="SchemaInfo")


@_attrs_define
class SchemaInfo:
    """Response shape for a Unity Catalog schema.

    ``full_name`` is always populated by the API layer from the parent
    catalog's current name plus the schema's own name. It is never read from
    the database — see :class:`soyuz_catalog.models.Schema` for the rationale.
    All other fields mirror ``CatalogInfo``: optional on the wire, always
    populated for rows the server owns.

        Attributes:
            catalog_name (None | str | Unset):
            comment (None | str | Unset):
            created_at (int | None | Unset):
            created_by (None | str | Unset):
            full_name (None | str | Unset):
            name (None | str | Unset):
            owner (None | str | Unset):
            properties (None | SchemaInfoPropertiesType0 | Unset):
            schema_id (None | str | Unset):
            storage_location (None | str | Unset):
            storage_root (None | str | Unset):
            updated_at (int | None | Unset):
            updated_by (None | str | Unset):
    """

    catalog_name: None | str | Unset = UNSET
    comment: None | str | Unset = UNSET
    created_at: int | None | Unset = UNSET
    created_by: None | str | Unset = UNSET
    full_name: None | str | Unset = UNSET
    name: None | str | Unset = UNSET
    owner: None | str | Unset = UNSET
    properties: None | SchemaInfoPropertiesType0 | Unset = UNSET
    schema_id: None | str | Unset = UNSET
    storage_location: None | str | Unset = UNSET
    storage_root: None | str | Unset = UNSET
    updated_at: int | None | Unset = UNSET
    updated_by: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.schema_info_properties_type_0 import SchemaInfoPropertiesType0

        catalog_name: None | str | Unset
        if isinstance(self.catalog_name, Unset):
            catalog_name = UNSET
        else:
            catalog_name = self.catalog_name

        comment: None | str | Unset
        if isinstance(self.comment, Unset):
            comment = UNSET
        else:
            comment = self.comment

        created_at: int | None | Unset
        if isinstance(self.created_at, Unset):
            created_at = UNSET
        else:
            created_at = self.created_at

        created_by: None | str | Unset
        if isinstance(self.created_by, Unset):
            created_by = UNSET
        else:
            created_by = self.created_by

        full_name: None | str | Unset
        if isinstance(self.full_name, Unset):
            full_name = UNSET
        else:
            full_name = self.full_name

        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        owner: None | str | Unset
        if isinstance(self.owner, Unset):
            owner = UNSET
        else:
            owner = self.owner

        properties: dict[str, Any] | None | Unset
        if isinstance(self.properties, Unset):
            properties = UNSET
        elif isinstance(self.properties, SchemaInfoPropertiesType0):
            properties = self.properties.to_dict()
        else:
            properties = self.properties

        schema_id: None | str | Unset
        if isinstance(self.schema_id, Unset):
            schema_id = UNSET
        else:
            schema_id = self.schema_id

        storage_location: None | str | Unset
        if isinstance(self.storage_location, Unset):
            storage_location = UNSET
        else:
            storage_location = self.storage_location

        storage_root: None | str | Unset
        if isinstance(self.storage_root, Unset):
            storage_root = UNSET
        else:
            storage_root = self.storage_root

        updated_at: int | None | Unset
        if isinstance(self.updated_at, Unset):
            updated_at = UNSET
        else:
            updated_at = self.updated_at

        updated_by: None | str | Unset
        if isinstance(self.updated_by, Unset):
            updated_by = UNSET
        else:
            updated_by = self.updated_by

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if catalog_name is not UNSET:
            field_dict["catalog_name"] = catalog_name
        if comment is not UNSET:
            field_dict["comment"] = comment
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if created_by is not UNSET:
            field_dict["created_by"] = created_by
        if full_name is not UNSET:
            field_dict["full_name"] = full_name
        if name is not UNSET:
            field_dict["name"] = name
        if owner is not UNSET:
            field_dict["owner"] = owner
        if properties is not UNSET:
            field_dict["properties"] = properties
        if schema_id is not UNSET:
            field_dict["schema_id"] = schema_id
        if storage_location is not UNSET:
            field_dict["storage_location"] = storage_location
        if storage_root is not UNSET:
            field_dict["storage_root"] = storage_root
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if updated_by is not UNSET:
            field_dict["updated_by"] = updated_by

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.schema_info_properties_type_0 import SchemaInfoPropertiesType0

        d = dict(src_dict)

        def _parse_catalog_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        catalog_name = _parse_catalog_name(d.pop("catalog_name", UNSET))

        def _parse_comment(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        comment = _parse_comment(d.pop("comment", UNSET))

        def _parse_created_at(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        created_at = _parse_created_at(d.pop("created_at", UNSET))

        def _parse_created_by(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        created_by = _parse_created_by(d.pop("created_by", UNSET))

        def _parse_full_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        full_name = _parse_full_name(d.pop("full_name", UNSET))

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_owner(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        owner = _parse_owner(d.pop("owner", UNSET))

        def _parse_properties(data: object) -> None | SchemaInfoPropertiesType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                properties_type_0 = SchemaInfoPropertiesType0.from_dict(data)

                return properties_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | SchemaInfoPropertiesType0 | Unset, data)

        properties = _parse_properties(d.pop("properties", UNSET))

        def _parse_schema_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        schema_id = _parse_schema_id(d.pop("schema_id", UNSET))

        def _parse_storage_location(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        storage_location = _parse_storage_location(d.pop("storage_location", UNSET))

        def _parse_storage_root(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        storage_root = _parse_storage_root(d.pop("storage_root", UNSET))

        def _parse_updated_at(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        updated_at = _parse_updated_at(d.pop("updated_at", UNSET))

        def _parse_updated_by(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        updated_by = _parse_updated_by(d.pop("updated_by", UNSET))

        schema_info = cls(
            catalog_name=catalog_name,
            comment=comment,
            created_at=created_at,
            created_by=created_by,
            full_name=full_name,
            name=name,
            owner=owner,
            properties=properties,
            schema_id=schema_id,
            storage_location=storage_location,
            storage_root=storage_root,
            updated_at=updated_at,
            updated_by=updated_by,
        )

        schema_info.additional_properties = d
        return schema_info

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
