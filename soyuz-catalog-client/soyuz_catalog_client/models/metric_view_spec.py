from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.metric_view_dimension import MetricViewDimension
    from ..models.metric_view_measure import MetricViewMeasure


T = TypeVar("T", bound="MetricViewSpec")


@_attrs_define
class MetricViewSpec:
    """The semantic-layer definition stored on a metric view.

    ``measures`` requires at least one entry (``min_length=1`` —
    surfacing as 422): a metric view without a measure is just a
    projection and belongs in a plain SQL view. ``dimensions`` may be
    empty (a single-row summary view is legitimate). ``filter`` is an
    optional opaque SQL predicate applied by the consumer before
    aggregation.

        Attributes:
            measures (list[MetricViewMeasure]):
            dimensions (list[MetricViewDimension] | Unset):
            filter_ (None | str | Unset):
    """

    measures: list[MetricViewMeasure]
    dimensions: list[MetricViewDimension] | Unset = UNSET
    filter_: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.metric_view_dimension import MetricViewDimension
        from ..models.metric_view_measure import MetricViewMeasure

        measures = []
        for measures_item_data in self.measures:
            measures_item = measures_item_data.to_dict()
            measures.append(measures_item)

        dimensions: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.dimensions, Unset):
            dimensions = []
            for dimensions_item_data in self.dimensions:
                dimensions_item = dimensions_item_data.to_dict()
                dimensions.append(dimensions_item)

        filter_: None | str | Unset
        if isinstance(self.filter_, Unset):
            filter_ = UNSET
        else:
            filter_ = self.filter_

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "measures": measures,
            }
        )
        if dimensions is not UNSET:
            field_dict["dimensions"] = dimensions
        if filter_ is not UNSET:
            field_dict["filter"] = filter_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.metric_view_dimension import MetricViewDimension
        from ..models.metric_view_measure import MetricViewMeasure

        d = dict(src_dict)
        measures = []
        _measures = d.pop("measures")
        for measures_item_data in _measures:
            measures_item = MetricViewMeasure.from_dict(measures_item_data)

            measures.append(measures_item)

        _dimensions = d.pop("dimensions", UNSET)
        dimensions: list[MetricViewDimension] | Unset = UNSET
        if _dimensions is not UNSET:
            dimensions = []
            for dimensions_item_data in _dimensions:
                dimensions_item = MetricViewDimension.from_dict(dimensions_item_data)

                dimensions.append(dimensions_item)

        def _parse_filter_(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        filter_ = _parse_filter_(d.pop("filter", UNSET))

        metric_view_spec = cls(
            measures=measures,
            dimensions=dimensions,
            filter_=filter_,
        )

        return metric_view_spec
