from __future__ import annotations

from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    BinaryIO,
    Generator,
    Literal,
    TextIO,
    TypeVar,
    cast,
)

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateSnapshotVersionUpdate")


@_attrs_define
class UpdateSnapshotVersionUpdate:
    """``update-metadata-snapshot-version`` — **rejected** as 501.

    External-tables-only post-commit-hook update; soyuz has no
    commit hook and no commit coordinator. ADR-0006 territory.

        Attributes:
            action (Literal['update-metadata-snapshot-version']):
            last_commit_timestamp_ms (int):
            last_commit_version (int):
    """

    action: Literal["update-metadata-snapshot-version"]
    last_commit_timestamp_ms: int
    last_commit_version: int

    def to_dict(self) -> dict[str, Any]:
        action = self.action

        last_commit_timestamp_ms = self.last_commit_timestamp_ms

        last_commit_version = self.last_commit_version

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "action": action,
                "last-commit-timestamp-ms": last_commit_timestamp_ms,
                "last-commit-version": last_commit_version,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        action = cast(Literal["update-metadata-snapshot-version"], d.pop("action"))
        if action != "update-metadata-snapshot-version":
            raise ValueError(
                f"action must match const 'update-metadata-snapshot-version', got '{action}'"
            )

        last_commit_timestamp_ms = d.pop("last-commit-timestamp-ms")

        last_commit_version = d.pop("last-commit-version")

        update_snapshot_version_update = cls(
            action=action,
            last_commit_timestamp_ms=last_commit_timestamp_ms,
            last_commit_version=last_commit_version,
        )

        return update_snapshot_version_update
