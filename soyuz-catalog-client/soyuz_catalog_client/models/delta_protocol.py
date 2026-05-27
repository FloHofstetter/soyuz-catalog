from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="DeltaProtocol")


@_attrs_define
class DeltaProtocol:
    """Delta table protocol version and feature flags.

    soyuz does not track per-table protocol versions — the project
    treats every table as readable by the standard Delta reader and
    writer versions — so on load responses this model is synthesised
    with a fixed default. On write paths (``createTable``,
    ``set-protocol`` update), the model is accepted from the client
    but its values are discarded; the response echoes the client's
    values so well-behaved clients see no drift within a single
    session. Documented in ADR-0009.

        Attributes:
            min_reader_version (int):
            min_writer_version (int):
            reader_features (list[str] | Unset):
            writer_features (list[str] | Unset):
    """

    min_reader_version: int
    min_writer_version: int
    reader_features: list[str] | Unset = UNSET
    writer_features: list[str] | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        min_reader_version = self.min_reader_version

        min_writer_version = self.min_writer_version

        reader_features: list[str] | Unset = UNSET
        if not isinstance(self.reader_features, Unset):
            reader_features = self.reader_features

        writer_features: list[str] | Unset = UNSET
        if not isinstance(self.writer_features, Unset):
            writer_features = self.writer_features

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "min-reader-version": min_reader_version,
                "min-writer-version": min_writer_version,
            }
        )
        if reader_features is not UNSET:
            field_dict["reader-features"] = reader_features
        if writer_features is not UNSET:
            field_dict["writer-features"] = writer_features

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        min_reader_version = d.pop("min-reader-version")

        min_writer_version = d.pop("min-writer-version")

        reader_features = cast(list[str], d.pop("reader-features", UNSET))

        writer_features = cast(list[str], d.pop("writer-features", UNSET))

        delta_protocol = cls(
            min_reader_version=min_reader_version,
            min_writer_version=min_writer_version,
            reader_features=reader_features,
            writer_features=writer_features,
        )

        return delta_protocol
