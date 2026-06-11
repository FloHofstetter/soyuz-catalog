from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.metric_view_spec import MetricViewSpec


T = TypeVar("T", bound="UpdateMetricView")


@_attrs_define
class UpdateMetricView:
    """Request body for ``PATCH /metric-views/{full_name}``.

    Replace-style PATCH semantics driven by ``model_fields_set`` in
    the service layer: ``spec`` replaces the whole stored definition
    (a per-dimension merge would have no predictable semantics), and
    an empty body is a no-op. ``new_name`` renames within the same
    schema — moving a metric view across schemas is a
    delete-and-recreate, same posture as every other child resource.

        Attributes:
            comment (None | str | Unset):
            new_name (None | str | Unset):
            owner (None | str | Unset):
            source_table_full_name (None | str | Unset):
            spec (MetricViewSpec | None | Unset):
    """

    comment: None | str | Unset = UNSET
    new_name: None | str | Unset = UNSET
    owner: None | str | Unset = UNSET
    source_table_full_name: None | str | Unset = UNSET
    spec: MetricViewSpec | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.metric_view_spec import MetricViewSpec

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

        owner: None | str | Unset
        if isinstance(self.owner, Unset):
            owner = UNSET
        else:
            owner = self.owner

        source_table_full_name: None | str | Unset
        if isinstance(self.source_table_full_name, Unset):
            source_table_full_name = UNSET
        else:
            source_table_full_name = self.source_table_full_name

        spec: dict[str, Any] | None | Unset
        if isinstance(self.spec, Unset):
            spec = UNSET
        elif isinstance(self.spec, MetricViewSpec):
            spec = self.spec.to_dict()
        else:
            spec = self.spec

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if comment is not UNSET:
            field_dict["comment"] = comment
        if new_name is not UNSET:
            field_dict["new_name"] = new_name
        if owner is not UNSET:
            field_dict["owner"] = owner
        if source_table_full_name is not UNSET:
            field_dict["source_table_full_name"] = source_table_full_name
        if spec is not UNSET:
            field_dict["spec"] = spec

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.metric_view_spec import MetricViewSpec

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

        def _parse_owner(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        owner = _parse_owner(d.pop("owner", UNSET))

        def _parse_source_table_full_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        source_table_full_name = _parse_source_table_full_name(
            d.pop("source_table_full_name", UNSET)
        )

        def _parse_spec(data: object) -> MetricViewSpec | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                spec_type_0 = MetricViewSpec.from_dict(data)

                return spec_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(MetricViewSpec | None | Unset, data)

        spec = _parse_spec(d.pop("spec", UNSET))

        update_metric_view = cls(
            comment=comment,
            new_name=new_name,
            owner=owner,
            source_table_full_name=source_table_full_name,
            spec=spec,
        )

        return update_metric_view
