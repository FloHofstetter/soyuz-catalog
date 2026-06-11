"""HTTP routes for the Delta Sharing Recipients management resource.

Over-the-spec addition (ADR-0015); skipped by the spec-conformance
subset check like every other extension. Recipients are the
bearer-token identities the protocol surface authenticates — the
plaintext token appears on exactly two responses (create and
rotate-token) and is never retrievable afterwards because soyuz
stores only its SHA-256 hash.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from soyuz_catalog.api.deps import get_db
from soyuz_catalog.api.schemas import (
    CreateRecipient,
    ListRecipientsResponse,
    RecipientInfo,
    RotateRecipientTokenResponse,
    UpdateRecipient,
)
from soyuz_catalog.models import Recipient
from soyuz_catalog.services import audit_service, sharing_service

router = APIRouter(prefix="/recipients", tags=["recipients"])


def _to_info(recipient: Recipient, token: str | None = None) -> RecipientInfo:
    """Assemble a :class:`RecipientInfo` response from an ORM row.

    ``bearer_token_hash`` deliberately never crosses the wire — the
    only secret-adjacent field is the plaintext ``token``, and only
    when the caller just minted it.

    Args:
        recipient: The recipient ORM row.
        token: Plaintext bearer token, supplied by the create route
            only (rotation has its own response shape).

    Returns:
        RecipientInfo: The wire-format response.
    """
    return RecipientInfo(
        name=recipient.name,
        id=recipient.id,
        comment=recipient.comment,
        owner=recipient.owner,
        token=token,
        created_at=recipient.created_at,
        created_by=recipient.created_by,
        updated_at=recipient.updated_at,
        updated_by=recipient.updated_by,
    )


@router.post(
    "",
    response_model=RecipientInfo,
    response_model_exclude_none=True,
    summary="Create recipient",
)
def create_recipient(payload: CreateRecipient, db: Session = Depends(get_db)) -> RecipientInfo:
    """Create a new recipient and mint its bearer token.

    The response carries the plaintext ``token`` — the only time it
    is ever visible. Store it; soyuz cannot re-serve it.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        RecipientInfo: The created recipient including the one-time
            plaintext ``token``.
    """
    recipient, token = sharing_service.create_recipient(db, payload)
    audit_service.log_action(
        db,
        action="recipient.created",
        target=payload.name,
        detail={"recipient_id": recipient.id},
    )
    return _to_info(recipient, token=token)


@router.get(
    "",
    response_model=ListRecipientsResponse,
    response_model_exclude_none=True,
    summary="List recipients",
)
def list_recipients(
    max_results: int | None = Query(default=None, ge=0, le=1000),
    page_token: str | None = None,
    db: Session = Depends(get_db),
) -> ListRecipientsResponse:
    """List recipients with keyset pagination.

    Args:
        max_results: Page size hint, 1..1000.
        page_token: Opaque cursor from a previous ``next_page_token``.
        db: Database session dependency.

    Returns:
        ListRecipientsResponse: One page of recipients plus the next
            page token (``None`` on the last page).
    """
    rows, next_token = sharing_service.list_recipients(
        db,
        max_results=max_results,
        page_token=page_token,
    )
    return ListRecipientsResponse(
        recipients=[_to_info(r) for r in rows],
        next_page_token=next_token,
    )


@router.get(
    "/{name}",
    response_model=RecipientInfo,
    response_model_exclude_none=True,
    summary="Get recipient by name",
)
def get_recipient(name: str, db: Session = Depends(get_db)) -> RecipientInfo:
    """Fetch a single recipient by name (never includes the token).

    Args:
        name: Recipient name.
        db: Database session dependency.

    Returns:
        RecipientInfo: The requested recipient.
    """
    recipient = sharing_service.get_recipient(db, name)
    return _to_info(recipient)


@router.patch(
    "/{name}",
    response_model=RecipientInfo,
    response_model_exclude_none=True,
    summary="Update recipient",
)
def update_recipient(
    name: str,
    payload: UpdateRecipient,
    db: Session = Depends(get_db),
) -> RecipientInfo:
    """Update an existing recipient's name, comment, or owner.

    Args:
        name: Current recipient name.
        payload: Patch body. Only fields explicitly present are
            applied; the bearer token has its own rotation endpoint.
        db: Database session dependency.

    Returns:
        RecipientInfo: The updated recipient.
    """
    recipient = sharing_service.update_recipient(db, name, payload, set(payload.model_fields_set))
    audit_service.log_action(
        db,
        action="recipient.updated",
        target=name,
        detail={"changes": sorted(payload.model_fields_set)},
    )
    return _to_info(recipient)


@router.delete("/{name}", summary="Delete recipient")
def delete_recipient(name: str, db: Session = Depends(get_db)) -> dict[str, str]:
    """Delete a recipient together with its grants.

    Args:
        name: Recipient name.
        db: Database session dependency.

    Returns:
        dict[str, str]: Empty success payload.
    """
    sharing_service.delete_recipient(db, name)
    audit_service.log_action(db, action="recipient.deleted", target=name)
    return {}


@router.post(
    "/{name}/rotate-token",
    response_model=RotateRecipientTokenResponse,
    summary="Rotate recipient bearer token",
)
def rotate_recipient_token(
    name: str,
    db: Session = Depends(get_db),
) -> RotateRecipientTokenResponse:
    """Replace the recipient's bearer token and return the new plaintext.

    The previous token stops authenticating immediately — there is no
    grace window. The audit entry records the event but never the
    token material.

    Args:
        name: Recipient name.
        db: Database session dependency.

    Returns:
        RotateRecipientTokenResponse: The fresh one-time plaintext
            token.
    """
    token = sharing_service.rotate_recipient_token(db, name)
    audit_service.log_action(db, action="recipient.token_rotated", target=name)
    return RotateRecipientTokenResponse(token=token)
