from __future__ import annotations

from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    BinaryIO,
    Generator,
    Literal,
    TextIO,
    TypeVar,
    cast,
)

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.delta_protocol import DeltaProtocol
    from ..models.required_properties import RequiredProperties
    from ..models.storage_credential import StorageCredential
    from ..models.suggested_properties import SuggestedProperties
    from ..models.suggested_protocol import SuggestedProtocol


T = TypeVar("T", bound="StagingTableResponse")


@_attrs_define
class StagingTableResponse:
    """Response body for ``createStagingTable``.

    The ``location`` is derived from the existing
    :class:`soyuz_catalog.models.StagingTable.staging_location` so a
    Delta client reaches the same UC-managed path through either the
    main UC API or the Delta API. ``required_protocol`` is soyuz'
    fixed default; ``storage_credentials`` is always empty; the
    ``required_properties`` and ``suggested_properties`` maps are
    always empty too — soyuz has no opinion on Delta-specific
    property constraints at allocation time.

        Attributes:
            location (str):
            required_protocol (DeltaProtocol): Delta table protocol version and feature flags.

                soyuz does not track per-table protocol versions — the project
                treats every table as readable by the standard Delta reader and
                writer versions — so on load responses this model is synthesised
                with a fixed default. On write paths (``createTable``,
                ``set-protocol`` update), the model is accepted from the client
                but its values are discarded; the response echoes the client's
                values so well-behaved clients see no drift within a single
                session. Documented in ADR-0009.
            table_id (str):
            table_type (Literal['MANAGED']):
            required_properties (RequiredProperties | Unset):
            storage_credentials (list[StorageCredential] | Unset):
            suggested_properties (SuggestedProperties | Unset):
            suggested_protocol (SuggestedProtocol | Unset): Suggested Delta features a client should enable if supported.

                soyuz advertises none — it does not have an opinion about which
                features a staging-table writer *should* use, only a minimum it
                *must* satisfy, which is carried by :class:`DeltaProtocol` on the
                ``required_protocol`` field.
    """

    location: str
    required_protocol: DeltaProtocol
    table_id: str
    table_type: Literal["MANAGED"]
    required_properties: RequiredProperties | Unset = UNSET
    storage_credentials: list[StorageCredential] | Unset = UNSET
    suggested_properties: SuggestedProperties | Unset = UNSET
    suggested_protocol: SuggestedProtocol | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.delta_protocol import DeltaProtocol
        from ..models.required_properties import RequiredProperties
        from ..models.storage_credential import StorageCredential
        from ..models.suggested_properties import SuggestedProperties
        from ..models.suggested_protocol import SuggestedProtocol

        location = self.location

        required_protocol = self.required_protocol.to_dict()

        table_id = self.table_id

        table_type = self.table_type

        required_properties: dict[str, Any] | Unset = UNSET
        if not isinstance(self.required_properties, Unset):
            required_properties = self.required_properties.to_dict()

        storage_credentials: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.storage_credentials, Unset):
            storage_credentials = []
            for storage_credentials_item_data in self.storage_credentials:
                storage_credentials_item = storage_credentials_item_data.to_dict()
                storage_credentials.append(storage_credentials_item)

        suggested_properties: dict[str, Any] | Unset = UNSET
        if not isinstance(self.suggested_properties, Unset):
            suggested_properties = self.suggested_properties.to_dict()

        suggested_protocol: dict[str, Any] | Unset = UNSET
        if not isinstance(self.suggested_protocol, Unset):
            suggested_protocol = self.suggested_protocol.to_dict()

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "location": location,
                "required-protocol": required_protocol,
                "table-id": table_id,
                "table-type": table_type,
            }
        )
        if required_properties is not UNSET:
            field_dict["required-properties"] = required_properties
        if storage_credentials is not UNSET:
            field_dict["storage-credentials"] = storage_credentials
        if suggested_properties is not UNSET:
            field_dict["suggested-properties"] = suggested_properties
        if suggested_protocol is not UNSET:
            field_dict["suggested-protocol"] = suggested_protocol

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.delta_protocol import DeltaProtocol
        from ..models.required_properties import RequiredProperties
        from ..models.storage_credential import StorageCredential
        from ..models.suggested_properties import SuggestedProperties
        from ..models.suggested_protocol import SuggestedProtocol

        d = dict(src_dict)
        location = d.pop("location")

        required_protocol = DeltaProtocol.from_dict(d.pop("required-protocol"))

        table_id = d.pop("table-id")

        table_type = cast(Literal["MANAGED"], d.pop("table-type"))
        if table_type != "MANAGED":
            raise ValueError(
                f"table-type must match const 'MANAGED', got '{table_type}'"
            )

        _required_properties = d.pop("required-properties", UNSET)
        required_properties: RequiredProperties | Unset
        if isinstance(_required_properties, Unset):
            required_properties = UNSET
        else:
            required_properties = RequiredProperties.from_dict(_required_properties)

        _storage_credentials = d.pop("storage-credentials", UNSET)
        storage_credentials: list[StorageCredential] | Unset = UNSET
        if _storage_credentials is not UNSET:
            storage_credentials = []
            for storage_credentials_item_data in _storage_credentials:
                storage_credentials_item = StorageCredential.from_dict(
                    storage_credentials_item_data
                )

                storage_credentials.append(storage_credentials_item)

        _suggested_properties = d.pop("suggested-properties", UNSET)
        suggested_properties: SuggestedProperties | Unset
        if isinstance(_suggested_properties, Unset):
            suggested_properties = UNSET
        else:
            suggested_properties = SuggestedProperties.from_dict(_suggested_properties)

        _suggested_protocol = d.pop("suggested-protocol", UNSET)
        suggested_protocol: SuggestedProtocol | Unset
        if isinstance(_suggested_protocol, Unset):
            suggested_protocol = UNSET
        else:
            suggested_protocol = SuggestedProtocol.from_dict(_suggested_protocol)

        staging_table_response = cls(
            location=location,
            required_protocol=required_protocol,
            table_id=table_id,
            table_type=table_type,
            required_properties=required_properties,
            storage_credentials=storage_credentials,
            suggested_properties=suggested_properties,
            suggested_protocol=suggested_protocol,
        )

        return staging_table_response
