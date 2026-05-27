from __future__ import annotations

from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    BinaryIO,
    Generator,
    Literal,
    TextIO,
    TypeVar,
    cast,
)

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.table_constraint import TableConstraint


T = TypeVar("T", bound="AddConstraintUpdate")


@_attrs_define
class AddConstraintUpdate:
    """``add-constraint`` variant of :data:`TableUpdate` (ADR-0012).

    Implemented in full: the service layer validates the
    constraint per type (column existence, at-most-one PK, FK
    parent resolution) and inserts a fresh row on the new
    ``table_constraints`` table. Rejecting duplicates by name on
    the same table returns 409 ``ALREADY_EXISTS`` via the
    ``(table_id, name)`` unique constraint — same race-safety
    posture as every other create path. See ADR-0012 for the
    rename-invariance and metadata-only rationale.

        Attributes:
            action (Literal['add-constraint']):
            constraint (TableConstraint): A single declared constraint on a table (ADR-0012).

                The wire shape mirrors the Databricks public SDK
                ``databricks.sdk.service.catalog.TableConstraint`` envelope so
                that a client that already knows Databricks' shape does not
                have to relearn. Exactly one of the four per-type fields is
                populated on the wire — the envelope is a thin discriminated
                union over :class:`PrimaryKeyConstraint` /
                :class:`ForeignKeyConstraint` / :class:`CheckConstraint` /
                :class:`NotNullConstraint`. A request with zero or more than
                one populated is rejected by the service layer with
                400 ``INVALID_ARGUMENT``.

                ``name`` is a user-chosen identifier unique per table (the
                ORM table enforces ``(table_id, name)``). It is the address
                used by ``drop-constraint`` — rename / re-add is not in scope.
    """

    action: Literal["add-constraint"]
    constraint: TableConstraint

    def to_dict(self) -> dict[str, Any]:
        from ..models.table_constraint import TableConstraint

        action = self.action

        constraint = self.constraint.to_dict()

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "action": action,
                "constraint": constraint,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.table_constraint import TableConstraint

        d = dict(src_dict)
        action = cast(Literal["add-constraint"], d.pop("action"))
        if action != "add-constraint":
            raise ValueError(
                f"action must match const 'add-constraint', got '{action}'"
            )

        constraint = TableConstraint.from_dict(d.pop("constraint"))

        add_constraint_update = cls(
            action=action,
            constraint=constraint,
        )

        return add_constraint_update
