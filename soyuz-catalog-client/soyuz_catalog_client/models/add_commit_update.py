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
    from ..models.add_commit_update_uniform_type_0 import AddCommitUpdateUniformType0
    from ..models.delta_log_commit import DeltaLogCommit


T = TypeVar("T", bound="AddCommitUpdate")


@_attrs_define
class AddCommitUpdate:
    """Register a CCv2 commit — **rejected** by soyuz as 501.

    soyuz does not act as a Delta commit coordinator (ADR-0006). The
    model still parses so the discriminated union round-trips and
    the route handler emits a dedicated
    ``COMMIT_COORDINATOR_UNSUPPORTED`` envelope instead of a generic
    422. See
    :class:`soyuz_catalog.exceptions.CommitCoordinatorUnsupportedError`.

        Attributes:
            action (Literal['add-commit']):
            commit (DeltaLogCommit): One unbackfilled CCv2 commit.

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
            uniform (AddCommitUpdateUniformType0 | None | Unset):
    """

    action: Literal["add-commit"]
    commit: DeltaLogCommit
    uniform: AddCommitUpdateUniformType0 | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.add_commit_update_uniform_type_0 import (
            AddCommitUpdateUniformType0,
        )
        from ..models.delta_log_commit import DeltaLogCommit

        action = self.action

        commit = self.commit.to_dict()

        uniform: dict[str, Any] | None | Unset
        if isinstance(self.uniform, Unset):
            uniform = UNSET
        elif isinstance(self.uniform, AddCommitUpdateUniformType0):
            uniform = self.uniform.to_dict()
        else:
            uniform = self.uniform

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "action": action,
                "commit": commit,
            }
        )
        if uniform is not UNSET:
            field_dict["uniform"] = uniform

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.add_commit_update_uniform_type_0 import (
            AddCommitUpdateUniformType0,
        )
        from ..models.delta_log_commit import DeltaLogCommit

        d = dict(src_dict)
        action = cast(Literal["add-commit"], d.pop("action"))
        if action != "add-commit":
            raise ValueError(f"action must match const 'add-commit', got '{action}'")

        commit = DeltaLogCommit.from_dict(d.pop("commit"))

        def _parse_uniform(data: object) -> AddCommitUpdateUniformType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                uniform_type_0 = AddCommitUpdateUniformType0.from_dict(data)

                return uniform_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(AddCommitUpdateUniformType0 | None | Unset, data)

        uniform = _parse_uniform(d.pop("uniform", UNSET))

        add_commit_update = cls(
            action=action,
            commit=commit,
            uniform=uniform,
        )

        return add_commit_update
