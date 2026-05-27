from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.add_commit_update import AddCommitUpdate
    from ..models.add_constraint_update import AddConstraintUpdate
    from ..models.assert_etag import AssertEtag
    from ..models.assert_table_uuid import AssertTableUUID
    from ..models.drop_constraint_update import DropConstraintUpdate
    from ..models.remove_domain_metadata_update import RemoveDomainMetadataUpdate
    from ..models.remove_properties_update import RemovePropertiesUpdate
    from ..models.set_domain_metadata_update import SetDomainMetadataUpdate
    from ..models.set_latest_backfilled_version_update import (
        SetLatestBackfilledVersionUpdate,
    )
    from ..models.set_partition_columns_update import SetPartitionColumnsUpdate
    from ..models.set_properties_update import SetPropertiesUpdate
    from ..models.set_protocol_update import SetProtocolUpdate
    from ..models.set_schema_update import SetSchemaUpdate
    from ..models.set_table_comment_update import SetTableCommentUpdate
    from ..models.update_snapshot_version_update import UpdateSnapshotVersionUpdate


T = TypeVar("T", bound="UpdateTableRequest")


@_attrs_define
class UpdateTableRequest:
    """Request body for ``POST .../tables/{table}``.

    Pre-conditions in ``requirements`` are validated first and a
    failure on any of them short-circuits the whole batch with 409
    before any mutation runs. Updates in ``updates`` are applied in
    order; a 501 on a commit-coordinator action (``add-commit`` et
    al.) happens at the very first such entry, leaving earlier
    entries in place — consistent with Delta's own
    "append-only commit" story for the parts that are applied and
    soyuz' "fail fast on unsupported" posture everywhere else.

        Attributes:
            requirements (list[AssertEtag | AssertTableUUID] | Unset):
            updates (list[AddCommitUpdate | AddConstraintUpdate | DropConstraintUpdate | RemoveDomainMetadataUpdate |
                RemovePropertiesUpdate | SetDomainMetadataUpdate | SetLatestBackfilledVersionUpdate | SetPartitionColumnsUpdate
                | SetPropertiesUpdate | SetProtocolUpdate | SetSchemaUpdate | SetTableCommentUpdate |
                UpdateSnapshotVersionUpdate] | Unset):
    """

    requirements: list[AssertEtag | AssertTableUUID] | Unset = UNSET
    updates: (
        list[
            AddCommitUpdate
            | AddConstraintUpdate
            | DropConstraintUpdate
            | RemoveDomainMetadataUpdate
            | RemovePropertiesUpdate
            | SetDomainMetadataUpdate
            | SetLatestBackfilledVersionUpdate
            | SetPartitionColumnsUpdate
            | SetPropertiesUpdate
            | SetProtocolUpdate
            | SetSchemaUpdate
            | SetTableCommentUpdate
            | UpdateSnapshotVersionUpdate
        ]
        | Unset
    ) = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.add_commit_update import AddCommitUpdate
        from ..models.add_constraint_update import AddConstraintUpdate
        from ..models.assert_etag import AssertEtag
        from ..models.assert_table_uuid import AssertTableUUID
        from ..models.drop_constraint_update import DropConstraintUpdate
        from ..models.remove_domain_metadata_update import RemoveDomainMetadataUpdate
        from ..models.remove_properties_update import RemovePropertiesUpdate
        from ..models.set_domain_metadata_update import SetDomainMetadataUpdate
        from ..models.set_latest_backfilled_version_update import (
            SetLatestBackfilledVersionUpdate,
        )
        from ..models.set_partition_columns_update import SetPartitionColumnsUpdate
        from ..models.set_properties_update import SetPropertiesUpdate
        from ..models.set_protocol_update import SetProtocolUpdate
        from ..models.set_schema_update import SetSchemaUpdate
        from ..models.set_table_comment_update import SetTableCommentUpdate
        from ..models.update_snapshot_version_update import UpdateSnapshotVersionUpdate

        requirements: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.requirements, Unset):
            requirements = []
            for requirements_item_data in self.requirements:
                requirements_item: dict[str, Any]
                if isinstance(requirements_item_data, AssertTableUUID):
                    requirements_item = requirements_item_data.to_dict()
                else:
                    requirements_item = requirements_item_data.to_dict()

                requirements.append(requirements_item)

        updates: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.updates, Unset):
            updates = []
            for updates_item_data in self.updates:
                updates_item: dict[str, Any]
                if isinstance(updates_item_data, SetPropertiesUpdate):
                    updates_item = updates_item_data.to_dict()
                elif isinstance(updates_item_data, RemovePropertiesUpdate):
                    updates_item = updates_item_data.to_dict()
                elif isinstance(updates_item_data, SetSchemaUpdate):
                    updates_item = updates_item_data.to_dict()
                elif isinstance(updates_item_data, SetTableCommentUpdate):
                    updates_item = updates_item_data.to_dict()
                elif isinstance(updates_item_data, AddCommitUpdate):
                    updates_item = updates_item_data.to_dict()
                elif isinstance(updates_item_data, SetLatestBackfilledVersionUpdate):
                    updates_item = updates_item_data.to_dict()
                elif isinstance(updates_item_data, SetProtocolUpdate):
                    updates_item = updates_item_data.to_dict()
                elif isinstance(updates_item_data, SetDomainMetadataUpdate):
                    updates_item = updates_item_data.to_dict()
                elif isinstance(updates_item_data, RemoveDomainMetadataUpdate):
                    updates_item = updates_item_data.to_dict()
                elif isinstance(updates_item_data, SetPartitionColumnsUpdate):
                    updates_item = updates_item_data.to_dict()
                elif isinstance(updates_item_data, UpdateSnapshotVersionUpdate):
                    updates_item = updates_item_data.to_dict()
                elif isinstance(updates_item_data, AddConstraintUpdate):
                    updates_item = updates_item_data.to_dict()
                else:
                    updates_item = updates_item_data.to_dict()

                updates.append(updates_item)

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if requirements is not UNSET:
            field_dict["requirements"] = requirements
        if updates is not UNSET:
            field_dict["updates"] = updates

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.add_commit_update import AddCommitUpdate
        from ..models.add_constraint_update import AddConstraintUpdate
        from ..models.assert_etag import AssertEtag
        from ..models.assert_table_uuid import AssertTableUUID
        from ..models.drop_constraint_update import DropConstraintUpdate
        from ..models.remove_domain_metadata_update import RemoveDomainMetadataUpdate
        from ..models.remove_properties_update import RemovePropertiesUpdate
        from ..models.set_domain_metadata_update import SetDomainMetadataUpdate
        from ..models.set_latest_backfilled_version_update import (
            SetLatestBackfilledVersionUpdate,
        )
        from ..models.set_partition_columns_update import SetPartitionColumnsUpdate
        from ..models.set_properties_update import SetPropertiesUpdate
        from ..models.set_protocol_update import SetProtocolUpdate
        from ..models.set_schema_update import SetSchemaUpdate
        from ..models.set_table_comment_update import SetTableCommentUpdate
        from ..models.update_snapshot_version_update import UpdateSnapshotVersionUpdate

        d = dict(src_dict)
        _requirements = d.pop("requirements", UNSET)
        requirements: list[AssertEtag | AssertTableUUID] | Unset = UNSET
        if _requirements is not UNSET:
            requirements = []
            for requirements_item_data in _requirements:

                def _parse_requirements_item(
                    data: object,
                ) -> AssertEtag | AssertTableUUID:
                    try:
                        if not isinstance(data, dict):
                            raise TypeError()
                        requirements_item_type_0 = AssertTableUUID.from_dict(data)

                        return requirements_item_type_0
                    except (TypeError, ValueError, AttributeError, KeyError):
                        pass
                    if not isinstance(data, dict):
                        raise TypeError()
                    requirements_item_type_1 = AssertEtag.from_dict(data)

                    return requirements_item_type_1

                requirements_item = _parse_requirements_item(requirements_item_data)

                requirements.append(requirements_item)

        _updates = d.pop("updates", UNSET)
        updates: (
            list[
                AddCommitUpdate
                | AddConstraintUpdate
                | DropConstraintUpdate
                | RemoveDomainMetadataUpdate
                | RemovePropertiesUpdate
                | SetDomainMetadataUpdate
                | SetLatestBackfilledVersionUpdate
                | SetPartitionColumnsUpdate
                | SetPropertiesUpdate
                | SetProtocolUpdate
                | SetSchemaUpdate
                | SetTableCommentUpdate
                | UpdateSnapshotVersionUpdate
            ]
            | Unset
        ) = UNSET
        if _updates is not UNSET:
            updates = []
            for updates_item_data in _updates:

                def _parse_updates_item(
                    data: object,
                ) -> (
                    AddCommitUpdate
                    | AddConstraintUpdate
                    | DropConstraintUpdate
                    | RemoveDomainMetadataUpdate
                    | RemovePropertiesUpdate
                    | SetDomainMetadataUpdate
                    | SetLatestBackfilledVersionUpdate
                    | SetPartitionColumnsUpdate
                    | SetPropertiesUpdate
                    | SetProtocolUpdate
                    | SetSchemaUpdate
                    | SetTableCommentUpdate
                    | UpdateSnapshotVersionUpdate
                ):
                    try:
                        if not isinstance(data, dict):
                            raise TypeError()
                        updates_item_type_0 = SetPropertiesUpdate.from_dict(data)

                        return updates_item_type_0
                    except (TypeError, ValueError, AttributeError, KeyError):
                        pass
                    try:
                        if not isinstance(data, dict):
                            raise TypeError()
                        updates_item_type_1 = RemovePropertiesUpdate.from_dict(data)

                        return updates_item_type_1
                    except (TypeError, ValueError, AttributeError, KeyError):
                        pass
                    try:
                        if not isinstance(data, dict):
                            raise TypeError()
                        updates_item_type_2 = SetSchemaUpdate.from_dict(data)

                        return updates_item_type_2
                    except (TypeError, ValueError, AttributeError, KeyError):
                        pass
                    try:
                        if not isinstance(data, dict):
                            raise TypeError()
                        updates_item_type_3 = SetTableCommentUpdate.from_dict(data)

                        return updates_item_type_3
                    except (TypeError, ValueError, AttributeError, KeyError):
                        pass
                    try:
                        if not isinstance(data, dict):
                            raise TypeError()
                        updates_item_type_4 = AddCommitUpdate.from_dict(data)

                        return updates_item_type_4
                    except (TypeError, ValueError, AttributeError, KeyError):
                        pass
                    try:
                        if not isinstance(data, dict):
                            raise TypeError()
                        updates_item_type_5 = (
                            SetLatestBackfilledVersionUpdate.from_dict(data)
                        )

                        return updates_item_type_5
                    except (TypeError, ValueError, AttributeError, KeyError):
                        pass
                    try:
                        if not isinstance(data, dict):
                            raise TypeError()
                        updates_item_type_6 = SetProtocolUpdate.from_dict(data)

                        return updates_item_type_6
                    except (TypeError, ValueError, AttributeError, KeyError):
                        pass
                    try:
                        if not isinstance(data, dict):
                            raise TypeError()
                        updates_item_type_7 = SetDomainMetadataUpdate.from_dict(data)

                        return updates_item_type_7
                    except (TypeError, ValueError, AttributeError, KeyError):
                        pass
                    try:
                        if not isinstance(data, dict):
                            raise TypeError()
                        updates_item_type_8 = RemoveDomainMetadataUpdate.from_dict(data)

                        return updates_item_type_8
                    except (TypeError, ValueError, AttributeError, KeyError):
                        pass
                    try:
                        if not isinstance(data, dict):
                            raise TypeError()
                        updates_item_type_9 = SetPartitionColumnsUpdate.from_dict(data)

                        return updates_item_type_9
                    except (TypeError, ValueError, AttributeError, KeyError):
                        pass
                    try:
                        if not isinstance(data, dict):
                            raise TypeError()
                        updates_item_type_10 = UpdateSnapshotVersionUpdate.from_dict(
                            data
                        )

                        return updates_item_type_10
                    except (TypeError, ValueError, AttributeError, KeyError):
                        pass
                    try:
                        if not isinstance(data, dict):
                            raise TypeError()
                        updates_item_type_11 = AddConstraintUpdate.from_dict(data)

                        return updates_item_type_11
                    except (TypeError, ValueError, AttributeError, KeyError):
                        pass
                    if not isinstance(data, dict):
                        raise TypeError()
                    updates_item_type_12 = DropConstraintUpdate.from_dict(data)

                    return updates_item_type_12

                updates_item = _parse_updates_item(updates_item_data)

                updates.append(updates_item)

        update_table_request = cls(
            requirements=requirements,
            updates=updates,
        )

        return update_table_request
