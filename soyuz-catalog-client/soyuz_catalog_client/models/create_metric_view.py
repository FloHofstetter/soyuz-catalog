from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.metric_view_spec import MetricViewSpec


T = TypeVar("T", bound="CreateMetricView")


@_attrs_define
class CreateMetricView:
    """Request body for ``POST /metric-views``.

    ``source_table_full_name`` must be a syntactically valid
    three-part name but is *not* resolved against the tables surface
    — a metric view may be authored before its source table is
    registered, exactly like a SQL view body referencing a yet-to-be
    created table. The parent catalog and schema, by contrast, must
    exist (404 otherwise). ``extra="forbid"`` rejects unknown fields
    with 422 instead of silently dropping them.

        Attributes:
            catalog_name (str):
            name (str):
            schema_name (str):
            source_table_full_name (str):
            spec (MetricViewSpec): The semantic-layer definition stored on a metric view.

                ``measures`` requires at least one entry (``min_length=1`` —
                surfacing as 422): a metric view without a measure is just a
                projection and belongs in a plain SQL view. ``dimensions`` may be
                empty (a single-row summary view is legitimate). ``filter`` is an
                optional opaque SQL predicate applied by the consumer before
                aggregation.
            comment (None | str | Unset):
            owner (None | str | Unset):
    """

    catalog_name: str
    name: str
    schema_name: str
    source_table_full_name: str
    spec: MetricViewSpec
    comment: None | str | Unset = UNSET
    owner: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.metric_view_spec import MetricViewSpec

        catalog_name = self.catalog_name

        name = self.name

        schema_name = self.schema_name

        source_table_full_name = self.source_table_full_name

        spec = self.spec.to_dict()

        comment: None | str | Unset
        if isinstance(self.comment, Unset):
            comment = UNSET
        else:
            comment = self.comment

        owner: None | str | Unset
        if isinstance(self.owner, Unset):
            owner = UNSET
        else:
            owner = self.owner

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "catalog_name": catalog_name,
                "name": name,
                "schema_name": schema_name,
                "source_table_full_name": source_table_full_name,
                "spec": spec,
            }
        )
        if comment is not UNSET:
            field_dict["comment"] = comment
        if owner is not UNSET:
            field_dict["owner"] = owner

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.metric_view_spec import MetricViewSpec

        d = dict(src_dict)
        catalog_name = d.pop("catalog_name")

        name = d.pop("name")

        schema_name = d.pop("schema_name")

        source_table_full_name = d.pop("source_table_full_name")

        spec = MetricViewSpec.from_dict(d.pop("spec"))

        def _parse_comment(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        comment = _parse_comment(d.pop("comment", UNSET))

        def _parse_owner(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        owner = _parse_owner(d.pop("owner", UNSET))

        create_metric_view = cls(
            catalog_name=catalog_name,
            name=name,
            schema_name=schema_name,
            source_table_full_name=source_table_full_name,
            spec=spec,
            comment=comment,
            owner=owner,
        )

        return create_metric_view
