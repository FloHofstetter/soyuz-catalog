from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="DeltaGetCommits")


@_attrs_define
class DeltaGetCommits:
    """Request body for ``GET /delta/preview/commits``.

    The UC OpenAPI spec models this endpoint as a GET-with-body — unusual
    but unambiguous — so the request shape is a Pydantic model rather than
    query parameters. ``table_id`` and ``table_uri`` must both be present:
    the spec requires the server to reject a request whose ``table_uri``
    does not match the currently-registered storage location of
    ``table_id``, so sending one without the other is a client bug.
    ``start_version`` bounds the returned row set inclusively from below;
    ``end_version`` bounds it inclusively from above when present.

    Per ADR-0011 the coordinator tracks unbackfilled commits, so
    ``start_version`` and ``end_version`` carry a real filtering
    role. See :mod:`soyuz_catalog.services.delta_commits_service`
    for how the service applies them.

        Attributes:
            start_version (int):
            table_id (str):
            table_uri (str):
            end_version (int | None | Unset):
    """

    start_version: int
    table_id: str
    table_uri: str
    end_version: int | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        start_version = self.start_version

        table_id = self.table_id

        table_uri = self.table_uri

        end_version: int | None | Unset
        if isinstance(self.end_version, Unset):
            end_version = UNSET
        else:
            end_version = self.end_version

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "start_version": start_version,
                "table_id": table_id,
                "table_uri": table_uri,
            }
        )
        if end_version is not UNSET:
            field_dict["end_version"] = end_version

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        start_version = d.pop("start_version")

        table_id = d.pop("table_id")

        table_uri = d.pop("table_uri")

        def _parse_end_version(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        end_version = _parse_end_version(d.pop("end_version", UNSET))

        delta_get_commits = cls(
            start_version=start_version,
            table_id=table_id,
            table_uri=table_uri,
            end_version=end_version,
        )

        return delta_get_commits
