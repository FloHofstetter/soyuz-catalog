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

T = TypeVar("T", bound="SetLatestBackfilledVersionUpdate")


@_attrs_define
class SetLatestBackfilledVersionUpdate:
    """``set-latest-backfilled-version`` — **rejected** as 501.

    Same posture as :class:`AddCommitUpdate`: this is
    commit-coordinator territory and soyuz rejects the whole class
    with a dedicated error code. ADR-0006.

        Attributes:
            action (Literal['set-latest-backfilled-version']):
            latest_published_version (int):
    """

    action: Literal["set-latest-backfilled-version"]
    latest_published_version: int

    def to_dict(self) -> dict[str, Any]:
        action = self.action

        latest_published_version = self.latest_published_version

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "action": action,
                "latest-published-version": latest_published_version,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        action = cast(Literal["set-latest-backfilled-version"], d.pop("action"))
        if action != "set-latest-backfilled-version":
            raise ValueError(
                f"action must match const 'set-latest-backfilled-version', got '{action}'"
            )

        latest_published_version = d.pop("latest-published-version")

        set_latest_backfilled_version_update = cls(
            action=action,
            latest_published_version=latest_published_version,
        )

        return set_latest_backfilled_version_update
