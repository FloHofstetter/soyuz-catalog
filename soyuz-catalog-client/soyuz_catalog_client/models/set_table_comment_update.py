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

T = TypeVar("T", bound="SetTableCommentUpdate")


@_attrs_define
class SetTableCommentUpdate:
    """Overwrite the table's comment in place.

    Empty string is accepted as "clear the comment" — soyuz stores
    it as ``NULL`` in that case, matching the ``UpdateTable``
    convention from the main UC API.

        Attributes:
            action (Literal['set-table-comment']):
            comment (str):
    """

    action: Literal["set-table-comment"]
    comment: str

    def to_dict(self) -> dict[str, Any]:
        action = self.action

        comment = self.comment

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "action": action,
                "comment": comment,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        action = cast(Literal["set-table-comment"], d.pop("action"))
        if action != "set-table-comment":
            raise ValueError(
                f"action must match const 'set-table-comment', got '{action}'"
            )

        comment = d.pop("comment")

        set_table_comment_update = cls(
            action=action,
            comment=comment,
        )

        return set_table_comment_update
