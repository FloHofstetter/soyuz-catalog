from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="DeltaLogCommit")


@_attrs_define
class DeltaLogCommit:
    """One unbackfilled CCv2 commit.

    soyuz does not act as a Delta commit coordinator (see ADR-0006),
    so this model only exists so :class:`LoadTableResponse` can
    declare ``commits: list[DeltaLogCommit]`` — the list is always
    empty on the wire. Kept in the module so the generated OpenAPI
    schema matches the upstream ``delta.yaml`` field-for-field.

    Named ``DeltaLogCommit`` rather than ``DeltaCommit`` to avoid
    an OpenAPI schema-name collision with the unrelated
    :class:`soyuz_catalog.api.schemas.DeltaCommit` request body
    for the commit coordinator endpoint — openapi-python-client
    cannot disambiguate two schemas that share a leaf name.

        Attributes:
            file_modification_timestamp (int):
            file_name (str):
            file_size (int):
            timestamp (int):
            version (int):
    """

    file_modification_timestamp: int
    file_name: str
    file_size: int
    timestamp: int
    version: int

    def to_dict(self) -> dict[str, Any]:
        file_modification_timestamp = self.file_modification_timestamp

        file_name = self.file_name

        file_size = self.file_size

        timestamp = self.timestamp

        version = self.version

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "file-modification-timestamp": file_modification_timestamp,
                "file-name": file_name,
                "file-size": file_size,
                "timestamp": timestamp,
                "version": version,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        file_modification_timestamp = d.pop("file-modification-timestamp")

        file_name = d.pop("file-name")

        file_size = d.pop("file-size")

        timestamp = d.pop("timestamp")

        version = d.pop("version")

        delta_log_commit = cls(
            file_modification_timestamp=file_modification_timestamp,
            file_name=file_name,
            file_size=file_size,
            timestamp=timestamp,
            version=version,
        )

        return delta_log_commit
