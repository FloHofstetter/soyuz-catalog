from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.create_catalog_type_type_0 import CreateCatalogTypeType0
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.create_catalog_options_type_0 import CreateCatalogOptionsType0
    from ..models.create_catalog_properties_type_0 import CreateCatalogPropertiesType0


T = TypeVar("T", bound="CreateCatalog")


@_attrs_define
class CreateCatalog:
    """Request body for ``POST /catalogs``.

    Only ``name`` is required by the spec; everything else is optional and
    defaults to ``None`` / empty. ``extra="forbid"`` mirrors the same policy
    used on ``UpdateCatalog``: silently dropping unknown fields is the UC OSS
    Java bug we exist to fix, so we reject them with HTTP 422 on create as
    well as on update.

    The Lakehouse-Federation foreign-catalog variant is opt-in: pass ``type="FOREIGN"``
    together with ``connection_name`` (and optional per-connector
    ``options``) and leave ``storage_root`` absent. The managed default
    is ``type="MANAGED"`` and the service layer rejects the two shapes'
    fields cross-contaminating — see ``catalog_service.create_catalog``
    for the exact gates and ``DIVERGENCES.md`` for the rule set.

        Attributes:
            name (str):
            comment (None | str | Unset):
            connection_name (None | str | Unset):
            options (CreateCatalogOptionsType0 | None | Unset):
            properties (CreateCatalogPropertiesType0 | None | Unset):
            storage_root (None | str | Unset):
            type_ (CreateCatalogTypeType0 | None | Unset):
    """

    name: str
    comment: None | str | Unset = UNSET
    connection_name: None | str | Unset = UNSET
    options: CreateCatalogOptionsType0 | None | Unset = UNSET
    properties: CreateCatalogPropertiesType0 | None | Unset = UNSET
    storage_root: None | str | Unset = UNSET
    type_: CreateCatalogTypeType0 | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.create_catalog_options_type_0 import CreateCatalogOptionsType0
        from ..models.create_catalog_properties_type_0 import (
            CreateCatalogPropertiesType0,
        )

        name = self.name

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

        options: dict[str, Any] | None | Unset
        if isinstance(self.options, Unset):
            options = UNSET
        elif isinstance(self.options, CreateCatalogOptionsType0):
            options = self.options.to_dict()
        else:
            options = self.options

        properties: dict[str, Any] | None | Unset
        if isinstance(self.properties, Unset):
            properties = UNSET
        elif isinstance(self.properties, CreateCatalogPropertiesType0):
            properties = self.properties.to_dict()
        else:
            properties = self.properties

        storage_root: None | str | Unset
        if isinstance(self.storage_root, Unset):
            storage_root = UNSET
        else:
            storage_root = self.storage_root

        type_: None | str | Unset
        if isinstance(self.type_, Unset):
            type_ = UNSET
        elif isinstance(self.type_, CreateCatalogTypeType0):
            type_ = self.type_.value
        else:
            type_ = self.type_

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
            }
        )
        if comment is not UNSET:
            field_dict["comment"] = comment
        if connection_name is not UNSET:
            field_dict["connection_name"] = connection_name
        if options is not UNSET:
            field_dict["options"] = options
        if properties is not UNSET:
            field_dict["properties"] = properties
        if storage_root is not UNSET:
            field_dict["storage_root"] = storage_root
        if type_ is not UNSET:
            field_dict["type"] = type_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.create_catalog_options_type_0 import CreateCatalogOptionsType0
        from ..models.create_catalog_properties_type_0 import (
            CreateCatalogPropertiesType0,
        )

        d = dict(src_dict)
        name = d.pop("name")

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

        def _parse_options(data: object) -> CreateCatalogOptionsType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                options_type_0 = CreateCatalogOptionsType0.from_dict(data)

                return options_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(CreateCatalogOptionsType0 | None | Unset, data)

        options = _parse_options(d.pop("options", UNSET))

        def _parse_properties(
            data: object,
        ) -> CreateCatalogPropertiesType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                properties_type_0 = CreateCatalogPropertiesType0.from_dict(data)

                return properties_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(CreateCatalogPropertiesType0 | None | Unset, data)

        properties = _parse_properties(d.pop("properties", UNSET))

        def _parse_storage_root(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        storage_root = _parse_storage_root(d.pop("storage_root", UNSET))

        def _parse_type_(data: object) -> CreateCatalogTypeType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                type_type_0 = CreateCatalogTypeType0(data)

                return type_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(CreateCatalogTypeType0 | None | Unset, data)

        type_ = _parse_type_(d.pop("type", UNSET))

        create_catalog = cls(
            name=name,
            comment=comment,
            connection_name=connection_name,
            options=options,
            properties=properties,
            storage_root=storage_root,
            type_=type_,
        )

        return create_catalog
