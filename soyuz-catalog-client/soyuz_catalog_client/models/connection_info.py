from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.connection_info_connection_type_type_0 import (
    ConnectionInfoConnectionTypeType0,
)
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.connection_info_options_type_0 import ConnectionInfoOptionsType0


T = TypeVar("T", bound="ConnectionInfo")


@_attrs_define
class ConnectionInfo:
    """Response shape for a Lakehouse-Federation connection.

    Over-the-spec addition (ADR-0013): upstream UC OSS
    ``all.yaml`` defines no ``Connection`` schema at all, so there is
    no upstream row to mirror — this shape is soyuz' contract for the
    metadata Databricks' ``Connection`` surface round-trips. soyuz
    does not store credential-bearing fields separately from
    ``options``; a future secrets-integration sprint can add a
    dedicated ``credential`` subresource without touching this wire
    shape.

        Attributes:
            comment (None | str | Unset):
            connection_type (ConnectionInfoConnectionTypeType0 | None | Unset):
            created_at (int | None | Unset):
            created_by (None | str | Unset):
            id (None | str | Unset):
            name (None | str | Unset):
            options (ConnectionInfoOptionsType0 | None | Unset):
            owner (None | str | Unset):
            read_only (bool | None | Unset):
            updated_at (int | None | Unset):
            updated_by (None | str | Unset):
    """

    comment: None | str | Unset = UNSET
    connection_type: ConnectionInfoConnectionTypeType0 | None | Unset = UNSET
    created_at: int | None | Unset = UNSET
    created_by: None | str | Unset = UNSET
    id: None | str | Unset = UNSET
    name: None | str | Unset = UNSET
    options: ConnectionInfoOptionsType0 | None | Unset = UNSET
    owner: None | str | Unset = UNSET
    read_only: bool | None | Unset = UNSET
    updated_at: int | None | Unset = UNSET
    updated_by: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.connection_info_options_type_0 import ConnectionInfoOptionsType0

        comment: None | str | Unset
        if isinstance(self.comment, Unset):
            comment = UNSET
        else:
            comment = self.comment

        connection_type: None | str | Unset
        if isinstance(self.connection_type, Unset):
            connection_type = UNSET
        elif isinstance(self.connection_type, ConnectionInfoConnectionTypeType0):
            connection_type = self.connection_type.value
        else:
            connection_type = self.connection_type

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
        elif isinstance(self.options, ConnectionInfoOptionsType0):
            options = self.options.to_dict()
        else:
            options = self.options

        owner: None | str | Unset
        if isinstance(self.owner, Unset):
            owner = UNSET
        else:
            owner = self.owner

        read_only: bool | None | Unset
        if isinstance(self.read_only, Unset):
            read_only = UNSET
        else:
            read_only = self.read_only

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
        if connection_type is not UNSET:
            field_dict["connection_type"] = connection_type
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
        if read_only is not UNSET:
            field_dict["read_only"] = read_only
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if updated_by is not UNSET:
            field_dict["updated_by"] = updated_by

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.connection_info_options_type_0 import ConnectionInfoOptionsType0

        d = dict(src_dict)

        def _parse_comment(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        comment = _parse_comment(d.pop("comment", UNSET))

        def _parse_connection_type(
            data: object,
        ) -> ConnectionInfoConnectionTypeType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                connection_type_type_0 = ConnectionInfoConnectionTypeType0(data)

                return connection_type_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(ConnectionInfoConnectionTypeType0 | None | Unset, data)

        connection_type = _parse_connection_type(d.pop("connection_type", UNSET))

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

        def _parse_options(data: object) -> ConnectionInfoOptionsType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                options_type_0 = ConnectionInfoOptionsType0.from_dict(data)

                return options_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(ConnectionInfoOptionsType0 | None | Unset, data)

        options = _parse_options(d.pop("options", UNSET))

        def _parse_owner(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        owner = _parse_owner(d.pop("owner", UNSET))

        def _parse_read_only(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        read_only = _parse_read_only(d.pop("read_only", UNSET))

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

        connection_info = cls(
            comment=comment,
            connection_type=connection_type,
            created_at=created_at,
            created_by=created_by,
            id=id,
            name=name,
            options=options,
            owner=owner,
            read_only=read_only,
            updated_at=updated_at,
            updated_by=updated_by,
        )

        connection_info.additional_properties = d
        return connection_info

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
