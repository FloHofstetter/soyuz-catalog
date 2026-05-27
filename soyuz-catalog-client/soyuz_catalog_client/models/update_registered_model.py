from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateRegisteredModel")


@_attrs_define
class UpdateRegisteredModel:
    """Request body for ``PATCH /models/{full_name}``.

    Replace-style PATCH semantics driven by ``model_fields_set`` in
    the service layer. The UC-OSS proto's ``UpdateRegisteredModel``
    message includes ``full_name`` as a body field that duplicates
    the URL path parameter (`unity_catalog_oss_messages.proto:82-95`)
    — MLflow's UC-OSS client sends it on every request, so we accept
    it and ignore it (the URL is the source of truth). ``extra="forbid"``
    still rejects truly unknown fields (storage_location, owner, …)
    with HTTP 422.

        Attributes:
            comment (None | str | Unset):
            full_name (None | str | Unset):
            new_name (None | str | Unset):
    """

    comment: None | str | Unset = UNSET
    full_name: None | str | Unset = UNSET
    new_name: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        comment: None | str | Unset
        if isinstance(self.comment, Unset):
            comment = UNSET
        else:
            comment = self.comment

        full_name: None | str | Unset
        if isinstance(self.full_name, Unset):
            full_name = UNSET
        else:
            full_name = self.full_name

        new_name: None | str | Unset
        if isinstance(self.new_name, Unset):
            new_name = UNSET
        else:
            new_name = self.new_name

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if comment is not UNSET:
            field_dict["comment"] = comment
        if full_name is not UNSET:
            field_dict["full_name"] = full_name
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

        def _parse_full_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        full_name = _parse_full_name(d.pop("full_name", UNSET))

        def _parse_new_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        new_name = _parse_new_name(d.pop("new_name", UNSET))

        update_registered_model = cls(
            comment=comment,
            full_name=full_name,
            new_name=new_name,
        )

        return update_registered_model
