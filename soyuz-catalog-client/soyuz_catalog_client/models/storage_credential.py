from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.storage_credential_operation import StorageCredentialOperation
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.config import Config


T = TypeVar("T", bound="StorageCredential")


@_attrs_define
class StorageCredential:
    """Temporary storage credential — always empty on the wire in soyuz.

    soyuz does not vend cloud credentials (explicitly out of scope —
    metadata-only is design principle 3 in the README). The model exists so
    :class:`CredentialsResponse` and :class:`StagingTableResponse`
    can declare the field on the spec-defined shape; the list is
    always empty. Clients that use the returned storage location
    directly via ``file://`` or an externally-configured credential
    see no difference.

        Attributes:
            expiration_time_ms (int):
            operation (StorageCredentialOperation):
            prefix (str):
            config (Config | Unset):
    """

    expiration_time_ms: int
    operation: StorageCredentialOperation
    prefix: str
    config: Config | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.config import Config

        expiration_time_ms = self.expiration_time_ms

        operation = self.operation.value

        prefix = self.prefix

        config: dict[str, Any] | Unset = UNSET
        if not isinstance(self.config, Unset):
            config = self.config.to_dict()

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "expiration-time-ms": expiration_time_ms,
                "operation": operation,
                "prefix": prefix,
            }
        )
        if config is not UNSET:
            field_dict["config"] = config

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.config import Config

        d = dict(src_dict)
        expiration_time_ms = d.pop("expiration-time-ms")

        operation = StorageCredentialOperation(d.pop("operation"))

        prefix = d.pop("prefix")

        _config = d.pop("config", UNSET)
        config: Config | Unset
        if isinstance(_config, Unset):
            config = UNSET
        else:
            config = Config.from_dict(_config)

        storage_credential = cls(
            expiration_time_ms=expiration_time_ms,
            operation=operation,
            prefix=prefix,
            config=config,
        )

        return storage_credential
