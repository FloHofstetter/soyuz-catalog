from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="LineageIngestResponse")


@_attrs_define
class LineageIngestResponse:
    """Response body for ``POST /lineage/v1/events``.

    Unlike the ingestion body, the response is strict-``forbid``: no
    ambiguity about what soyuz returned. ``accepted_edges`` counts the
    rows actually inserted on this call (redeliveries report ``0``);
    ``rejected_datasets`` counts dataset entries whose ``name`` failed
    to resolve to a soyuz table and were therefore dropped. The
    combination lets producers tell "soyuz saw my event but couldn't
    map it" apart from "soyuz already had it".

    Two more counters cover the optional column-lineage and
    (non-spec, producer-defined) value-change facets:
    ``accepted_column_edges`` / ``accepted_value_changes``.
    Producers that don't emit either facet always see ``0`` for both
    — the response shape is additive.

        Attributes:
            accepted_edges (int):
            rejected_datasets (int):
            run_id (str):
            state (str):
            accepted_column_edges (int | Unset):  Default: 0.
            accepted_value_changes (int | Unset):  Default: 0.
    """

    accepted_edges: int
    rejected_datasets: int
    run_id: str
    state: str
    accepted_column_edges: int | Unset = 0
    accepted_value_changes: int | Unset = 0

    def to_dict(self) -> dict[str, Any]:
        accepted_edges = self.accepted_edges

        rejected_datasets = self.rejected_datasets

        run_id = self.run_id

        state = self.state

        accepted_column_edges = self.accepted_column_edges

        accepted_value_changes = self.accepted_value_changes

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "accepted_edges": accepted_edges,
                "rejected_datasets": rejected_datasets,
                "run_id": run_id,
                "state": state,
            }
        )
        if accepted_column_edges is not UNSET:
            field_dict["accepted_column_edges"] = accepted_column_edges
        if accepted_value_changes is not UNSET:
            field_dict["accepted_value_changes"] = accepted_value_changes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        accepted_edges = d.pop("accepted_edges")

        rejected_datasets = d.pop("rejected_datasets")

        run_id = d.pop("run_id")

        state = d.pop("state")

        accepted_column_edges = d.pop("accepted_column_edges", UNSET)

        accepted_value_changes = d.pop("accepted_value_changes", UNSET)

        lineage_ingest_response = cls(
            accepted_edges=accepted_edges,
            rejected_datasets=rejected_datasets,
            run_id=run_id,
            state=state,
            accepted_column_edges=accepted_column_edges,
            accepted_value_changes=accepted_value_changes,
        )

        return lineage_ingest_response
