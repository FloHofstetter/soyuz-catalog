from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.catalog_info_type_type_0 import CatalogInfoTypeType0
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.catalog_info_options_type_0 import CatalogInfoOptionsType0
    from ..models.catalog_info_properties_type_0 import CatalogInfoPropertiesType0


T = TypeVar("T", bound="CatalogInfo")


@_attrs_define
class CatalogInfo:
    """Response shape for a Unity Catalog catalog.

    All fields are optional in the spec; we always populate the system
    fields we own. ``type``, ``connection_name``, and ``options`` back
    the Lakehouse-Federation foreign-catalog variant (ADR-0013): a
    managed catalog serialises with ``type="MANAGED"`` and leaves the
    two connection fields
    ``None`` (the route's ``exclude_none`` drops them from the wire);
    a foreign catalog flips ``type`` to ``"FOREIGN"``, populates
    ``connection_name`` from the live :class:`soyuz_catalog.models.Connection`
    relationship (rename-invariant, same trick as
    :class:`ExternalLocationInfo.credential_name`), and leaves
    ``storage_root`` / ``storage_location`` ``None``.

        Attributes:
            comment (None | str | Unset):
            connection_name (None | str | Unset):
            created_at (int | None | Unset):
            created_by (None | str | Unset):
            id (None | str | Unset):
            name (None | str | Unset):
            options (CatalogInfoOptionsType0 | None | Unset):
            owner (None | str | Unset):
            properties (CatalogInfoPropertiesType0 | None | Unset):
            storage_location (None | str | Unset):
            storage_root (None | str | Unset):
            type_ (CatalogInfoTypeType0 | None | Unset):
            updated_at (int | None | Unset):
            updated_by (None | str | Unset):
    """

    comment: None | str | Unset = UNSET
    connection_name: None | str | Unset = UNSET
    created_at: int | None | Unset = UNSET
    created_by: None | str | Unset = UNSET
    id: None | str | Unset = UNSET
    name: None | str | Unset = UNSET
    options: CatalogInfoOptionsType0 | None | Unset = UNSET
    owner: None | str | Unset = UNSET
    properties: CatalogInfoPropertiesType0 | None | Unset = UNSET
    storage_location: None | str | Unset = UNSET
    storage_root: None | str | Unset = UNSET
    type_: CatalogInfoTypeType0 | None | Unset = UNSET
    updated_at: int | None | Unset = UNSET
    updated_by: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.catalog_info_options_type_0 import CatalogInfoOptionsType0
        from ..models.catalog_info_properties_type_0 import CatalogInfoPropertiesType0

        comment: None | str | Unset
        if isinstance(self.comment, Unset):
            comment = UNSET
        else:
            comment = self.comment

        connection_name: None | str | Unset
        if isinstance(self.connection_name, Unset):
            connection_name = UNSET
        else:
            connection_name = self.connection_name

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

        options: dict[str, Any] | None | Unset
        if isinstance(self.options, Unset):
            options = UNSET
        elif isinstance(self.options, CatalogInfoOptionsType0):
            options = self.options.to_dict()
        else:
            options = self.options

        owner: None | str | Unset
        if isinstance(self.owner, Unset):
            owner = UNSET
        else:
            owner = self.owner

        properties: dict[str, Any] | None | Unset
        if isinstance(self.properties, Unset):
            properties = UNSET
        elif isinstance(self.properties, CatalogInfoPropertiesType0):
            properties = self.properties.to_dict()
        else:
            properties = self.properties

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

        type_: None | str | Unset
        if isinstance(self.type_, Unset):
            type_ = UNSET
        elif isinstance(self.type_, CatalogInfoTypeType0):
            type_ = self.type_.value
        else:
            type_ = self.type_

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
        if comment is not UNSET:
            field_dict["comment"] = comment
        if connection_name is not UNSET:
            field_dict["connection_name"] = connection_name
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if created_by is not UNSET:
            field_dict["created_by"] = created_by
        if id is not UNSET:
            field_dict["id"] = id
        if name is not UNSET:
            field_dict["name"] = name
        if options is not UNSET:
            field_dict["options"] = options
        if owner is not UNSET:
            field_dict["owner"] = owner
        if properties is not UNSET:
            field_dict["properties"] = properties
        if storage_location is not UNSET:
            field_dict["storage_location"] = storage_location
        if storage_root is not UNSET:
            field_dict["storage_root"] = storage_root
        if type_ is not UNSET:
            field_dict["type"] = type_
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if updated_by is not UNSET:
            field_dict["updated_by"] = updated_by

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.catalog_info_options_type_0 import CatalogInfoOptionsType0
        from ..models.catalog_info_properties_type_0 import CatalogInfoPropertiesType0

        d = dict(src_dict)

        def _parse_comment(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        comment = _parse_comment(d.pop("comment", UNSET))

        def _parse_connection_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        connection_name = _parse_connection_name(d.pop("connection_name", UNSET))

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

        def _parse_options(data: object) -> CatalogInfoOptionsType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                options_type_0 = CatalogInfoOptionsType0.from_dict(data)

                return options_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(CatalogInfoOptionsType0 | None | Unset, data)

        options = _parse_options(d.pop("options", UNSET))

        def _parse_owner(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        owner = _parse_owner(d.pop("owner", UNSET))

        def _parse_properties(
            data: object,
        ) -> CatalogInfoPropertiesType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                properties_type_0 = CatalogInfoPropertiesType0.from_dict(data)

                return properties_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(CatalogInfoPropertiesType0 | None | Unset, data)

        properties = _parse_properties(d.pop("properties", UNSET))

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

        def _parse_type_(data: object) -> CatalogInfoTypeType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                type_type_0 = CatalogInfoTypeType0(data)

                return type_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(CatalogInfoTypeType0 | None | Unset, data)

        type_ = _parse_type_(d.pop("type", UNSET))

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

        catalog_info = cls(
            comment=comment,
            connection_name=connection_name,
            created_at=created_at,
            created_by=created_by,
            id=id,
            name=name,
            options=options,
            owner=owner,
            properties=properties,
            storage_location=storage_location,
            storage_root=storage_root,
            type_=type_,
            updated_at=updated_at,
            updated_by=updated_by,
        )

        catalog_info.additional_properties = d
        return catalog_info

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
