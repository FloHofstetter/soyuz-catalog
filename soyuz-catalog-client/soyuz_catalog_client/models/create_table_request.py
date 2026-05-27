from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.create_table_request_data_source_format import (
    CreateTableRequestDataSourceFormat,
)
from ..models.create_table_request_table_type import CreateTableRequestTableType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.delta_column import DeltaColumn
    from ..models.delta_protocol import DeltaProtocol
    from ..models.domain_metadata_updates import DomainMetadataUpdates
    from ..models.properties import Properties


T = TypeVar("T", bound="CreateTableRequest")


@_attrs_define
class CreateTableRequest:
    """Request body for ``POST .../tables``.

    Every field mirrors the spec's ``CreateTableRequest``. The
    ``protocol`` and ``domain_metadata`` fields are **accepted and
    discarded** by the service layer — soyuz does not track per-table
    protocol versions or domain metadata and rejecting them would
    break Delta clients that always emit them. See ADR-0009.

        Attributes:
            columns (list[DeltaColumn]):
            data_source_format (CreateTableRequestDataSourceFormat):
            location (str):
            name (str):
            protocol (DeltaProtocol): Delta table protocol version and feature flags.

                soyuz does not track per-table protocol versions — the project
                treats every table as readable by the standard Delta reader and
                writer versions — so on load responses this model is synthesised
                with a fixed default. On write paths (``createTable``,
                ``set-protocol`` update), the model is accepted from the client
                but its values are discarded; the response echoes the client's
                values so well-behaved clients see no drift within a single
                session. Documented in ADR-0009.
            table_type (CreateTableRequestTableType):
            comment (None | str | Unset):
            domain_metadata (DomainMetadataUpdates | None | Unset):
            partition_columns (list[str] | Unset):
            properties (Properties | Unset):
    """

    columns: list[DeltaColumn]
    data_source_format: CreateTableRequestDataSourceFormat
    location: str
    name: str
    protocol: DeltaProtocol
    table_type: CreateTableRequestTableType
    comment: None | str | Unset = UNSET
    domain_metadata: DomainMetadataUpdates | None | Unset = UNSET
    partition_columns: list[str] | Unset = UNSET
    properties: Properties | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.delta_column import DeltaColumn
        from ..models.delta_protocol import DeltaProtocol
        from ..models.domain_metadata_updates import DomainMetadataUpdates
        from ..models.properties import Properties

        columns = []
        for columns_item_data in self.columns:
            columns_item = columns_item_data.to_dict()
            columns.append(columns_item)

        data_source_format = self.data_source_format.value

        location = self.location

        name = self.name

        protocol = self.protocol.to_dict()

        table_type = self.table_type.value

        comment: None | str | Unset
        if isinstance(self.comment, Unset):
            comment = UNSET
        else:
            comment = self.comment

        domain_metadata: dict[str, Any] | None | Unset
        if isinstance(self.domain_metadata, Unset):
            domain_metadata = UNSET
        elif isinstance(self.domain_metadata, DomainMetadataUpdates):
            domain_metadata = self.domain_metadata.to_dict()
        else:
            domain_metadata = self.domain_metadata

        partition_columns: list[str] | Unset = UNSET
        if not isinstance(self.partition_columns, Unset):
            partition_columns = self.partition_columns

        properties: dict[str, Any] | Unset = UNSET
        if not isinstance(self.properties, Unset):
            properties = self.properties.to_dict()

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "columns": columns,
                "data-source-format": data_source_format,
                "location": location,
                "name": name,
                "protocol": protocol,
                "table-type": table_type,
            }
        )
        if comment is not UNSET:
            field_dict["comment"] = comment
        if domain_metadata is not UNSET:
            field_dict["domain-metadata"] = domain_metadata
        if partition_columns is not UNSET:
            field_dict["partition-columns"] = partition_columns
        if properties is not UNSET:
            field_dict["properties"] = properties

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.delta_column import DeltaColumn
        from ..models.delta_protocol import DeltaProtocol
        from ..models.domain_metadata_updates import DomainMetadataUpdates
        from ..models.properties import Properties

        d = dict(src_dict)
        columns = []
        _columns = d.pop("columns")
        for columns_item_data in _columns:
            columns_item = DeltaColumn.from_dict(columns_item_data)

            columns.append(columns_item)

        data_source_format = CreateTableRequestDataSourceFormat(
            d.pop("data-source-format")
        )

        location = d.pop("location")

        name = d.pop("name")

        protocol = DeltaProtocol.from_dict(d.pop("protocol"))

        table_type = CreateTableRequestTableType(d.pop("table-type"))

        def _parse_comment(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        comment = _parse_comment(d.pop("comment", UNSET))

        def _parse_domain_metadata(
            data: object,
        ) -> DomainMetadataUpdates | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                domain_metadata_type_0 = DomainMetadataUpdates.from_dict(data)

                return domain_metadata_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(DomainMetadataUpdates | None | Unset, data)

        domain_metadata = _parse_domain_metadata(d.pop("domain-metadata", UNSET))

        partition_columns = cast(list[str], d.pop("partition-columns", UNSET))

        _properties = d.pop("properties", UNSET)
        properties: Properties | Unset
        if isinstance(_properties, Unset):
            properties = UNSET
        else:
            properties = Properties.from_dict(_properties)

        create_table_request = cls(
            columns=columns,
            data_source_format=data_source_format,
            location=location,
            name=name,
            protocol=protocol,
            table_type=table_type,
            comment=comment,
            domain_metadata=domain_metadata,
            partition_columns=partition_columns,
            properties=properties,
        )

        return create_table_request
