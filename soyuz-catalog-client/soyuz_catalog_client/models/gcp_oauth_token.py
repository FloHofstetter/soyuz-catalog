from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="GcpOauthToken")


@_attrs_define
class GcpOauthToken:
    """GCP OAuth token payload (nested in ``TemporaryCredentials``).

    Same "defined for spec parity but never populated" story as
    :class:`AwsCredentials`.

        Attributes:
            oauth_token (None | str | Unset):
    """

    oauth_token: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        oauth_token: None | str | Unset
        if isinstance(self.oauth_token, Unset):
            oauth_token = UNSET
        else:
            oauth_token = self.oauth_token

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if oauth_token is not UNSET:
            field_dict["oauth_token"] = oauth_token

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_oauth_token(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        oauth_token = _parse_oauth_token(d.pop("oauth_token", UNSET))

        gcp_oauth_token = cls(
            oauth_token=oauth_token,
        )

        gcp_oauth_token.additional_properties = d
        return gcp_oauth_token

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
