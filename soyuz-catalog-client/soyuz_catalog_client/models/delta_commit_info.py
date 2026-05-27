from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="DeltaCommitInfo")


@_attrs_define
class DeltaCommitInfo:
    """One unbackfilled Delta commit tracked by the coordinator.

    The five fields are required by the upstream spec and describe a
    staged commit file the Delta Kernel client has written to
    ``_delta_log/.tmp/<uuid>.json`` but has not yet published to
    ``_delta_log/NNNNN.json``. soyuz persists one row of these values
    in :class:`soyuz_catalog.models.DeltaUnbackfilledCommit` per
    ``(table_id, version)`` and returns them from ``GET /delta/preview/
    commits`` until the client signals a completed publish via a
    follow-up ``POST`` carrying ``latest_backfilled_version``.

        Attributes:
            file_modification_timestamp (int):
            file_name (str):
            file_size (int):
            timestamp (int):
            version (int):
    """

    file_modification_timestamp: int
    file_name: str
    file_size: int
    timestamp: int
    version: int

    def to_dict(self) -> dict[str, Any]:
        file_modification_timestamp = self.file_modification_timestamp

        file_name = self.file_name

        file_size = self.file_size

        timestamp = self.timestamp

        version = self.version

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "file_modification_timestamp": file_modification_timestamp,
                "file_name": file_name,
                "file_size": file_size,
                "timestamp": timestamp,
                "version": version,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        file_modification_timestamp = d.pop("file_modification_timestamp")

        file_name = d.pop("file_name")

        file_size = d.pop("file_size")

        timestamp = d.pop("timestamp")

        version = d.pop("version")

        delta_commit_info = cls(
            file_modification_timestamp=file_modification_timestamp,
            file_name=file_name,
            file_size=file_size,
            timestamp=timestamp,
            version=version,
        )

        return delta_commit_info
