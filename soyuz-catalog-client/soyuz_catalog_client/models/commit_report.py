from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.file_size_histogram import FileSizeHistogram


T = TypeVar("T", bound="CommitReport")


@_attrs_define
class CommitReport:
    """Commit-level metrics inside a ``reportMetrics`` request.

    Accepted but discarded. Every field is optional because Delta
    clients emit slightly different shapes depending on the commit
    type (data-only vs metadata vs mixed). soyuz stores nothing.

        Attributes:
            file_size_histogram (FileSizeHistogram | None | Unset):
            num_bytes_added (int | None | Unset):
            num_bytes_removed (int | None | Unset):
            num_files_added (int | None | Unset):
            num_files_removed (int | None | Unset):
            num_rows_inserted (int | None | Unset):
            num_rows_removed (int | None | Unset):
            num_rows_updated (int | None | Unset):
    """

    file_size_histogram: FileSizeHistogram | None | Unset = UNSET
    num_bytes_added: int | None | Unset = UNSET
    num_bytes_removed: int | None | Unset = UNSET
    num_files_added: int | None | Unset = UNSET
    num_files_removed: int | None | Unset = UNSET
    num_rows_inserted: int | None | Unset = UNSET
    num_rows_removed: int | None | Unset = UNSET
    num_rows_updated: int | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.file_size_histogram import FileSizeHistogram

        file_size_histogram: dict[str, Any] | None | Unset
        if isinstance(self.file_size_histogram, Unset):
            file_size_histogram = UNSET
        elif isinstance(self.file_size_histogram, FileSizeHistogram):
            file_size_histogram = self.file_size_histogram.to_dict()
        else:
            file_size_histogram = self.file_size_histogram

        num_bytes_added: int | None | Unset
        if isinstance(self.num_bytes_added, Unset):
            num_bytes_added = UNSET
        else:
            num_bytes_added = self.num_bytes_added

        num_bytes_removed: int | None | Unset
        if isinstance(self.num_bytes_removed, Unset):
            num_bytes_removed = UNSET
        else:
            num_bytes_removed = self.num_bytes_removed

        num_files_added: int | None | Unset
        if isinstance(self.num_files_added, Unset):
            num_files_added = UNSET
        else:
            num_files_added = self.num_files_added

        num_files_removed: int | None | Unset
        if isinstance(self.num_files_removed, Unset):
            num_files_removed = UNSET
        else:
            num_files_removed = self.num_files_removed

        num_rows_inserted: int | None | Unset
        if isinstance(self.num_rows_inserted, Unset):
            num_rows_inserted = UNSET
        else:
            num_rows_inserted = self.num_rows_inserted

        num_rows_removed: int | None | Unset
        if isinstance(self.num_rows_removed, Unset):
            num_rows_removed = UNSET
        else:
            num_rows_removed = self.num_rows_removed

        num_rows_updated: int | None | Unset
        if isinstance(self.num_rows_updated, Unset):
            num_rows_updated = UNSET
        else:
            num_rows_updated = self.num_rows_updated

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if file_size_histogram is not UNSET:
            field_dict["file-size-histogram"] = file_size_histogram
        if num_bytes_added is not UNSET:
            field_dict["num-bytes-added"] = num_bytes_added
        if num_bytes_removed is not UNSET:
            field_dict["num-bytes-removed"] = num_bytes_removed
        if num_files_added is not UNSET:
            field_dict["num-files-added"] = num_files_added
        if num_files_removed is not UNSET:
            field_dict["num-files-removed"] = num_files_removed
        if num_rows_inserted is not UNSET:
            field_dict["num-rows-inserted"] = num_rows_inserted
        if num_rows_removed is not UNSET:
            field_dict["num-rows-removed"] = num_rows_removed
        if num_rows_updated is not UNSET:
            field_dict["num-rows-updated"] = num_rows_updated

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.file_size_histogram import FileSizeHistogram

        d = dict(src_dict)

        def _parse_file_size_histogram(
            data: object,
        ) -> FileSizeHistogram | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                file_size_histogram_type_0 = FileSizeHistogram.from_dict(data)

                return file_size_histogram_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(FileSizeHistogram | None | Unset, data)

        file_size_histogram = _parse_file_size_histogram(
            d.pop("file-size-histogram", UNSET)
        )

        def _parse_num_bytes_added(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        num_bytes_added = _parse_num_bytes_added(d.pop("num-bytes-added", UNSET))

        def _parse_num_bytes_removed(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        num_bytes_removed = _parse_num_bytes_removed(d.pop("num-bytes-removed", UNSET))

        def _parse_num_files_added(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        num_files_added = _parse_num_files_added(d.pop("num-files-added", UNSET))

        def _parse_num_files_removed(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        num_files_removed = _parse_num_files_removed(d.pop("num-files-removed", UNSET))

        def _parse_num_rows_inserted(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        num_rows_inserted = _parse_num_rows_inserted(d.pop("num-rows-inserted", UNSET))

        def _parse_num_rows_removed(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        num_rows_removed = _parse_num_rows_removed(d.pop("num-rows-removed", UNSET))

        def _parse_num_rows_updated(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        num_rows_updated = _parse_num_rows_updated(d.pop("num-rows-updated", UNSET))

        commit_report = cls(
            file_size_histogram=file_size_histogram,
            num_bytes_added=num_bytes_added,
            num_bytes_removed=num_bytes_removed,
            num_files_added=num_files_added,
            num_files_removed=num_files_removed,
            num_rows_inserted=num_rows_inserted,
            num_rows_removed=num_rows_removed,
            num_rows_updated=num_rows_updated,
        )

        commit_report.additional_properties = d
        return commit_report

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
