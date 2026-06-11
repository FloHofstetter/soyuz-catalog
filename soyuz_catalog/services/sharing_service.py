"""Business logic for the Delta Sharing management surface (ADR-0015).

Over-the-spec addition: CRUD for shares, share objects, recipients,
and grants. This module owns the *write* side of Delta Sharing — who
may read what. The read-only protocol surface that recipients hit
with their bearer tokens lives in
:mod:`soyuz_catalog.services.delta_sharing_service`.

Like every other management route in soyuz, these endpoints carry no
authentication — ADR-0005's auth-proxy posture applies. The protocol
surface is the exception (bearer tokens are part of the open Delta
Sharing wire contract itself); the split is deliberate and documented
in ADR-0015.

Token handling: recipients authenticate with a server-generated
bearer token whose **SHA-256 hash** is the only thing stored. The
plaintext is returned exactly once per generation (create / rotate);
a lost token is unrecoverable by design and rotation is the remedy.
"""

from __future__ import annotations

import hashlib
import secrets

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from soyuz_catalog.api.schemas import (
    AddShareObject,
    CreateRecipient,
    CreateShare,
    UpdateRecipient,
    UpdateShare,
)
from soyuz_catalog.db import commit_or_conflict
from soyuz_catalog.exceptions import ConflictError, InvalidRequestError, NotFoundError
from soyuz_catalog.models import Recipient, Share, ShareGrant, ShareObject, _now_ms
from soyuz_catalog.pagination import apply_keyset, build_next_token
from soyuz_catalog.services import table_service


def hash_token(token: str) -> str:
    """Return the SHA-256 hex digest of a bearer token.

    The single hashing primitive shared by token generation (this
    module) and protocol authentication
    (:mod:`soyuz_catalog.services.delta_sharing_service`), so the two
    sides can never drift. Plain SHA-256 without a salt is the right
    tool here — bearer tokens are 256-bit random secrets, not human
    passwords, so rainbow tables and per-entry salts are moot and a
    deterministic digest is required for the indexed equality lookup.

    Args:
        token: The plaintext bearer token.

    Returns:
        str: 64-char lowercase hex digest.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _generate_token() -> tuple[str, str]:
    """Generate a fresh bearer token and its storage hash.

    Returns:
        tuple[str, str]: ``(plaintext, sha256_hex)``. The plaintext
            is URL-safe base64 over 32 random bytes — the same
            entropy class the reference Delta Sharing server uses.
    """
    token = secrets.token_urlsafe(32)
    return token, hash_token(token)


def effective_placement(table_full_name: str, shared_as: str | None) -> tuple[str, str]:
    """Resolve a share object's protocol-side ``(schema, table)`` address.

    ``shared_as`` (a two-part ``schema.table`` alias) wins when
    present; otherwise the placement derives from the stored full
    name's schema and table segments — the catalog segment never
    appears on the protocol surface because Delta Sharing namespaces
    are only two levels deep below the share.

    Args:
        table_full_name: The stored three-part UC table name.
        shared_as: Optional two-part alias.

    Returns:
        tuple[str, str]: ``(schema_name, table_name)`` as exposed to
            recipients.
    """
    if shared_as is not None:
        schema_name, table_name = shared_as.split(".", 1)
        return schema_name, table_name
    _catalog, schema_name, table_name = table_full_name.split(".", 2)
    return schema_name, table_name


def _validate_shared_as(shared_as: str) -> None:
    """Reject ``shared_as`` aliases that are not two-part names.

    Args:
        shared_as: The client-supplied alias.

    Raises:
        InvalidRequestError: If the alias is not exactly two
            dot-separated non-empty parts.
    """
    parts = shared_as.split(".")
    if len(parts) != 2 or not all(parts):
        raise InvalidRequestError(
            f"shared_as '{shared_as}' must be of the form 'schema_name.table_name'",
        )


# ---------------------------------------------------------------------------
# Shares
# ---------------------------------------------------------------------------


def create_share(session: Session, payload: CreateShare) -> Share:
    """Insert a new share row.

    Duplicate detection relies on the ``name`` unique index plus
    ``IntegrityError`` translation rather than a pre-check ``SELECT``
    — same race-safe pattern as every other ``create_*``. Shares are
    created empty; tables enter through :func:`add_share_object`.

    Args:
        session: Active SQLAlchemy session.
        payload: Validated create request.

    Returns:
        Share: The newly created share row.

    Raises:
        ConflictError: If a share with the same name already exists.
    """
    share = Share(name=payload.name, comment=payload.comment, owner=payload.owner)
    session.add(share)
    with commit_or_conflict(session, f"Share '{payload.name}' already exists"):
        pass
    session.refresh(share)
    return share


def get_share(session: Session, name: str) -> Share:
    """Fetch a share by name.

    Args:
        session: Active SQLAlchemy session.
        name: Share name.

    Returns:
        Share: The matching row.

    Raises:
        NotFoundError: If no share with the given name exists.
    """
    share = session.scalar(select(Share).where(Share.name == name))
    if share is None:
        raise NotFoundError(f"Share '{name}' does not exist")
    return share


def list_shares(
    session: Session,
    max_results: int | None = None,
    page_token: str | None = None,
) -> tuple[list[Share], str | None]:
    """List shares with keyset pagination.

    Args:
        session: Active SQLAlchemy session.
        max_results: Spec-defined page size hint.
        page_token: Opaque pagination cursor.

    Returns:
        tuple[list[Share], str | None]: One page of shares plus the
            next page token (``None`` if last).
    """
    stmt, limit = apply_keyset(select(Share), Share, page_token, max_results)
    rows = list(session.scalars(stmt))
    return build_next_token(rows, limit)


def list_share_objects(session: Session, share_id: str) -> list[ShareObject]:
    """Return every object row of a share, oldest-first.

    Not paginated: a share object is one table reference, so even a
    very large share is a few hundred small rows — the management
    response inlines them all and the protocol surface paginates its
    own derived views in memory.

    Args:
        session: Active SQLAlchemy session.
        share_id: Opaque share id.

    Returns:
        list[ShareObject]: The share's objects ordered by
            ``(created_at, id)``.
    """
    return list(
        session.scalars(
            select(ShareObject)
            .where(ShareObject.share_id == share_id)
            .order_by(ShareObject.created_at.asc(), ShareObject.id.asc()),
        ),
    )


def update_share(
    session: Session,
    name: str,
    payload: UpdateShare,
    fields_set: set[str],
) -> Share:
    """Apply a PATCH to a share.

    Replace-style semantics driven by ``fields_set``; an empty body
    is a no-op. A rename collides on the ``name`` unique index and
    surfaces as 409. Renames are safe for recipients mid-flight only
    in the sense that the *next* protocol call uses the new name —
    grants bind by opaque ``share_id`` so they survive the rename.

    Args:
        session: Active SQLAlchemy session.
        name: Current share name (path parameter).
        payload: Validated update request.
        fields_set: Names of fields explicitly present in the body.

    Returns:
        Share: The updated row.

    Raises:
        ConflictError: If ``new_name`` collides with an existing share.
    """
    share = get_share(session, name)
    if not fields_set:
        return share
    if "new_name" in fields_set and payload.new_name is not None:
        share.name = payload.new_name
    if "comment" in fields_set:
        share.comment = payload.comment
    if "owner" in fields_set:
        share.owner = payload.owner
    share.updated_at = _now_ms()
    with commit_or_conflict(
        session,
        f"Share rename to '{payload.new_name}' collides with an existing share",
    ):
        pass
    session.refresh(share)
    return share


def delete_share(session: Session, name: str) -> None:
    """Delete a share together with its objects and grants.

    No ``force`` gate: objects and grants are weak composition — they
    have no meaning outside their share, the same way table columns
    ride along with their table — so requiring ``force=true`` would
    just be ceremony. Recipients lose visibility the moment the
    grants disappear; in-flight pre-signed file URLs keep working
    until their short TTL expires (documented in ADR-0015).

    Args:
        session: Active SQLAlchemy session.
        name: Share name.

    Raises:
        NotFoundError: Propagates from :func:`get_share` when the
            name does not resolve.
    """
    share = get_share(session, name)
    session.execute(delete(ShareObject).where(ShareObject.share_id == share.id))
    session.execute(delete(ShareGrant).where(ShareGrant.share_id == share.id))
    session.delete(share)
    session.commit()


# ---------------------------------------------------------------------------
# Share objects
# ---------------------------------------------------------------------------


def add_share_object(session: Session, share_name: str, payload: AddShareObject) -> ShareObject:
    """Place a table inside a share.

    The table must resolve at add time (404 otherwise) so a typo'd
    name fails at the management surface instead of surfacing as a
    mystery 404 to a recipient later. The resolved row is *not*
    bound by opaque id — see :class:`soyuz_catalog.models.ShareObject`
    for the name-keying rationale. Two uniqueness gates apply: the
    ``(share_id, table_full_name)`` constraint (the same table twice)
    and the derived protocol placement (two objects answering to one
    ``schema.table`` address via ``shared_as`` aliasing) — both 409.

    Args:
        session: Active SQLAlchemy session.
        share_name: Name of the target share.
        payload: Validated add request.

    Returns:
        ShareObject: The newly created object row.

    Raises:
        ConflictError: If the table is already in the share, or
            another object already occupies the same effective
            ``schema.table`` placement. (``NotFoundError`` propagates
            when the share or the table does not exist;
            ``InvalidRequestError`` when ``table_full_name`` or
            ``shared_as`` is malformed.)
    """
    share = get_share(session, share_name)
    # Validates the three-part shape (400) and existence (404).
    table_service.get_table(session, payload.table_full_name)
    if payload.shared_as is not None:
        _validate_shared_as(payload.shared_as)

    placement = effective_placement(payload.table_full_name, payload.shared_as)
    for existing in list_share_objects(session, share.id):
        if effective_placement(existing.table_full_name, existing.shared_as) == placement:
            raise ConflictError(
                f"Share '{share_name}' already exposes a table at "
                f"'{placement[0]}.{placement[1]}'; remove it or pick a "
                "different shared_as alias",
            )

    share_object = ShareObject(
        share_id=share.id,
        table_full_name=payload.table_full_name,
        shared_as=payload.shared_as,
    )
    session.add(share_object)
    with commit_or_conflict(
        session,
        f"Table '{payload.table_full_name}' is already in share '{share_name}'",
    ):
        pass
    session.refresh(share_object)
    return share_object


def remove_share_object(session: Session, share_name: str, table_full_name: str) -> None:
    """Remove a table from a share.

    Addressed by the stored ``table_full_name`` (not the alias): the
    full name is the management-side identity, while ``shared_as``
    only affects the protocol-side address.

    Args:
        session: Active SQLAlchemy session.
        share_name: Name of the share.
        table_full_name: The stored three-part table name to remove.

    Raises:
        NotFoundError: If the share does not exist or the table is
            not in it.
    """
    share = get_share(session, share_name)
    share_object = session.scalar(
        select(ShareObject).where(
            ShareObject.share_id == share.id,
            ShareObject.table_full_name == table_full_name,
        ),
    )
    if share_object is None:
        raise NotFoundError(
            f"Table '{table_full_name}' is not in share '{share_name}'",
        )
    session.delete(share_object)
    session.commit()


# ---------------------------------------------------------------------------
# Recipients
# ---------------------------------------------------------------------------


def create_recipient(session: Session, payload: CreateRecipient) -> tuple[Recipient, str]:
    """Insert a new recipient row and mint its bearer token.

    The plaintext token is returned to the caller exactly once —
    only the SHA-256 hash is persisted, so this is the route layer's
    single chance to put it on the wire.

    Args:
        session: Active SQLAlchemy session.
        payload: Validated create request.

    Returns:
        tuple[Recipient, str]: The new row and the plaintext token.

    Raises:
        ConflictError: If a recipient with the same name already
            exists.
    """
    token, token_hash = _generate_token()
    recipient = Recipient(
        name=payload.name,
        comment=payload.comment,
        owner=payload.owner,
        bearer_token_hash=token_hash,
    )
    session.add(recipient)
    with commit_or_conflict(session, f"Recipient '{payload.name}' already exists"):
        pass
    session.refresh(recipient)
    return recipient, token


def get_recipient(session: Session, name: str) -> Recipient:
    """Fetch a recipient by name.

    Args:
        session: Active SQLAlchemy session.
        name: Recipient name.

    Returns:
        Recipient: The matching row.

    Raises:
        NotFoundError: If no recipient with the given name exists.
    """
    recipient = session.scalar(select(Recipient).where(Recipient.name == name))
    if recipient is None:
        raise NotFoundError(f"Recipient '{name}' does not exist")
    return recipient


def list_recipients(
    session: Session,
    max_results: int | None = None,
    page_token: str | None = None,
) -> tuple[list[Recipient], str | None]:
    """List recipients with keyset pagination.

    Args:
        session: Active SQLAlchemy session.
        max_results: Spec-defined page size hint.
        page_token: Opaque pagination cursor.

    Returns:
        tuple[list[Recipient], str | None]: One page of recipients
            plus the next page token (``None`` if last).
    """
    stmt, limit = apply_keyset(select(Recipient), Recipient, page_token, max_results)
    rows = list(session.scalars(stmt))
    return build_next_token(rows, limit)


def update_recipient(
    session: Session,
    name: str,
    payload: UpdateRecipient,
    fields_set: set[str],
) -> Recipient:
    """Apply a PATCH to a recipient.

    Replace-style semantics driven by ``fields_set``; an empty body
    is a no-op. The bearer token is untouchable here — rotation has
    its own endpoint so credential events stay separately auditable.

    Args:
        session: Active SQLAlchemy session.
        name: Current recipient name (path parameter).
        payload: Validated update request.
        fields_set: Names of fields explicitly present in the body.

    Returns:
        Recipient: The updated row.

    Raises:
        ConflictError: If ``new_name`` collides with an existing
            recipient.
    """
    recipient = get_recipient(session, name)
    if not fields_set:
        return recipient
    if "new_name" in fields_set and payload.new_name is not None:
        recipient.name = payload.new_name
    if "comment" in fields_set:
        recipient.comment = payload.comment
    if "owner" in fields_set:
        recipient.owner = payload.owner
    recipient.updated_at = _now_ms()
    with commit_or_conflict(
        session,
        f"Recipient rename to '{payload.new_name}' collides with an existing recipient",
    ):
        pass
    session.refresh(recipient)
    return recipient


def delete_recipient(session: Session, name: str) -> None:
    """Delete a recipient together with its grants.

    No ``force`` gate — grants are weak composition (see
    :func:`delete_share`). The recipient's bearer token stops
    authenticating the moment the row is gone.

    Args:
        session: Active SQLAlchemy session.
        name: Recipient name.

    Raises:
        NotFoundError: Propagates from :func:`get_recipient` when the
            name does not resolve.
    """
    recipient = get_recipient(session, name)
    session.execute(delete(ShareGrant).where(ShareGrant.recipient_id == recipient.id))
    session.delete(recipient)
    session.commit()


def rotate_recipient_token(session: Session, name: str) -> str:
    """Replace a recipient's bearer token, returning the new plaintext.

    The previous token stops authenticating the moment this commits —
    there is no dual-token grace window in the MVP, so callers should
    hand the fresh token to the recipient before their next protocol
    call. Rotation is the only remedy for a lost token because soyuz
    stores hashes exclusively.

    Args:
        session: Active SQLAlchemy session.
        name: Recipient name.

    Returns:
        str: The fresh plaintext bearer token.

    Raises:
        NotFoundError: Propagates from :func:`get_recipient` when the
            name does not resolve.
    """
    recipient = get_recipient(session, name)
    token, token_hash = _generate_token()
    recipient.bearer_token_hash = token_hash
    recipient.updated_at = _now_ms()
    session.commit()
    return token


# ---------------------------------------------------------------------------
# Grants
# ---------------------------------------------------------------------------


def grant_share(session: Session, share_name: str, recipient_name: str) -> None:
    """Make a share visible to a recipient.

    Idempotent (it backs a ``PUT``): re-granting an existing pair is
    a no-op detected via the ``(share_id, recipient_id)`` unique
    constraint rather than a pre-check ``SELECT``, so two racing
    grant calls both succeed.

    Args:
        session: Active SQLAlchemy session.
        share_name: Name of the share.
        recipient_name: Name of the recipient.

    Raises:
        NotFoundError: Propagates when the share or recipient does
            not exist.
    """
    share = get_share(session, share_name)
    recipient = get_recipient(session, recipient_name)
    grant = ShareGrant(share_id=share.id, recipient_id=recipient.id)
    session.add(grant)
    try:
        session.commit()
    except IntegrityError:
        # The (share_id, recipient_id) unique constraint fired: the
        # grant already exists, which for an idempotent PUT is success
        # — including when a concurrent request inserted it between
        # our resolution and our commit.
        session.rollback()


def revoke_share(session: Session, share_name: str, recipient_name: str) -> None:
    """Remove a recipient's visibility of a share.

    Args:
        session: Active SQLAlchemy session.
        share_name: Name of the share.
        recipient_name: Name of the recipient.

    Raises:
        NotFoundError: If the share or recipient does not exist, or
            no grant binds them.
    """
    share = get_share(session, share_name)
    recipient = get_recipient(session, recipient_name)
    grant = session.scalar(
        select(ShareGrant).where(
            ShareGrant.share_id == share.id,
            ShareGrant.recipient_id == recipient.id,
        ),
    )
    if grant is None:
        raise NotFoundError(
            f"Share '{share_name}' is not granted to recipient '{recipient_name}'",
        )
    session.delete(grant)
    session.commit()
