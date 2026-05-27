from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="OpenLineageRun")


@_attrs_define
class OpenLineageRun:
    """The ``run`` block of an OpenLineage event.

    ``runId`` is the OpenLineage producer's UUID for this execution.
    soyuz stores it verbatim as the :class:`LineageRun` primary key with
    hyphens stripped, so two soyuz instances that happen to receive the
    same event produce the same row. ``facets`` are accepted but ignored.

        Attributes:
            run_id (str):
    """

    run_id: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        run_id = self.run_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "runId": run_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        run_id = d.pop("runId")

        open_lineage_run = cls(
            run_id=run_id,
        )

        open_lineage_run.additional_properties = d
        return open_lineage_run

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
