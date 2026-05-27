from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AwsCredentials")


@_attrs_define
class AwsCredentials:
    """AWS STS temporary credentials payload (nested in ``TemporaryCredentials``).

    Shape mirrors the UC OpenAPI ``AwsCredentials`` schema exactly. soyuz
    never populates this object — real STS vending is out of scope (no
    credential vending; see README design principle 3) — but the class
    exists so the response schema is 1:1 with the spec for clients
    that rely on OpenAPI-generated types.

        Attributes:
            access_key_id (None | str | Unset):
            secret_access_key (None | str | Unset):
            session_token (None | str | Unset):
    """

    access_key_id: None | str | Unset = UNSET
    secret_access_key: None | str | Unset = UNSET
    session_token: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        access_key_id: None | str | Unset
        if isinstance(self.access_key_id, Unset):
            access_key_id = UNSET
        else:
            access_key_id = self.access_key_id

        secret_access_key: None | str | Unset
        if isinstance(self.secret_access_key, Unset):
            secret_access_key = UNSET
        else:
            secret_access_key = self.secret_access_key

        session_token: None | str | Unset
        if isinstance(self.session_token, Unset):
            session_token = UNSET
        else:
            session_token = self.session_token

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if access_key_id is not UNSET:
            field_dict["access_key_id"] = access_key_id
        if secret_access_key is not UNSET:
            field_dict["secret_access_key"] = secret_access_key
        if session_token is not UNSET:
            field_dict["session_token"] = session_token

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_access_key_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        access_key_id = _parse_access_key_id(d.pop("access_key_id", UNSET))

        def _parse_secret_access_key(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        secret_access_key = _parse_secret_access_key(d.pop("secret_access_key", UNSET))

        def _parse_session_token(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        session_token = _parse_session_token(d.pop("session_token", UNSET))

        aws_credentials = cls(
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
            session_token=session_token,
        )

        aws_credentials.additional_properties = d
        return aws_credentials

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
