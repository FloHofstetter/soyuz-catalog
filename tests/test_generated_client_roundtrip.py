"""Generated-client round-trips for the extended-resource namespaces.

Per ADR-0007, the raw-httpx integration round-trips for credentials,
external locations, functions, registered models, metastore, staging
tables, temporary path credentials, and permissions are tests that
drive the generated ``soyuz-catalog-client``. The point is twofold:

1. Completeness lackmus: if a namespace stops being emitted by the
   generator because the OpenAPI document lost a route, the ``from
   soyuz_catalog_client.api.<ns>`` imports below fail at collection
   time — long before any assertion runs. That is the fail-fast
   signal we want.
2. Typed wire shapes: the generated dataclasses catch a
   field-renamed / field-dropped drift as an ``AttributeError``. The
   dedicated unit tests under ``tests/test_<resource>.py`` still pin
   the full wire shape against soyuz' own Pydantic schemas — the tests
   here are smoke checks that the client can actually talk to a live
   server end-to-end.

Upstream-SDK round-trips (catalog/schema/table/volume) remain in
``tests/test_sdk_crud_roundtrip.py`` — the two tracks co-exist; see
ADR-0007 for the rationale.
"""

from __future__ import annotations

import uuid

import pytest

pytest.importorskip("soyuz_catalog_client")

from soyuz_catalog_client import Client  # noqa: E402
from soyuz_catalog_client.api.catalogs import (  # noqa: E402
    create_catalog_api_2_1_unity_catalog_catalogs_post as _create_catalog,
)
from soyuz_catalog_client.api.catalogs import (
    delete_catalog_api_2_1_unity_catalog_catalogs_name_delete as _delete_catalog,
)
from soyuz_catalog_client.api.connections import (  # noqa: E402
    create_connection_api_2_1_unity_catalog_connections_post as _create_connection,
)
from soyuz_catalog_client.api.connections import (
    delete_connection_api_2_1_unity_catalog_connections_name_delete as _delete_connection,
)
from soyuz_catalog_client.api.connections import (
    get_connection_api_2_1_unity_catalog_connections_name_get as _get_connection,
)
from soyuz_catalog_client.api.connections import (
    update_connection_api_2_1_unity_catalog_connections_name_patch as _update_connection,
)
from soyuz_catalog_client.api.credentials import (  # noqa: E402
    create_credential_api_2_1_unity_catalog_credentials_post as _create_credential,
)
from soyuz_catalog_client.api.credentials import (
    delete_credential_api_2_1_unity_catalog_credentials_name_delete as _delete_credential,
)
from soyuz_catalog_client.api.credentials import (
    get_credential_api_2_1_unity_catalog_credentials_name_get as _get_credential,
)
from soyuz_catalog_client.api.credentials import (
    list_credentials_api_2_1_unity_catalog_credentials_get as _list_credentials,
)
from soyuz_catalog_client.api.credentials import (
    update_credential_api_2_1_unity_catalog_credentials_name_patch as _update_credential,
)
from soyuz_catalog_client.api.external_locations import (  # noqa: E402
    create_external_location_api_2_1_unity_catalog_external_locations_post as _create_external_location,
)
from soyuz_catalog_client.api.external_locations import (
    delete_external_location_api_2_1_unity_catalog_external_locations_name_delete as _delete_external_location,
)
from soyuz_catalog_client.api.external_locations import (
    get_external_location_api_2_1_unity_catalog_external_locations_name_get as _get_external_location,
)
from soyuz_catalog_client.api.functions import (  # noqa: E402
    create_function_api_2_1_unity_catalog_functions_post as _create_function,
)
from soyuz_catalog_client.api.functions import (
    delete_function_api_2_1_unity_catalog_functions_full_name_delete as _delete_function,
)
from soyuz_catalog_client.api.functions import (
    get_function_api_2_1_unity_catalog_functions_full_name_get as _get_function,
)
from soyuz_catalog_client.api.metastore import (  # noqa: E402
    get_metastore_summary_api_2_1_unity_catalog_metastore_summary_get as _get_metastore_summary,
)
from soyuz_catalog_client.api.model_versions import (  # noqa: E402
    create_model_version_api_2_1_unity_catalog_models_versions_post as _create_model_version,
)
from soyuz_catalog_client.api.permissions import (  # noqa: E402
    get_permissions_api_2_1_unity_catalog_permissions_securable_type_full_name_get as _get_permissions,
)
from soyuz_catalog_client.api.permissions import (
    update_permissions_api_2_1_unity_catalog_permissions_securable_type_full_name_patch as _update_permissions,
)
from soyuz_catalog_client.api.permissions.get_permissions_api_2_1_unity_catalog_permissions_securable_type_full_name_get import (  # noqa: E402,E501
    GetPermissionsApi21UnityCatalogPermissionsSecurableTypeFullNameGetSecurableType as _GetSecurableType,  # noqa: E501
)
from soyuz_catalog_client.api.permissions.update_permissions_api_2_1_unity_catalog_permissions_securable_type_full_name_patch import (  # noqa: E402,E501
    UpdatePermissionsApi21UnityCatalogPermissionsSecurableTypeFullNamePatchSecurableType as _UpdateSecurableType,  # noqa: E501
)
from soyuz_catalog_client.api.registered_models import (  # noqa: E402
    create_registered_model_api_2_1_unity_catalog_models_post as _create_registered_model,
)
from soyuz_catalog_client.api.registered_models import (
    delete_registered_model_api_2_1_unity_catalog_models_full_name_delete as _delete_registered_model,
)
from soyuz_catalog_client.api.schemas import (  # noqa: E402
    create_schema_api_2_1_unity_catalog_schemas_post as _create_schema,
)
from soyuz_catalog_client.api.tables import (  # noqa: E402
    create_staging_table_api_2_1_unity_catalog_staging_tables_post as _create_staging_table,
)
from soyuz_catalog_client.api.temporary_credentials import (  # noqa: E402
    generate_temporary_path_credentials_api_2_1_unity_catalog_temporary_path_credentials_post as _generate_path_credentials,
)
from soyuz_catalog_client.models import (  # noqa: E402
    AwsIamRoleRequest,
    ConnectionInfo,
    CreateCatalog,
    CreateCatalogTypeType0,
    CreateConnection,
    CreateConnectionConnectionType,
    CreateCredentialRequest,
    CreateExternalLocation,
    CreateFunction,
    CreateFunctionRequest,
    CreateFunctionRoutineBody,
    CreateFunctionSqlDataAccess,
    CreateModelVersion,
    CreateRegisteredModel,
    CreateSchema,
    CreateStagingTable,
    CredentialInfo,
    ExternalLocationInfo,
    FunctionInfo,
    FunctionParameterInfo,
    FunctionParameterInfos,
    GenerateTemporaryPathCredential,
    GenerateTemporaryPathCredentialOperation,
    GetMetastoreSummaryResponse,
    ListCredentialsResponse,
    ModelVersionInfo,
    Options,
    PermissionsChange,
    PermissionsChangeAddItem,
    PermissionsList,
    RegisteredModelInfo,
    StagingTableInfo,
    TemporaryCredentials,
    UpdateCredentialRequest,
    UpdatePermissions,
)

from tests._generated_client import make_generated_client

pytestmark = pytest.mark.integration


def _suffix() -> str:
    """Return an 8-hex-char token unique to the caller."""
    return uuid.uuid4().hex[:8]


def _make_parent(client: Client) -> tuple[str, str]:
    """Create a ``(catalog, schema)`` pair and return their names.

    Integration fixtures for nested-resource tests need a fresh
    parent tree. Returned names are unique per call so concurrent
    test runs cannot alias.
    """
    catalog = f"cat_{_suffix()}"
    schema = f"sch_{_suffix()}"
    created_catalog = _create_catalog.sync(
        client=client,
        body=CreateCatalog(name=catalog),
    )
    assert created_catalog is not None
    _create_schema.sync(
        client=client,
        body=CreateSchema(name=schema, catalog_name=catalog),
    )
    return catalog, schema


# ---------------------------------------------------------------------------
# Credentials + External Locations
# ---------------------------------------------------------------------------


def test_generated_client_credential_crud(live_server: str) -> None:
    client = make_generated_client(live_server)
    name = f"cred_{_suffix()}"
    role_arn = "arn:aws:iam::123456789012:role/soyuz-gen-test"

    created = _create_credential.sync(
        client=client,
        body=CreateCredentialRequest(
            name=name,
            aws_iam_role=AwsIamRoleRequest(role_arn=role_arn),
            comment="initial",
        ),
    )
    assert isinstance(created, CredentialInfo)
    assert created.name == name
    assert created.purpose == "STORAGE"
    assert created.aws_iam_role is not None
    assert created.aws_iam_role.role_arn == role_arn  # type: ignore[union-attr]
    external_id = created.aws_iam_role.external_id  # type: ignore[union-attr]

    fetched = _get_credential.sync(client=client, name=name)
    assert isinstance(fetched, CredentialInfo)
    assert fetched.id == created.id

    listed = _list_credentials.sync(client=client, purpose="STORAGE")
    assert isinstance(listed, ListCredentialsResponse)
    assert any(c.name == name for c in (listed.credentials or []))

    updated = _update_credential.sync(
        client=client,
        name=name,
        body=UpdateCredentialRequest(comment="edited"),
    )
    assert isinstance(updated, CredentialInfo)
    assert updated.comment == "edited"
    # external_id must not rotate on PATCH.
    assert updated.aws_iam_role.external_id == external_id  # type: ignore[union-attr]

    _delete_credential.sync(client=client, name=name)
    # Subsequent GET must 404 — raise_on_unexpected_status surfaces it.
    with pytest.raises(Exception):
        _get_credential.sync(client=client, name=name)


def test_generated_client_external_location_crud(live_server: str) -> None:
    client = make_generated_client(live_server)
    cred_name = f"cred_{_suffix()}"
    loc_name = f"loc_{_suffix()}"

    _create_credential.sync(
        client=client,
        body=CreateCredentialRequest(
            name=cred_name,
            aws_iam_role=AwsIamRoleRequest(
                role_arn="arn:aws:iam::123456789012:role/soyuz-gen-test",
            ),
        ),
    )
    created = _create_external_location.sync(
        client=client,
        body=CreateExternalLocation(
            name=loc_name,
            url=f"s3://bucket/{loc_name}",
            credential_name=cred_name,
            comment="initial",
        ),
    )
    assert isinstance(created, ExternalLocationInfo)
    assert created.name == loc_name
    assert created.credential_name == cred_name

    fetched = _get_external_location.sync(client=client, name=loc_name)
    assert isinstance(fetched, ExternalLocationInfo)
    assert fetched.id == created.id

    _delete_external_location.sync(client=client, name=loc_name)
    _delete_credential.sync(client=client, name=cred_name)


# ---------------------------------------------------------------------------
# Functions + Registered Models
# ---------------------------------------------------------------------------


def test_generated_client_function_crud(live_server: str) -> None:
    client = make_generated_client(live_server)
    catalog, schema = _make_parent(client)
    fn = f"fn_{_suffix()}"

    created = _create_function.sync(
        client=client,
        body=CreateFunctionRequest(
            function_info=CreateFunction(
                catalog_name=catalog,
                schema_name=schema,
                name=fn,
                data_type="INT",
                full_data_type="INT",
                input_params=FunctionParameterInfos(
                    parameters=[
                        FunctionParameterInfo(
                            name="x",
                            position=0,
                            type_json='{"type":"int"}',
                            type_name="INT",
                            type_text="int",
                        ),
                    ],
                ),
                return_params=FunctionParameterInfos(parameters=[]),
                is_deterministic=True,
                is_null_call=False,
                parameter_style="S",
                routine_body=CreateFunctionRoutineBody.SQL,
                routine_definition="SELECT x + 1",
                security_type="DEFINER",
                specific_name=fn,
                sql_data_access=CreateFunctionSqlDataAccess.CONTAINS_SQL,
            ),
        ),
    )
    assert isinstance(created, FunctionInfo)
    assert created.full_name == f"{catalog}.{schema}.{fn}"

    fetched = _get_function.sync(client=client, full_name=f"{catalog}.{schema}.{fn}")
    assert isinstance(fetched, FunctionInfo)
    assert fetched.function_id == created.function_id

    _delete_function.sync(client=client, full_name=f"{catalog}.{schema}.{fn}")


def test_generated_client_registered_model_crud(live_server: str) -> None:
    client = make_generated_client(live_server)
    catalog, schema = _make_parent(client)
    model = f"rm_{_suffix()}"

    created = _create_registered_model.sync(
        client=client,
        body=CreateRegisteredModel(
            name=model,
            catalog_name=catalog,
            schema_name=schema,
        ),
    )
    assert isinstance(created, RegisteredModelInfo)
    assert created.full_name == f"{catalog}.{schema}.{model}"

    version = _create_model_version.sync(
        client=client,
        body=CreateModelVersion(
            model_name=model,
            catalog_name=catalog,
            schema_name=schema,
            source="s3://artifacts/a",
        ),
    )
    assert isinstance(version, ModelVersionInfo)
    assert version.version == 1
    assert version.status == "READY"  # type: ignore[comparison-overlap]

    # Force cascade so the child version does not block deletion.
    _delete_registered_model.sync(
        client=client,
        full_name=f"{catalog}.{schema}.{model}",
        force=True,
    )


# ---------------------------------------------------------------------------
# Metastore summary + Staging tables + Path credentials
# ---------------------------------------------------------------------------


def test_generated_client_metastore_summary(live_server: str) -> None:
    client = make_generated_client(live_server)
    summary = _get_metastore_summary.sync(client=client)
    assert isinstance(summary, GetMetastoreSummaryResponse)
    assert summary.metastore_id is not None
    assert len(summary.metastore_id) == 32  # type: ignore[arg-type]

    # Stable across calls.
    again = _get_metastore_summary.sync(client=client)
    assert isinstance(again, GetMetastoreSummaryResponse)
    assert again.metastore_id == summary.metastore_id


def test_generated_client_staging_table_allocation(live_server: str) -> None:
    client = make_generated_client(live_server)
    catalog = f"cat_{_suffix()}"
    schema = f"sch_{_suffix()}"

    _create_catalog.sync(
        client=client,
        body=CreateCatalog(name=catalog, storage_root=f"s3://bucket/{catalog}"),
    )
    _create_schema.sync(
        client=client,
        body=CreateSchema(name=schema, catalog_name=catalog),
    )

    staged = _create_staging_table.sync(
        client=client,
        body=CreateStagingTable(
            name="st",
            catalog_name=catalog,
            schema_name=schema,
        ),
    )
    assert isinstance(staged, StagingTableInfo)
    assert staged.name == "st"
    assert staged.catalog_name == catalog
    assert staged.schema_name == schema
    assert staged.staging_location is not None
    assert "__staging__" in staged.staging_location  # type: ignore[operator]
    assert staged.staging_location.endswith("/st")  # type: ignore[union-attr]


@pytest.mark.parametrize(
    ("url", "expect_attr"),
    [
        ("s3://bucket/p", "aws_temp_credentials"),
        ("abfss://c@a.dfs.core.windows.net/p", "azure_user_delegation_sas"),
        ("gs://bucket/p", "gcp_oauth_token"),
    ],
)
def test_generated_client_temporary_path_credentials(
    live_server: str,
    url: str,
    expect_attr: str,
) -> None:
    client = make_generated_client(live_server)
    resp = _generate_path_credentials.sync(
        client=client,
        body=GenerateTemporaryPathCredential(
            url=url,
            operation=GenerateTemporaryPathCredentialOperation.PATH_READ,
        ),
    )
    assert isinstance(resp, TemporaryCredentials)
    assert getattr(resp, expect_attr) is not None
    assert resp.expiration_time > 0  # type: ignore[operator]


# ---------------------------------------------------------------------------
# Permissions
# ---------------------------------------------------------------------------


def test_generated_client_permissions_round_trip(live_server: str) -> None:
    client = make_generated_client(live_server)
    name = f"cat_{_suffix()}"
    _create_catalog.sync(client=client, body=CreateCatalog(name=name))

    empty = _get_permissions.sync(
        client=client,
        securable_type=_GetSecurableType.CATALOG,
        full_name=name,
    )
    assert isinstance(empty, PermissionsList)
    assert empty.privilege_assignments == []

    patched = _update_permissions.sync(
        client=client,
        securable_type=_UpdateSecurableType.CATALOG,
        full_name=name,
        body=UpdatePermissions(
            changes=[
                PermissionsChange(
                    principal="alice@example.com",
                    add=[PermissionsChangeAddItem.USE_CATALOG],
                    remove=[],
                ),
            ],
        ),
    )
    assert isinstance(patched, PermissionsList)
    assert patched.privilege_assignments is not None
    assert len(patched.privilege_assignments) == 1  # type: ignore[arg-type]
    assignment = patched.privilege_assignments[0]  # type: ignore[index]
    assert assignment.principal == "alice@example.com"

    # Cleanup cascades the grant.
    _delete_catalog.sync(client=client, name=name)


# ---------------------------------------------------------------------------
# Connections + Foreign catalogs
# ---------------------------------------------------------------------------


def test_generated_client_connection_crud(live_server: str) -> None:
    """End-to-end typed round-trip for Connections and foreign catalogs.

    Drives the Lakehouse-Federation surface through the generated
    client: create a
    connection, bind a foreign catalog to it, rebind PATCH, and finally
    delete the connection with ``force=true`` to cascade the foreign
    catalog away. The point is the same as every other sibling test in
    this module — a drift in the wire shape surfaces as an AttributeError
    or import failure, not a silent shape mismatch.
    """
    client = make_generated_client(live_server)
    conn_name = f"conn_{_suffix()}"

    options = Options()
    options["host"] = "db.example.com"
    options["port"] = "5432"
    created = _create_connection.sync(
        client=client,
        body=CreateConnection(
            name=conn_name,
            connection_type=CreateConnectionConnectionType.POSTGRESQL,
            options=options,
            comment="initial",
        ),
    )
    assert isinstance(created, ConnectionInfo)
    assert created.name == conn_name

    fetched = _get_connection.sync(client=client, name=conn_name)
    assert isinstance(fetched, ConnectionInfo)
    assert fetched.id == created.id

    # Rename the connection and confirm the new name resolves.
    from soyuz_catalog_client.models import UpdateConnection as _UpdateConnection

    renamed_name = f"{conn_name}_renamed"
    renamed = _update_connection.sync(
        client=client,
        name=conn_name,
        body=_UpdateConnection(new_name=renamed_name),
    )
    assert isinstance(renamed, ConnectionInfo)
    assert renamed.name == renamed_name

    # Bind a foreign catalog to the renamed connection.
    cat_name = f"fcat_{_suffix()}"
    foreign = _create_catalog.sync(
        client=client,
        body=CreateCatalog(
            name=cat_name,
            type_=CreateCatalogTypeType0.FOREIGN,
            connection_name=renamed_name,
        ),
    )
    assert foreign is not None
    # Type narrowing: the union includes the error envelope; pick off the
    # happy-path attribute access tolerantly.
    assert getattr(foreign, "type_", None) == "FOREIGN"
    assert getattr(foreign, "connection_name", None) == renamed_name

    # Cascade delete: force-delete the connection and confirm both rows
    # are gone.
    _delete_connection.sync(client=client, name=renamed_name, force=True)
    with pytest.raises(Exception):
        _get_connection.sync(client=client, name=renamed_name)
