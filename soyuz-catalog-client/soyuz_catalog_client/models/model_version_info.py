from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.model_version_info_status_type_0 import ModelVersionInfoStatusType0
from ..types import UNSET, Unset

T = TypeVar("T", bound="ModelVersionInfo")


@_attrs_define
class ModelVersionInfo:
    """Response shape for a single registered-model version.

    Addressed in the URL by ``(full_name, version_int)`` and in this
    payload the ``model_name`` / ``catalog_name`` / ``schema_name``
    are computed from the live parent registered model at response
    time, same rename-propagation trick as every other nested
    resource in this module.

    ``status`` is always ``READY`` on rows soyuz creates — see
    :class:`soyuz_catalog.models.ModelVersion` and DIVERGENCES.

        Attributes:
            catalog_name (None | str | Unset):
            comment (None | str | Unset):
            created_at (int | None | Unset):
            created_by (None | str | Unset):
            id (None | str | Unset):
            model_name (None | str | Unset):
            run_id (None | str | Unset):
            schema_name (None | str | Unset):
            source (None | str | Unset):
            status (ModelVersionInfoStatusType0 | None | Unset):
            storage_location (None | str | Unset):
            updated_at (int | None | Unset):
            updated_by (None | str | Unset):
            version (int | None | Unset):
    """

    catalog_name: None | str | Unset = UNSET
    comment: None | str | Unset = UNSET
    created_at: int | None | Unset = UNSET
    created_by: None | str | Unset = UNSET
    id: None | str | Unset = UNSET
    model_name: None | str | Unset = UNSET
    run_id: None | str | Unset = UNSET
    schema_name: None | str | Unset = UNSET
    source: None | str | Unset = UNSET
    status: ModelVersionInfoStatusType0 | None | Unset = UNSET
    storage_location: None | str | Unset = UNSET
    updated_at: int | None | Unset = UNSET
    updated_by: None | str | Unset = UNSET
    version: int | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
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

        id: None | str | Unset
        if isinstance(self.id, Unset):
            id = UNSET
        else:
            id = self.id

        model_name: None | str | Unset
        if isinstance(self.model_name, Unset):
            model_name = UNSET
        else:
            model_name = self.model_name

        run_id: None | str | Unset
        if isinstance(self.run_id, Unset):
            run_id = UNSET
        else:
            run_id = self.run_id

        schema_name: None | str | Unset
        if isinstance(self.schema_name, Unset):
            schema_name = UNSET
        else:
            schema_name = self.schema_name

        source: None | str | Unset
        if isinstance(self.source, Unset):
            source = UNSET
        else:
            source = self.source

        status: None | str | Unset
        if isinstance(self.status, Unset):
            status = UNSET
        elif isinstance(self.status, ModelVersionInfoStatusType0):
            status = self.status.value
        else:
            status = self.status

        storage_location: None | str | Unset
        if isinstance(self.storage_location, Unset):
            storage_location = UNSET
        else:
            storage_location = self.storage_location

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

        version: int | None | Unset
        if isinstance(self.version, Unset):
            version = UNSET
        else:
            version = self.version

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
        if id is not UNSET:
            field_dict["id"] = id
        if model_name is not UNSET:
            field_dict["model_name"] = model_name
        if run_id is not UNSET:
            field_dict["run_id"] = run_id
        if schema_name is not UNSET:
            field_dict["schema_name"] = schema_name
        if source is not UNSET:
            field_dict["source"] = source
        if status is not UNSET:
            field_dict["status"] = status
        if storage_location is not UNSET:
            field_dict["storage_location"] = storage_location
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if updated_by is not UNSET:
            field_dict["updated_by"] = updated_by
        if version is not UNSET:
            field_dict["version"] = version

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

        def _parse_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        id = _parse_id(d.pop("id", UNSET))

        def _parse_model_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        model_name = _parse_model_name(d.pop("model_name", UNSET))

        def _parse_run_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        run_id = _parse_run_id(d.pop("run_id", UNSET))

        def _parse_schema_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        schema_name = _parse_schema_name(d.pop("schema_name", UNSET))

        def _parse_source(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        source = _parse_source(d.pop("source", UNSET))

        def _parse_status(data: object) -> ModelVersionInfoStatusType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                status_type_0 = ModelVersionInfoStatusType0(data)

                return status_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(ModelVersionInfoStatusType0 | None | Unset, data)

        status = _parse_status(d.pop("status", UNSET))

        def _parse_storage_location(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        storage_location = _parse_storage_location(d.pop("storage_location", UNSET))

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

        def _parse_version(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        version = _parse_version(d.pop("version", UNSET))

        model_version_info = cls(
            catalog_name=catalog_name,
            comment=comment,
            created_at=created_at,
            created_by=created_by,
            id=id,
            model_name=model_name,
            run_id=run_id,
            schema_name=schema_name,
            source=source,
            status=status,
            storage_location=storage_location,
            updated_at=updated_at,
            updated_by=updated_by,
            version=version,
        )

        model_version_info.additional_properties = d
        return model_version_info

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
