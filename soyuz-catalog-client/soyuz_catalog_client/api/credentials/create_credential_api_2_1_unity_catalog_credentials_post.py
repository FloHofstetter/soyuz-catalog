from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_credential_request import CreateCredentialRequest
from ...models.credential_info import CredentialInfo
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response


def _get_kwargs(
    *,
    body: CreateCredentialRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/2.1/unity-catalog/credentials",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> CredentialInfo | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = CredentialInfo.from_dict(response.json())

        return response_200

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[CredentialInfo | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateCredentialRequest,
) -> Response[CredentialInfo | HTTPValidationError]:
    """Create storage credential

     Create a new storage credential.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        CredentialInfo: The created credential.

    Args:
        body (CreateCredentialRequest): Request body for ``POST /credentials``.

            ``name`` is required. ``aws_iam_role`` is the only supported
            credential payload because the upstream UC OpenAPI ``all.yaml`` we
            pin as the contract defines only that shape; Azure and GCP
            variants that exist in forks are deliberately not modelled (see
            :class:`soyuz_catalog.models.Credential` for the reasoning).

            ``purpose`` is optional and defaults to ``STORAGE`` — the only
            value defined by ``CredentialPurpose`` today. Typing it as a
            ``Literal`` means a typo (``STORGE``) surfaces as 422 at the
            Pydantic layer instead of silently landing in the DB.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CredentialInfo | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: CreateCredentialRequest,
) -> CredentialInfo | HTTPValidationError | None:
    """Create storage credential

     Create a new storage credential.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        CredentialInfo: The created credential.

    Args:
        body (CreateCredentialRequest): Request body for ``POST /credentials``.

            ``name`` is required. ``aws_iam_role`` is the only supported
            credential payload because the upstream UC OpenAPI ``all.yaml`` we
            pin as the contract defines only that shape; Azure and GCP
            variants that exist in forks are deliberately not modelled (see
            :class:`soyuz_catalog.models.Credential` for the reasoning).

            ``purpose`` is optional and defaults to ``STORAGE`` — the only
            value defined by ``CredentialPurpose`` today. Typing it as a
            ``Literal`` means a typo (``STORGE``) surfaces as 422 at the
            Pydantic layer instead of silently landing in the DB.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CredentialInfo | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateCredentialRequest,
) -> Response[CredentialInfo | HTTPValidationError]:
    """Create storage credential

     Create a new storage credential.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        CredentialInfo: The created credential.

    Args:
        body (CreateCredentialRequest): Request body for ``POST /credentials``.

            ``name`` is required. ``aws_iam_role`` is the only supported
            credential payload because the upstream UC OpenAPI ``all.yaml`` we
            pin as the contract defines only that shape; Azure and GCP
            variants that exist in forks are deliberately not modelled (see
            :class:`soyuz_catalog.models.Credential` for the reasoning).

            ``purpose`` is optional and defaults to ``STORAGE`` — the only
            value defined by ``CredentialPurpose`` today. Typing it as a
            ``Literal`` means a typo (``STORGE``) surfaces as 422 at the
            Pydantic layer instead of silently landing in the DB.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CredentialInfo | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreateCredentialRequest,
) -> CredentialInfo | HTTPValidationError | None:
    """Create storage credential

     Create a new storage credential.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        CredentialInfo: The created credential.

    Args:
        body (CreateCredentialRequest): Request body for ``POST /credentials``.

            ``name`` is required. ``aws_iam_role`` is the only supported
            credential payload because the upstream UC OpenAPI ``all.yaml`` we
            pin as the contract defines only that shape; Azure and GCP
            variants that exist in forks are deliberately not modelled (see
            :class:`soyuz_catalog.models.Credential` for the reasoning).

            ``purpose`` is optional and defaults to ``STORAGE`` — the only
            value defined by ``CredentialPurpose`` today. Typing it as a
            ``Literal`` means a typo (``STORGE``) surfaces as 422 at the
            Pydantic layer instead of silently landing in the DB.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CredentialInfo | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
