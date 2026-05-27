from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.aws_iam_role_request import AwsIamRoleRequest


T = TypeVar("T", bound="UpdateCredentialRequest")


@_attrs_define
class UpdateCredentialRequest:
    """Request body for ``PATCH /credentials/{name}``.

    Replace-style PATCH semantics driven by ``model_fields_set`` in
    the service layer, same as every other update endpoint. The spec
    allows ``new_name``, ``comment``, ``owner``, and a fresh
    ``aws_iam_role`` payload. ``extra="forbid"`` rejects unknown or
    read-only fields (``id``, ``purpose``, ``created_at``, …) with
    HTTP 422.

        Attributes:
            aws_iam_role (AwsIamRoleRequest | None | Unset):
            comment (None | str | Unset):
            new_name (None | str | Unset):
            owner (None | str | Unset):
    """

    aws_iam_role: AwsIamRoleRequest | None | Unset = UNSET
    comment: None | str | Unset = UNSET
    new_name: None | str | Unset = UNSET
    owner: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.aws_iam_role_request import AwsIamRoleRequest

        aws_iam_role: dict[str, Any] | None | Unset
        if isinstance(self.aws_iam_role, Unset):
            aws_iam_role = UNSET
        elif isinstance(self.aws_iam_role, AwsIamRoleRequest):
            aws_iam_role = self.aws_iam_role.to_dict()
        else:
            aws_iam_role = self.aws_iam_role

        comment: None | str | Unset
        if isinstance(self.comment, Unset):
            comment = UNSET
        else:
            comment = self.comment

        new_name: None | str | Unset
        if isinstance(self.new_name, Unset):
            new_name = UNSET
        else:
            new_name = self.new_name

        owner: None | str | Unset
        if isinstance(self.owner, Unset):
            owner = UNSET
        else:
            owner = self.owner

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if aws_iam_role is not UNSET:
            field_dict["aws_iam_role"] = aws_iam_role
        if comment is not UNSET:
            field_dict["comment"] = comment
        if new_name is not UNSET:
            field_dict["new_name"] = new_name
        if owner is not UNSET:
            field_dict["owner"] = owner

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.aws_iam_role_request import AwsIamRoleRequest

        d = dict(src_dict)

        def _parse_aws_iam_role(data: object) -> AwsIamRoleRequest | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                aws_iam_role_type_0 = AwsIamRoleRequest.from_dict(data)

                return aws_iam_role_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(AwsIamRoleRequest | None | Unset, data)

        aws_iam_role = _parse_aws_iam_role(d.pop("aws_iam_role", UNSET))

        def _parse_comment(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        comment = _parse_comment(d.pop("comment", UNSET))

        def _parse_new_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        new_name = _parse_new_name(d.pop("new_name", UNSET))

        def _parse_owner(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        owner = _parse_owner(d.pop("owner", UNSET))

        update_credential_request = cls(
            aws_iam_role=aws_iam_role,
            comment=comment,
            new_name=new_name,
            owner=owner,
        )

        return update_credential_request
