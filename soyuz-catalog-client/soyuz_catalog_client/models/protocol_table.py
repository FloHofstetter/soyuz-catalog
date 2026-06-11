from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ProtocolTable")


@_attrs_define
class ProtocolTable:
    """One table as exposed on the protocol surface.

    The wire field ``schema`` is carried by the Python attribute
    ``schema_name`` (serialisation alias) because pydantic reserves
    ``schema`` as a ``BaseModel`` attribute name. FastAPI serialises
    response models with ``by_alias=True``, so the alias is what
    recipients see. ``id`` is the share-object row id (stable per
    placement within the share) and ``shareId`` the share row id,
    both per the protocol's optional-identifier slots.

        Attributes:
            name (str):
            schema (str):
            share (str):
            id (None | str | Unset):
            share_id (None | str | Unset):
    """

    name: str
    schema: str
    share: str
    id: None | str | Unset = UNSET
    share_id: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        schema = self.schema

        share = self.share

        id: None | str | Unset
        if isinstance(self.id, Unset):
            id = UNSET
        else:
            id = self.id

        share_id: None | str | Unset
        if isinstance(self.share_id, Unset):
            share_id = UNSET
        else:
            share_id = self.share_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "schema": schema,
                "share": share,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if share_id is not UNSET:
            field_dict["shareId"] = share_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        schema = d.pop("schema")

        share = d.pop("share")

        def _parse_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        id = _parse_id(d.pop("id", UNSET))

        def _parse_share_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        share_id = _parse_share_id(d.pop("shareId", UNSET))

        protocol_table = cls(
            name=name,
            schema=schema,
            share=share,
            id=id,
            share_id=share_id,
        )

        protocol_table.additional_properties = d
        return protocol_table

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
