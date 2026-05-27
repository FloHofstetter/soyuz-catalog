from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateModelVersion")


@_attrs_define
class CreateModelVersion:
    """Request body for ``POST /models/versions``.

    The UC spec addresses the parent registered model by the triple
    ``(catalog_name, schema_name, model_name)`` on the create body
    rather than via a nested URL, which is why this endpoint is
    mounted at ``/models/versions`` instead of
    ``/models/{full_name}/versions``. ``source`` is required; the
    server assigns a monotonic ``version`` integer unique per
    registered model.

        Attributes:
            catalog_name (str):
            model_name (str):
            schema_name (str):
            source (str):
            comment (None | str | Unset):
            run_id (None | str | Unset):
    """

    catalog_name: str
    model_name: str
    schema_name: str
    source: str
    comment: None | str | Unset = UNSET
    run_id: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        catalog_name = self.catalog_name

        model_name = self.model_name

        schema_name = self.schema_name

        source = self.source

        comment: None | str | Unset
        if isinstance(self.comment, Unset):
            comment = UNSET
        else:
            comment = self.comment

        run_id: None | str | Unset
        if isinstance(self.run_id, Unset):
            run_id = UNSET
        else:
            run_id = self.run_id

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "catalog_name": catalog_name,
                "model_name": model_name,
                "schema_name": schema_name,
                "source": source,
            }
        )
        if comment is not UNSET:
            field_dict["comment"] = comment
        if run_id is not UNSET:
            field_dict["run_id"] = run_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        catalog_name = d.pop("catalog_name")

        model_name = d.pop("model_name")

        schema_name = d.pop("schema_name")

        source = d.pop("source")

        def _parse_comment(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        comment = _parse_comment(d.pop("comment", UNSET))

        def _parse_run_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        run_id = _parse_run_id(d.pop("run_id", UNSET))

        create_model_version = cls(
            catalog_name=catalog_name,
            model_name=model_name,
            schema_name=schema_name,
            source=source,
            comment=comment,
            run_id=run_id,
        )

        return create_model_version
