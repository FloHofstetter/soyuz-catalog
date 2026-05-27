from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateExternalLocation")


@_attrs_define
class UpdateExternalLocation:
    """Request body for ``PATCH /external-locations/{name}``.

    Replace-style PATCH semantics, same as every other update
    endpoint. All fields are optional; ``credential_name`` triggers a
    re-resolution to ``credential_id`` at the service layer.
    ``extra="forbid"`` rejects read-only fields (``id``,
    ``credential_id``, ``created_at``, …).

        Attributes:
            comment (None | str | Unset):
            credential_name (None | str | Unset):
            new_name (None | str | Unset):
            owner (None | str | Unset):
            url (None | str | Unset):
    """

    comment: None | str | Unset = UNSET
    credential_name: None | str | Unset = UNSET
    new_name: None | str | Unset = UNSET
    owner: None | str | Unset = UNSET
    url: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        comment: None | str | Unset
        if isinstance(self.comment, Unset):
            comment = UNSET
        else:
            comment = self.comment

        credential_name: None | str | Unset
        if isinstance(self.credential_name, Unset):
            credential_name = UNSET
        else:
            credential_name = self.credential_name

        new_name: None | str | Unset
        if isinstance(self.new_name, Unset):
            new_name = UNSET
        else:
            new_name = self.new_name

        owner: None | str | Unset
        if isinstance(self.owner, Unset):
            owner = UNSET
        else:
            owner = self.owner

        url: None | str | Unset
        if isinstance(self.url, Unset):
            url = UNSET
        else:
            url = self.url

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if comment is not UNSET:
            field_dict["comment"] = comment
        if credential_name is not UNSET:
            field_dict["credential_name"] = credential_name
        if new_name is not UNSET:
            field_dict["new_name"] = new_name
        if owner is not UNSET:
            field_dict["owner"] = owner
        if url is not UNSET:
            field_dict["url"] = url

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

        def _parse_credential_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        credential_name = _parse_credential_name(d.pop("credential_name", UNSET))

        def _parse_new_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        new_name = _parse_new_name(d.pop("new_name", UNSET))

        def _parse_owner(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        owner = _parse_owner(d.pop("owner", UNSET))

        def _parse_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        url = _parse_url(d.pop("url", UNSET))

        update_external_location = cls(
            comment=comment,
            credential_name=credential_name,
            new_name=new_name,
            owner=owner,
            url=url,
        )

        return update_external_location
