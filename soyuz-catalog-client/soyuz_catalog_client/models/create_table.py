from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.column_info import ColumnInfo
    from ..models.create_table_properties_type_0 import CreateTablePropertiesType0


T = TypeVar("T", bound="CreateTable")


@_attrs_define
class CreateTable:
    """Request body for ``POST /tables``.

    The UC spec requires ``name``, ``catalog_name``, ``schema_name``,
    ``table_type``, ``data_source_format``, ``columns``, and
    ``storage_location`` on create — there is no legitimate table without
    a physical storage location or a declared format, even for managed
    tables where the server will later rewrite it.

    ``extra="forbid"`` rejects unknown fields; the same policy applies to
    each element of ``columns`` via :class:`ColumnInfo`. There is no
    ``UpdateTable`` counterpart: the UC OpenAPI spec defines no
    ``PATCH /tables`` endpoint and soyuz registers no handler for it, so
    the route returns 405 Method Not Allowed (see ``DIVERGENCES.md``).

        Attributes:
            catalog_name (str):
            columns (list[ColumnInfo]):
            data_source_format (str):
            name (str):
            schema_name (str):
            storage_location (str):
            table_type (str):
            comment (None | str | Unset):
            properties (CreateTablePropertiesType0 | None | Unset):
    """

    catalog_name: str
    columns: list[ColumnInfo]
    data_source_format: str
    name: str
    schema_name: str
    storage_location: str
    table_type: str
    comment: None | str | Unset = UNSET
    properties: CreateTablePropertiesType0 | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.column_info import ColumnInfo
        from ..models.create_table_properties_type_0 import CreateTablePropertiesType0

        catalog_name = self.catalog_name

        columns = []
        for columns_item_data in self.columns:
            columns_item = columns_item_data.to_dict()
            columns.append(columns_item)

        data_source_format = self.data_source_format

        name = self.name

        schema_name = self.schema_name

        storage_location = self.storage_location

        table_type = self.table_type

        comment: None | str | Unset
        if isinstance(self.comment, Unset):
            comment = UNSET
        else:
            comment = self.comment

        properties: dict[str, Any] | None | Unset
        if isinstance(self.properties, Unset):
            properties = UNSET
        elif isinstance(self.properties, CreateTablePropertiesType0):
            properties = self.properties.to_dict()
        else:
            properties = self.properties

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "catalog_name": catalog_name,
                "columns": columns,
                "data_source_format": data_source_format,
                "name": name,
                "schema_name": schema_name,
                "storage_location": storage_location,
                "table_type": table_type,
            }
        )
        if comment is not UNSET:
            field_dict["comment"] = comment
        if properties is not UNSET:
            field_dict["properties"] = properties

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.column_info import ColumnInfo
        from ..models.create_table_properties_type_0 import CreateTablePropertiesType0

        d = dict(src_dict)
        catalog_name = d.pop("catalog_name")

        columns = []
        _columns = d.pop("columns")
        for columns_item_data in _columns:
            columns_item = ColumnInfo.from_dict(columns_item_data)

            columns.append(columns_item)

        data_source_format = d.pop("data_source_format")

        name = d.pop("name")

        schema_name = d.pop("schema_name")

        storage_location = d.pop("storage_location")

        table_type = d.pop("table_type")

        def _parse_comment(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        comment = _parse_comment(d.pop("comment", UNSET))

        def _parse_properties(
            data: object,
        ) -> CreateTablePropertiesType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                properties_type_0 = CreateTablePropertiesType0.from_dict(data)

                return properties_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(CreateTablePropertiesType0 | None | Unset, data)

        properties = _parse_properties(d.pop("properties", UNSET))

        create_table = cls(
            catalog_name=catalog_name,
            columns=columns,
            data_source_format=data_source_format,
            name=name,
            schema_name=schema_name,
            storage_location=storage_location,
            table_type=table_type,
            comment=comment,
            properties=properties,
        )

        return create_table
