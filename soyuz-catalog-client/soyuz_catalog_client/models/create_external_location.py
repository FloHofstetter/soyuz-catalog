from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateExternalLocation")


@_attrs_define
class CreateExternalLocation:
    """Request body for ``POST /external-locations``.

    The UC spec requires ``name``, ``url``, and ``credential_name`` on
    create. The service resolves ``credential_name`` to a persistent
    ``credential_id`` so a subsequent credential rename does not break
    the binding. ``extra="forbid"`` rejects unknown fields — including
    ``credential_id`` itself, which is a read-only server-derived
    field on the response and must not be accepted on create.

        Attributes:
            credential_name (str):
            name (str):
            url (str):
            comment (None | str | Unset):
    """

    credential_name: str
    name: str
    url: str
    comment: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        credential_name = self.credential_name

        name = self.name

        url = self.url

        comment: None | str | Unset
        if isinstance(self.comment, Unset):
            comment = UNSET
        else:
            comment = self.comment

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "credential_name": credential_name,
                "name": name,
                "url": url,
            }
        )
        if comment is not UNSET:
            field_dict["comment"] = comment

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        credential_name = d.pop("credential_name")

        name = d.pop("name")

        url = d.pop("url")

        def _parse_comment(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        comment = _parse_comment(d.pop("comment", UNSET))

        create_external_location = cls(
            credential_name=credential_name,
            name=name,
            url=url,
            comment=comment,
        )

        return create_external_location
