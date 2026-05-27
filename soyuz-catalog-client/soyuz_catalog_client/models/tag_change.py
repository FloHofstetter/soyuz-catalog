from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.tag_change_op import TagChangeOp
from ..types import UNSET, Unset

T = TypeVar("T", bound="TagChange")


@_attrs_define
class TagChange:
    """One element of an ``UpdateTags`` request body.

    The additive shape mirrors :class:`PermissionsChange`: instead of a full
    desired state the client submits a list of set/remove operations and the
    service applies them transactionally. ``op="set"`` upserts the key with
    the given ``value``; ``op="remove"`` deletes the key if present and is a
    no-op otherwise. ``value`` is ignored on remove (and must not be sent —
    ``extra="forbid"`` catches stray fields but the service also treats
    ``value`` on a remove as meaningless).

    Overlapping operations within a single PATCH resolve as *set wins*: the
    service applies removes first, then sets, so a ``(remove key, set key)``
    pair ends with the key present.

        Attributes:
            key (str):
            op (TagChangeOp):
            value (None | str | Unset):
    """

    key: str
    op: TagChangeOp
    value: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        key = self.key

        op = self.op.value

        value: None | str | Unset
        if isinstance(self.value, Unset):
            value = UNSET
        else:
            value = self.value

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "key": key,
                "op": op,
            }
        )
        if value is not UNSET:
            field_dict["value"] = value

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        key = d.pop("key")

        op = TagChangeOp(d.pop("op"))

        def _parse_value(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        value = _parse_value(d.pop("value", UNSET))

        tag_change = cls(
            key=key,
            op=op,
            value=value,
        )

        return tag_change
