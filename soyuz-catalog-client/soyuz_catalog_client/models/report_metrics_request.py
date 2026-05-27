from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.metrics_report import MetricsReport


T = TypeVar("T", bound="ReportMetricsRequest")


@_attrs_define
class ReportMetricsRequest:
    """Request body for ``POST .../tables/{table}/metrics``.

    soyuz parses the body (so a malformed payload surfaces as 422)
    and then discards it — there is no metrics sink in the project.
    The 204 response is accept-and-discard; ADR-0009 explains why
    this beats 501 for Delta client compatibility.

        Attributes:
            table_id (str):
            report (MetricsReport | None | Unset):
    """

    table_id: str
    report: MetricsReport | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.metrics_report import MetricsReport

        table_id = self.table_id

        report: dict[str, Any] | None | Unset
        if isinstance(self.report, Unset):
            report = UNSET
        elif isinstance(self.report, MetricsReport):
            report = self.report.to_dict()
        else:
            report = self.report

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "table-id": table_id,
            }
        )
        if report is not UNSET:
            field_dict["report"] = report

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.metrics_report import MetricsReport

        d = dict(src_dict)
        table_id = d.pop("table-id")

        def _parse_report(data: object) -> MetricsReport | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                report_type_0 = MetricsReport.from_dict(data)

                return report_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(MetricsReport | None | Unset, data)

        report = _parse_report(d.pop("report", UNSET))

        report_metrics_request = cls(
            table_id=table_id,
            report=report,
        )

        return report_metrics_request
