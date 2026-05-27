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

T = TypeVar("T", bound="RemoveDomainMetadataUpdate")


@_attrs_define
class RemoveDomainMetadataUpdate:
    """``remove-domain-metadata`` variant of :data:`TableUpdate`.

    Complementary to :class:`SetDomainMetadataUpdate`: clients use it
    to drop a domain entry (clustering config, row tracking) that
    they previously set. soyuz never stored those entries in the
    first place, so the action is parsed and then silently
    discarded. ADR-0009.

        Attributes:
            action (Literal['remove-domain-metadata']):
            domains (list[str]):
    """

    action: Literal["remove-domain-metadata"]
    domains: list[str]

    def to_dict(self) -> dict[str, Any]:
        action = self.action

        domains = self.domains

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "action": action,
                "domains": domains,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        action = cast(Literal["remove-domain-metadata"], d.pop("action"))
        if action != "remove-domain-metadata":
            raise ValueError(
                f"action must match const 'remove-domain-metadata', got '{action}'"
            )

        domains = cast(list[str], d.pop("domains"))

        remove_domain_metadata_update = cls(
            action=action,
            domains=domains,
        )

        return remove_domain_metadata_update
