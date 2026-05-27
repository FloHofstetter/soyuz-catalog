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

from ..models.function_info_routine_body_type_0 import FunctionInfoRoutineBodyType0
from ..models.function_info_sql_data_access_type_0 import FunctionInfoSqlDataAccessType0
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.function_info_routine_dependencies_type_0 import (
        FunctionInfoRoutineDependenciesType0,
    )
    from ..models.function_parameter_infos import FunctionParameterInfos


T = TypeVar("T", bound="FunctionInfo")


@_attrs_define
class FunctionInfo:
    """Response shape for a Unity Catalog function.

    ``full_name`` / ``catalog_name`` / ``schema_name`` are *not*
    stored columns — they are computed at response time from the
    live parent schema's (and its parent catalog's) names so that a
    rename of either parent propagates to every child function for
    free, same trick as :class:`TableInfo` and :class:`VolumeInfo`.

        Attributes:
            catalog_name (None | str | Unset):
            comment (None | str | Unset):
            created_at (int | None | Unset):
            created_by (None | str | Unset):
            data_type (None | str | Unset):
            external_language (None | str | Unset):
            full_data_type (None | str | Unset):
            full_name (None | str | Unset):
            function_id (None | str | Unset):
            input_params (FunctionParameterInfos | None | Unset):
            is_deterministic (bool | None | Unset):
            is_null_call (bool | None | Unset):
            name (None | str | Unset):
            owner (None | str | Unset):
            parameter_style (Literal['S'] | None | Unset):
            properties (None | str | Unset):
            return_params (FunctionParameterInfos | None | Unset):
            routine_body (FunctionInfoRoutineBodyType0 | None | Unset):
            routine_definition (None | str | Unset):
            routine_dependencies (FunctionInfoRoutineDependenciesType0 | None | Unset):
            schema_name (None | str | Unset):
            security_type (Literal['DEFINER'] | None | Unset):
            specific_name (None | str | Unset):
            sql_data_access (FunctionInfoSqlDataAccessType0 | None | Unset):
            updated_at (int | None | Unset):
            updated_by (None | str | Unset):
    """

    catalog_name: None | str | Unset = UNSET
    comment: None | str | Unset = UNSET
    created_at: int | None | Unset = UNSET
    created_by: None | str | Unset = UNSET
    data_type: None | str | Unset = UNSET
    external_language: None | str | Unset = UNSET
    full_data_type: None | str | Unset = UNSET
    full_name: None | str | Unset = UNSET
    function_id: None | str | Unset = UNSET
    input_params: FunctionParameterInfos | None | Unset = UNSET
    is_deterministic: bool | None | Unset = UNSET
    is_null_call: bool | None | Unset = UNSET
    name: None | str | Unset = UNSET
    owner: None | str | Unset = UNSET
    parameter_style: Literal["S"] | None | Unset = UNSET
    properties: None | str | Unset = UNSET
    return_params: FunctionParameterInfos | None | Unset = UNSET
    routine_body: FunctionInfoRoutineBodyType0 | None | Unset = UNSET
    routine_definition: None | str | Unset = UNSET
    routine_dependencies: FunctionInfoRoutineDependenciesType0 | None | Unset = UNSET
    schema_name: None | str | Unset = UNSET
    security_type: Literal["DEFINER"] | None | Unset = UNSET
    specific_name: None | str | Unset = UNSET
    sql_data_access: FunctionInfoSqlDataAccessType0 | None | Unset = UNSET
    updated_at: int | None | Unset = UNSET
    updated_by: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.function_info_routine_dependencies_type_0 import (
            FunctionInfoRoutineDependenciesType0,
        )
        from ..models.function_parameter_infos import FunctionParameterInfos

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

        data_type: None | str | Unset
        if isinstance(self.data_type, Unset):
            data_type = UNSET
        else:
            data_type = self.data_type

        external_language: None | str | Unset
        if isinstance(self.external_language, Unset):
            external_language = UNSET
        else:
            external_language = self.external_language

        full_data_type: None | str | Unset
        if isinstance(self.full_data_type, Unset):
            full_data_type = UNSET
        else:
            full_data_type = self.full_data_type

        full_name: None | str | Unset
        if isinstance(self.full_name, Unset):
            full_name = UNSET
        else:
            full_name = self.full_name

        function_id: None | str | Unset
        if isinstance(self.function_id, Unset):
            function_id = UNSET
        else:
            function_id = self.function_id

        input_params: dict[str, Any] | None | Unset
        if isinstance(self.input_params, Unset):
            input_params = UNSET
        elif isinstance(self.input_params, FunctionParameterInfos):
            input_params = self.input_params.to_dict()
        else:
            input_params = self.input_params

        is_deterministic: bool | None | Unset
        if isinstance(self.is_deterministic, Unset):
            is_deterministic = UNSET
        else:
            is_deterministic = self.is_deterministic

        is_null_call: bool | None | Unset
        if isinstance(self.is_null_call, Unset):
            is_null_call = UNSET
        else:
            is_null_call = self.is_null_call

        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        owner: None | str | Unset
        if isinstance(self.owner, Unset):
            owner = UNSET
        else:
            owner = self.owner

        parameter_style: Literal["S"] | None | Unset
        if isinstance(self.parameter_style, Unset):
            parameter_style = UNSET
        else:
            parameter_style = self.parameter_style

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

        routine_body: None | str | Unset
        if isinstance(self.routine_body, Unset):
            routine_body = UNSET
        elif isinstance(self.routine_body, FunctionInfoRoutineBodyType0):
            routine_body = self.routine_body.value
        else:
            routine_body = self.routine_body

        routine_definition: None | str | Unset
        if isinstance(self.routine_definition, Unset):
            routine_definition = UNSET
        else:
            routine_definition = self.routine_definition

        routine_dependencies: dict[str, Any] | None | Unset
        if isinstance(self.routine_dependencies, Unset):
            routine_dependencies = UNSET
        elif isinstance(
            self.routine_dependencies, FunctionInfoRoutineDependenciesType0
        ):
            routine_dependencies = self.routine_dependencies.to_dict()
        else:
            routine_dependencies = self.routine_dependencies

        schema_name: None | str | Unset
        if isinstance(self.schema_name, Unset):
            schema_name = UNSET
        else:
            schema_name = self.schema_name

        security_type: Literal["DEFINER"] | None | Unset
        if isinstance(self.security_type, Unset):
            security_type = UNSET
        else:
            security_type = self.security_type

        specific_name: None | str | Unset
        if isinstance(self.specific_name, Unset):
            specific_name = UNSET
        else:
            specific_name = self.specific_name

        sql_data_access: None | str | Unset
        if isinstance(self.sql_data_access, Unset):
            sql_data_access = UNSET
        elif isinstance(self.sql_data_access, FunctionInfoSqlDataAccessType0):
            sql_data_access = self.sql_data_access.value
        else:
            sql_data_access = self.sql_data_access

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
        if catalog_name is not UNSET:
            field_dict["catalog_name"] = catalog_name
        if comment is not UNSET:
            field_dict["comment"] = comment
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if created_by is not UNSET:
            field_dict["created_by"] = created_by
        if data_type is not UNSET:
            field_dict["data_type"] = data_type
        if external_language is not UNSET:
            field_dict["external_language"] = external_language
        if full_data_type is not UNSET:
            field_dict["full_data_type"] = full_data_type
        if full_name is not UNSET:
            field_dict["full_name"] = full_name
        if function_id is not UNSET:
            field_dict["function_id"] = function_id
        if input_params is not UNSET:
            field_dict["input_params"] = input_params
        if is_deterministic is not UNSET:
            field_dict["is_deterministic"] = is_deterministic
        if is_null_call is not UNSET:
            field_dict["is_null_call"] = is_null_call
        if name is not UNSET:
            field_dict["name"] = name
        if owner is not UNSET:
            field_dict["owner"] = owner
        if parameter_style is not UNSET:
            field_dict["parameter_style"] = parameter_style
        if properties is not UNSET:
            field_dict["properties"] = properties
        if return_params is not UNSET:
            field_dict["return_params"] = return_params
        if routine_body is not UNSET:
            field_dict["routine_body"] = routine_body
        if routine_definition is not UNSET:
            field_dict["routine_definition"] = routine_definition
        if routine_dependencies is not UNSET:
            field_dict["routine_dependencies"] = routine_dependencies
        if schema_name is not UNSET:
            field_dict["schema_name"] = schema_name
        if security_type is not UNSET:
            field_dict["security_type"] = security_type
        if specific_name is not UNSET:
            field_dict["specific_name"] = specific_name
        if sql_data_access is not UNSET:
            field_dict["sql_data_access"] = sql_data_access
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if updated_by is not UNSET:
            field_dict["updated_by"] = updated_by

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.function_info_routine_dependencies_type_0 import (
            FunctionInfoRoutineDependenciesType0,
        )
        from ..models.function_parameter_infos import FunctionParameterInfos

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

        def _parse_data_type(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        data_type = _parse_data_type(d.pop("data_type", UNSET))

        def _parse_external_language(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        external_language = _parse_external_language(d.pop("external_language", UNSET))

        def _parse_full_data_type(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        full_data_type = _parse_full_data_type(d.pop("full_data_type", UNSET))

        def _parse_full_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        full_name = _parse_full_name(d.pop("full_name", UNSET))

        def _parse_function_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        function_id = _parse_function_id(d.pop("function_id", UNSET))

        def _parse_input_params(data: object) -> FunctionParameterInfos | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                input_params_type_0 = FunctionParameterInfos.from_dict(data)

                return input_params_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(FunctionParameterInfos | None | Unset, data)

        input_params = _parse_input_params(d.pop("input_params", UNSET))

        def _parse_is_deterministic(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        is_deterministic = _parse_is_deterministic(d.pop("is_deterministic", UNSET))

        def _parse_is_null_call(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        is_null_call = _parse_is_null_call(d.pop("is_null_call", UNSET))

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_owner(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        owner = _parse_owner(d.pop("owner", UNSET))

        def _parse_parameter_style(data: object) -> Literal["S"] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            parameter_style_type_0 = cast(Literal["S"], data)
            if parameter_style_type_0 != "S":
                raise ValueError(
                    f"parameter_style_type_0 must match const 'S', got '{parameter_style_type_0}'"
                )
            return parameter_style_type_0
            return cast(Literal["S"] | None | Unset, data)

        parameter_style = _parse_parameter_style(d.pop("parameter_style", UNSET))

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

        def _parse_routine_body(
            data: object,
        ) -> FunctionInfoRoutineBodyType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                routine_body_type_0 = FunctionInfoRoutineBodyType0(data)

                return routine_body_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(FunctionInfoRoutineBodyType0 | None | Unset, data)

        routine_body = _parse_routine_body(d.pop("routine_body", UNSET))

        def _parse_routine_definition(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        routine_definition = _parse_routine_definition(
            d.pop("routine_definition", UNSET)
        )

        def _parse_routine_dependencies(
            data: object,
        ) -> FunctionInfoRoutineDependenciesType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                routine_dependencies_type_0 = (
                    FunctionInfoRoutineDependenciesType0.from_dict(data)
                )

                return routine_dependencies_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(FunctionInfoRoutineDependenciesType0 | None | Unset, data)

        routine_dependencies = _parse_routine_dependencies(
            d.pop("routine_dependencies", UNSET)
        )

        def _parse_schema_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        schema_name = _parse_schema_name(d.pop("schema_name", UNSET))

        def _parse_security_type(data: object) -> Literal["DEFINER"] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            security_type_type_0 = cast(Literal["DEFINER"], data)
            if security_type_type_0 != "DEFINER":
                raise ValueError(
                    f"security_type_type_0 must match const 'DEFINER', got '{security_type_type_0}'"
                )
            return security_type_type_0
            return cast(Literal["DEFINER"] | None | Unset, data)

        security_type = _parse_security_type(d.pop("security_type", UNSET))

        def _parse_specific_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        specific_name = _parse_specific_name(d.pop("specific_name", UNSET))

        def _parse_sql_data_access(
            data: object,
        ) -> FunctionInfoSqlDataAccessType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                sql_data_access_type_0 = FunctionInfoSqlDataAccessType0(data)

                return sql_data_access_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(FunctionInfoSqlDataAccessType0 | None | Unset, data)

        sql_data_access = _parse_sql_data_access(d.pop("sql_data_access", UNSET))

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

        function_info = cls(
            catalog_name=catalog_name,
            comment=comment,
            created_at=created_at,
            created_by=created_by,
            data_type=data_type,
            external_language=external_language,
            full_data_type=full_data_type,
            full_name=full_name,
            function_id=function_id,
            input_params=input_params,
            is_deterministic=is_deterministic,
            is_null_call=is_null_call,
            name=name,
            owner=owner,
            parameter_style=parameter_style,
            properties=properties,
            return_params=return_params,
            routine_body=routine_body,
            routine_definition=routine_definition,
            routine_dependencies=routine_dependencies,
            schema_name=schema_name,
            security_type=security_type,
            specific_name=specific_name,
            sql_data_access=sql_data_access,
            updated_at=updated_at,
            updated_by=updated_by,
        )

        function_info.additional_properties = d
        return function_info

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
