#!/usr/bin/env bash
# Record the heroic README demo: boot soyuz, create a catalog, list catalogs.
#
# Output goes to docs/assets/demo.svg via the asciinema -> svg-term-cli
# pipeline. Re-run after changing the wire protocol or the demo script.
#
# Requirements (one-time install):
#   uv tool install asciinema
#   npm install -g svg-term-cli   (or: --prefix ~/.npm-global)
#
# Re-record: bash scripts/record_demo.sh
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
cast="/tmp/soyuz-demo.cast"
svg="$repo_root/docs/assets/demo.svg"
demo_inner="$(mktemp --tmpdir soyuz-demo-inner.XXXXXX.sh)"

cat > "$demo_inner" <<'INNER'
#!/usr/bin/env bash
# Inner demo recorded by asciinema. Runs inside a 100x22 PTY.
set -e

# Clean state: temp SQLite the server boots against.
db=/tmp/soyuz-demo-recording.db
rm -f "$db"
export SOYUZ_DATABASE_URL="sqlite:///$db"

prompt() { printf '\033[1;32m$\033[0m \033[1m%s\033[0m\n' "$*"; sleep 0.4; }

# Project a subset of catalog fields for a focused JSON view.
project() {
  python3 -c 'import sys, json; d=json.load(sys.stdin); k=["name","comment","type","created_at","id"]; print(json.dumps({x:d.get(x) for x in k}, indent=2))'
}

prompt 'uv run uvicorn soyuz_catalog.api.main:app --port 18000 &'
uv run --quiet uvicorn soyuz_catalog.api.main:app \
       --host 127.0.0.1 --port 18000 --log-level warning >/tmp/soyuz.log 2>&1 &
server_pid=$!

for _ in $(seq 1 80); do
  if curl -sf http://127.0.0.1:18000/healthz >/dev/null 2>&1; then break; fi
  sleep 0.1
done
printf '\033[2mINFO  soyuz-catalog ready  (sqlite, alembic head)\033[0m\n'
sleep 1.2

prompt "curl -sX POST .../catalogs -d '{\"name\":\"sales\"}' | jq"
curl -sX POST http://127.0.0.1:18000/api/2.1/unity-catalog/catalogs \
  -H 'Content-Type: application/json' \
  -d '{"name":"sales","comment":"Q3 revenue"}' \
  | project
sleep 1.4

prompt 'curl -s .../catalogs/sales | jq'
curl -s http://127.0.0.1:18000/api/2.1/unity-catalog/catalogs/sales \
  | project
sleep 2.0

kill "$server_pid" 2>/dev/null || true
wait 2>/dev/null || true
INNER
chmod +x "$demo_inner"

cd "$repo_root"
rm -f "$cast"

# Record (non-interactive). Idle limit 1.4s keeps long pauses readable but
# prevents the boot wait from becoming dead air. --overwrite is unsupported
# in asciinema 2, so remove the cast first.
asciinema rec --quiet --cols 100 --rows 22 --idle-time-limit 1.4 \
  --command "bash $demo_inner" "$cast"

# Build the SVG. --window adds the title-bar chrome; --no-cursor cuts noise.
~/.npm-global/node_modules/.bin/svg-term \
  --in "$cast" \
  --out "$svg" \
  --window \
  --no-cursor \
  --width 100 \
  --height 22

rm -f "$demo_inner"

printf '\nSVG written: %s (%s)\n' "$svg" "$(du -h "$svg" | cut -f1)"
