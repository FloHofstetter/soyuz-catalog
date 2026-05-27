"""Business logic for the Storage Credentials resource."""

from __future__ import annotations

import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from soyuz_catalog.api.schemas import CreateCredentialRequest, UpdateCredentialRequest
from soyuz_catalog.db import commit_or_conflict
from soyuz_catalog.exceptions import ConflictError, NotFoundError
from soyuz_catalog.models import Credential, ExternalLocation, _now_ms
from soyuz_catalog.pagination import apply_keyset, build_next_token
from soyuz_catalog.services.permissions_service import wipe_permissions_for


def _new_external_id() -> str:
    """Mint a fresh server-owned ``external_id`` for a credential.

    The UC spec surfaces ``external_id`` on ``AwsIamRoleResponse`` as
    the confused-deputy mitigation used during AWS STS role assumption:
    a caller forging the ``role_arn`` still cannot assume the role
    without knowing this opaque, server-generated value. soyuz does
    not actually vend STS tokens (cloud credential vending is
    explicitly out of scope — metadata-only design, README design
    principle 3) but we still mint the value so the response shape
    is faithful and a future vending implementation has something
    to compare against on assume-role.

    The value is a 128-bit random UUID4 hex string, same generator as
    every other opaque id in the project.

    Returns:
        str: A random UUID4 hex string suitable as an STS ``ExternalId``.
    """
    return uuid.uuid4().hex


def create_credential(session: Session, payload: CreateCredentialRequest) -> Credential:
    """Insert a new storage credential row.

    Duplicate detection relies on the ``name`` unique index plus
    ``IntegrityError`` translation rather than a pre-check ``SELECT``,
    which would race with concurrent inserts — same pattern as every
    other ``create_*`` in the service layer. ``purpose`` defaults to
    ``STORAGE`` (the only value the upstream spec defines today) when
    the client omits it.

    A fresh ``aws_iam_role_external_id`` is minted here on create and
    **never** rotated by PATCH: the UC spec defines no rotate-external-id
    operation and leaking the value through a rotate path would defeat
    its purpose as a confused-deputy mitigation.
    ``aws_iam_role_unity_catalog_iam_arn`` is always ``None`` — soyuz
    has no runtime IAM identity of its own, see ``DIVERGENCES.md``.

    Args:
        session: Active SQLAlchemy session.
        payload: Validated create request.

    Returns:
        Credential: The newly created credential row.

    Raises:
        ConflictError: If a credential with the same name already exists.
    """
    credential = Credential(
        name=payload.name,
        purpose=payload.purpose or "STORAGE",
        comment=payload.comment,
        aws_iam_role_arn=payload.aws_iam_role.role_arn if payload.aws_iam_role else None,
        aws_iam_role_external_id=_new_external_id() if payload.aws_iam_role else None,
        aws_iam_role_unity_catalog_iam_arn=None,
    )
    session.add(credential)
    with commit_or_conflict(session, f"Credential '{payload.name}' already exists"):
        pass
    session.refresh(credential)
    return credential


def get_credential(session: Session, name: str) -> Credential:
    """Fetch a credential by name.

    Credentials are addressed by the user-facing ``name`` column across
    every REST endpoint — the opaque ``id`` is stored only so
    :class:`soyuz_catalog.models.ExternalLocation` can bind against a
    rename-stable handle.

    Args:
        session: Active SQLAlchemy session.
        name: Credential name.

    Returns:
        Credential: The matching credential row.

    Raises:
        NotFoundError: If no credential with the given name exists.
    """
    credential = session.scalar(select(Credential).where(Credential.name == name))
    if credential is None:
        raise NotFoundError(f"Credential '{name}' does not exist")
    return credential


def list_credentials(
    session: Session,
    purpose: str | None = None,
    max_results: int | None = None,
    page_token: str | None = None,
) -> tuple[list[Credential], str | None]:
    """List credentials with optional purpose filter and keyset pagination.

    The ``purpose`` filter is a literal WHERE clause that currently
    cannot narrow the result set (``STORAGE`` is the only value defined
    by the upstream spec) but is wired anyway so that a future upstream
    addition — and any client that sends the filter today — is
    future-proof without a schema change. Ordering is ``(created_at
    ASC, id ASC)`` via :func:`soyuz_catalog.pagination.apply_keyset`.

    ``InvalidRequestError`` may propagate from
    :func:`soyuz_catalog.pagination.apply_keyset` on malformed
    pagination parameters.

    Args:
        session: Active SQLAlchemy session.
        purpose: Optional ``CredentialPurpose`` filter. Only
            ``"STORAGE"`` is valid today; the route layer enforces the
            ``Literal`` at query-param parse time.
        max_results: Spec-defined page size hint.
        page_token: Opaque pagination cursor.

    Returns:
        tuple[list[Credential], str | None]: One page of credentials
            plus the next page token (``None`` if last).
    """
    stmt = select(Credential)
    if purpose is not None:
        stmt = stmt.where(Credential.purpose == purpose)
    stmt, limit = apply_keyset(stmt, Credential, page_token, max_results)
    rows = list(session.scalars(stmt))
    return build_next_token(rows, limit)


def update_credential(
    session: Session,
    name: str,
    payload: UpdateCredentialRequest,
    fields_set: set[str],
) -> Credential:
    """Apply a PATCH to a credential.

    Replace-style semantics driven by ``fields_set`` (from
    ``model_fields_set``) so ``{"comment": null}`` clears the comment
    while an empty body is a no-op instead of a 500 — the latter is a
    regression pin against the same UC OSS Java behaviour
    :mod:`soyuz_catalog.services.volume_service` guards against.
    ``aws_iam_role`` PATCH replaces ``role_arn`` only; the server-minted
    ``external_id`` is deliberately **not** rotated (see
    :func:`create_credential`).

    A rename collides on the ``name`` unique index and surfaces as 409.

    Args:
        session: Active SQLAlchemy session.
        name: Current credential name (path parameter).
        payload: Validated update request.
        fields_set: Names of fields explicitly present in the request body.

    Returns:
        Credential: The updated credential row.

    Raises:
        ConflictError: If ``new_name`` collides with an existing credential.
    """
    credential = get_credential(session, name)

    if not fields_set:
        return credential

    if "new_name" in fields_set and payload.new_name is not None:
        credential.name = payload.new_name
    if "comment" in fields_set:
        credential.comment = payload.comment
    if "owner" in fields_set:
        credential.owner = payload.owner
    if "aws_iam_role" in fields_set and payload.aws_iam_role is not None:
        credential.aws_iam_role_arn = payload.aws_iam_role.role_arn

    credential.updated_at = _now_ms()

    with commit_or_conflict(
        session,
        f"Credential rename to '{payload.new_name}' collides with an existing credential",
    ):
        pass
    session.refresh(credential)
    return credential


def delete_credential(session: Session, name: str, force: bool = False) -> None:
    """Delete a credential.

    If one or more external locations still reference the credential
    and ``force`` is false, the delete is rejected with 409 — same
    shape as "cannot delete catalog with schemas". With ``force=true``,
    the service deletes every referencing external location first and
    then removes the credential row, all in one transaction. This
    matches UC OSS Java's ``DELETE /credentials/{name}?force=true``
    behaviour (see ``DIVERGENCES.md`` — rare case where we align with
    OSS instead of diverging).

    Args:
        session: Active SQLAlchemy session.
        name: Credential name.
        force: When true, cascade-delete every referencing external
            location. When false, refuse the delete if any external
            location still binds to this credential.

    Raises:
        ConflictError: If referencing external locations exist and
            ``force`` is false.
    """
    credential = get_credential(session, name)
    ref_count = session.scalar(
        select(func.count())
        .select_from(ExternalLocation)
        .where(ExternalLocation.credential_id == credential.id),
    )
    if ref_count and not force:
        raise ConflictError(
            f"Cannot delete credential '{name}' because {ref_count} external "
            "location(s) still reference it. Pass force=true to cascade.",
        )
    if ref_count:
        # Collect the referencing external location ids for the grants
        # cascade before the DELETE removes the rows they were keyed on.
        ext_ids = list(
            session.scalars(
                select(ExternalLocation.id).where(
                    ExternalLocation.credential_id == credential.id,
                ),
            ),
        )
        wipe_permissions_for(
            session,
            [("external_location", eid) for eid in ext_ids],
        )
        session.execute(
            delete(ExternalLocation).where(
                ExternalLocation.credential_id == credential.id,
            ),
        )
    wipe_permissions_for(session, [("credential", credential.id)])
    session.delete(credential)
    session.commit()
