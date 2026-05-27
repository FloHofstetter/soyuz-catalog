from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.function_parameter_info import FunctionParameterInfo


T = TypeVar("T", bound="FunctionParameterInfos")


@_attrs_define
class FunctionParameterInfos:
    """Wrapper around the ``parameters`` array of a function's params.

    The UC spec defines this wrapper object so that a function without
    parameters round-trips as ``{"parameters": []}`` instead of
    ``null``, and so that a future spec revision can add sibling
    metadata fields without breaking the wire shape. soyuz stores the
    wrapped array verbatim in a JSON column and reconstructs this
    model from it at response time.

        Attributes:
            parameters (list[FunctionParameterInfo] | Unset):
    """

    parameters: list[FunctionParameterInfo] | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.function_parameter_info import FunctionParameterInfo

        parameters: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.parameters, Unset):
            parameters = []
            for parameters_item_data in self.parameters:
                parameters_item = parameters_item_data.to_dict()
                parameters.append(parameters_item)

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if parameters is not UNSET:
            field_dict["parameters"] = parameters

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.function_parameter_info import FunctionParameterInfo

        d = dict(src_dict)
        _parameters = d.pop("parameters", UNSET)
        parameters: list[FunctionParameterInfo] | Unset = UNSET
        if _parameters is not UNSET:
            parameters = []
            for parameters_item_data in _parameters:
                parameters_item = FunctionParameterInfo.from_dict(parameters_item_data)

                parameters.append(parameters_item)

        function_parameter_infos = cls(
            parameters=parameters,
        )

        return function_parameter_infos
