from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.table_info import TableInfo


T = TypeVar("T", bound="ListTablesResponse")


@_attrs_define
class ListTablesResponse:
    """Response shape for ``GET /tables``.

    ``next_page_token`` is the opaque keyset cursor — ``None`` on the
    last page, otherwise the encoded ``(created_at, id)`` tuple to
    feed back as ``page_token`` on the next call. See
    :mod:`soyuz_catalog.pagination` and ADR-0003.

        Attributes:
            tables (list[TableInfo]):
            next_page_token (None | str | Unset):
    """

    tables: list[TableInfo]
    next_page_token: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.table_info import TableInfo

        tables = []
        for tables_item_data in self.tables:
            tables_item = tables_item_data.to_dict()
            tables.append(tables_item)

        next_page_token: None | str | Unset
        if isinstance(self.next_page_token, Unset):
            next_page_token = UNSET
        else:
            next_page_token = self.next_page_token

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "tables": tables,
            }
        )
        if next_page_token is not UNSET:
            field_dict["next_page_token"] = next_page_token

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.table_info import TableInfo

        d = dict(src_dict)
        tables = []
        _tables = d.pop("tables")
        for tables_item_data in _tables:
            tables_item = TableInfo.from_dict(tables_item_data)

            tables.append(tables_item)

        def _parse_next_page_token(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        next_page_token = _parse_next_page_token(d.pop("next_page_token", UNSET))

        list_tables_response = cls(
            tables=tables,
            next_page_token=next_page_token,
        )

        list_tables_response.additional_properties = d
        return list_tables_response

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
