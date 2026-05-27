from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.registered_model_info import RegisteredModelInfo


T = TypeVar("T", bound="ListRegisteredModelsResponse")


@_attrs_define
class ListRegisteredModelsResponse:
    """Response shape for ``GET /models``.

    Keyset pagination via ``next_page_token``. Both ``catalog_name``
    and ``schema_name`` query filters are *optional* — the spec
    allows a metastore-wide list — which differs from
    :class:`ListFunctionsResponse` where both are required.

        Attributes:
            registered_models (list[RegisteredModelInfo]):
            next_page_token (None | str | Unset):
    """

    registered_models: list[RegisteredModelInfo]
    next_page_token: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.registered_model_info import RegisteredModelInfo

        registered_models = []
        for registered_models_item_data in self.registered_models:
            registered_models_item = registered_models_item_data.to_dict()
            registered_models.append(registered_models_item)

        next_page_token: None | str | Unset
        if isinstance(self.next_page_token, Unset):
            next_page_token = UNSET
        else:
            next_page_token = self.next_page_token

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "registered_models": registered_models,
            }
        )
        if next_page_token is not UNSET:
            field_dict["next_page_token"] = next_page_token

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.registered_model_info import RegisteredModelInfo

        d = dict(src_dict)
        registered_models = []
        _registered_models = d.pop("registered_models")
        for registered_models_item_data in _registered_models:
            registered_models_item = RegisteredModelInfo.from_dict(
                registered_models_item_data
            )

            registered_models.append(registered_models_item)

        def _parse_next_page_token(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        next_page_token = _parse_next_page_token(d.pop("next_page_token", UNSET))

        list_registered_models_response = cls(
            registered_models=registered_models,
            next_page_token=next_page_token,
        )

        list_registered_models_response.additional_properties = d
        return list_registered_models_response

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
