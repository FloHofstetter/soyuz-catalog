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
    from ..models.aws_iam_role_response import AwsIamRoleResponse


T = TypeVar("T", bound="CredentialInfo")


@_attrs_define
class CredentialInfo:
    """Response shape for a Unity Catalog storage credential.

    Credentials live at the root of the metastore namespace (no catalog
    or schema parent), so there is no ``full_name`` trick to compute —
    the user-facing identifier is just ``name`` and the spec does not
    even define ``full_name`` for this resource. ``aws_iam_role`` is
    always populated on credentials that were created with a role, with
    ``external_id`` as the server-minted confused-deputy mitigation.

        Attributes:
            aws_iam_role (AwsIamRoleResponse | None | Unset):
            comment (None | str | Unset):
            created_at (int | None | Unset):
            created_by (None | str | Unset):
            id (None | str | Unset):
            name (None | str | Unset):
            owner (None | str | Unset):
            purpose (Literal['STORAGE'] | None | Unset):
            updated_at (int | None | Unset):
            updated_by (None | str | Unset):
    """

    aws_iam_role: AwsIamRoleResponse | None | Unset = UNSET
    comment: None | str | Unset = UNSET
    created_at: int | None | Unset = UNSET
    created_by: None | str | Unset = UNSET
    id: None | str | Unset = UNSET
    name: None | str | Unset = UNSET
    owner: None | str | Unset = UNSET
    purpose: Literal["STORAGE"] | None | Unset = UNSET
    updated_at: int | None | Unset = UNSET
    updated_by: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.aws_iam_role_response import AwsIamRoleResponse

        aws_iam_role: dict[str, Any] | None | Unset
        if isinstance(self.aws_iam_role, Unset):
            aws_iam_role = UNSET
        elif isinstance(self.aws_iam_role, AwsIamRoleResponse):
            aws_iam_role = self.aws_iam_role.to_dict()
        else:
            aws_iam_role = self.aws_iam_role

        comment: None | str | Unset
        if isinstance(self.comment, Unset):
            comment = UNSET
        else:
            comment = self.comment

        created_at: int | None | Unset
        if isinstance(self.created_at, Unset):
            created_at = UNSET
        else:
            created_at = self.created_at

        created_by: None | str | Unset
        if isinstance(self.created_by, Unset):
            created_by = UNSET
        else:
            created_by = self.created_by

        id: None | str | Unset
        if isinstance(self.id, Unset):
            id = UNSET
        else:
            id = self.id

        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        owner: None | str | Unset
        if isinstance(self.owner, Unset):
            owner = UNSET
        else:
            owner = self.owner

        purpose: Literal["STORAGE"] | None | Unset
        if isinstance(self.purpose, Unset):
            purpose = UNSET
        else:
            purpose = self.purpose

        updated_at: int | None | Unset
        if isinstance(self.updated_at, Unset):
            updated_at = UNSET
        else:
            updated_at = self.updated_at

        updated_by: None | str | Unset
        if isinstance(self.updated_by, Unset):
            updated_by = UNSET
        else:
            updated_by = self.updated_by

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if aws_iam_role is not UNSET:
            field_dict["aws_iam_role"] = aws_iam_role
        if comment is not UNSET:
            field_dict["comment"] = comment
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if created_by is not UNSET:
            field_dict["created_by"] = created_by
        if id is not UNSET:
            field_dict["id"] = id
        if name is not UNSET:
            field_dict["name"] = name
        if owner is not UNSET:
            field_dict["owner"] = owner
        if purpose is not UNSET:
            field_dict["purpose"] = purpose
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if updated_by is not UNSET:
            field_dict["updated_by"] = updated_by

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.aws_iam_role_response import AwsIamRoleResponse

        d = dict(src_dict)

        def _parse_aws_iam_role(data: object) -> AwsIamRoleResponse | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                aws_iam_role_type_0 = AwsIamRoleResponse.from_dict(data)

                return aws_iam_role_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(AwsIamRoleResponse | None | Unset, data)

        aws_iam_role = _parse_aws_iam_role(d.pop("aws_iam_role", UNSET))

        def _parse_comment(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        comment = _parse_comment(d.pop("comment", UNSET))

        def _parse_created_at(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        created_at = _parse_created_at(d.pop("created_at", UNSET))

        def _parse_created_by(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        created_by = _parse_created_by(d.pop("created_by", UNSET))

        def _parse_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        id = _parse_id(d.pop("id", UNSET))

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_owner(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        owner = _parse_owner(d.pop("owner", UNSET))

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

        def _parse_updated_at(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        updated_at = _parse_updated_at(d.pop("updated_at", UNSET))

        def _parse_updated_by(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        updated_by = _parse_updated_by(d.pop("updated_by", UNSET))

        credential_info = cls(
            aws_iam_role=aws_iam_role,
            comment=comment,
            created_at=created_at,
            created_by=created_by,
            id=id,
            name=name,
            owner=owner,
            purpose=purpose,
            updated_at=updated_at,
            updated_by=updated_by,
        )

        credential_info.additional_properties = d
        return credential_info

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
