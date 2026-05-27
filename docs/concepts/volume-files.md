# Volume files

soyuz-catalog adds four routes under `/volumes/{full_name}/files/*`
so single-node deployments can store and serve files **without
provisioning an object store**. The upstream spec defines only the
five volume *metadata* endpoints (create, list, get, update, delete)
— a real Databricks UC deployment delegates file IO to S3, ABFSS, or
GCS via pre-signed URLs. That assumption breaks for dev laptops,
demos, integration tests, and very small self-hosted setups. The
volume-files extension is the smallest thing that makes "soyuz on
your laptop" actually useful.

The endpoint set is documented as an over-the-spec extension in
[DIVERGENCES.md](../divergences.md) and explicitly excluded from the
spec-conformance gate.

## What the routes do, and what stays spec

The metadata surface is unchanged. A volume row is still created,
read, updated, and deleted exactly as the UC spec describes. The
extension adds an IO layer **on top of** the metadata, addressed by
the volume's `full_name`:

| Route | Effect |
|---|---|
| `POST /volumes/{full_name}/files?path=<dest>` | Stream a `multipart/form-data` body into the volume at `dest`. |
| `GET /volumes/{full_name}/files` | List every file in the volume. Returns `{path, size_bytes, is_dir}` per entry. |
| `GET /volumes/{full_name}/files/{path:path}` | Stream the file's bytes out. |
| `DELETE /volumes/{full_name}/files/{path:path}` | Remove the file. |

Bytes never touch the metadata database — they go straight to the
backend selected by the volume's `storage_location`. The metadata
table just supplies the routing target.

## When to use it, when not

!!! warning "Single-node only"

    The volume-files routes serve from the local filesystem of the
    soyuz process. Do not put them behind a load balancer with more
    than one replica — configure external locations instead.

**Use it for:**

- Local-dev demos where standing up MinIO or a real bucket would be
  overkill.
- Integration tests that need real file IO against a real soyuz, not
  a mocked storage layer.
- Single-node hobby deployments.

**Don't use it for:**

- Multi-node production. The routes serve files from the process's
  local filesystem (or whichever backend the URI scheme selects on
  that one host) — a second soyuz replica would not see the bytes.
  Configure an external location with a real cloud backend instead.
- Hot serving of large files. soyuz is a metadata server; it streams
  bytes through itself, which is fine for `O(100 MB)` integration
  fixtures and wrong for `O(10 GB)` data files. Use a CDN or a
  pre-signed URL flow from a real object store.

## The pluggable backend protocol

`soyuz_catalog/storage/volume_files.py` defines a
`VolumeFileBackend` protocol with four methods: `upload`, `browse`,
`download`, `delete`. Today the only implementation is the
filesystem-backed one for `file://` URIs. Adding cloud backends is
deliberately a one-class change:

1. Implement the four-method protocol against the cloud SDK.
2. Add a case in `get_backend` that maps the URI scheme
   (`s3://`, `abfss://`, `gs://`) to the new class.

No route change. No schema change. Calling code dispatches on the
volume's `storage_location` URI scheme.

## How writes and reads stream

Uploads chunk through soyuz in 64 KB blocks — the request body
flows directly into the backend without buffering the whole file in
memory. Downloads use FastAPI's `FileResponse`, which streams from
disk back to the client with the same chunked transfer.

Path-traversal attempts (`../`, absolute paths, symlinks pointing
out of the volume root) are rejected at the backend layer as 400
`INVALID_ARGUMENT`. The volume root, derived from the metadata
row's `storage_location`, is the hard boundary.

## See also

- [Walkthrough: files API on a volume](../guides/walkthroughs/volume-files.md)
  — concrete upload / list / download / delete sequence.
- [Concepts → Credentials](credentials.md) — why soyuz does not vend
  cloud tokens, and how that interacts with cloud-backed volumes.
- [Extensions over the spec](extensions-over-spec.md) — where this
  fits in the broader extension picture.
- [Divergences → Volumes: file IO](../divergences.md) — wire-level
  definition and the explicit conformance-test skip.
