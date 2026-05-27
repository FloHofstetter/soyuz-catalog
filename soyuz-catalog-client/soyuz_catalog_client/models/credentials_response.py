from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.storage_credential import StorageCredential


T = TypeVar("T", bound="CredentialsResponse")


@_attrs_define
class CredentialsResponse:
    """Response for every credential-vending endpoint in the Delta API.

    soyuz always returns ``storage_credentials = []``. This matches
    the existing soyuz temporary-credentials stub posture (see
    ``DIVERGENCES.md``) and is preferred over a 501 because Delta
    clients interpret an empty list as "use the URL directly" and
    keep progressing, whereas a 501 would abort the whole write
    path on a non-feature. ADR-0009 covers the rationale.

        Attributes:
            storage_credentials (list[StorageCredential] | Unset):
    """

    storage_credentials: list[StorageCredential] | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.storage_credential import StorageCredential

        storage_credentials: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.storage_credentials, Unset):
            storage_credentials = []
            for storage_credentials_item_data in self.storage_credentials:
                storage_credentials_item = storage_credentials_item_data.to_dict()
                storage_credentials.append(storage_credentials_item)

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if storage_credentials is not UNSET:
            field_dict["storage-credentials"] = storage_credentials

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.storage_credential import StorageCredential

        d = dict(src_dict)
        _storage_credentials = d.pop("storage-credentials", UNSET)
        storage_credentials: list[StorageCredential] | Unset = UNSET
        if _storage_credentials is not UNSET:
            storage_credentials = []
            for storage_credentials_item_data in _storage_credentials:
                storage_credentials_item = StorageCredential.from_dict(
                    storage_credentials_item_data
                )

                storage_credentials.append(storage_credentials_item)

        credentials_response = cls(
            storage_credentials=storage_credentials,
        )

        return credentials_response
