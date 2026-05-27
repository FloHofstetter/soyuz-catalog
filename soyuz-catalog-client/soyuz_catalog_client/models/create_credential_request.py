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

if TYPE_CHECKING:
    from ..models.aws_iam_role_request import AwsIamRoleRequest


T = TypeVar("T", bound="CreateCredentialRequest")


@_attrs_define
class CreateCredentialRequest:
    """Request body for ``POST /credentials``.

    ``name`` is required. ``aws_iam_role`` is the only supported
    credential payload because the upstream UC OpenAPI ``all.yaml`` we
    pin as the contract defines only that shape; Azure and GCP
    variants that exist in forks are deliberately not modelled (see
    :class:`soyuz_catalog.models.Credential` for the reasoning).

    ``purpose`` is optional and defaults to ``STORAGE`` — the only
    value defined by ``CredentialPurpose`` today. Typing it as a
    ``Literal`` means a typo (``STORGE``) surfaces as 422 at the
    Pydantic layer instead of silently landing in the DB.

        Attributes:
            name (str):
            aws_iam_role (AwsIamRoleRequest | None | Unset):
            comment (None | str | Unset):
            purpose (Literal['STORAGE'] | None | Unset):
    """

    name: str
    aws_iam_role: AwsIamRoleRequest | None | Unset = UNSET
    comment: None | str | Unset = UNSET
    purpose: Literal["STORAGE"] | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.aws_iam_role_request import AwsIamRoleRequest

        name = self.name

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

        purpose: Literal["STORAGE"] | None | Unset
        if isinstance(self.purpose, Unset):
            purpose = UNSET
        else:
            purpose = self.purpose

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
            }
        )
        if aws_iam_role is not UNSET:
            field_dict["aws_iam_role"] = aws_iam_role
        if comment is not UNSET:
            field_dict["comment"] = comment
        if purpose is not UNSET:
            field_dict["purpose"] = purpose

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.aws_iam_role_request import AwsIamRoleRequest

        d = dict(src_dict)
        name = d.pop("name")

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

        def _parse_purpose(data: object) -> Literal["STORAGE"] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            purpose_type_0 = cast(Literal["STORAGE"], data)
            if purpose_type_0 != "STORAGE":
                raise ValueError(
                    f"purpose_type_0 must match const 'STORAGE', got '{purpose_type_0}'"
                )
            return purpose_type_0
            return cast(Literal["STORAGE"] | None | Unset, data)

        purpose = _parse_purpose(d.pop("purpose", UNSET))

        create_credential_request = cls(
            name=name,
            aws_iam_role=aws_iam_role,
            comment=comment,
            purpose=purpose,
        )

        return create_credential_request
