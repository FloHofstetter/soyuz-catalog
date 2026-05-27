from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.table_identifier_with_data_source_format import (
        TableIdentifierWithDataSourceFormat,
    )


T = TypeVar("T", bound="DeltaListTablesResponse")


@_attrs_define
class DeltaListTablesResponse:
    """Paginated ``listTables`` response.

    Shape matches the spec verbatim: a list of
    :class:`TableIdentifierWithDataSourceFormat` entries plus an
    optional ``next-page-token`` (absent on the last page). soyuz'
    existing keyset pagination is reused under the hood; see
    :func:`soyuz_catalog.services.table_service.list_tables`.

    Named ``DeltaListTablesResponse`` rather than ``ListTablesResponse``
    to avoid an OpenAPI schema-name collision with the unrelated
    :class:`soyuz_catalog.api.schemas.ListTablesResponse` (the UC
    ``/tables`` response) — openapi-python-client cannot disambiguate
    two schemas that share a leaf name.

        Attributes:
            identifiers (list[TableIdentifierWithDataSourceFormat] | Unset):
            next_page_token (None | str | Unset):
    """

    identifiers: list[TableIdentifierWithDataSourceFormat] | Unset = UNSET
    next_page_token: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.table_identifier_with_data_source_format import (
            TableIdentifierWithDataSourceFormat,
        )

        identifiers: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.identifiers, Unset):
            identifiers = []
            for identifiers_item_data in self.identifiers:
                identifiers_item = identifiers_item_data.to_dict()
                identifiers.append(identifiers_item)

        next_page_token: None | str | Unset
        if isinstance(self.next_page_token, Unset):
            next_page_token = UNSET
        else:
            next_page_token = self.next_page_token

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if identifiers is not UNSET:
            field_dict["identifiers"] = identifiers
        if next_page_token is not UNSET:
            field_dict["next-page-token"] = next_page_token

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.table_identifier_with_data_source_format import (
            TableIdentifierWithDataSourceFormat,
        )

        d = dict(src_dict)
        _identifiers = d.pop("identifiers", UNSET)
        identifiers: list[TableIdentifierWithDataSourceFormat] | Unset = UNSET
        if _identifiers is not UNSET:
            identifiers = []
            for identifiers_item_data in _identifiers:
                identifiers_item = TableIdentifierWithDataSourceFormat.from_dict(
                    identifiers_item_data
                )

                identifiers.append(identifiers_item)

        def _parse_next_page_token(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        next_page_token = _parse_next_page_token(d.pop("next-page-token", UNSET))

        delta_list_tables_response = cls(
            identifiers=identifiers,
            next_page_token=next_page_token,
        )

        return delta_list_tables_response
