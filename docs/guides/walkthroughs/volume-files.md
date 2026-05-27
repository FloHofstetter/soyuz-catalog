# Walkthrough — Files API on a volume

> **Goal:** create a volume backed by the local filesystem, upload a
> file, read it, list directory contents, delete it.
>
> **Surface:** `/api/2.1/unity-catalog/volumes/{full_name}/files/{path:path}`
> (over-the-spec extension).
>
> **Prereqs:** soyuz running on `:8000`.

The `/files` routes are not in the open Unity Catalog spec. They exist
so single-node deployments can store and serve files without provisioning
an object store. See [Divergences → Volumes: file IO](../../divergences.md).

```bash
BASE=http://127.0.0.1:8000/api/2.1/unity-catalog
H="content-type:application/json"
```

## 1. Seed a catalog and schema

**Action**

```bash
curl -sX POST "$BASE/catalogs" -H $H -d '{"name":"ops"}' > /dev/null
curl -sX POST "$BASE/schemas"  -H $H -d '{"name":"staging","catalog_name":"ops"}' > /dev/null
```

**Expect**

No output.

## 2. Create a volume with a `file://` location

**Action**

```bash
mkdir -p /tmp/ops-staging-uploads
curl -sX POST "$BASE/volumes" -H $H -d '{
  "name":"uploads",
  "catalog_name":"ops",
  "schema_name":"staging",
  "volume_type":"EXTERNAL",
  "storage_location":"file:///tmp/ops-staging-uploads"
}'
```

**Expect**

`200 OK`. Response has `"full_name":"ops.staging.uploads"` and the
storage location you provided.

## 3. Upload a file

The PUT route takes the path as a URL segment after `/files/`. Bytes
are read from the request body.

**Action**

```bash
curl -sX POST "$BASE/volumes/ops.staging.uploads/files/hello.txt" \
     --data-binary "hello, soyuz"
```

**Expect**

`200 OK`. The body of the response confirms `path` and (optionally)
`size_bytes`.

## 4. List files in the volume

**Action**

```bash
curl -s "$BASE/volumes/ops.staging.uploads/files" | jq '.files[].path'
```

**Expect**

```
"hello.txt"
```

## 5. Download the file

**Action**

```bash
curl -s "$BASE/volumes/ops.staging.uploads/files/hello.txt"
```

**Expect**

`hello, soyuz` printed to stdout.

## 6. Path traversal is rejected

The route refuses paths that escape the volume root.

**Action**

```bash
curl -sX POST "$BASE/volumes/ops.staging.uploads/files/../../etc/passwd" \
     --data-binary "nope"
```

**Expect**

`400 BAD_REQUEST` with an `INVALID_ARGUMENT` error code. soyuz never
writes anything to `/etc`.

## 7. Delete the file

**Action**

```bash
curl -sX DELETE "$BASE/volumes/ops.staging.uploads/files/hello.txt"
curl -s        "$BASE/volumes/ops.staging.uploads/files" | jq '.files | length'
```

**Expect**

`0`.

## 8. Clean up

```bash
curl -sX DELETE "$BASE/volumes/ops.staging.uploads"              > /dev/null
curl -sX DELETE "$BASE/schemas/ops.staging?force=true"           > /dev/null
curl -sX DELETE "$BASE/catalogs/ops"                              > /dev/null
rm -rf /tmp/ops-staging-uploads
```

## Why this exists

A real UC deployment delegates file IO to whichever cloud the volume
lives on (S3, ABFSS, GCS), via pre-signed URLs and separate object-store
credentials. soyuz includes a minimal direct-IO surface so the
single-node and local-development cases do not require an object store.

The backend is pluggable through the `VolumeFileBackend` protocol in
[`soyuz_catalog/storage/`](https://github.com/FloHofstetter/soyuz-catalog/tree/main/soyuz_catalog/storage)
— today the `file://` backend ships; cloud backends drop in as new
implementations of the same protocol.

## See also

- [Divergences → Volumes: file IO](../../divergences.md)
- [Concepts → Extensions over the spec](../../concepts/extensions-over-spec.md)
- [REST API reference](../../reference/api.md) — volume endpoints.
