from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.tag_change import TagChange


T = TypeVar("T", bound="UpdateTags")


@_attrs_define
class UpdateTags:
    """Request body for ``PATCH /tags/{securable_type}/{full_name}``.

    Like :class:`UpdatePermissions`, this shape is **not** replace-style: the
    client submits a list of additive/subtractive changes rather than a full
    desired state. This makes multi-writer workflows safe — two clients
    editing disjoint key sets do not clobber each other's tags — and matches
    the Databricks ``UpdateTags`` wire shape. See ``DIVERGENCES.md`` and
    ADR-0010 for the over-the-spec rationale.

        Attributes:
            changes (list[TagChange]):
    """

    changes: list[TagChange]

    def to_dict(self) -> dict[str, Any]:
        from ..models.tag_change import TagChange

        changes = []
        for changes_item_data in self.changes:
            changes_item = changes_item_data.to_dict()
            changes.append(changes_item)

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "changes": changes,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.tag_change import TagChange

        d = dict(src_dict)
        changes = []
        _changes = d.pop("changes")
        for changes_item_data in _changes:
            changes_item = TagChange.from_dict(changes_item_data)

            changes.append(changes_item)

        update_tags = cls(
            changes=changes,
        )

        return update_tags
