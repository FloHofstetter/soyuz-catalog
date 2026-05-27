#!/usr/bin/env bash
# Regenerate the soyuz-catalog-client subpackage from the live FastAPI
# OpenAPI document.
#
# ADR-0007: the generated client is a second, additive SDK track
# alongside the upstream `unitycatalog` package. This script is the
# source-of-truth producer for every regeneration — the CI
# `client-drift` job runs it into a tmp directory and diffs the result
# against the committed state, so **any** manual edit under
# `soyuz-catalog-client/soyuz_catalog_client/` will fail the build.
#
# `--meta=none` means only the package directory is written; the
# hand-maintained `pyproject.toml` and `README.md` under
# `soyuz-catalog-client/` are outside the drift check by design.
set -euo pipefail

cd "$(dirname "$0")/.."

OUTPUT_DIR="${1:-soyuz-catalog-client/soyuz_catalog_client}"
OPENAPI_JSON="$(mktemp --tmpdir soyuz-openapi.XXXXXX.json)"
trap 'rm -f "$OPENAPI_JSON"' EXIT

uv run python scripts/dump_openapi.py > "$OPENAPI_JSON"

mkdir -p "$OUTPUT_DIR"
uv run openapi-python-client generate \
    --path "$OPENAPI_JSON" \
    --config .openapi-python-client.yaml \
    --meta none \
    --output-path "$OUTPUT_DIR" \
    --overwrite

echo "regenerated client at $OUTPUT_DIR"
