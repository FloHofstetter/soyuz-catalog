from __future__ import annotations

from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    BinaryIO,
    Generator,
    Literal,
    TextIO,
    TypeVar,
    cast,
)

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.function_parameter_info_parameter_type_type_0 import (
    FunctionParameterInfoParameterTypeType0,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="FunctionParameterInfo")


@_attrs_define
class FunctionParameterInfo:
    """A single function parameter (input or return) in ``FunctionInfo``.

    Used symmetrically on request and response because the UC OpenAPI
    spec reuses the same schema for both directions. ``extra="forbid"``
    rejects typos on write — the service layer stores the parameter
    list as an opaque JSON object, so an unchecked unknown key would
    round-trip silently and mask a client bug. On the response side
    the forbid policy is a no-op because soyuz never emits extras.

        Attributes:
            name (str):
            position (int):
            type_json (str):
            type_name (str):
            type_text (str):
            comment (None | str | Unset):
            parameter_default (None | str | Unset):
            parameter_mode (Literal['IN'] | None | Unset):
            parameter_type (FunctionParameterInfoParameterTypeType0 | None | Unset):
            type_interval_type (None | str | Unset):
            type_precision (int | None | Unset):
            type_scale (int | None | Unset):
    """

    name: str
    position: int
    type_json: str
    type_name: str
    type_text: str
    comment: None | str | Unset = UNSET
    parameter_default: None | str | Unset = UNSET
    parameter_mode: Literal["IN"] | None | Unset = UNSET
    parameter_type: FunctionParameterInfoParameterTypeType0 | None | Unset = UNSET
    type_interval_type: None | str | Unset = UNSET
    type_precision: int | None | Unset = UNSET
    type_scale: int | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        position = self.position

        type_json = self.type_json

        type_name = self.type_name

        type_text = self.type_text

        comment: None | str | Unset
        if isinstance(self.comment, Unset):
            comment = UNSET
        else:
            comment = self.comment

        parameter_default: None | str | Unset
        if isinstance(self.parameter_default, Unset):
            parameter_default = UNSET
        else:
            parameter_default = self.parameter_default

        parameter_mode: Literal["IN"] | None | Unset
        if isinstance(self.parameter_mode, Unset):
            parameter_mode = UNSET
        else:
            parameter_mode = self.parameter_mode

        parameter_type: None | str | Unset
        if isinstance(self.parameter_type, Unset):
            parameter_type = UNSET
        elif isinstance(self.parameter_type, FunctionParameterInfoParameterTypeType0):
            parameter_type = self.parameter_type.value
        else:
            parameter_type = self.parameter_type

        type_interval_type: None | str | Unset
        if isinstance(self.type_interval_type, Unset):
            type_interval_type = UNSET
        else:
            type_interval_type = self.type_interval_type

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

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
                "position": position,
                "type_json": type_json,
                "type_name": type_name,
                "type_text": type_text,
            }
        )
        if comment is not UNSET:
            field_dict["comment"] = comment
        if parameter_default is not UNSET:
            field_dict["parameter_default"] = parameter_default
        if parameter_mode is not UNSET:
            field_dict["parameter_mode"] = parameter_mode
        if parameter_type is not UNSET:
            field_dict["parameter_type"] = parameter_type
        if type_interval_type is not UNSET:
            field_dict["type_interval_type"] = type_interval_type
        if type_precision is not UNSET:
            field_dict["type_precision"] = type_precision
        if type_scale is not UNSET:
            field_dict["type_scale"] = type_scale

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        position = d.pop("position")

        type_json = d.pop("type_json")

        type_name = d.pop("type_name")

        type_text = d.pop("type_text")

        def _parse_comment(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        comment = _parse_comment(d.pop("comment", UNSET))

        def _parse_parameter_default(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        parameter_default = _parse_parameter_default(d.pop("parameter_default", UNSET))

        def _parse_parameter_mode(data: object) -> Literal["IN"] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            parameter_mode_type_0 = cast(Literal["IN"], data)
            if parameter_mode_type_0 != "IN":
                raise ValueError(
                    f"parameter_mode_type_0 must match const 'IN', got '{parameter_mode_type_0}'"
                )
            return parameter_mode_type_0
            return cast(Literal["IN"] | None | Unset, data)

        parameter_mode = _parse_parameter_mode(d.pop("parameter_mode", UNSET))

        def _parse_parameter_type(
            data: object,
        ) -> FunctionParameterInfoParameterTypeType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                parameter_type_type_0 = FunctionParameterInfoParameterTypeType0(data)

                return parameter_type_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(FunctionParameterInfoParameterTypeType0 | None | Unset, data)

        parameter_type = _parse_parameter_type(d.pop("parameter_type", UNSET))

        def _parse_type_interval_type(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        type_interval_type = _parse_type_interval_type(
            d.pop("type_interval_type", UNSET)
        )

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

        function_parameter_info = cls(
            name=name,
            position=position,
            type_json=type_json,
            type_name=type_name,
            type_text=type_text,
            comment=comment,
            parameter_default=parameter_default,
            parameter_mode=parameter_mode,
            parameter_type=parameter_type,
            type_interval_type=type_interval_type,
            type_precision=type_precision,
            type_scale=type_scale,
        )

        return function_parameter_info
