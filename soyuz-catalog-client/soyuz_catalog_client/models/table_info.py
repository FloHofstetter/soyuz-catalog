from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.column_info import ColumnInfo
    from ..models.table_constraint import TableConstraint
    from ..models.table_info_properties_type_0 import TableInfoPropertiesType0


T = TypeVar("T", bound="TableInfo")


@_attrs_define
class TableInfo:
    """Response shape for a Unity Catalog table.

    ``full_name`` is computed from the live parent catalog and schema names
    at response time — never stored — so a rename of either parent
    propagates to every child table for free. ``columns`` is always
    populated from the live ``table_columns`` rows, ordered by ``position``
    via the ORM relationship's ``order_by``.

    ``table_constraints`` (ADR-0012) is the ordered list of
    declared constraints; it is populated from live ``table_constraints``
    rows at response time and is ``None`` (not ``[]``) when the table has
    no declared constraints — matches how other optional nested fields
    behave and keeps existing fixtures stable.

        Attributes:
            catalog_name (None | str | Unset):
            columns (list[ColumnInfo] | None | Unset):
            comment (None | str | Unset):
            created_at (int | None | Unset):
            created_by (None | str | Unset):
            data_source_format (None | str | Unset):
            full_name (None | str | Unset):
            name (None | str | Unset):
            owner (None | str | Unset):
            properties (None | TableInfoPropertiesType0 | Unset):
            schema_name (None | str | Unset):
            storage_location (None | str | Unset):
            table_constraints (list[TableConstraint] | None | Unset):
            table_id (None | str | Unset):
            table_type (None | str | Unset):
            updated_at (int | None | Unset):
            updated_by (None | str | Unset):
    """

    catalog_name: None | str | Unset = UNSET
    columns: list[ColumnInfo] | None | Unset = UNSET
    comment: None | str | Unset = UNSET
    created_at: int | None | Unset = UNSET
    created_by: None | str | Unset = UNSET
    data_source_format: None | str | Unset = UNSET
    full_name: None | str | Unset = UNSET
    name: None | str | Unset = UNSET
    owner: None | str | Unset = UNSET
    properties: None | TableInfoPropertiesType0 | Unset = UNSET
    schema_name: None | str | Unset = UNSET
    storage_location: None | str | Unset = UNSET
    table_constraints: list[TableConstraint] | None | Unset = UNSET
    table_id: None | str | Unset = UNSET
    table_type: None | str | Unset = UNSET
    updated_at: int | None | Unset = UNSET
    updated_by: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.column_info import ColumnInfo
        from ..models.table_constraint import TableConstraint
        from ..models.table_info_properties_type_0 import TableInfoPropertiesType0

        catalog_name: None | str | Unset
        if isinstance(self.catalog_name, Unset):
            catalog_name = UNSET
        else:
            catalog_name = self.catalog_name

        columns: list[dict[str, Any]] | None | Unset
        if isinstance(self.columns, Unset):
            columns = UNSET
        elif isinstance(self.columns, list):
            columns = []
            for columns_type_0_item_data in self.columns:
                columns_type_0_item = columns_type_0_item_data.to_dict()
                columns.append(columns_type_0_item)

        else:
            columns = self.columns

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

        data_source_format: None | str | Unset
        if isinstance(self.data_source_format, Unset):
            data_source_format = UNSET
        else:
            data_source_format = self.data_source_format

        full_name: None | str | Unset
        if isinstance(self.full_name, Unset):
            full_name = UNSET
        else:
            full_name = self.full_name

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

        properties: dict[str, Any] | None | Unset
        if isinstance(self.properties, Unset):
            properties = UNSET
        elif isinstance(self.properties, TableInfoPropertiesType0):
            properties = self.properties.to_dict()
        else:
            properties = self.properties

        schema_name: None | str | Unset
        if isinstance(self.schema_name, Unset):
            schema_name = UNSET
        else:
            schema_name = self.schema_name

        storage_location: None | str | Unset
        if isinstance(self.storage_location, Unset):
            storage_location = UNSET
        else:
            storage_location = self.storage_location

        table_constraints: list[dict[str, Any]] | None | Unset
        if isinstance(self.table_constraints, Unset):
            table_constraints = UNSET
        elif isinstance(self.table_constraints, list):
            table_constraints = []
            for table_constraints_type_0_item_data in self.table_constraints:
                table_constraints_type_0_item = (
                    table_constraints_type_0_item_data.to_dict()
                )
                table_constraints.append(table_constraints_type_0_item)

        else:
            table_constraints = self.table_constraints

        table_id: None | str | Unset
        if isinstance(self.table_id, Unset):
            table_id = UNSET
        else:
            table_id = self.table_id

        table_type: None | str | Unset
        if isinstance(self.table_type, Unset):
            table_type = UNSET
        else:
            table_type = self.table_type

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
        if columns is not UNSET:
            field_dict["columns"] = columns
        if comment is not UNSET:
            field_dict["comment"] = comment
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if created_by is not UNSET:
            field_dict["created_by"] = created_by
        if data_source_format is not UNSET:
            field_dict["data_source_format"] = data_source_format
        if full_name is not UNSET:
            field_dict["full_name"] = full_name
        if name is not UNSET:
            field_dict["name"] = name
        if owner is not UNSET:
            field_dict["owner"] = owner
        if properties is not UNSET:
            field_dict["properties"] = properties
        if schema_name is not UNSET:
            field_dict["schema_name"] = schema_name
        if storage_location is not UNSET:
            field_dict["storage_location"] = storage_location
        if table_constraints is not UNSET:
            field_dict["table_constraints"] = table_constraints
        if table_id is not UNSET:
            field_dict["table_id"] = table_id
        if table_type is not UNSET:
            field_dict["table_type"] = table_type
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if updated_by is not UNSET:
            field_dict["updated_by"] = updated_by

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.column_info import ColumnInfo
        from ..models.table_constraint import TableConstraint
        from ..models.table_info_properties_type_0 import TableInfoPropertiesType0

        d = dict(src_dict)

        def _parse_catalog_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        catalog_name = _parse_catalog_name(d.pop("catalog_name", UNSET))

        def _parse_columns(data: object) -> list[ColumnInfo] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                columns_type_0 = []
                _columns_type_0 = data
                for columns_type_0_item_data in _columns_type_0:
                    columns_type_0_item = ColumnInfo.from_dict(columns_type_0_item_data)

                    columns_type_0.append(columns_type_0_item)

                return columns_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[ColumnInfo] | None | Unset, data)

        columns = _parse_columns(d.pop("columns", UNSET))

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

        def _parse_data_source_format(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        data_source_format = _parse_data_source_format(
            d.pop("data_source_format", UNSET)
        )

        def _parse_full_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        full_name = _parse_full_name(d.pop("full_name", UNSET))

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

        def _parse_properties(data: object) -> None | TableInfoPropertiesType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                properties_type_0 = TableInfoPropertiesType0.from_dict(data)

                return properties_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | TableInfoPropertiesType0 | Unset, data)

        properties = _parse_properties(d.pop("properties", UNSET))

        def _parse_schema_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        schema_name = _parse_schema_name(d.pop("schema_name", UNSET))

        def _parse_storage_location(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        storage_location = _parse_storage_location(d.pop("storage_location", UNSET))

        def _parse_table_constraints(
            data: object,
        ) -> list[TableConstraint] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                table_constraints_type_0 = []
                _table_constraints_type_0 = data
                for table_constraints_type_0_item_data in _table_constraints_type_0:
                    table_constraints_type_0_item = TableConstraint.from_dict(
                        table_constraints_type_0_item_data
                    )

                    table_constraints_type_0.append(table_constraints_type_0_item)

                return table_constraints_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[TableConstraint] | None | Unset, data)

        table_constraints = _parse_table_constraints(d.pop("table_constraints", UNSET))

        def _parse_table_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        table_id = _parse_table_id(d.pop("table_id", UNSET))

        def _parse_table_type(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        table_type = _parse_table_type(d.pop("table_type", UNSET))

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

        table_info = cls(
            catalog_name=catalog_name,
            columns=columns,
            comment=comment,
            created_at=created_at,
            created_by=created_by,
            data_source_format=data_source_format,
            full_name=full_name,
            name=name,
            owner=owner,
            properties=properties,
            schema_name=schema_name,
            storage_location=storage_location,
            table_constraints=table_constraints,
            table_id=table_id,
            table_type=table_type,
            updated_at=updated_at,
            updated_by=updated_by,
        )

        table_info.additional_properties = d
        return table_info

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
