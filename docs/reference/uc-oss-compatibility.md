# UC-OSS MODEL Securable — Proto-vs-soyuz Compatibility Report

**Status**: snapshot, captured 2026-04-30. Not regenerated on every release.
**Source proto**: MLflow's `unity_catalog_oss_service.proto` +
`unity_catalog_oss_messages.proto` (MLflow ref `19d8dc349`).
**Soyuz ref at capture**: `33915330` (`v0.2.0rc5`).
**API prefix**: `/api/2.1/unity-catalog` (the settings default).

This report compares the RPCs MLflow's UC-OSS client expects against
soyuz' implementation. A follow-up regeneration is needed when either
the MLflow proto or soyuz' model-version surface materially changes.

## Summary

- ✅ ready (no work): 9 RPCs
- ⚠️ tweak needed: 1 RPC (createModelVersion — status state machine)
- ❌ missing: 2 RPCs (finalizeModelVersion, generateTemporaryModelVersionCredential)

Path-prefix difference: proto says `/unity-catalog/...`, soyuz mounts under
`/api/2.1/unity-catalog/...`. The MLflow client constructs URLs from
`set_registry_uri(...)`. Configurable via
`MLFLOW_REGISTRY_URI=uc-oss://host:port/api/2.1/unity-catalog` — no server-side
aliasing required.

## RPC-by-RPC matrix

| # | RPC | Proto endpoint | Soyuz route | Status |
| --- | --- | --- | --- | --- |
| 1 | `createRegisteredModel` | `POST /unity-catalog/models` | `POST {prefix}/models` ([registered_models.py:55](https://github.com/FloHofstetter/soyuz-catalog/blob/main/soyuz_catalog/api/routes/registered_models.py#L55)) | ✅ |
| 2 | `getRegisteredModel` | `GET /unity-catalog/models/{full_name}` | `GET {prefix}/models/{full_name}` ([:112](https://github.com/FloHofstetter/soyuz-catalog/blob/main/soyuz_catalog/api/routes/registered_models.py#L112)) | ✅ |
| 3 | `updateRegisteredModel` | `PATCH /unity-catalog/models/{full_name}` | `PATCH {prefix}/models/{full_name}` ([:134](https://github.com/FloHofstetter/soyuz-catalog/blob/main/soyuz_catalog/api/routes/registered_models.py#L134)) | ✅ |
| 4 | `deleteRegisteredModel` | `DELETE /unity-catalog/models/{full_name}` | `DELETE {prefix}/models/{full_name}` ([:163](https://github.com/FloHofstetter/soyuz-catalog/blob/main/soyuz_catalog/api/routes/registered_models.py#L163)) | ✅ |
| 5 | `listRegisteredModels` | `GET /unity-catalog/models` | `GET {prefix}/models` ([:73](https://github.com/FloHofstetter/soyuz-catalog/blob/main/soyuz_catalog/api/routes/registered_models.py#L73)) | ✅ |
| 6 | `createModelVersion` | `POST /unity-catalog/models/versions` | `POST {prefix}/models/versions` ([model_versions.py:64](https://github.com/FloHofstetter/soyuz-catalog/blob/main/soyuz_catalog/api/routes/model_versions.py#L64)) | ⚠️ |
| 7 | `getModelVersion` | `GET /unity-catalog/models/{full_name}/versions/{version}` | `GET {prefix}/models/{full_name}/versions/{version}` ([:122](https://github.com/FloHofstetter/soyuz-catalog/blob/main/soyuz_catalog/api/routes/model_versions.py#L122)) | ✅ |
| 8 | `updateModelVersion` | `PATCH /unity-catalog/models/{full_name}/versions/{version}` | `PATCH {prefix}/models/{full_name}/versions/{version}` ([:146](https://github.com/FloHofstetter/soyuz-catalog/blob/main/soyuz_catalog/api/routes/model_versions.py#L146)) | ✅ |
| 9 | `deleteModelVersion` | `DELETE /unity-catalog/models/{full_name}/versions/{version}` | `DELETE {prefix}/models/{full_name}/versions/{version}` ([:182](https://github.com/FloHofstetter/soyuz-catalog/blob/main/soyuz_catalog/api/routes/model_versions.py#L182)) | ✅ |
| 10 | `listModelVersions` | `GET /unity-catalog/models/{full_name}/versions` | `GET {prefix}/models/{full_name}/versions` ([:91](https://github.com/FloHofstetter/soyuz-catalog/blob/main/soyuz_catalog/api/routes/model_versions.py#L91)) | ✅ |
| 11 | **`finalizeModelVersion`** | `PATCH /unity-catalog/models/{full_name}/versions/{version}/finalize` | ❌ NOT IMPLEMENTED | ❌ |
| 12 | **`generateTemporaryModelVersionCredential`** | `POST /unity-catalog/temporary-model-version-credentials` | ❌ NOT IMPLEMENTED | ❌ |

## Field-shape verification

### CreateRegisteredModel (✅ ready)

Proto request fields (`unity_catalog_oss_messages.proto:47-62`):

- `name` (REQ), `catalog_name` (REQ), `schema_name` (REQ), `comment` (OPT), `storage_location` (IGN on create)

Soyuz `CreateRegisteredModel` ([schemas.py:1091-1106](https://github.com/FloHofstetter/soyuz-catalog/blob/main/soyuz_catalog/api/schemas.py#L1091)):

- `name` Field(min_length=1) ✓, `catalog_name` ✓, `schema_name` ✓, `comment` Optional ✓
- ⚠️ `storage_location` not accepted (`extra="forbid"`). Proto says IGN on create — soyuz being strict here is *more* compliant than the spec.

Response (Proto wraps in `{registered_model_info: RegisteredModelInfo}`):

- Soyuz returns flat `RegisteredModelInfo` directly — **the MLflow OSS client
  expects flat too** based on its `_get_response_from_method()` parsing in
  `uc_oss_rest_store.py`. Field-by-field shape match between proto's
  `RegisteredModelInfo` and `RegisteredModelInfo` schema confirmed.

### CreateModelVersion (⚠️ tweak needed: status state machine)

Proto says:

- `ModelVersionStatus` enum has 4 values: `MODEL_VERSION_STATUS_UNKNOWN=0`,
  `PENDING_REGISTRATION=1`, `FAILED_REGISTRATION=2`, `READY=3`
- `RegisteredModelInfo.storage_location` (output-only) — server populates this
  with a writable URI so the client can upload artifacts there before
  `finalizeModelVersion` is called

Soyuz today writes `status="READY"` directly on create
([models.py:732](https://github.com/FloHofstetter/soyuz-catalog/blob/main/soyuz_catalog/models.py#L732), default value `"READY"`),
and never populates `storage_location` on `ModelVersion`. This breaks the
MLflow OSS client's create-then-finalize flow.

**Required fix**:

- `model_version_service.create_model_version()` writes `status="PENDING_REGISTRATION"`
  and computes `storage_location = f"{model_artifact_root}/{model_id}/{version}/"`
- New setting `model_artifact_root` defaults to `file:///{appdata}/model_artifacts/`

### Other RegisteredModelInfo / ModelVersionInfo fields (✅ ready)

Proto field-by-field map for `RegisteredModelInfo`:

| Proto field | Soyuz field | Match |
| --- | --- | --- |
| `name` | `name` | ✓ |
| `catalog_name` | `catalog_name` (computed) | ✓ |
| `schema_name` | `schema_name` (computed) | ✓ |
| `full_name` | `full_name` (computed) | ✓ |
| `storage_location` | `storage_location` (always None) | ✓ (None ≡ omitted via `exclude_none=True`) |
| `comment` | `comment` | ✓ |
| `created_at` | `created_at` | ✓ |
| `created_by` | `created_by` | ✓ |
| `updated_at` | `updated_at` | ✓ |
| `updated_by` | `updated_by` | ✓ |
| `id` | `id` | ✓ |
| `browse_only` | ❌ not exposed | ⚠️ but field is OPT and `exclude_none=True` strips it — client treats absent as default |

Soyuz adds `owner` field which is not in the proto — over-spec, harmless
(MLflow OSS client ignores unknown fields).

For `ModelVersionInfo`:

| Proto field | Soyuz field | Match |
| --- | --- | --- |
| `model_name` | `model_name` (computed) | ✓ |
| `catalog_name` | `catalog_name` (computed) | ✓ |
| `schema_name` | `schema_name` (computed) | ✓ |
| `version` | `version` | ✓ |
| `source` | `source` | ✓ |
| `run_id` | `run_id` | ✓ |
| `status` | `status` (Literal of all 4 values) | ✓ once Step 2 lands |
| `storage_location` | `storage_location` (currently None) | ✓ once Step 2 lands |
| `comment` | `comment` | ✓ |
| `created_at` | `created_at` | ✓ |
| `created_by` | `created_by` | ✓ |
| `updated_at` | `updated_at` | ✓ |
| `updated_by` | `updated_by` | ✓ |
| `id` | `id` | ✓ |

## ❌ Missing — Step 3: `finalizeModelVersion`

**Proto**:

```proto
rpc finalizeModelVersion(FinalizeModelVersion) returns (FinalizeModelVersion.Response) {
  endpoints: { method: "PATCH"; path: "/unity-catalog/models/{full_name}/versions/{version}/finalize" }
}
message FinalizeModelVersion {
  optional string full_name = 1;
  optional int64 version = 2;
  message Response {
    optional ModelVersionInfo model_version_info = 1;
  }
}
```

**Required**:

- New PATCH route: `/{full_name}/versions/{version}/finalize` in
  `model_versions.py`
- New service: `finalize_model_version(db, full_name, version) -> ModelVersion`
- Idempotent: re-finalize on `READY` is no-op
- 409 if status is `FAILED_REGISTRATION`

**Wire shape**: Empty body (URL-only); response is the same flat
`ModelVersionInfo` as `getModelVersion`.

## ❌ Missing — Step 4: `generateTemporaryModelVersionCredential`

**Proto**:

```proto
rpc generateTemporaryModelVersionCredential(GenerateTemporaryModelVersionCredential) returns (...) {
  endpoints: { method: "POST"; path: "/unity-catalog/temporary-model-version-credentials" }
}
message GenerateTemporaryModelVersionCredential {
  optional string catalog_name = 1;
  optional string schema_name = 2;
  optional string model_name = 3;
  optional int64 version = 4;
  optional ModelVersionOperation operation = 5;  // READ_MODEL_VERSION=1, READ_WRITE_MODEL_VERSION=2
}
```

**Required**:

- New POST route: `/temporary-model-version-credentials` in
  `temporary_credentials.py` — sibling to existing
  `/temporary-table-credentials`, `/temporary-volume-credentials`,
  `/temporary-path-credentials`
- New request schema `GenerateTemporaryModelVersionCredential` in
  `schemas.py`
- New service `generate_model_version_credentials(db, payload)` in new file
  `services/model_version_credentials_service.py`
- For `file://` storage_location → return `TemporaryCredentials` with only
  `expiration_time` populated (matches existing stub pattern;
  MLflow client falls back to `LocalArtifactRepository` per
  `uc_oss_rest_store.py:412-431`)
- For `s3://` / `abfss://` / `gs://` → 501 with error_code
  `FEATURE_DISABLED` (out of scope for 21.1)

## MLflow client behavior reference

`mlflow/store/_unity_catalog/registry/uc_oss_rest_store.py:259-297`
(`create_model_version` flow):

1. `CreateModelVersion` HTTP POST → returns `ModelVersionInfo` with
   `status=PENDING_REGISTRATION` + `storage_location`
2. Client downloads/stages local artifact via `_local_model_dir(source, ...)`
3. Client calls `_get_temporary_model_version_write_credentials_oss(...)`
   → POST `/temporary-model-version-credentials` with
   `operation=READ_WRITE_MODEL_VERSION`
4. For `file://` storage_location: `_get_artifact_repo()` returns
   `LocalArtifactRepository(model_version.storage_location)` and writes
   directly to disk (no presigning needed)
5. After upload completes: `FinalizeModelVersion` HTTP PATCH
   → `status=READY`

Failure path: if step 4 fails, finalize never runs, version stays `PENDING_REGISTRATION`
indefinitely. Soyuz does not need GC for these — they're addressable for
delete via existing DELETE route.

## Out-of-scope confirmations

- **Aliases** (`set_registered_model_alias`, etc.) — explicitly NOT in UC-OSS
  proto; only in `databricks_uc_registry_service.proto`. MLflow OSS client
  raises `NotImplementedError` for these. No alias table needed in soyuz.
- **Tags on models** — UC-OSS proto has no `set_registered_model_tag`. Soyuz's
  current `TagSecurableType` exclusion of `registered_model` (`schemas.py:1778-1782`)
  is fine for UC-OSS-compliance. A `comment`-JSON bridge is available as a
  short-term workaround; real model tags would require a TagSecurableType
  extension.
- **`transition_model_version_stage`** — legacy MLflow API, not in UC-OSS.
  Client raises `NotImplementedError`.
- **Cloud credentials** (S3/Azure/GCP) — the snapshot covers `file://` only.
  Cloud branches are 501-stubbed.

## Verification

After Steps 2/3/4 land and the soyuz-catalog client is regenerated, the
MLflow UC-OSS smoke test at `tests/test_mlflow_uc_oss_smoke.py` should
round-trip: create → finalize → get → list → delete → end without
raising.
