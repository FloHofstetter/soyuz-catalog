from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.generate_temporary_volume_credential_operation import (
    GenerateTemporaryVolumeCredentialOperation,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="GenerateTemporaryVolumeCredential")


@_attrs_define
class GenerateTemporaryVolumeCredential:
    """Request body for ``POST /temporary-volume-credentials``.

    Mirrors :class:`GenerateTemporaryTableCredential`: addresses the
    volume by its opaque ``volume_id`` and restricts ``operation`` to the
    spec enum. ``UNKNOWN_VOLUME_OPERATION`` is accepted at the Pydantic
    layer but rejected as an invalid request at the service layer for the
    same reason the table variant rejects its own sentinel.

        Attributes:
            operation (GenerateTemporaryVolumeCredentialOperation):
            volume_id (str):
    """

    operation: GenerateTemporaryVolumeCredentialOperation
    volume_id: str

    def to_dict(self) -> dict[str, Any]:
        operation = self.operation.value

        volume_id = self.volume_id

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "operation": operation,
                "volume_id": volume_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        operation = GenerateTemporaryVolumeCredentialOperation(d.pop("operation"))

        volume_id = d.pop("volume_id")

        generate_temporary_volume_credential = cls(
            operation=operation,
            volume_id=volume_id,
        )

        return generate_temporary_volume_credential
