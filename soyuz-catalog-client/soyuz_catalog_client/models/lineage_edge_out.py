from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="LineageEdgeOut")


@_attrs_define
class LineageEdgeOut:
    """One directed edge in a lineage traversal response.

    ``source_full_name`` and ``target_full_name`` follow the same
    "null means the securable id no longer resolves" rule as
    :class:`LineageNode`. ``run_id`` is exposed so a client can pivot
    from "show me the graph" to "show me the job that produced this
    edge" without a second round-trip.

        Attributes:
            run_id (str):
            source_securable_id (str):
            target_securable_id (str):
            operation (None | str | Unset):
            source_full_name (None | str | Unset):
            target_full_name (None | str | Unset):
    """

    run_id: str
    source_securable_id: str
    target_securable_id: str
    operation: None | str | Unset = UNSET
    source_full_name: None | str | Unset = UNSET
    target_full_name: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        run_id = self.run_id

        source_securable_id = self.source_securable_id

        target_securable_id = self.target_securable_id

        operation: None | str | Unset
        if isinstance(self.operation, Unset):
            operation = UNSET
        else:
            operation = self.operation

        source_full_name: None | str | Unset
        if isinstance(self.source_full_name, Unset):
            source_full_name = UNSET
        else:
            source_full_name = self.source_full_name

        target_full_name: None | str | Unset
        if isinstance(self.target_full_name, Unset):
            target_full_name = UNSET
        else:
            target_full_name = self.target_full_name

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "run_id": run_id,
                "source_securable_id": source_securable_id,
                "target_securable_id": target_securable_id,
            }
        )
        if operation is not UNSET:
            field_dict["operation"] = operation
        if source_full_name is not UNSET:
            field_dict["source_full_name"] = source_full_name
        if target_full_name is not UNSET:
            field_dict["target_full_name"] = target_full_name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        run_id = d.pop("run_id")

        source_securable_id = d.pop("source_securable_id")

        target_securable_id = d.pop("target_securable_id")

        def _parse_operation(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        operation = _parse_operation(d.pop("operation", UNSET))

        def _parse_source_full_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        source_full_name = _parse_source_full_name(d.pop("source_full_name", UNSET))

        def _parse_target_full_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        target_full_name = _parse_target_full_name(d.pop("target_full_name", UNSET))

        lineage_edge_out = cls(
            run_id=run_id,
            source_securable_id=source_securable_id,
            target_securable_id=target_securable_id,
            operation=operation,
            source_full_name=source_full_name,
            target_full_name=target_full_name,
        )

        return lineage_edge_out
