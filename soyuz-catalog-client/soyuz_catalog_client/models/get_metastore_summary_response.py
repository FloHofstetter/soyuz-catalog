from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="GetMetastoreSummaryResponse")


@_attrs_define
class GetMetastoreSummaryResponse:
    """Response shape for ``GET /metastore_summary``.

    The upstream UC OpenAPI spec defines a single field on this
    object: ``metastore_id``. soyuz does not silently extend it with
    ``name``, ``storage_root``, ``region``, ``owner``, or any of the
    other fields that appear on Databricks-flavoured forks of the
    spec — same no-silent-spec-extensions policy as every other
    response model in this module.

        Attributes:
            metastore_id (None | str | Unset):
    """

    metastore_id: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        metastore_id: None | str | Unset
        if isinstance(self.metastore_id, Unset):
            metastore_id = UNSET
        else:
            metastore_id = self.metastore_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if metastore_id is not UNSET:
            field_dict["metastore_id"] = metastore_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_metastore_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        metastore_id = _parse_metastore_id(d.pop("metastore_id", UNSET))

        get_metastore_summary_response = cls(
            metastore_id=metastore_id,
        )

        get_metastore_summary_response.additional_properties = d
        return get_metastore_summary_response

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
