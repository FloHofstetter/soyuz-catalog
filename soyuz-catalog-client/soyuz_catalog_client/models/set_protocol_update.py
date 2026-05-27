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


T = TypeVar("T", bound="SetProtocolUpdate")


@_attrs_define
class SetProtocolUpdate:
    """``set-protocol`` — accepted as a no-op.

    soyuz does not track per-table protocol versions; rejecting
    these would break clients that always bump protocol on write.
    The service layer logs a warning and discards the payload; the
    response echoes the original client value so well-behaved
    clients see no drift. ADR-0009.

        Attributes:
            action (Literal['set-protocol']):
            protocol (DeltaProtocol): Delta table protocol version and feature flags.

                soyuz does not track per-table protocol versions — the project
                treats every table as readable by the standard Delta reader and
                writer versions — so on load responses this model is synthesised
                with a fixed default. On write paths (``createTable``,
                ``set-protocol`` update), the model is accepted from the client
                but its values are discarded; the response echoes the client's
                values so well-behaved clients see no drift within a single
                session. Documented in ADR-0009.
    """

    action: Literal["set-protocol"]
    protocol: DeltaProtocol

    def to_dict(self) -> dict[str, Any]:
        from ..models.delta_protocol import DeltaProtocol

        action = self.action

        protocol = self.protocol.to_dict()

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "action": action,
                "protocol": protocol,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.delta_protocol import DeltaProtocol

        d = dict(src_dict)
        action = cast(Literal["set-protocol"], d.pop("action"))
        if action != "set-protocol":
            raise ValueError(f"action must match const 'set-protocol', got '{action}'")

        protocol = DeltaProtocol.from_dict(d.pop("protocol"))

        set_protocol_update = cls(
            action=action,
            protocol=protocol,
        )

        return set_protocol_update
