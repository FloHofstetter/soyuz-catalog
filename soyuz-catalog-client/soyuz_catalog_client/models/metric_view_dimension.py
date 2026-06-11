from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="MetricViewDimension")


@_attrs_define
class MetricViewDimension:
    """One dimension in a metric-view spec.

    ``expr`` is an opaque SQL expression string — soyuz never parses
    it (there is no query side to validate it against; the consumer's
    compiler is where a malformed expression surfaces). ``name`` is
    the column name the compiled view exposes, so it shares one flat
    namespace with measure names — uniqueness across the combined set
    is enforced by the service layer.

        Attributes:
            expr (str):
            name (str):
            comment (None | str | Unset):
    """

    expr: str
    name: str
    comment: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        expr = self.expr

        name = self.name

        comment: None | str | Unset
        if isinstance(self.comment, Unset):
            comment = UNSET
        else:
            comment = self.comment

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "expr": expr,
                "name": name,
            }
        )
        if comment is not UNSET:
            field_dict["comment"] = comment

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        expr = d.pop("expr")

        name = d.pop("name")

        def _parse_comment(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        comment = _parse_comment(d.pop("comment", UNSET))

        metric_view_dimension = cls(
            expr=expr,
            name=name,
            comment=comment,
        )

        return metric_view_dimension
