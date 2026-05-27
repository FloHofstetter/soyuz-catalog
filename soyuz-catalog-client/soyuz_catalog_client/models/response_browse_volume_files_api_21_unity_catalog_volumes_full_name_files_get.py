from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.response_browse_volume_files_api_21_unity_catalog_volumes_full_name_files_get_additional_property_item import (
        ResponseBrowseVolumeFilesApi21UnityCatalogVolumesFullNameFilesGetAdditionalPropertyItem,
    )


T = TypeVar(
    "T", bound="ResponseBrowseVolumeFilesApi21UnityCatalogVolumesFullNameFilesGet"
)


@_attrs_define
class ResponseBrowseVolumeFilesApi21UnityCatalogVolumesFullNameFilesGet:
    """ """

    additional_properties: dict[
        str,
        list[
            ResponseBrowseVolumeFilesApi21UnityCatalogVolumesFullNameFilesGetAdditionalPropertyItem
        ],
    ] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.response_browse_volume_files_api_21_unity_catalog_volumes_full_name_files_get_additional_property_item import (
            ResponseBrowseVolumeFilesApi21UnityCatalogVolumesFullNameFilesGetAdditionalPropertyItem,
        )

        field_dict: dict[str, Any] = {}
        for prop_name, prop in self.additional_properties.items():
            field_dict[prop_name] = []
            for additional_property_item_data in prop:
                additional_property_item = additional_property_item_data.to_dict()
                field_dict[prop_name].append(additional_property_item)

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.response_browse_volume_files_api_21_unity_catalog_volumes_full_name_files_get_additional_property_item import (
            ResponseBrowseVolumeFilesApi21UnityCatalogVolumesFullNameFilesGetAdditionalPropertyItem,
        )

        d = dict(src_dict)
        response_browse_volume_files_api_21_unity_catalog_volumes_full_name_files_get = cls()

        additional_properties = {}
        for prop_name, prop_dict in d.items():
            additional_property = []
            _additional_property = prop_dict
            for additional_property_item_data in _additional_property:
                additional_property_item = ResponseBrowseVolumeFilesApi21UnityCatalogVolumesFullNameFilesGetAdditionalPropertyItem.from_dict(
                    additional_property_item_data
                )

                additional_property.append(additional_property_item)

            additional_properties[prop_name] = additional_property

        response_browse_volume_files_api_21_unity_catalog_volumes_full_name_files_get.additional_properties = additional_properties
        return response_browse_volume_files_api_21_unity_catalog_volumes_full_name_files_get

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(
        self, key: str
    ) -> list[
        ResponseBrowseVolumeFilesApi21UnityCatalogVolumesFullNameFilesGetAdditionalPropertyItem
    ]:
        return self.additional_properties[key]

    def __setitem__(
        self,
        key: str,
        value: list[
            ResponseBrowseVolumeFilesApi21UnityCatalogVolumesFullNameFilesGetAdditionalPropertyItem
        ],
    ) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
