from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.delta_column_type_type_1 import DeltaColumnTypeType1
    from ..models.metadata import Metadata


T = TypeVar("T", bound="DeltaColumn")


@_attrs_define
class DeltaColumn:
    """One column in a Delta table as carried on the Delta REST wire.

    The ``type`` field is a **string-or-object union**: a primitive
    like ``"long"`` or ``"decimal(10,2)"`` is a bare JSON string,
    while a complex type (``array``, ``map``, ``struct``) is a nested
    JSON object whose own ``type`` field discriminates the variant.
    OpenAPI cannot express this union, so upstream
    ``delta.yaml`` leaves the field untyped and Delta clients parse
    it through their own type serialiser. soyuz therefore models it
    as ``str | dict[str, Any]`` and round-trips it verbatim via
    :class:`soyuz_catalog.models.Column.type_json`; see
    ADR-0009 for the storage strategy.

    ``metadata`` carries arbitrary Spark/Delta per-column metadata
    (comments, column-mapping ids, generated-column expressions).
    soyuz accepts any JSON object and stores it in the column's
    ``type_json`` payload alongside the type — clients are free to
    attach whatever they need.

        Attributes:
            name (str):
            nullable (bool):
            type_ (DeltaColumnTypeType1 | str):
            metadata (Metadata | Unset):
    """

    name: str
    nullable: bool
    type_: DeltaColumnTypeType1 | str
    metadata: Metadata | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.delta_column_type_type_1 import DeltaColumnTypeType1
        from ..models.metadata import Metadata

        name = self.name

        nullable = self.nullable

        type_: dict[str, Any] | str
        if isinstance(self.type_, DeltaColumnTypeType1):
            type_ = self.type_.to_dict()
        else:
            type_ = self.type_

        metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
                "nullable": nullable,
                "type": type_,
            }
        )
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.delta_column_type_type_1 import DeltaColumnTypeType1
        from ..models.metadata import Metadata

        d = dict(src_dict)
        name = d.pop("name")

        nullable = d.pop("nullable")

        def _parse_type_(data: object) -> DeltaColumnTypeType1 | str:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                type_type_1 = DeltaColumnTypeType1.from_dict(data)

                return type_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(DeltaColumnTypeType1 | str, data)

        type_ = _parse_type_(d.pop("type"))

        _metadata = d.pop("metadata", UNSET)
        metadata: Metadata | Unset
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = Metadata.from_dict(_metadata)

        delta_column = cls(
            name=name,
            nullable=nullable,
            type_=type_,
            metadata=metadata,
        )

        return delta_column
