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
    from ..models.domain_metadata_updates import DomainMetadataUpdates


T = TypeVar("T", bound="SetDomainMetadataUpdate")


@_attrs_define
class SetDomainMetadataUpdate:
    """``set-domain-metadata`` variant of :data:`TableUpdate`.

    Delta clients emit this action whenever clustering config or row
    tracking changes; soyuz does not store domain metadata at all
    because nothing in the project consumes it. The payload is
    validated so malformed shapes still surface as 422, but the
    service layer silently discards it. Rejecting would break every
    Delta client that always emits ``delta.clustering`` or
    ``delta.rowTracking`` on schema evolution. ADR-0009 covers the
    accept-and-discard posture.

        Attributes:
            action (Literal['set-domain-metadata']):
            updates (DomainMetadataUpdates): Known Delta domain-metadata subkeys, plus a catch-all via ``extra``.

                soyuz does not store domain metadata (clustering config, row
                tracking) because nothing in the project consumes it. The model
                still validates the shape so that ``set-domain-metadata`` updates
                can be parsed and then silently discarded — rejecting them would
                break Delta clients that always emit them. See ADR-0009.
    """

    action: Literal["set-domain-metadata"]
    updates: DomainMetadataUpdates

    def to_dict(self) -> dict[str, Any]:
        from ..models.domain_metadata_updates import DomainMetadataUpdates

        action = self.action

        updates = self.updates.to_dict()

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "action": action,
                "updates": updates,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.domain_metadata_updates import DomainMetadataUpdates

        d = dict(src_dict)
        action = cast(Literal["set-domain-metadata"], d.pop("action"))
        if action != "set-domain-metadata":
            raise ValueError(
                f"action must match const 'set-domain-metadata', got '{action}'"
            )

        updates = DomainMetadataUpdates.from_dict(d.pop("updates"))

        set_domain_metadata_update = cls(
            action=action,
            updates=updates,
        )

        return set_domain_metadata_update
