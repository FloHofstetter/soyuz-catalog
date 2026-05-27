from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateModelVersion")


@_attrs_define
class UpdateModelVersion:
    """Request body for ``PATCH /models/{full_name}/versions/{version}``.

    The UC-OSS proto's ``UpdateModelVersion`` message duplicates the
    URL parameters (``full_name``, ``version``) in the body
    (`unity_catalog_oss_messages.proto:215-228`) — MLflow's UC-OSS
    client sends them on every request, so we accept and ignore them
    (URL parameters are the source of truth). The only mutable field
    is ``comment``: ``source``, ``run_id``, and ``status`` are
    immutable after registration. ``extra="forbid"`` still rejects
    truly unknown fields with 422.

        Attributes:
            comment (None | str | Unset):
            full_name (None | str | Unset):
            version (int | None | Unset):
    """

    comment: None | str | Unset = UNSET
    full_name: None | str | Unset = UNSET
    version: int | None | Unset = UNSET

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

        version: int | None | Unset
        if isinstance(self.version, Unset):
            version = UNSET
        else:
            version = self.version

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if comment is not UNSET:
            field_dict["comment"] = comment
        if full_name is not UNSET:
            field_dict["full_name"] = full_name
        if version is not UNSET:
            field_dict["version"] = version

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

        def _parse_version(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        version = _parse_version(d.pop("version", UNSET))

        update_model_version = cls(
            comment=comment,
            full_name=full_name,
            version=version,
        )

        return update_model_version
