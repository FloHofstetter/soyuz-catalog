from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.commit_report import CommitReport


T = TypeVar("T", bound="MetricsReport")


@_attrs_define
class MetricsReport:
    """``report`` block of a ``reportMetrics`` request.

    Accepted but discarded. Wraps :class:`CommitReport` with room
    for future metric kinds the Delta spec may add.

        Attributes:
            commit_report (CommitReport | None | Unset):
    """

    commit_report: CommitReport | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.commit_report import CommitReport

        commit_report: dict[str, Any] | None | Unset
        if isinstance(self.commit_report, Unset):
            commit_report = UNSET
        elif isinstance(self.commit_report, CommitReport):
            commit_report = self.commit_report.to_dict()
        else:
            commit_report = self.commit_report

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if commit_report is not UNSET:
            field_dict["commit-report"] = commit_report

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.commit_report import CommitReport

        d = dict(src_dict)

        def _parse_commit_report(data: object) -> CommitReport | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                commit_report_type_0 = CommitReport.from_dict(data)

                return commit_report_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(CommitReport | None | Unset, data)

        commit_report = _parse_commit_report(d.pop("commit-report", UNSET))

        metrics_report = cls(
            commit_report=commit_report,
        )

        metrics_report.additional_properties = d
        return metrics_report

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
