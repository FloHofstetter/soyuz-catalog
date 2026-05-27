from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.create_connection_connection_type import CreateConnectionConnectionType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.options import Options


T = TypeVar("T", bound="CreateConnection")


@_attrs_define
class CreateConnection:
    """Request body for ``POST /connections``.

    ``name``, ``connection_type``, and ``options`` are required;
    everything else is optional. ``extra="forbid"`` rejects unknown
    fields (including ``id``, ``created_at``, …) with 422 instead of
    silently dropping them — the same bug class soyuz exists to fix.

    ``connection_type`` is a ``Literal`` pinned to the common connector
    set so typos (``POSTGRES`` vs ``POSTGRESQL``) surface at the
    pydantic layer. The DB column is stored as a free string for
    future extensibility — see
    :class:`soyuz_catalog.models.Connection` for the rationale and
    ``DIVERGENCES.md`` for the soyuz-vs-Databricks difference.

    ``options`` is a free-form ``dict[str, str]`` passthrough. soyuz
    does **not** validate per-connector option sets (there is no query
    side to enforce them against) and **does not** encrypt sensitive
    values (``password``, ``token``, …); both postures are documented
    in ``DIVERGENCES.md``.

        Attributes:
            connection_type (CreateConnectionConnectionType):
            name (str):
            comment (None | str | Unset):
            options (Options | Unset):
            owner (None | str | Unset):
            read_only (bool | None | Unset):
    """

    connection_type: CreateConnectionConnectionType
    name: str
    comment: None | str | Unset = UNSET
    options: Options | Unset = UNSET
    owner: None | str | Unset = UNSET
    read_only: bool | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.options import Options

        connection_type = self.connection_type.value

        name = self.name

        comment: None | str | Unset
        if isinstance(self.comment, Unset):
            comment = UNSET
        else:
            comment = self.comment

        options: dict[str, Any] | Unset = UNSET
        if not isinstance(self.options, Unset):
            options = self.options.to_dict()

        owner: None | str | Unset
        if isinstance(self.owner, Unset):
            owner = UNSET
        else:
            owner = self.owner

        read_only: bool | None | Unset
        if isinstance(self.read_only, Unset):
            read_only = UNSET
        else:
            read_only = self.read_only

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "connection_type": connection_type,
                "name": name,
            }
        )
        if comment is not UNSET:
            field_dict["comment"] = comment
        if options is not UNSET:
            field_dict["options"] = options
        if owner is not UNSET:
            field_dict["owner"] = owner
        if read_only is not UNSET:
            field_dict["read_only"] = read_only

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.options import Options

        d = dict(src_dict)
        connection_type = CreateConnectionConnectionType(d.pop("connection_type"))

        name = d.pop("name")

        def _parse_comment(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        comment = _parse_comment(d.pop("comment", UNSET))

        _options = d.pop("options", UNSET)
        options: Options | Unset
        if isinstance(_options, Unset):
            options = UNSET
        else:
            options = Options.from_dict(_options)

        def _parse_owner(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        owner = _parse_owner(d.pop("owner", UNSET))

        def _parse_read_only(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        read_only = _parse_read_only(d.pop("read_only", UNSET))

        create_connection = cls(
            connection_type=connection_type,
            name=name,
            comment=comment,
            options=options,
            owner=owner,
            read_only=read_only,
        )

        return create_connection
