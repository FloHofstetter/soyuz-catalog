from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.aws_credentials import AwsCredentials
    from ..models.azure_user_delegation_sas import AzureUserDelegationSAS
    from ..models.gcp_oauth_token import GcpOauthToken


T = TypeVar("T", bound="TemporaryCredentials")


@_attrs_define
class TemporaryCredentials:
    """Response shape for the two ``/temporary-*-credentials`` endpoints.

    Every field is optional in the spec, which is fortunate because soyuz
    ships this endpoint as a spec-conformant **stub**: we always return
    ``expiration_time`` (so clients that cache on it behave correctly)
    but leave every cloud-specific field unset. The route serialises with
    ``response_model_exclude_none=True`` so the wire JSON is
    ``{"expiration_time": …}`` rather than a document full of nulls.

    The stub is deliberate: actual STS / SAS / OAuth vending requires
    boto3 / azure-identity / google-auth as runtime dependencies and
    per-deployment IAM configuration, which is out of scope for the
    metadata-only design (see README design principle 3 and
    ``DIVERGENCES.md`` for the full rationale).

        Attributes:
            aws_temp_credentials (AwsCredentials | None | Unset):
            azure_user_delegation_sas (AzureUserDelegationSAS | None | Unset):
            expiration_time (int | None | Unset):
            gcp_oauth_token (GcpOauthToken | None | Unset):
    """

    aws_temp_credentials: AwsCredentials | None | Unset = UNSET
    azure_user_delegation_sas: AzureUserDelegationSAS | None | Unset = UNSET
    expiration_time: int | None | Unset = UNSET
    gcp_oauth_token: GcpOauthToken | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.aws_credentials import AwsCredentials
        from ..models.azure_user_delegation_sas import AzureUserDelegationSAS
        from ..models.gcp_oauth_token import GcpOauthToken

        aws_temp_credentials: dict[str, Any] | None | Unset
        if isinstance(self.aws_temp_credentials, Unset):
            aws_temp_credentials = UNSET
        elif isinstance(self.aws_temp_credentials, AwsCredentials):
            aws_temp_credentials = self.aws_temp_credentials.to_dict()
        else:
            aws_temp_credentials = self.aws_temp_credentials

        azure_user_delegation_sas: dict[str, Any] | None | Unset
        if isinstance(self.azure_user_delegation_sas, Unset):
            azure_user_delegation_sas = UNSET
        elif isinstance(self.azure_user_delegation_sas, AzureUserDelegationSAS):
            azure_user_delegation_sas = self.azure_user_delegation_sas.to_dict()
        else:
            azure_user_delegation_sas = self.azure_user_delegation_sas

        expiration_time: int | None | Unset
        if isinstance(self.expiration_time, Unset):
            expiration_time = UNSET
        else:
            expiration_time = self.expiration_time

        gcp_oauth_token: dict[str, Any] | None | Unset
        if isinstance(self.gcp_oauth_token, Unset):
            gcp_oauth_token = UNSET
        elif isinstance(self.gcp_oauth_token, GcpOauthToken):
            gcp_oauth_token = self.gcp_oauth_token.to_dict()
        else:
            gcp_oauth_token = self.gcp_oauth_token

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if aws_temp_credentials is not UNSET:
            field_dict["aws_temp_credentials"] = aws_temp_credentials
        if azure_user_delegation_sas is not UNSET:
            field_dict["azure_user_delegation_sas"] = azure_user_delegation_sas
        if expiration_time is not UNSET:
            field_dict["expiration_time"] = expiration_time
        if gcp_oauth_token is not UNSET:
            field_dict["gcp_oauth_token"] = gcp_oauth_token

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.aws_credentials import AwsCredentials
        from ..models.azure_user_delegation_sas import AzureUserDelegationSAS
        from ..models.gcp_oauth_token import GcpOauthToken

        d = dict(src_dict)

        def _parse_aws_temp_credentials(data: object) -> AwsCredentials | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                aws_temp_credentials_type_0 = AwsCredentials.from_dict(data)

                return aws_temp_credentials_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(AwsCredentials | None | Unset, data)

        aws_temp_credentials = _parse_aws_temp_credentials(
            d.pop("aws_temp_credentials", UNSET)
        )

        def _parse_azure_user_delegation_sas(
            data: object,
        ) -> AzureUserDelegationSAS | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                azure_user_delegation_sas_type_0 = AzureUserDelegationSAS.from_dict(
                    data
                )

                return azure_user_delegation_sas_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(AzureUserDelegationSAS | None | Unset, data)

        azure_user_delegation_sas = _parse_azure_user_delegation_sas(
            d.pop("azure_user_delegation_sas", UNSET)
        )

        def _parse_expiration_time(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        expiration_time = _parse_expiration_time(d.pop("expiration_time", UNSET))

        def _parse_gcp_oauth_token(data: object) -> GcpOauthToken | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                gcp_oauth_token_type_0 = GcpOauthToken.from_dict(data)

                return gcp_oauth_token_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(GcpOauthToken | None | Unset, data)

        gcp_oauth_token = _parse_gcp_oauth_token(d.pop("gcp_oauth_token", UNSET))

        temporary_credentials = cls(
            aws_temp_credentials=aws_temp_credentials,
            azure_user_delegation_sas=azure_user_delegation_sas,
            expiration_time=expiration_time,
            gcp_oauth_token=gcp_oauth_token,
        )

        temporary_credentials.additional_properties = d
        return temporary_credentials

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
