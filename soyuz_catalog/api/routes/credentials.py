"""HTTP routes for the Storage Credentials CRUD resource.

Not to be confused with :mod:`soyuz_catalog.api.routes.temporary_credentials`,
which hosts the ``/temporary-*-credentials`` stub endpoints. Those are
the credential-vending endpoints; this module is the metastore-level
CRUD surface for **storage credential definitions** (named credentials
that external locations bind to for governance). The two concepts
share a word but are entirely separate resources in the UC spec.
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from soyuz_catalog.api.deps import get_db
from soyuz_catalog.api.schemas import (
    AwsIamRoleResponse,
    CreateCredentialRequest,
    CredentialInfo,
    ListCredentialsResponse,
    UpdateCredentialRequest,
)
from soyuz_catalog.models import Credential
from soyuz_catalog.services import credential_service

router = APIRouter(prefix="/credentials", tags=["credentials"])


def _to_info(credential: Credential) -> CredentialInfo:
    """Assemble a :class:`CredentialInfo` response from an ORM row.

    The AWS IAM role triple is reconstructed into the nested
    :class:`AwsIamRoleResponse` here rather than by a
    ``from_attributes=True`` model validation because the ORM stores
    the three fields flat on the row (see
    :class:`soyuz_catalog.models.Credential` for why). The nested
    object is only built when there is a ``role_arn`` on the row; a
    credential created without an AWS payload serialises with
    ``aws_iam_role`` absent so clients do not see a phantom empty
    object.

    Args:
        credential: The credential ORM row.

    Returns:
        CredentialInfo: The wire-format response.
    """
    aws_iam_role: AwsIamRoleResponse | None = None
    if credential.aws_iam_role_arn is not None:
        aws_iam_role = AwsIamRoleResponse(
            role_arn=credential.aws_iam_role_arn,
            external_id=credential.aws_iam_role_external_id,
            unity_catalog_iam_arn=credential.aws_iam_role_unity_catalog_iam_arn,
        )
    return CredentialInfo(
        name=credential.name,
        id=credential.id,
        purpose=credential.purpose,  # type: ignore[arg-type]
        comment=credential.comment,
        owner=credential.owner,
        aws_iam_role=aws_iam_role,
        created_at=credential.created_at,
        created_by=credential.created_by,
        updated_at=credential.updated_at,
        updated_by=credential.updated_by,
    )


@router.post(
    "",
    response_model=CredentialInfo,
    response_model_exclude_none=True,
    summary="Create storage credential",
)
def create_credential(
    payload: CreateCredentialRequest,
    db: Session = Depends(get_db),
) -> CredentialInfo:
    """Create a new storage credential.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        CredentialInfo: The created credential.
    """
    credential = credential_service.create_credential(db, payload)
    return _to_info(credential)


@router.get(
    "",
    response_model=ListCredentialsResponse,
    response_model_exclude_none=True,
    summary="List storage credentials",
)
def list_credentials(
    purpose: Literal["STORAGE"] | None = Query(default=None),
    max_results: int | None = Query(default=None, ge=0, le=1000),
    page_token: str | None = None,
    db: Session = Depends(get_db),
) -> ListCredentialsResponse:
    """List credentials with keyset pagination and optional purpose filter.

    Args:
        purpose: Optional ``CredentialPurpose`` filter. Currently only
            ``STORAGE`` is defined by the upstream spec; typing it as
            a ``Literal`` means a typo surfaces as 422 from FastAPI's
            query-param validator.
        max_results: Page size hint, 1..1000.
        page_token: Opaque cursor from a previous ``next_page_token``.
        db: Database session dependency.

    Returns:
        ListCredentialsResponse: One page of credentials plus the next
            page token (``None`` on the last page).
    """
    rows, next_token = credential_service.list_credentials(
        db,
        purpose=purpose,
        max_results=max_results,
        page_token=page_token,
    )
    return ListCredentialsResponse(
        credentials=[_to_info(r) for r in rows],
        next_page_token=next_token,
    )


@router.get(
    "/{name}",
    response_model=CredentialInfo,
    response_model_exclude_none=True,
    summary="Get storage credential by name",
)
def get_credential(name: str, db: Session = Depends(get_db)) -> CredentialInfo:
    """Fetch a single credential by name.

    Args:
        name: Credential name.
        db: Database session dependency.

    Returns:
        CredentialInfo: The requested credential.
    """
    credential = credential_service.get_credential(db, name)
    return _to_info(credential)


@router.patch(
    "/{name}",
    response_model=CredentialInfo,
    response_model_exclude_none=True,
    summary="Update storage credential",
)
def update_credential(
    name: str,
    payload: UpdateCredentialRequest,
    db: Session = Depends(get_db),
) -> CredentialInfo:
    """Update an existing credential.

    Args:
        name: Current credential name.
        payload: Patch body. Only fields explicitly present are applied.
        db: Database session dependency.

    Returns:
        CredentialInfo: The updated credential.
    """
    credential = credential_service.update_credential(
        db,
        name,
        payload,
        set(payload.model_fields_set),
    )
    return _to_info(credential)


@router.delete("/{name}", summary="Delete storage credential")
def delete_credential(
    name: str,
    force: bool = False,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Delete a credential.

    Args:
        name: Credential name.
        force: Cascade flag. Without ``force``, referenced external
            locations cause a 409; with ``force=true`` the service
            deletes every referencing external location first, then
            the credential itself.
        db: Database session dependency.

    Returns:
        dict[str, str]: Empty success payload.
    """
    credential_service.delete_credential(db, name, force=force)
    return {}
