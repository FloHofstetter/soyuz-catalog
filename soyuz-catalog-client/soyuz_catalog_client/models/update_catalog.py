from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.update_catalog_options_type_0 import UpdateCatalogOptionsType0
    from ..models.update_catalog_properties_type_0 import UpdateCatalogPropertiesType0


T = TypeVar("T", bound="UpdateCatalog")


@_attrs_define
class UpdateCatalog:
    """Request body for ``PATCH /catalogs/{name}``.

    Replace-style PATCH semantics: every field is optional, but a field that
    *is* present in the request body — including ``properties: {}`` — is
    written through to the row. The service layer reads ``model_fields_set``
    rather than checking ``is None`` so it can distinguish "field omitted"
    from "field set to null/empty".

    ``extra="forbid"`` rejects unknown or read-only fields (e.g. ``owner``)
    with HTTP 422 instead of silently ignoring them as UC OSS Java does. This
    is one of the documented divergences from the Java reference; see
    ``DIVERGENCES.md``.

    The catalog ``type`` field is **deliberately not exposed** on this
    shape: flipping a managed catalog to foreign (or vice versa) would
    orphan the other variant's bookkeeping state (``storage_location``
    on managed, ``connection_id`` on foreign) and has no well-defined
    semantics. A catalog's type is decided at create time and frozen.
    ``connection_name`` PATCH is accepted on foreign catalogs only; the
    service rejects it with 400 on a managed catalog. ``options`` PATCH
    is allowed on both and is replace-style like ``properties``.

        Attributes:
            comment (None | str | Unset):
            connection_name (None | str | Unset):
            new_name (None | str | Unset):
            options (None | Unset | UpdateCatalogOptionsType0):
            properties (None | Unset | UpdateCatalogPropertiesType0):
    """

    comment: None | str | Unset = UNSET
    connection_name: None | str | Unset = UNSET
    new_name: None | str | Unset = UNSET
    options: None | Unset | UpdateCatalogOptionsType0 = UNSET
    properties: None | Unset | UpdateCatalogPropertiesType0 = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.update_catalog_options_type_0 import UpdateCatalogOptionsType0
        from ..models.update_catalog_properties_type_0 import (
            UpdateCatalogPropertiesType0,
        )

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

        new_name: None | str | Unset
        if isinstance(self.new_name, Unset):
            new_name = UNSET
        else:
            new_name = self.new_name

        options: dict[str, Any] | None | Unset
        if isinstance(self.options, Unset):
            options = UNSET
        elif isinstance(self.options, UpdateCatalogOptionsType0):
            options = self.options.to_dict()
        else:
            options = self.options

        properties: dict[str, Any] | None | Unset
        if isinstance(self.properties, Unset):
            properties = UNSET
        elif isinstance(self.properties, UpdateCatalogPropertiesType0):
            properties = self.properties.to_dict()
        else:
            properties = self.properties

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if comment is not UNSET:
            field_dict["comment"] = comment
        if connection_name is not UNSET:
            field_dict["connection_name"] = connection_name
        if new_name is not UNSET:
            field_dict["new_name"] = new_name
        if options is not UNSET:
            field_dict["options"] = options
        if properties is not UNSET:
            field_dict["properties"] = properties

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.update_catalog_options_type_0 import UpdateCatalogOptionsType0
        from ..models.update_catalog_properties_type_0 import (
            UpdateCatalogPropertiesType0,
        )

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

        def _parse_new_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        new_name = _parse_new_name(d.pop("new_name", UNSET))

        def _parse_options(data: object) -> None | Unset | UpdateCatalogOptionsType0:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                options_type_0 = UpdateCatalogOptionsType0.from_dict(data)

                return options_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UpdateCatalogOptionsType0, data)

        options = _parse_options(d.pop("options", UNSET))

        def _parse_properties(
            data: object,
        ) -> None | Unset | UpdateCatalogPropertiesType0:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                properties_type_0 = UpdateCatalogPropertiesType0.from_dict(data)

                return properties_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UpdateCatalogPropertiesType0, data)

        properties = _parse_properties(d.pop("properties", UNSET))

        update_catalog = cls(
            comment=comment,
            connection_name=connection_name,
            new_name=new_name,
            options=options,
            properties=properties,
        )

        return update_catalog
