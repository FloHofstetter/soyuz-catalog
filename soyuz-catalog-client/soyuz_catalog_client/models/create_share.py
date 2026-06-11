from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateShare")


@_attrs_define
class CreateShare:
    """Request body for ``POST /shares``.

    ``extra="forbid"`` rejects unknown fields (including ``id``,
    ``objects``, …) with 422 — tables enter a share through the
    dedicated ``POST /shares/{name}/objects`` endpoint, never inline
    on create.

        Attributes:
            name (str):
            comment (None | str | Unset):
            owner (None | str | Unset):
    """

    name: str
    comment: None | str | Unset = UNSET
    owner: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        comment: None | str | Unset
        if isinstance(self.comment, Unset):
            comment = UNSET
        else:
            comment = self.comment

        owner: None | str | Unset
        if isinstance(self.owner, Unset):
            owner = UNSET
        else:
            owner = self.owner

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
            }
        )
        if comment is not UNSET:
            field_dict["comment"] = comment
        if owner is not UNSET:
            field_dict["owner"] = owner

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        def _parse_comment(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        comment = _parse_comment(d.pop("comment", UNSET))

        def _parse_owner(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        owner = _parse_owner(d.pop("owner", UNSET))

        create_share = cls(
            name=name,
            comment=comment,
            owner=owner,
        )

        return create_share
