from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.tag_entry import TagEntry


T = TypeVar("T", bound="TagList")


@_attrs_define
class TagList:
    """Response shape for ``GET`` / ``PATCH /tags/{securable_type}/{full_name}``.

    Both endpoints return the same shape: ``GET`` returns the current tag
    set, ``PATCH`` returns the state after the submitted changes have been
    applied. Tags are sorted by ``key`` so two calls against an unchanged
    state return byte-identical bodies — a property tests rely on and a
    convenience for clients that diff responses.

        Attributes:
            tags (list[TagEntry] | Unset):
    """

    tags: list[TagEntry] | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.tag_entry import TagEntry

        tags: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.tags, Unset):
            tags = []
            for tags_item_data in self.tags:
                tags_item = tags_item_data.to_dict()
                tags.append(tags_item)

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if tags is not UNSET:
            field_dict["tags"] = tags

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.tag_entry import TagEntry

        d = dict(src_dict)
        _tags = d.pop("tags", UNSET)
        tags: list[TagEntry] | Unset = UNSET
        if _tags is not UNSET:
            tags = []
            for tags_item_data in _tags:
                tags_item = TagEntry.from_dict(tags_item_data)

                tags.append(tags_item)

        tag_list = cls(
            tags=tags,
        )

        return tag_list
