from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="SuggestedProtocol")


@_attrs_define
class SuggestedProtocol:
    """Suggested Delta features a client should enable if supported.

    soyuz advertises none — it does not have an opinion about which
    features a staging-table writer *should* use, only a minimum it
    *must* satisfy, which is carried by :class:`DeltaProtocol` on the
    ``required_protocol`` field.

        Attributes:
            reader_features (list[str] | Unset):
            writer_features (list[str] | Unset):
    """

    reader_features: list[str] | Unset = UNSET
    writer_features: list[str] | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        reader_features: list[str] | Unset = UNSET
        if not isinstance(self.reader_features, Unset):
            reader_features = self.reader_features

        writer_features: list[str] | Unset = UNSET
        if not isinstance(self.writer_features, Unset):
            writer_features = self.writer_features

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if reader_features is not UNSET:
            field_dict["reader-features"] = reader_features
        if writer_features is not UNSET:
            field_dict["writer-features"] = writer_features

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        reader_features = cast(list[str], d.pop("reader-features", UNSET))

        writer_features = cast(list[str], d.pop("writer-features", UNSET))

        suggested_protocol = cls(
            reader_features=reader_features,
            writer_features=writer_features,
        )

        return suggested_protocol
