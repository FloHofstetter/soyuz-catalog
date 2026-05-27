from __future__ import annotations

import json
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from .. import types
from ..types import UNSET, Unset

T = TypeVar("T", bound="BodyUploadVolumeFileApi21UnityCatalogVolumesFullNameFilesPost")


@_attrs_define
class BodyUploadVolumeFileApi21UnityCatalogVolumesFullNameFilesPost:
    """
    Attributes:
        upload (str):
    """

    upload: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        upload = self.upload

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "upload": upload,
            }
        )

        return field_dict

    def to_multipart(self) -> types.RequestFiles:
        files: types.RequestFiles = []

        files.append(("upload", (None, str(self.upload).encode(), "text/plain")))

        for prop_name, prop in self.additional_properties.items():
            files.append((prop_name, (None, str(prop).encode(), "text/plain")))

        return files

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        upload = d.pop("upload")

        body_upload_volume_file_api_21_unity_catalog_volumes_full_name_files_post = cls(
            upload=upload,
        )

        body_upload_volume_file_api_21_unity_catalog_volumes_full_name_files_post.additional_properties = d
        return body_upload_volume_file_api_21_unity_catalog_volumes_full_name_files_post

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
