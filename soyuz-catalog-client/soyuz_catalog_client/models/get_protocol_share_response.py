from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.protocol_share import ProtocolShare


T = TypeVar("T", bound="GetProtocolShareResponse")


@_attrs_define
class GetProtocolShareResponse:
    """Response shape for ``GET /delta-sharing/shares/{share}``.

    Attributes:
        share (ProtocolShare): One share as listed on the protocol surface.

            Only ``name`` and ``id`` are populated — the protocol marks
            ``displayName`` / ``comment`` / ``properties`` optional and soyuz
            keeps descriptive metadata on the management surface, where the
            data provider (not the recipient) reads it.
    """

    share: ProtocolShare
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.protocol_share import ProtocolShare

        share = self.share.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "share": share,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.protocol_share import ProtocolShare

        d = dict(src_dict)
        share = ProtocolShare.from_dict(d.pop("share"))

        get_protocol_share_response = cls(
            share=share,
        )

        get_protocol_share_response.additional_properties = d
        return get_protocol_share_response

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
