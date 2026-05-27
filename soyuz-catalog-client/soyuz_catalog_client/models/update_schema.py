from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.update_schema_properties_type_0 import UpdateSchemaPropertiesType0


T = TypeVar("T", bound="UpdateSchema")


@_attrs_define
class UpdateSchema:
    """Request body for ``PATCH /schemas/{full_name}``.

    Shape is intentionally identical to :class:`UpdateCatalog`: replace-style
    PATCH semantics driven by ``model_fields_set`` in the service layer, and
    ``extra="forbid"`` rejects unknown or read-only fields (including
    ``owner``, ``catalog_name``, ``full_name``) with HTTP 422 instead of
    silently dropping them.

        Attributes:
            comment (None | str | Unset):
            new_name (None | str | Unset):
            properties (None | Unset | UpdateSchemaPropertiesType0):
    """

    comment: None | str | Unset = UNSET
    new_name: None | str | Unset = UNSET
    properties: None | Unset | UpdateSchemaPropertiesType0 = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.update_schema_properties_type_0 import UpdateSchemaPropertiesType0

        comment: None | str | Unset
        if isinstance(self.comment, Unset):
            comment = UNSET
        else:
            comment = self.comment

        new_name: None | str | Unset
        if isinstance(self.new_name, Unset):
            new_name = UNSET
        else:
            new_name = self.new_name

        properties: dict[str, Any] | None | Unset
        if isinstance(self.properties, Unset):
            properties = UNSET
        elif isinstance(self.properties, UpdateSchemaPropertiesType0):
            properties = self.properties.to_dict()
        else:
            properties = self.properties

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if comment is not UNSET:
            field_dict["comment"] = comment
        if new_name is not UNSET:
            field_dict["new_name"] = new_name
        if properties is not UNSET:
            field_dict["properties"] = properties

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.update_schema_properties_type_0 import UpdateSchemaPropertiesType0

        d = dict(src_dict)

        def _parse_comment(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        comment = _parse_comment(d.pop("comment", UNSET))

        def _parse_new_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        new_name = _parse_new_name(d.pop("new_name", UNSET))

        def _parse_properties(
            data: object,
        ) -> None | Unset | UpdateSchemaPropertiesType0:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                properties_type_0 = UpdateSchemaPropertiesType0.from_dict(data)

                return properties_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UpdateSchemaPropertiesType0, data)

        properties = _parse_properties(d.pop("properties", UNSET))

        update_schema = cls(
            comment=comment,
            new_name=new_name,
            properties=properties,
        )

        return update_schema
