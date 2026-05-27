from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.delta_commit_info import DeltaCommitInfo


T = TypeVar("T", bound="DeltaGetCommitsResponse")


@_attrs_define
class DeltaGetCommitsResponse:
    """Response body for ``GET /delta/preview/commits``.

    ``commits`` carries the rows currently tracked by the coordinator
    (ADR-0011) for the requested table in
    ``[start_version, end_version]``. ``latest_table_version`` is the
    highest version the coordinator has ever seen for the table — max
    over live rows (including the one marked
    ``is_backfilled_latest_commit`` as the anchor after pruning), or
    :py:meth:`deltalake.DeltaTable.version` on the on-disk log when
    the coordinator has no rows for the table (the read-path for
    freshly-attached tables that never staged a commit through
    soyuz). Delta Kernel readers apply the returned ``commits``
    **in-memory** — they do not themselves backfill to disk.

        Attributes:
            latest_table_version (int):
            commits (list[DeltaCommitInfo] | Unset):
    """

    latest_table_version: int
    commits: list[DeltaCommitInfo] | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.delta_commit_info import DeltaCommitInfo

        latest_table_version = self.latest_table_version

        commits: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.commits, Unset):
            commits = []
            for commits_item_data in self.commits:
                commits_item = commits_item_data.to_dict()
                commits.append(commits_item)

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "latest_table_version": latest_table_version,
            }
        )
        if commits is not UNSET:
            field_dict["commits"] = commits

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.delta_commit_info import DeltaCommitInfo

        d = dict(src_dict)
        latest_table_version = d.pop("latest_table_version")

        _commits = d.pop("commits", UNSET)
        commits: list[DeltaCommitInfo] | Unset = UNSET
        if _commits is not UNSET:
            commits = []
            for commits_item_data in _commits:
                commits_item = DeltaCommitInfo.from_dict(commits_item_data)

                commits.append(commits_item)

        delta_get_commits_response = cls(
            latest_table_version=latest_table_version,
            commits=commits,
        )

        return delta_get_commits_response
