from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateVolume")


@_attrs_define
class UpdateVolume:
    """Request body for ``PATCH /volumes/{name}``.

    The UC spec is explicit that *only* ``new_name`` and ``comment`` may
    be updated on a volume — ``storage_location`` and ``volume_type`` are
    immutable (a managed volume cannot become external mid-life, and the
    underlying storage path cannot be moved without re-registering the
    volume). Volumes have no ``properties`` field on the wire, so there
    is no PATCH path for them either.

    ``extra="forbid"`` rejects unknown or read-only fields (including
    ``storage_location``, ``volume_type``, ``owner``, ``catalog_name``)
    with HTTP 422 instead of silently dropping them.

        Attributes:
            comment (None | str | Unset):
            new_name (None | str | Unset):
    """

    comment: None | str | Unset = UNSET
    new_name: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        comment: None | str | Unset
        if isinstance(self.comment, Unset):
            comment = UNSET
        else:
            comment = self.comment

        new_name: None | str | Unset
        if isinstance(self.new_name, Unset):
            new_name = UNSET
        else:
            new_name = self.new_name

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if comment is not UNSET:
            field_dict["comment"] = comment
        if new_name is not UNSET:
            field_dict["new_name"] = new_name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_comment(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        comment = _parse_comment(d.pop("comment", UNSET))

        def _parse_new_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        new_name = _parse_new_name(d.pop("new_name", UNSET))

        update_volume = cls(
            comment=comment,
            new_name=new_name,
        )

        return update_volume
