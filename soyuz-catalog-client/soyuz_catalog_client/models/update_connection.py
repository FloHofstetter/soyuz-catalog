from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.update_connection_options_type_0 import UpdateConnectionOptionsType0


T = TypeVar("T", bound="UpdateConnection")


@_attrs_define
class UpdateConnection:
    """Request body for ``PATCH /connections/{name}``.

    Replace-style PATCH semantics driven by ``model_fields_set`` in
    the service layer. ``connection_type`` is **not** exposed: flipping
    a live connection from Postgres to Snowflake would orphan every
    bound foreign catalog's ``options`` dictionary, so it is frozen at
    create time. ``new_name`` renames propagate to every bound foreign
    catalog automatically because the catalog row stores
    ``connection_id`` and reconstructs ``connection_name`` at response
    time.

    ``extra="forbid"`` rejects read-only fields (``id``, ``created_at``,
    …) with 422.

        Attributes:
            comment (None | str | Unset):
            new_name (None | str | Unset):
            options (None | Unset | UpdateConnectionOptionsType0):
            owner (None | str | Unset):
            read_only (bool | None | Unset):
    """

    comment: None | str | Unset = UNSET
    new_name: None | str | Unset = UNSET
    options: None | Unset | UpdateConnectionOptionsType0 = UNSET
    owner: None | str | Unset = UNSET
    read_only: bool | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.update_connection_options_type_0 import (
            UpdateConnectionOptionsType0,
        )

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

        options: dict[str, Any] | None | Unset
        if isinstance(self.options, Unset):
            options = UNSET
        elif isinstance(self.options, UpdateConnectionOptionsType0):
            options = self.options.to_dict()
        else:
            options = self.options

        owner: None | str | Unset
        if isinstance(self.owner, Unset):
            owner = UNSET
        else:
            owner = self.owner

        read_only: bool | None | Unset
        if isinstance(self.read_only, Unset):
            read_only = UNSET
        else:
            read_only = self.read_only

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if comment is not UNSET:
            field_dict["comment"] = comment
        if new_name is not UNSET:
            field_dict["new_name"] = new_name
        if options is not UNSET:
            field_dict["options"] = options
        if owner is not UNSET:
            field_dict["owner"] = owner
        if read_only is not UNSET:
            field_dict["read_only"] = read_only

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.update_connection_options_type_0 import (
            UpdateConnectionOptionsType0,
        )

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

        def _parse_options(data: object) -> None | Unset | UpdateConnectionOptionsType0:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                options_type_0 = UpdateConnectionOptionsType0.from_dict(data)

                return options_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UpdateConnectionOptionsType0, data)

        options = _parse_options(d.pop("options", UNSET))

        def _parse_owner(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        owner = _parse_owner(d.pop("owner", UNSET))

        def _parse_read_only(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        read_only = _parse_read_only(d.pop("read_only", UNSET))

        update_connection = cls(
            comment=comment,
            new_name=new_name,
            options=options,
            owner=owner,
            read_only=read_only,
        )

        return update_connection
