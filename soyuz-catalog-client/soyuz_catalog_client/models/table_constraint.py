from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.check_constraint import CheckConstraint
    from ..models.foreign_key_constraint import ForeignKeyConstraint
    from ..models.not_null_constraint import NotNullConstraint
    from ..models.primary_key_constraint import PrimaryKeyConstraint


T = TypeVar("T", bound="TableConstraint")


@_attrs_define
class TableConstraint:
    """A single declared constraint on a table (ADR-0012).

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

        Attributes:
            name (str):
            check_constraint (CheckConstraint | None | Unset):
            foreign_key_constraint (ForeignKeyConstraint | None | Unset):
            named_table_constraint (None | NotNullConstraint | Unset):
            primary_key_constraint (None | PrimaryKeyConstraint | Unset):
    """

    name: str
    check_constraint: CheckConstraint | None | Unset = UNSET
    foreign_key_constraint: ForeignKeyConstraint | None | Unset = UNSET
    named_table_constraint: None | NotNullConstraint | Unset = UNSET
    primary_key_constraint: None | PrimaryKeyConstraint | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.check_constraint import CheckConstraint
        from ..models.foreign_key_constraint import ForeignKeyConstraint
        from ..models.not_null_constraint import NotNullConstraint
        from ..models.primary_key_constraint import PrimaryKeyConstraint

        name = self.name

        check_constraint: dict[str, Any] | None | Unset
        if isinstance(self.check_constraint, Unset):
            check_constraint = UNSET
        elif isinstance(self.check_constraint, CheckConstraint):
            check_constraint = self.check_constraint.to_dict()
        else:
            check_constraint = self.check_constraint

        foreign_key_constraint: dict[str, Any] | None | Unset
        if isinstance(self.foreign_key_constraint, Unset):
            foreign_key_constraint = UNSET
        elif isinstance(self.foreign_key_constraint, ForeignKeyConstraint):
            foreign_key_constraint = self.foreign_key_constraint.to_dict()
        else:
            foreign_key_constraint = self.foreign_key_constraint

        named_table_constraint: dict[str, Any] | None | Unset
        if isinstance(self.named_table_constraint, Unset):
            named_table_constraint = UNSET
        elif isinstance(self.named_table_constraint, NotNullConstraint):
            named_table_constraint = self.named_table_constraint.to_dict()
        else:
            named_table_constraint = self.named_table_constraint

        primary_key_constraint: dict[str, Any] | None | Unset
        if isinstance(self.primary_key_constraint, Unset):
            primary_key_constraint = UNSET
        elif isinstance(self.primary_key_constraint, PrimaryKeyConstraint):
            primary_key_constraint = self.primary_key_constraint.to_dict()
        else:
            primary_key_constraint = self.primary_key_constraint

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
            }
        )
        if check_constraint is not UNSET:
            field_dict["check_constraint"] = check_constraint
        if foreign_key_constraint is not UNSET:
            field_dict["foreign_key_constraint"] = foreign_key_constraint
        if named_table_constraint is not UNSET:
            field_dict["named_table_constraint"] = named_table_constraint
        if primary_key_constraint is not UNSET:
            field_dict["primary_key_constraint"] = primary_key_constraint

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.check_constraint import CheckConstraint
        from ..models.foreign_key_constraint import ForeignKeyConstraint
        from ..models.not_null_constraint import NotNullConstraint
        from ..models.primary_key_constraint import PrimaryKeyConstraint

        d = dict(src_dict)
        name = d.pop("name")

        def _parse_check_constraint(data: object) -> CheckConstraint | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                check_constraint_type_0 = CheckConstraint.from_dict(data)

                return check_constraint_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(CheckConstraint | None | Unset, data)

        check_constraint = _parse_check_constraint(d.pop("check_constraint", UNSET))

        def _parse_foreign_key_constraint(
            data: object,
        ) -> ForeignKeyConstraint | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                foreign_key_constraint_type_0 = ForeignKeyConstraint.from_dict(data)

                return foreign_key_constraint_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(ForeignKeyConstraint | None | Unset, data)

        foreign_key_constraint = _parse_foreign_key_constraint(
            d.pop("foreign_key_constraint", UNSET)
        )

        def _parse_named_table_constraint(
            data: object,
        ) -> None | NotNullConstraint | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                named_table_constraint_type_0 = NotNullConstraint.from_dict(data)

                return named_table_constraint_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | NotNullConstraint | Unset, data)

        named_table_constraint = _parse_named_table_constraint(
            d.pop("named_table_constraint", UNSET)
        )

        def _parse_primary_key_constraint(
            data: object,
        ) -> None | PrimaryKeyConstraint | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                primary_key_constraint_type_0 = PrimaryKeyConstraint.from_dict(data)

                return primary_key_constraint_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | PrimaryKeyConstraint | Unset, data)

        primary_key_constraint = _parse_primary_key_constraint(
            d.pop("primary_key_constraint", UNSET)
        )

        table_constraint = cls(
            name=name,
            check_constraint=check_constraint,
            foreign_key_constraint=foreign_key_constraint,
            named_table_constraint=named_table_constraint,
            primary_key_constraint=primary_key_constraint,
        )

        return table_constraint
