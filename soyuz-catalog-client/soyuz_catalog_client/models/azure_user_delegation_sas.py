from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AzureUserDelegationSAS")


@_attrs_define
class AzureUserDelegationSAS:
    """Azure user delegation SAS payload (nested in ``TemporaryCredentials``).

    Same "defined for spec parity but never populated" story as
    :class:`AwsCredentials`.

        Attributes:
            sas_token (None | str | Unset):
    """

    sas_token: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        sas_token: None | str | Unset
        if isinstance(self.sas_token, Unset):
            sas_token = UNSET
        else:
            sas_token = self.sas_token

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if sas_token is not UNSET:
            field_dict["sas_token"] = sas_token

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_sas_token(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        sas_token = _parse_sas_token(d.pop("sas_token", UNSET))

        azure_user_delegation_sas = cls(
            sas_token=sas_token,
        )

        azure_user_delegation_sas.additional_properties = d
        return azure_user_delegation_sas

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
