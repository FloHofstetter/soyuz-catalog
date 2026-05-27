from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CatalogConfig")


@_attrs_define
class CatalogConfig:
    """Response body for ``GET /v1/config``.

    Advertises the list of endpoint paths soyuz implements under
    the Delta surface and the negotiated protocol version. soyuz
    has exactly one implementation (``"1.0"``) so the
    ``protocol-versions`` query parameter does not branch behaviour.

        Attributes:
            endpoints (list[str]):
            protocol_version (str):
    """

    endpoints: list[str]
    protocol_version: str

    def to_dict(self) -> dict[str, Any]:
        endpoints = self.endpoints

        protocol_version = self.protocol_version

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "endpoints": endpoints,
                "protocol-version": protocol_version,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        endpoints = cast(list[str], d.pop("endpoints"))

        protocol_version = d.pop("protocol-version")

        catalog_config = cls(
            endpoints=endpoints,
            protocol_version=protocol_version,
        )

        return catalog_config
