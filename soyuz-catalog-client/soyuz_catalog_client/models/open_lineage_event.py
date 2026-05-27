from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.open_lineage_event_eventtype import OpenLineageEventEventtype
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.open_lineage_dataset import OpenLineageDataset
    from ..models.open_lineage_job import OpenLineageJob
    from ..models.open_lineage_run import OpenLineageRun


T = TypeVar("T", bound="OpenLineageEvent")


@_attrs_define
class OpenLineageEvent:
    """An OpenLineage ``RunEvent`` body posted to ``/lineage/v1/events``.

    Permissively validated: unknown top-level fields and unknown
    sub-fields are accepted because OpenLineage evolves independently of
    soyuz and the endpoint must not crash producers when a new facet
    ships. The strict-``forbid`` policy still applies to every soyuz
    *response* shape and every spec-sourced request shape; this is the
    only documented exception. See ADR-0008.

    soyuz extracts a small fixed set of fields:

    * ``eventType`` drives the :class:`LineageRun.state` transition.
    * ``eventTime`` (ISO-8601) is parsed to epoch milliseconds and
      stored as ``started_at`` on the first event (``ended_at`` on the
      terminal event).
    * ``run.runId`` is the run primary key.
    * ``job.namespace`` / ``job.name`` populate the run's denormalised
      job columns and ``job.name`` also becomes each edge's
      ``operation`` label.
    * ``inputs`` × ``outputs`` cross product produces
      :class:`LineageEdge` rows, dropping datasets whose names do not
      resolve to an existing soyuz table.
    * Two additional facets are ingested when present on output
      datasets:

      * ``columnLineage`` — OpenLineage 1.x standard.  Each
        ``fields[target_column].inputFields`` entry produces one
        :class:`LineageColumnEdge` row.  ``transformations[0].type``
        (when present) populates ``transformation_type`` verbatim.
      * ``valueChange`` — **non-spec producer extension**, identified
        on the wire by its ``_producer`` URI on the facet payload.
        The body shape is ``{changes: [{rowId, column, oldValue,
        newValue}]}``; one :class:`LineageValueChange` row per
        entry.  soyuz stores the values verbatim and does no
        redaction of its own — producers handling PII are expected
        to redact upstream.  The shape is producer-defined, not
        part of OpenLineage 1.x.

        Attributes:
            event_time (str):
            event_type (OpenLineageEventEventtype):
            job (OpenLineageJob): The ``job`` block of an OpenLineage event.

                Only ``namespace`` and ``name`` are pulled out at this layer; any
                ``facets`` that OpenLineage producers attach are kept via
                ``extra="allow"`` but not interpreted — soyuz does not want its
                storage shape pinned to any one producer's facet conventions. See
                ADR-0008 for why ``job.name`` alone is stored as the edge
                ``operation``.
            run (OpenLineageRun): The ``run`` block of an OpenLineage event.

                ``runId`` is the OpenLineage producer's UUID for this execution.
                soyuz stores it verbatim as the :class:`LineageRun` primary key with
                hyphens stripped, so two soyuz instances that happen to receive the
                same event produce the same row. ``facets`` are accepted but ignored.
            inputs (list[OpenLineageDataset] | Unset):
            outputs (list[OpenLineageDataset] | Unset):
    """

    event_time: str
    event_type: OpenLineageEventEventtype
    job: OpenLineageJob
    run: OpenLineageRun
    inputs: list[OpenLineageDataset] | Unset = UNSET
    outputs: list[OpenLineageDataset] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.open_lineage_dataset import OpenLineageDataset
        from ..models.open_lineage_job import OpenLineageJob
        from ..models.open_lineage_run import OpenLineageRun

        event_time = self.event_time

        event_type = self.event_type.value

        job = self.job.to_dict()

        run = self.run.to_dict()

        inputs: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.inputs, Unset):
            inputs = []
            for inputs_item_data in self.inputs:
                inputs_item = inputs_item_data.to_dict()
                inputs.append(inputs_item)

        outputs: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.outputs, Unset):
            outputs = []
            for outputs_item_data in self.outputs:
                outputs_item = outputs_item_data.to_dict()
                outputs.append(outputs_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "eventTime": event_time,
                "eventType": event_type,
                "job": job,
                "run": run,
            }
        )
        if inputs is not UNSET:
            field_dict["inputs"] = inputs
        if outputs is not UNSET:
            field_dict["outputs"] = outputs

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.open_lineage_dataset import OpenLineageDataset
        from ..models.open_lineage_job import OpenLineageJob
        from ..models.open_lineage_run import OpenLineageRun

        d = dict(src_dict)
        event_time = d.pop("eventTime")

        event_type = OpenLineageEventEventtype(d.pop("eventType"))

        job = OpenLineageJob.from_dict(d.pop("job"))

        run = OpenLineageRun.from_dict(d.pop("run"))

        _inputs = d.pop("inputs", UNSET)
        inputs: list[OpenLineageDataset] | Unset = UNSET
        if _inputs is not UNSET:
            inputs = []
            for inputs_item_data in _inputs:
                inputs_item = OpenLineageDataset.from_dict(inputs_item_data)

                inputs.append(inputs_item)

        _outputs = d.pop("outputs", UNSET)
        outputs: list[OpenLineageDataset] | Unset = UNSET
        if _outputs is not UNSET:
            outputs = []
            for outputs_item_data in _outputs:
                outputs_item = OpenLineageDataset.from_dict(outputs_item_data)

                outputs.append(outputs_item)

        open_lineage_event = cls(
            event_time=event_time,
            event_type=event_type,
            job=job,
            run=run,
            inputs=inputs,
            outputs=outputs,
        )

        open_lineage_event.additional_properties = d
        return open_lineage_event

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
