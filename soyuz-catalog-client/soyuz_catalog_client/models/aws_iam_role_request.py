from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AwsIamRoleRequest")


@_attrs_define
class AwsIamRoleRequest:
    """AWS IAM role payload nested in credential create/update requests.

    The UC spec defines exactly one required field, ``role_arn``.
    ``extra="forbid"`` rejects typos (e.g. ``rolearn``) with 422
    instead of silently dropping them — same bug-fix policy as every
    other request body.

        Attributes:
            role_arn (str):
    """

    role_arn: str

    def to_dict(self) -> dict[str, Any]:
        role_arn = self.role_arn

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "role_arn": role_arn,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        role_arn = d.pop("role_arn")

        aws_iam_role_request = cls(
            role_arn=role_arn,
        )

        return aws_iam_role_request
