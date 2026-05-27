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

T = TypeVar("T", bound="AssertEtag")


@_attrs_define
class AssertEtag:
    """``assert-etag`` pre-condition variant of ``TableRequirement``.

    The etag soyuz synthesises is ``str(Table.updated_at)`` — every
    mutation bumps ``updated_at``, so a stale etag fails the
    assertion. A failure maps to 409 ``REQUIREMENT_NOT_MET`` just
    like :class:`AssertTableUUID`.

        Attributes:
            etag (str):
            type_ (Literal['assert-etag']):
    """

    etag: str
    type_: Literal["assert-etag"]

    def to_dict(self) -> dict[str, Any]:
        etag = self.etag

        type_ = self.type_

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "etag": etag,
                "type": type_,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        etag = d.pop("etag")

        type_ = cast(Literal["assert-etag"], d.pop("type"))
        if type_ != "assert-etag":
            raise ValueError(f"type must match const 'assert-etag', got '{type_}'")

        assert_etag = cls(
            etag=etag,
            type_=type_,
        )

        return assert_etag
