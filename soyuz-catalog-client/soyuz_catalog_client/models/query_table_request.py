from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="QueryTableRequest")


@_attrs_define
class QueryTableRequest:
    """Request body for ``POST .../tables/{table}/query``.

    Permissively validated (``extra="allow"``): the protocol evolves
    independently of soyuz and clients legitimately send fields from
    newer revisions (``maxFiles``, ``includeRefreshToken``, …) —
    rejecting them with 422 would break real recipients. This is the
    same documented exception to the project-wide ``extra="forbid"``
    policy that the OpenLineage ingest shapes use (ADR-0008).

    ``predicateHints``, ``jsonPredicateHints``, and ``limitHint`` are
    accepted and ignored — the protocol defines all three as hints
    the server may disregard, and soyuz returns the full file list.
    ``version`` pins the snapshot. ``timestamp``,
    ``startingVersion``, and ``endingVersion`` belong to the
    timestamp-resolution / CDF features soyuz does not implement and
    are rejected with 501 at the service layer.

        Attributes:
            ending_version (int | None | Unset):
            json_predicate_hints (None | str | Unset):
            limit_hint (int | None | Unset):
            predicate_hints (list[str] | None | Unset):
            starting_version (int | None | Unset):
            timestamp (None | str | Unset):
            version (int | None | Unset):
    """

    ending_version: int | None | Unset = UNSET
    json_predicate_hints: None | str | Unset = UNSET
    limit_hint: int | None | Unset = UNSET
    predicate_hints: list[str] | None | Unset = UNSET
    starting_version: int | None | Unset = UNSET
    timestamp: None | str | Unset = UNSET
    version: int | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        ending_version: int | None | Unset
        if isinstance(self.ending_version, Unset):
            ending_version = UNSET
        else:
            ending_version = self.ending_version

        json_predicate_hints: None | str | Unset
        if isinstance(self.json_predicate_hints, Unset):
            json_predicate_hints = UNSET
        else:
            json_predicate_hints = self.json_predicate_hints

        limit_hint: int | None | Unset
        if isinstance(self.limit_hint, Unset):
            limit_hint = UNSET
        else:
            limit_hint = self.limit_hint

        predicate_hints: list[str] | None | Unset
        if isinstance(self.predicate_hints, Unset):
            predicate_hints = UNSET
        elif isinstance(self.predicate_hints, list):
            predicate_hints = self.predicate_hints

        else:
            predicate_hints = self.predicate_hints

        starting_version: int | None | Unset
        if isinstance(self.starting_version, Unset):
            starting_version = UNSET
        else:
            starting_version = self.starting_version

        timestamp: None | str | Unset
        if isinstance(self.timestamp, Unset):
            timestamp = UNSET
        else:
            timestamp = self.timestamp

        version: int | None | Unset
        if isinstance(self.version, Unset):
            version = UNSET
        else:
            version = self.version

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if ending_version is not UNSET:
            field_dict["endingVersion"] = ending_version
        if json_predicate_hints is not UNSET:
            field_dict["jsonPredicateHints"] = json_predicate_hints
        if limit_hint is not UNSET:
            field_dict["limitHint"] = limit_hint
        if predicate_hints is not UNSET:
            field_dict["predicateHints"] = predicate_hints
        if starting_version is not UNSET:
            field_dict["startingVersion"] = starting_version
        if timestamp is not UNSET:
            field_dict["timestamp"] = timestamp
        if version is not UNSET:
            field_dict["version"] = version

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_ending_version(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        ending_version = _parse_ending_version(d.pop("endingVersion", UNSET))

        def _parse_json_predicate_hints(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        json_predicate_hints = _parse_json_predicate_hints(
            d.pop("jsonPredicateHints", UNSET)
        )

        def _parse_limit_hint(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        limit_hint = _parse_limit_hint(d.pop("limitHint", UNSET))

        def _parse_predicate_hints(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                predicate_hints_type_0 = cast(list[str], data)

                return predicate_hints_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        predicate_hints = _parse_predicate_hints(d.pop("predicateHints", UNSET))

        def _parse_starting_version(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        starting_version = _parse_starting_version(d.pop("startingVersion", UNSET))

        def _parse_timestamp(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        timestamp = _parse_timestamp(d.pop("timestamp", UNSET))

        def _parse_version(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        version = _parse_version(d.pop("version", UNSET))

        query_table_request = cls(
            ending_version=ending_version,
            json_predicate_hints=json_predicate_hints,
            limit_hint=limit_hint,
            predicate_hints=predicate_hints,
            starting_version=starting_version,
            timestamp=timestamp,
            version=version,
        )

        query_table_request.additional_properties = d
        return query_table_request

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
