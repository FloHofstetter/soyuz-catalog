from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ColumnInfo")


@_attrs_define
class ColumnInfo:
    """A single column in a Unity Catalog table.

    The same shape is used for both create requests (as an element of
    ``CreateTable.columns``) and read responses (as an element of
    ``TableInfo.columns``) — UC OpenAPI defines one ``ColumnInfo`` schema
    for both directions. On create every field is logically optional at
    the Pydantic level; the service layer relies on the fact that the
    non-nullable ORM columns (``name``, ``type_text``, ``type_json``,
    ``type_name``, ``position``) will raise an ``IntegrityError`` if
    omitted, which is surfaced as a 422 by the request validator when the
    field is missing from the payload entirely.

    ``extra="forbid"`` rejects unknown fields inside a column the same way
    it does on the top-level request: a typo like ``type_neme`` must not
    be silently dropped.

        Attributes:
            comment (None | str | Unset):
            name (None | str | Unset):
            nullable (bool | None | Unset):
            partition_index (int | None | Unset):
            position (int | None | Unset):
            type_interval_type (None | str | Unset):
            type_json (None | str | Unset):
            type_name (None | str | Unset):
            type_precision (int | None | Unset):
            type_scale (int | None | Unset):
            type_text (None | str | Unset):
    """

    comment: None | str | Unset = UNSET
    name: None | str | Unset = UNSET
    nullable: bool | None | Unset = UNSET
    partition_index: int | None | Unset = UNSET
    position: int | None | Unset = UNSET
    type_interval_type: None | str | Unset = UNSET
    type_json: None | str | Unset = UNSET
    type_name: None | str | Unset = UNSET
    type_precision: int | None | Unset = UNSET
    type_scale: int | None | Unset = UNSET
    type_text: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        comment: None | str | Unset
        if isinstance(self.comment, Unset):
            comment = UNSET
        else:
            comment = self.comment

        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        nullable: bool | None | Unset
        if isinstance(self.nullable, Unset):
            nullable = UNSET
        else:
            nullable = self.nullable

        partition_index: int | None | Unset
        if isinstance(self.partition_index, Unset):
            partition_index = UNSET
        else:
            partition_index = self.partition_index

        position: int | None | Unset
        if isinstance(self.position, Unset):
            position = UNSET
        else:
            position = self.position

        type_interval_type: None | str | Unset
        if isinstance(self.type_interval_type, Unset):
            type_interval_type = UNSET
        else:
            type_interval_type = self.type_interval_type

        type_json: None | str | Unset
        if isinstance(self.type_json, Unset):
            type_json = UNSET
        else:
            type_json = self.type_json

        type_name: None | str | Unset
        if isinstance(self.type_name, Unset):
            type_name = UNSET
        else:
            type_name = self.type_name

        type_precision: int | None | Unset
        if isinstance(self.type_precision, Unset):
            type_precision = UNSET
        else:
            type_precision = self.type_precision

        type_scale: int | None | Unset
        if isinstance(self.type_scale, Unset):
            type_scale = UNSET
        else:
            type_scale = self.type_scale

        type_text: None | str | Unset
        if isinstance(self.type_text, Unset):
            type_text = UNSET
        else:
            type_text = self.type_text

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if comment is not UNSET:
            field_dict["comment"] = comment
        if name is not UNSET:
            field_dict["name"] = name
        if nullable is not UNSET:
            field_dict["nullable"] = nullable
        if partition_index is not UNSET:
            field_dict["partition_index"] = partition_index
        if position is not UNSET:
            field_dict["position"] = position
        if type_interval_type is not UNSET:
            field_dict["type_interval_type"] = type_interval_type
        if type_json is not UNSET:
            field_dict["type_json"] = type_json
        if type_name is not UNSET:
            field_dict["type_name"] = type_name
        if type_precision is not UNSET:
            field_dict["type_precision"] = type_precision
        if type_scale is not UNSET:
            field_dict["type_scale"] = type_scale
        if type_text is not UNSET:
            field_dict["type_text"] = type_text

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_comment(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        comment = _parse_comment(d.pop("comment", UNSET))

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_nullable(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        nullable = _parse_nullable(d.pop("nullable", UNSET))

        def _parse_partition_index(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        partition_index = _parse_partition_index(d.pop("partition_index", UNSET))

        def _parse_position(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        position = _parse_position(d.pop("position", UNSET))

        def _parse_type_interval_type(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        type_interval_type = _parse_type_interval_type(
            d.pop("type_interval_type", UNSET)
        )

        def _parse_type_json(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        type_json = _parse_type_json(d.pop("type_json", UNSET))

        def _parse_type_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        type_name = _parse_type_name(d.pop("type_name", UNSET))

        def _parse_type_precision(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        type_precision = _parse_type_precision(d.pop("type_precision", UNSET))

        def _parse_type_scale(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        type_scale = _parse_type_scale(d.pop("type_scale", UNSET))

        def _parse_type_text(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        type_text = _parse_type_text(d.pop("type_text", UNSET))

        column_info = cls(
            comment=comment,
            name=name,
            nullable=nullable,
            partition_index=partition_index,
            position=position,
            type_interval_type=type_interval_type,
            type_json=type_json,
            type_name=type_name,
            type_precision=type_precision,
            type_scale=type_scale,
            type_text=type_text,
        )

        return column_info
