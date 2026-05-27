from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.generate_temporary_table_credential_operation import (
    GenerateTemporaryTableCredentialOperation,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="GenerateTemporaryTableCredential")


@_attrs_define
class GenerateTemporaryTableCredential:
    """Request body for ``POST /temporary-table-credentials``.

    The UC spec addresses the table by its opaque ``table_id`` rather than
    its ``full_name`` because credentials are scoped to the physical
    storage identity, not the namespace path: a rename of the parent
    catalog or schema must not invalidate an outstanding credential.

    ``operation`` is a tri-state enum in the spec
    (``UNKNOWN_TABLE_OPERATION``, ``READ``, ``READ_WRITE``). We accept the
    two real values via :class:`typing.Literal` so a typo surfaces as 422
    at the Pydantic layer and reject ``UNKNOWN_TABLE_OPERATION`` at the
    service layer as an invalid request — the sentinel exists in the spec
    only as a protobuf default and accepting it here would reproduce the
    same silently-accept-garbage behaviour that ``extra="forbid"`` is
    everywhere else written to prevent (see ``DIVERGENCES.md``).

        Attributes:
            operation (GenerateTemporaryTableCredentialOperation):
            table_id (str):
    """

    operation: GenerateTemporaryTableCredentialOperation
    table_id: str

    def to_dict(self) -> dict[str, Any]:
        operation = self.operation.value

        table_id = self.table_id

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "operation": operation,
                "table_id": table_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        operation = GenerateTemporaryTableCredentialOperation(d.pop("operation"))

        table_id = d.pop("table_id")

        generate_temporary_table_credential = cls(
            operation=operation,
            table_id=table_id,
        )

        return generate_temporary_table_credential
