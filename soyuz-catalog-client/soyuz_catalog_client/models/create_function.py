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

from ..models.create_function_routine_body import CreateFunctionRoutineBody
from ..models.create_function_sql_data_access import CreateFunctionSqlDataAccess
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.create_function_routine_dependencies_type_0 import (
        CreateFunctionRoutineDependenciesType0,
    )
    from ..models.function_parameter_infos import FunctionParameterInfos


T = TypeVar("T", bound="CreateFunction")


@_attrs_define
class CreateFunction:
    """Inner payload of ``CreateFunctionRequest`` — a full ``FunctionInfo`` body.

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

        Attributes:
            catalog_name (str):
            data_type (str):
            full_data_type (str):
            input_params (FunctionParameterInfos): Wrapper around the ``parameters`` array of a function's params.

                The UC spec defines this wrapper object so that a function without
                parameters round-trips as ``{"parameters": []}`` instead of
                ``null``, and so that a future spec revision can add sibling
                metadata fields without breaking the wire shape. soyuz stores the
                wrapped array verbatim in a JSON column and reconstructs this
                model from it at response time.
            is_deterministic (bool):
            is_null_call (bool):
            name (str):
            parameter_style (Literal['S']):
            routine_body (CreateFunctionRoutineBody):
            routine_definition (str):
            schema_name (str):
            security_type (Literal['DEFINER']):
            specific_name (str):
            sql_data_access (CreateFunctionSqlDataAccess):
            comment (None | str | Unset):
            external_language (None | str | Unset):
            properties (None | str | Unset):
            return_params (FunctionParameterInfos | None | Unset):
            routine_dependencies (CreateFunctionRoutineDependenciesType0 | None | Unset):
    """

    catalog_name: str
    data_type: str
    full_data_type: str
    input_params: FunctionParameterInfos
    is_deterministic: bool
    is_null_call: bool
    name: str
    parameter_style: Literal["S"]
    routine_body: CreateFunctionRoutineBody
    routine_definition: str
    schema_name: str
    security_type: Literal["DEFINER"]
    specific_name: str
    sql_data_access: CreateFunctionSqlDataAccess
    comment: None | str | Unset = UNSET
    external_language: None | str | Unset = UNSET
    properties: None | str | Unset = UNSET
    return_params: FunctionParameterInfos | None | Unset = UNSET
    routine_dependencies: CreateFunctionRoutineDependenciesType0 | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.create_function_routine_dependencies_type_0 import (
            CreateFunctionRoutineDependenciesType0,
        )
        from ..models.function_parameter_infos import FunctionParameterInfos

        catalog_name = self.catalog_name

        data_type = self.data_type

        full_data_type = self.full_data_type

        input_params = self.input_params.to_dict()

        is_deterministic = self.is_deterministic

        is_null_call = self.is_null_call

        name = self.name

        parameter_style = self.parameter_style

        routine_body = self.routine_body.value

        routine_definition = self.routine_definition

        schema_name = self.schema_name

        security_type = self.security_type

        specific_name = self.specific_name

        sql_data_access = self.sql_data_access.value

        comment: None | str | Unset
        if isinstance(self.comment, Unset):
            comment = UNSET
        else:
            comment = self.comment

        external_language: None | str | Unset
        if isinstance(self.external_language, Unset):
            external_language = UNSET
        else:
            external_language = self.external_language

        properties: None | str | Unset
        if isinstance(self.properties, Unset):
            properties = UNSET
        else:
            properties = self.properties

        return_params: dict[str, Any] | None | Unset
        if isinstance(self.return_params, Unset):
            return_params = UNSET
        elif isinstance(self.return_params, FunctionParameterInfos):
            return_params = self.return_params.to_dict()
        else:
            return_params = self.return_params

        routine_dependencies: dict[str, Any] | None | Unset
        if isinstance(self.routine_dependencies, Unset):
            routine_dependencies = UNSET
        elif isinstance(
            self.routine_dependencies, CreateFunctionRoutineDependenciesType0
        ):
            routine_dependencies = self.routine_dependencies.to_dict()
        else:
            routine_dependencies = self.routine_dependencies

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "catalog_name": catalog_name,
                "data_type": data_type,
                "full_data_type": full_data_type,
                "input_params": input_params,
                "is_deterministic": is_deterministic,
                "is_null_call": is_null_call,
                "name": name,
                "parameter_style": parameter_style,
                "routine_body": routine_body,
                "routine_definition": routine_definition,
                "schema_name": schema_name,
                "security_type": security_type,
                "specific_name": specific_name,
                "sql_data_access": sql_data_access,
            }
        )
        if comment is not UNSET:
            field_dict["comment"] = comment
        if external_language is not UNSET:
            field_dict["external_language"] = external_language
        if properties is not UNSET:
            field_dict["properties"] = properties
        if return_params is not UNSET:
            field_dict["return_params"] = return_params
        if routine_dependencies is not UNSET:
            field_dict["routine_dependencies"] = routine_dependencies

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.create_function_routine_dependencies_type_0 import (
            CreateFunctionRoutineDependenciesType0,
        )
        from ..models.function_parameter_infos import FunctionParameterInfos

        d = dict(src_dict)
        catalog_name = d.pop("catalog_name")

        data_type = d.pop("data_type")

        full_data_type = d.pop("full_data_type")

        input_params = FunctionParameterInfos.from_dict(d.pop("input_params"))

        is_deterministic = d.pop("is_deterministic")

        is_null_call = d.pop("is_null_call")

        name = d.pop("name")

        parameter_style = cast(Literal["S"], d.pop("parameter_style"))
        if parameter_style != "S":
            raise ValueError(
                f"parameter_style must match const 'S', got '{parameter_style}'"
            )

        routine_body = CreateFunctionRoutineBody(d.pop("routine_body"))

        routine_definition = d.pop("routine_definition")

        schema_name = d.pop("schema_name")

        security_type = cast(Literal["DEFINER"], d.pop("security_type"))
        if security_type != "DEFINER":
            raise ValueError(
                f"security_type must match const 'DEFINER', got '{security_type}'"
            )

        specific_name = d.pop("specific_name")

        sql_data_access = CreateFunctionSqlDataAccess(d.pop("sql_data_access"))

        def _parse_comment(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        comment = _parse_comment(d.pop("comment", UNSET))

        def _parse_external_language(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        external_language = _parse_external_language(d.pop("external_language", UNSET))

        def _parse_properties(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        properties = _parse_properties(d.pop("properties", UNSET))

        def _parse_return_params(data: object) -> FunctionParameterInfos | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                return_params_type_0 = FunctionParameterInfos.from_dict(data)

                return return_params_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(FunctionParameterInfos | None | Unset, data)

        return_params = _parse_return_params(d.pop("return_params", UNSET))

        def _parse_routine_dependencies(
            data: object,
        ) -> CreateFunctionRoutineDependenciesType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                routine_dependencies_type_0 = (
                    CreateFunctionRoutineDependenciesType0.from_dict(data)
                )

                return routine_dependencies_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(CreateFunctionRoutineDependenciesType0 | None | Unset, data)

        routine_dependencies = _parse_routine_dependencies(
            d.pop("routine_dependencies", UNSET)
        )

        create_function = cls(
            catalog_name=catalog_name,
            data_type=data_type,
            full_data_type=full_data_type,
            input_params=input_params,
            is_deterministic=is_deterministic,
            is_null_call=is_null_call,
            name=name,
            parameter_style=parameter_style,
            routine_body=routine_body,
            routine_definition=routine_definition,
            schema_name=schema_name,
            security_type=security_type,
            specific_name=specific_name,
            sql_data_access=sql_data_access,
            comment=comment,
            external_language=external_language,
            properties=properties,
            return_params=return_params,
            routine_dependencies=routine_dependencies,
        )

        return create_function
