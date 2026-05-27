from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.create_volume_volume_type import CreateVolumeVolumeType
from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateVolume")


@_attrs_define
class CreateVolume:
    """Request body for ``POST /volumes``.

    The UC spec requires ``catalog_name``, ``schema_name``, ``name``, and
    ``volume_type`` on create. ``storage_location`` and ``comment`` are
    optional. ``volume_type`` is constrained to the spec enum
    ``{"MANAGED", "EXTERNAL"}`` at the Pydantic layer so that a typo
    surfaces as 422 rather than reaching the database as a free-form
    string.

    ``extra="forbid"`` rejects unknown fields, same UC OSS bug-fix policy
    as every other request body in this module.

        Attributes:
            catalog_name (str):
            name (str):
            schema_name (str):
            volume_type (CreateVolumeVolumeType):
            comment (None | str | Unset):
            storage_location (None | str | Unset):
    """

    catalog_name: str
    name: str
    schema_name: str
    volume_type: CreateVolumeVolumeType
    comment: None | str | Unset = UNSET
    storage_location: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        catalog_name = self.catalog_name

        name = self.name

        schema_name = self.schema_name

        volume_type = self.volume_type.value

        comment: None | str | Unset
        if isinstance(self.comment, Unset):
            comment = UNSET
        else:
            comment = self.comment

        storage_location: None | str | Unset
        if isinstance(self.storage_location, Unset):
            storage_location = UNSET
        else:
            storage_location = self.storage_location

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "catalog_name": catalog_name,
                "name": name,
                "schema_name": schema_name,
                "volume_type": volume_type,
            }
        )
        if comment is not UNSET:
            field_dict["comment"] = comment
        if storage_location is not UNSET:
            field_dict["storage_location"] = storage_location

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        catalog_name = d.pop("catalog_name")

        name = d.pop("name")

        schema_name = d.pop("schema_name")

        volume_type = CreateVolumeVolumeType(d.pop("volume_type"))

        def _parse_comment(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        comment = _parse_comment(d.pop("comment", UNSET))

        def _parse_storage_location(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        storage_location = _parse_storage_location(d.pop("storage_location", UNSET))

        create_volume = cls(
            catalog_name=catalog_name,
            name=name,
            schema_name=schema_name,
            volume_type=volume_type,
            comment=comment,
            storage_location=storage_location,
        )

        return create_volume
