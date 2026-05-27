from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.connection_info import ConnectionInfo


T = TypeVar("T", bound="ListConnectionsResponse")


@_attrs_define
class ListConnectionsResponse:
    """Response shape for ``GET /connections``.

    Keyset pagination via ``next_page_token``; same shape as every
    other list response in this module.

        Attributes:
            connections (list[ConnectionInfo]):
            next_page_token (None | str | Unset):
    """

    connections: list[ConnectionInfo]
    next_page_token: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.connection_info import ConnectionInfo

        connections = []
        for connections_item_data in self.connections:
            connections_item = connections_item_data.to_dict()
            connections.append(connections_item)

        next_page_token: None | str | Unset
        if isinstance(self.next_page_token, Unset):
            next_page_token = UNSET
        else:
            next_page_token = self.next_page_token

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "connections": connections,
            }
        )
        if next_page_token is not UNSET:
            field_dict["next_page_token"] = next_page_token

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.connection_info import ConnectionInfo

        d = dict(src_dict)
        connections = []
        _connections = d.pop("connections")
        for connections_item_data in _connections:
            connections_item = ConnectionInfo.from_dict(connections_item_data)

            connections.append(connections_item)

        def _parse_next_page_token(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        next_page_token = _parse_next_page_token(d.pop("next_page_token", UNSET))

        list_connections_response = cls(
            connections=connections,
            next_page_token=next_page_token,
        )

        list_connections_response.additional_properties = d
        return list_connections_response

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
