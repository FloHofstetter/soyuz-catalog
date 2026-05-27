from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.delta_commit_info import DeltaCommitInfo
    from ..models.delta_commit_metadata_type_0 import DeltaCommitMetadataType0
    from ..models.delta_commit_uniform_type_0 import DeltaCommitUniformType0


T = TypeVar("T", bound="DeltaCommit")


@_attrs_define
class DeltaCommit:
    """Request body for ``POST /delta/preview/commits``.

    Request shape for the passthrough Delta commit coordinator
    (ADR-0011). The request fuses two conceptually
    independent operations the Delta Kernel client may send in a
    single call: a **commit** registration (``commit_info`` set,
    carrying the metadata of a freshly-staged ``_delta_log/.tmp/``
    file) and a **backfill acknowledgement** (``latest_backfilled_version``
    set, signalling that the client has published everything up to
    that version and the coordinator can prune). Either field, or
    both, may be present — the spec's ``oneOf-ish`` requirement is
    enforced by :meth:`_require_at_least_one_action` below and
    re-checked defensively in
    :func:`soyuz_catalog.services.delta_commits_service.commit`.

    ``metadata`` and ``uniform`` are accepted as opaque pass-through
    dicts: the upstream protocol forwards them to downstream Delta
    Kernel consumers (protocol upgrades, Iceberg conversion hints)
    and soyuz stores neither. Their shapes are not pinned on this
    side because doing so would couple soyuz to a Kernel-side
    contract that evolves independently and does not participate in
    the `all.yaml` conformance test.

        Attributes:
            table_id (str):
            table_uri (str):
            commit_info (DeltaCommitInfo | None | Unset):
            latest_backfilled_version (int | None | Unset):
            metadata (DeltaCommitMetadataType0 | None | Unset):
            uniform (DeltaCommitUniformType0 | None | Unset):
    """

    table_id: str
    table_uri: str
    commit_info: DeltaCommitInfo | None | Unset = UNSET
    latest_backfilled_version: int | None | Unset = UNSET
    metadata: DeltaCommitMetadataType0 | None | Unset = UNSET
    uniform: DeltaCommitUniformType0 | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.delta_commit_info import DeltaCommitInfo
        from ..models.delta_commit_metadata_type_0 import DeltaCommitMetadataType0
        from ..models.delta_commit_uniform_type_0 import DeltaCommitUniformType0

        table_id = self.table_id

        table_uri = self.table_uri

        commit_info: dict[str, Any] | None | Unset
        if isinstance(self.commit_info, Unset):
            commit_info = UNSET
        elif isinstance(self.commit_info, DeltaCommitInfo):
            commit_info = self.commit_info.to_dict()
        else:
            commit_info = self.commit_info

        latest_backfilled_version: int | None | Unset
        if isinstance(self.latest_backfilled_version, Unset):
            latest_backfilled_version = UNSET
        else:
            latest_backfilled_version = self.latest_backfilled_version

        metadata: dict[str, Any] | None | Unset
        if isinstance(self.metadata, Unset):
            metadata = UNSET
        elif isinstance(self.metadata, DeltaCommitMetadataType0):
            metadata = self.metadata.to_dict()
        else:
            metadata = self.metadata

        uniform: dict[str, Any] | None | Unset
        if isinstance(self.uniform, Unset):
            uniform = UNSET
        elif isinstance(self.uniform, DeltaCommitUniformType0):
            uniform = self.uniform.to_dict()
        else:
            uniform = self.uniform

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "table_id": table_id,
                "table_uri": table_uri,
            }
        )
        if commit_info is not UNSET:
            field_dict["commit_info"] = commit_info
        if latest_backfilled_version is not UNSET:
            field_dict["latest_backfilled_version"] = latest_backfilled_version
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if uniform is not UNSET:
            field_dict["uniform"] = uniform

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.delta_commit_info import DeltaCommitInfo
        from ..models.delta_commit_metadata_type_0 import DeltaCommitMetadataType0
        from ..models.delta_commit_uniform_type_0 import DeltaCommitUniformType0

        d = dict(src_dict)
        table_id = d.pop("table_id")

        table_uri = d.pop("table_uri")

        def _parse_commit_info(data: object) -> DeltaCommitInfo | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                commit_info_type_0 = DeltaCommitInfo.from_dict(data)

                return commit_info_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(DeltaCommitInfo | None | Unset, data)

        commit_info = _parse_commit_info(d.pop("commit_info", UNSET))

        def _parse_latest_backfilled_version(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        latest_backfilled_version = _parse_latest_backfilled_version(
            d.pop("latest_backfilled_version", UNSET)
        )

        def _parse_metadata(data: object) -> DeltaCommitMetadataType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                metadata_type_0 = DeltaCommitMetadataType0.from_dict(data)

                return metadata_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(DeltaCommitMetadataType0 | None | Unset, data)

        metadata = _parse_metadata(d.pop("metadata", UNSET))

        def _parse_uniform(data: object) -> DeltaCommitUniformType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                uniform_type_0 = DeltaCommitUniformType0.from_dict(data)

                return uniform_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(DeltaCommitUniformType0 | None | Unset, data)

        uniform = _parse_uniform(d.pop("uniform", UNSET))

        delta_commit = cls(
            table_id=table_id,
            table_uri=table_uri,
            commit_info=commit_info,
            latest_backfilled_version=latest_backfilled_version,
            metadata=metadata,
            uniform=uniform,
        )

        return delta_commit
