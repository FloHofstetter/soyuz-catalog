from __future__ import annotations

from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    BinaryIO,
    Generator,
    Literal,
    TextIO,
    TypeVar,
    cast,
)

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AssertTableUUID")


@_attrs_define
class AssertTableUUID:
    """``assert-table-uuid`` pre-condition variant of ``TableRequirement``.

    soyuz implements this as a plain string equality check against
    :class:`soyuz_catalog.models.Table.id`. A failure maps to 409
    :class:`soyuz_catalog.exceptions.ConflictError` with the
    dedicated ``REQUIREMENT_NOT_MET`` error_code so clients can tell
    the failure apart from a duplicate-name conflict.

        Attributes:
            type_ (Literal['assert-table-uuid']):
            uuid (str):
    """

    type_: Literal["assert-table-uuid"]
    uuid: str

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_

        uuid = self.uuid

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "type": type_,
                "uuid": uuid,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        type_ = cast(Literal["assert-table-uuid"], d.pop("type"))
        if type_ != "assert-table-uuid":
            raise ValueError(
                f"type must match const 'assert-table-uuid', got '{type_}'"
            )

        uuid = d.pop("uuid")

        assert_table_uuid = cls(
            type_=type_,
            uuid=uuid,
        )

        return assert_table_uuid
