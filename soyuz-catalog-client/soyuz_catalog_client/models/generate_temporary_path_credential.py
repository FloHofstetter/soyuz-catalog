from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.generate_temporary_path_credential_operation import (
    GenerateTemporaryPathCredentialOperation,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="GenerateTemporaryPathCredential")


@_attrs_define
class GenerateTemporaryPathCredential:
    """Request body for ``POST /temporary-path-credentials``.

    Mirrors :class:`GenerateTemporaryTableCredential` / ...Volume: the
    request carries a user-supplied storage URL and a ``PathOperation``
    enum. ``PATH_READ`` / ``PATH_READ_WRITE`` / ``PATH_CREATE_TABLE``
    are the three real values; the protobuf-default
    ``UNKNOWN_PATH_OPERATION`` sentinel is accepted at the Pydantic
    layer and rejected at the service layer for the same reason the
    table/volume variants reject their own sentinels. Unknown keys
    surface as 422 via ``extra="forbid"``.

        Attributes:
            operation (GenerateTemporaryPathCredentialOperation):
            url (str):
    """

    operation: GenerateTemporaryPathCredentialOperation
    url: str

    def to_dict(self) -> dict[str, Any]:
        operation = self.operation.value

        url = self.url

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "operation": operation,
                "url": url,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        operation = GenerateTemporaryPathCredentialOperation(d.pop("operation"))

        url = d.pop("url")

        generate_temporary_path_credential = cls(
            operation=operation,
            url=url,
        )

        return generate_temporary_path_credential
