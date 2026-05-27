from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.generate_temporary_model_version_credential_operation import (
    GenerateTemporaryModelVersionCredentialOperation,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="GenerateTemporaryModelVersionCredential")


@_attrs_define
class GenerateTemporaryModelVersionCredential:
    """Request body for ``POST /temporary-model-version-credentials``.

    Implements MLflow's UC-OSS
    ``generateTemporaryModelVersionCredential`` RPC. The version is
    addressed by the four-part triple ``(catalog_name, schema_name,
    model_name, version)`` rather than an opaque ``model_version_id``
    because that is what the proto specifies — see
    ``unity_catalog_oss_messages.proto:GenerateTemporaryModelVersionCredential``.

    The operation enum follows the proto's ``ModelVersionOperation``:
    ``READ_MODEL_VERSION`` for downloads, ``READ_WRITE_MODEL_VERSION``
    for the create-then-upload flow. ``UNKNOWN_MODEL_VERSION_OPERATION``
    is the proto's default sentinel and is rejected as 400 at the
    service layer for the same reason the table/volume variants reject
    their own sentinels.

        Attributes:
            catalog_name (str):
            model_name (str):
            operation (GenerateTemporaryModelVersionCredentialOperation):
            schema_name (str):
            version (int):
    """

    catalog_name: str
    model_name: str
    operation: GenerateTemporaryModelVersionCredentialOperation
    schema_name: str
    version: int

    def to_dict(self) -> dict[str, Any]:
        catalog_name = self.catalog_name

        model_name = self.model_name

        operation = self.operation.value

        schema_name = self.schema_name

        version = self.version

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "catalog_name": catalog_name,
                "model_name": model_name,
                "operation": operation,
                "schema_name": schema_name,
                "version": version,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        catalog_name = d.pop("catalog_name")

        model_name = d.pop("model_name")

        operation = GenerateTemporaryModelVersionCredentialOperation(d.pop("operation"))

        schema_name = d.pop("schema_name")

        version = d.pop("version")

        generate_temporary_model_version_credential = cls(
            catalog_name=catalog_name,
            model_name=model_name,
            operation=operation,
            schema_name=schema_name,
            version=version,
        )

        return generate_temporary_model_version_credential
