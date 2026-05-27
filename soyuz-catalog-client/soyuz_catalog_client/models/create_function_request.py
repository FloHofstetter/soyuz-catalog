from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.create_function import CreateFunction


T = TypeVar("T", bound="CreateFunctionRequest")


@_attrs_define
class CreateFunctionRequest:
    """Outer wrapper for ``POST /functions``.

    The UC spec defines the create request as ``{"function_info":
    CreateFunction}`` rather than a flat body — an unusual nesting
    driven by the way the protobuf IDL is translated into JSON. We
    mirror the wrapper exactly so OpenAPI-generated clients keep
    working.

        Attributes:
            function_info (CreateFunction): Inner payload of ``CreateFunctionRequest`` — a full ``FunctionInfo`` body.

                The UC spec requires the client to send every structural field on
                create: ``input_params``, ``data_type``, ``full_data_type``,
                ``routine_body``, ``routine_definition``, ``parameter_style``,
                ``is_deterministic``, ``sql_data_access``, ``is_null_call``,
                ``security_type``, and ``specific_name``. ``return_params`` is
                optional because an EXTERNAL routine does not have one.
                ``extra="forbid"`` rejects unknown fields, same bug-fix policy
                as every other request body.

                ``properties`` is a free-form JSON-encoded string, not a dict, per
                the spec's *"JSON-serialized key-value pair map, encoded
                (escaped) as a string"* contract. soyuz stores it verbatim.
    """

    function_info: CreateFunction

    def to_dict(self) -> dict[str, Any]:
        from ..models.create_function import CreateFunction

        function_info = self.function_info.to_dict()

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "function_info": function_info,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.create_function import CreateFunction

        d = dict(src_dict)
        function_info = CreateFunction.from_dict(d.pop("function_info"))

        create_function_request = cls(
            function_info=function_info,
        )

        return create_function_request
