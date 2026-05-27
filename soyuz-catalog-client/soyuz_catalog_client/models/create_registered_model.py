from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateRegisteredModel")


@_attrs_define
class CreateRegisteredModel:
    """Request body for ``POST /models``.

    The UC spec requires ``name``, ``catalog_name``, and
    ``schema_name``; ``comment`` is the only optional field.
    ``extra="forbid"`` rejects unknown fields — notably including
    ``storage_location``, which is a server-derived field on the
    response and must not be accepted on create.

        Attributes:
            catalog_name (str):
            name (str):
            schema_name (str):
            comment (None | str | Unset):
    """

    catalog_name: str
    name: str
    schema_name: str
    comment: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        catalog_name = self.catalog_name

        name = self.name

        schema_name = self.schema_name

        comment: None | str | Unset
        if isinstance(self.comment, Unset):
            comment = UNSET
        else:
            comment = self.comment

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "catalog_name": catalog_name,
                "name": name,
                "schema_name": schema_name,
            }
        )
        if comment is not UNSET:
            field_dict["comment"] = comment

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        catalog_name = d.pop("catalog_name")

        name = d.pop("name")

        schema_name = d.pop("schema_name")

        def _parse_comment(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        comment = _parse_comment(d.pop("comment", UNSET))

        create_registered_model = cls(
            catalog_name=catalog_name,
            name=name,
            schema_name=schema_name,
            comment=comment,
        )

        return create_registered_model
