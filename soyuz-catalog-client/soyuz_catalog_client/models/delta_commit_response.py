from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="DeltaCommitResponse")


@_attrs_define
class DeltaCommitResponse:
    """Response body for ``POST /delta/preview/commits``.

    Deliberately empty: the upstream ``DeltaCommitResponse`` schema
    defines no fields, and the coordinator's ``commit`` operation
    communicates success through the HTTP status alone (200 = the
    row was accepted; 4xx carries the semantic failure). The class
    exists to give the route a strict ``response_model`` so FastAPI
    serialises ``{}`` on the wire and rejects any accidental
    response-shape drift during review.

    """

    def to_dict(self) -> dict[str, Any]:

        field_dict: dict[str, Any] = {}

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        delta_commit_response = cls()

        return delta_commit_response
