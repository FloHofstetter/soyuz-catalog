from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="OpenLineageJob")


@_attrs_define
class OpenLineageJob:
    """The ``job`` block of an OpenLineage event.

    Only ``namespace`` and ``name`` are pulled out at this layer; any
    ``facets`` that OpenLineage producers attach are kept via
    ``extra="allow"`` but not interpreted — soyuz does not want its
    storage shape pinned to any one producer's facet conventions. See
    ADR-0008 for why ``job.name`` alone is stored as the edge
    ``operation``.

        Attributes:
            name (str):
            namespace (str):
    """

    name: str
    namespace: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        namespace = self.namespace

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "namespace": namespace,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        namespace = d.pop("namespace")

        open_lineage_job = cls(
            name=name,
            namespace=namespace,
        )

        open_lineage_job.additional_properties = d
        return open_lineage_job

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
