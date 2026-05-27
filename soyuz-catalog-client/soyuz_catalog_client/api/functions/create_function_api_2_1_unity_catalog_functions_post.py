from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_function_request import CreateFunctionRequest
from ...models.function_info import FunctionInfo
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response


def _get_kwargs(
    *,
    body: CreateFunctionRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/2.1/unity-catalog/functions",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> FunctionInfo | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = FunctionInfo.from_dict(response.json())

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
) -> Response[FunctionInfo | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateFunctionRequest,
) -> Response[FunctionInfo | HTTPValidationError]:
    r"""Create function

     Create a new function under an existing schema.

    The request body is the double-wrapped ``{\"function_info\": {...}}``
    shape from the UC spec — we unwrap the inner ``CreateFunction``
    before handing it to the service layer.

    Args:
        payload: Create request wrapper.
        db: Database session dependency.

    Returns:
        FunctionInfo: The created function.

    Args:
        body (CreateFunctionRequest): Outer wrapper for ``POST /functions``.

            The UC spec defines the create request as ``{"function_info":
            CreateFunction}`` rather than a flat body — an unusual nesting
            driven by the way the protobuf IDL is translated into JSON. We
            mirror the wrapper exactly so OpenAPI-generated clients keep
            working.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[FunctionInfo | HTTPValidationError]
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
    body: CreateFunctionRequest,
) -> FunctionInfo | HTTPValidationError | None:
    r"""Create function

     Create a new function under an existing schema.

    The request body is the double-wrapped ``{\"function_info\": {...}}``
    shape from the UC spec — we unwrap the inner ``CreateFunction``
    before handing it to the service layer.

    Args:
        payload: Create request wrapper.
        db: Database session dependency.

    Returns:
        FunctionInfo: The created function.

    Args:
        body (CreateFunctionRequest): Outer wrapper for ``POST /functions``.

            The UC spec defines the create request as ``{"function_info":
            CreateFunction}`` rather than a flat body — an unusual nesting
            driven by the way the protobuf IDL is translated into JSON. We
            mirror the wrapper exactly so OpenAPI-generated clients keep
            working.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        FunctionInfo | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateFunctionRequest,
) -> Response[FunctionInfo | HTTPValidationError]:
    r"""Create function

     Create a new function under an existing schema.

    The request body is the double-wrapped ``{\"function_info\": {...}}``
    shape from the UC spec — we unwrap the inner ``CreateFunction``
    before handing it to the service layer.

    Args:
        payload: Create request wrapper.
        db: Database session dependency.

    Returns:
        FunctionInfo: The created function.

    Args:
        body (CreateFunctionRequest): Outer wrapper for ``POST /functions``.

            The UC spec defines the create request as ``{"function_info":
            CreateFunction}`` rather than a flat body — an unusual nesting
            driven by the way the protobuf IDL is translated into JSON. We
            mirror the wrapper exactly so OpenAPI-generated clients keep
            working.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[FunctionInfo | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreateFunctionRequest,
) -> FunctionInfo | HTTPValidationError | None:
    r"""Create function

     Create a new function under an existing schema.

    The request body is the double-wrapped ``{\"function_info\": {...}}``
    shape from the UC spec — we unwrap the inner ``CreateFunction``
    before handing it to the service layer.

    Args:
        payload: Create request wrapper.
        db: Database session dependency.

    Returns:
        FunctionInfo: The created function.

    Args:
        body (CreateFunctionRequest): Outer wrapper for ``POST /functions``.

            The UC spec defines the create request as ``{"function_info":
            CreateFunction}`` rather than a flat body — an unusual nesting
            driven by the way the protobuf IDL is translated into JSON. We
            mirror the wrapper exactly so OpenAPI-generated clients keep
            working.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        FunctionInfo | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
