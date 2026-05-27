from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AwsIamRoleResponse")


@_attrs_define
class AwsIamRoleResponse:
    """AWS IAM role payload on ``CredentialInfo`` responses.

    Mirrors the UC spec's ``AwsIamRoleResponse``: ``role_arn`` is the
    one the client supplied, ``external_id`` is the confused-deputy
    mitigation (server-minted once on create, never rotated by
    PATCH), and ``unity_catalog_iam_arn`` is the IAM identity the
    Unity Catalog server itself runs as. soyuz has no such identity —
    see ``DIVERGENCES.md`` — so that field is always ``None`` and the
    route serialises with ``exclude_none`` to keep it off the wire.

        Attributes:
            external_id (None | str | Unset):
            role_arn (None | str | Unset):
            unity_catalog_iam_arn (None | str | Unset):
    """

    external_id: None | str | Unset = UNSET
    role_arn: None | str | Unset = UNSET
    unity_catalog_iam_arn: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        external_id: None | str | Unset
        if isinstance(self.external_id, Unset):
            external_id = UNSET
        else:
            external_id = self.external_id

        role_arn: None | str | Unset
        if isinstance(self.role_arn, Unset):
            role_arn = UNSET
        else:
            role_arn = self.role_arn

        unity_catalog_iam_arn: None | str | Unset
        if isinstance(self.unity_catalog_iam_arn, Unset):
            unity_catalog_iam_arn = UNSET
        else:
            unity_catalog_iam_arn = self.unity_catalog_iam_arn

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if external_id is not UNSET:
            field_dict["external_id"] = external_id
        if role_arn is not UNSET:
            field_dict["role_arn"] = role_arn
        if unity_catalog_iam_arn is not UNSET:
            field_dict["unity_catalog_iam_arn"] = unity_catalog_iam_arn

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_external_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        external_id = _parse_external_id(d.pop("external_id", UNSET))

        def _parse_role_arn(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        role_arn = _parse_role_arn(d.pop("role_arn", UNSET))

        def _parse_unity_catalog_iam_arn(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        unity_catalog_iam_arn = _parse_unity_catalog_iam_arn(
            d.pop("unity_catalog_iam_arn", UNSET)
        )

        aws_iam_role_response = cls(
            external_id=external_id,
            role_arn=role_arn,
            unity_catalog_iam_arn=unity_catalog_iam_arn,
        )

        aws_iam_role_response.additional_properties = d
        return aws_iam_role_response

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
