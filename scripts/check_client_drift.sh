#!/usr/bin/env bash
# Fail if the committed `soyuz-catalog-client/soyuz_catalog_client/`
# package drifts from a freshly regenerated copy.
#
# ADR-0007: used by the `client-drift` CI job **and** the pre-push
# pre-commit hook. The same rule that applies to `docs/reference/api.md`:
# drift is the enemy, surface it at commit time instead of letting a
# stale client ship.
set -euo pipefail

cd "$(dirname "$0")/.."

TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

bash scripts/regen_client.sh "$TMPDIR/soyuz_catalog_client" >/dev/null

DIFF_FLAGS=(-r -q --exclude=__pycache__ --exclude=.ruff_cache)
if diff "${DIFF_FLAGS[@]}" \
    soyuz-catalog-client/soyuz_catalog_client \
    "$TMPDIR/soyuz_catalog_client" >/dev/null; then
    echo "client in sync with /openapi.json"
    exit 0
fi

echo "ERROR: soyuz-catalog-client is out of sync with /openapi.json" >&2
echo "" >&2
echo "Run \`bash scripts/regen_client.sh\` and commit the result." >&2
echo "" >&2
echo "--- committed (left) vs. regenerated (right) ---" >&2
diff -r -u --exclude=__pycache__ --exclude=.ruff_cache \
    soyuz-catalog-client/soyuz_catalog_client \
    "$TMPDIR/soyuz_catalog_client" >&2 || true
exit 1
