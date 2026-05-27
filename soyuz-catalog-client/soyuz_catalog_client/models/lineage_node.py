from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="LineageNode")


@_attrs_define
class LineageNode:
    """One node in a lineage traversal response.

    ``securable_id`` is always the opaque row id. ``full_name`` is
    reconstructed at query time by joining
    :class:`soyuz_catalog.models.Table` → ``Schema`` → ``Catalog``; it
    is ``None`` for ids that no longer resolve (the underlying table
    was deleted after the edge was recorded). Clients that want to
    distinguish "never existed" from "used to exist" can read the
    ``null`` full_name as the latter.

        Attributes:
            depth (int):
            securable_id (str):
            full_name (None | str | Unset):
    """

    depth: int
    securable_id: str
    full_name: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        depth = self.depth

        securable_id = self.securable_id

        full_name: None | str | Unset
        if isinstance(self.full_name, Unset):
            full_name = UNSET
        else:
            full_name = self.full_name

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "depth": depth,
                "securable_id": securable_id,
            }
        )
        if full_name is not UNSET:
            field_dict["full_name"] = full_name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        depth = d.pop("depth")

        securable_id = d.pop("securable_id")

        def _parse_full_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        full_name = _parse_full_name(d.pop("full_name", UNSET))

        lineage_node = cls(
            depth=depth,
            securable_id=securable_id,
            full_name=full_name,
        )

        return lineage_node
