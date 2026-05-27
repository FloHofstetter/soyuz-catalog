from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="FileSizeHistogram")


@_attrs_define
class FileSizeHistogram:
    """Histogram payload inside a ``reportMetrics`` commit report.

    Accepted but discarded. Present only so the request body parses
    cleanly — no soyuz code reads any field.

        Attributes:
            file_counts (list[int]):
            sorted_bin_boundaries (list[int]):
            total_bytes (list[int]):
            commit_version (int | None | Unset):
    """

    file_counts: list[int]
    sorted_bin_boundaries: list[int]
    total_bytes: list[int]
    commit_version: int | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        file_counts = self.file_counts

        sorted_bin_boundaries = self.sorted_bin_boundaries

        total_bytes = self.total_bytes

        commit_version: int | None | Unset
        if isinstance(self.commit_version, Unset):
            commit_version = UNSET
        else:
            commit_version = self.commit_version

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "file-counts": file_counts,
                "sorted-bin-boundaries": sorted_bin_boundaries,
                "total-bytes": total_bytes,
            }
        )
        if commit_version is not UNSET:
            field_dict["commit-version"] = commit_version

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        file_counts = cast(list[int], d.pop("file-counts"))

        sorted_bin_boundaries = cast(list[int], d.pop("sorted-bin-boundaries"))

        total_bytes = cast(list[int], d.pop("total-bytes"))

        def _parse_commit_version(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        commit_version = _parse_commit_version(d.pop("commit-version", UNSET))

        file_size_histogram = cls(
            file_counts=file_counts,
            sorted_bin_boundaries=sorted_bin_boundaries,
            total_bytes=total_bytes,
            commit_version=commit_version,
        )

        return file_size_histogram
