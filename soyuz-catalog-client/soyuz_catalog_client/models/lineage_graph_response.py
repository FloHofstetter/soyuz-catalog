from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.lineage_graph_response_direction import LineageGraphResponseDirection
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.lineage_edge_out import LineageEdgeOut
    from ..models.lineage_node import LineageNode


T = TypeVar("T", bound="LineageGraphResponse")


@_attrs_define
class LineageGraphResponse:
    """Response body for ``GET /lineage/{upstream,downstream}/{full_name}``.

    The shape is symmetric between upstream and downstream queries —
    ``direction`` is the only hint about which way the graph was
    walked. ``root`` echoes the path parameter (unnormalised) so the
    client can render a breadcrumb without re-parsing its own request.
    ``nodes`` contains one entry per reachable securable id including
    the root at ``depth=0``; ``edges`` contains every edge traversed in
    reaching those nodes, deduplicated.

        Attributes:
            direction (LineageGraphResponseDirection):
            root (str):
            edges (list[LineageEdgeOut] | Unset):
            nodes (list[LineageNode] | Unset):
    """

    direction: LineageGraphResponseDirection
    root: str
    edges: list[LineageEdgeOut] | Unset = UNSET
    nodes: list[LineageNode] | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.lineage_edge_out import LineageEdgeOut
        from ..models.lineage_node import LineageNode

        direction = self.direction.value

        root = self.root

        edges: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.edges, Unset):
            edges = []
            for edges_item_data in self.edges:
                edges_item = edges_item_data.to_dict()
                edges.append(edges_item)

        nodes: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.nodes, Unset):
            nodes = []
            for nodes_item_data in self.nodes:
                nodes_item = nodes_item_data.to_dict()
                nodes.append(nodes_item)

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "direction": direction,
                "root": root,
            }
        )
        if edges is not UNSET:
            field_dict["edges"] = edges
        if nodes is not UNSET:
            field_dict["nodes"] = nodes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.lineage_edge_out import LineageEdgeOut
        from ..models.lineage_node import LineageNode

        d = dict(src_dict)
        direction = LineageGraphResponseDirection(d.pop("direction"))

        root = d.pop("root")

        _edges = d.pop("edges", UNSET)
        edges: list[LineageEdgeOut] | Unset = UNSET
        if _edges is not UNSET:
            edges = []
            for edges_item_data in _edges:
                edges_item = LineageEdgeOut.from_dict(edges_item_data)

                edges.append(edges_item)

        _nodes = d.pop("nodes", UNSET)
        nodes: list[LineageNode] | Unset = UNSET
        if _nodes is not UNSET:
            nodes = []
            for nodes_item_data in _nodes:
                nodes_item = LineageNode.from_dict(nodes_item_data)

                nodes.append(nodes_item)

        lineage_graph_response = cls(
            direction=direction,
            root=root,
            edges=edges,
            nodes=nodes,
        )

        return lineage_graph_response
