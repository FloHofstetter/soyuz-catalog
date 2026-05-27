from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.credential_info import CredentialInfo


T = TypeVar("T", bound="ListCredentialsResponse")


@_attrs_define
class ListCredentialsResponse:
    """Response shape for ``GET /credentials``.

    Keyset pagination via ``next_page_token``; ``?purpose=`` query
    filter is accepted (currently only ``STORAGE`` exists) and
    validated as a ``Literal`` in the route signature.

        Attributes:
            credentials (list[CredentialInfo]):
            next_page_token (None | str | Unset):
    """

    credentials: list[CredentialInfo]
    next_page_token: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.credential_info import CredentialInfo

        credentials = []
        for credentials_item_data in self.credentials:
            credentials_item = credentials_item_data.to_dict()
            credentials.append(credentials_item)

        next_page_token: None | str | Unset
        if isinstance(self.next_page_token, Unset):
            next_page_token = UNSET
        else:
            next_page_token = self.next_page_token

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "credentials": credentials,
            }
        )
        if next_page_token is not UNSET:
            field_dict["next_page_token"] = next_page_token

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.credential_info import CredentialInfo

        d = dict(src_dict)
        credentials = []
        _credentials = d.pop("credentials")
        for credentials_item_data in _credentials:
            credentials_item = CredentialInfo.from_dict(credentials_item_data)

            credentials.append(credentials_item)

        def _parse_next_page_token(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        next_page_token = _parse_next_page_token(d.pop("next_page_token", UNSET))

        list_credentials_response = cls(
            credentials=credentials,
            next_page_token=next_page_token,
        )

        list_credentials_response.additional_properties = d
        return list_credentials_response

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
