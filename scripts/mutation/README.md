# Mutation testing

Mutation testing measures whether the test suite actually *detects*
behavioural changes, not just whether it executes the code. mutmut
rewrites each target function into many small "mutants" (flip a `>` to
`>=`, drop a `+ 1`, swap a string) and runs the tests against each. A
mutant that the tests still pass on **survived** — a blind spot. One the
tests catch is **killed**.

This project mutates the business-logic seams that are unit-tested at the
function level:

- `soyuz_catalog/services/` — the CRUD + behaviour services (the bulk of
  the logic, exercised by `tests/test_<resource>.py`),
- `soyuz_catalog/storage/` — storage-URI parsing and volume-file path
  handling (`tests/test_storage_uri.py`, `tests/test_volume_files.py`),
- `soyuz_catalog/pagination.py` — opaque page-token encode/decode and
  bounds logic (`tests/test_pagination.py`).

The `api/` routes, `models.py` ORM declarations, `settings.py`, and `db.py`
are integration-shell code covered end-to-end through the FastAPI
`TestClient`, not at the seam mutmut probes, so they are left out of
`paths_to_mutate`.

## Why a wrapper (and not bare `mutmut`)

mutmut 3.x's generated trampoline reads `os.environ['MUTANT_UNDER_TEST']`
with a hard index. A test that swaps `os.environ` wholesale makes that
index raise `KeyError` and aborts the run.
[`run_mutmut.py`](run_mutmut.py) patches the trampoline template to read
the variable defensively **before** mutmut builds its mutant CST, then
forwards every argument to the real mutmut CLI. soyuz-catalog's suite does
not currently swap the environment that way, so the patch is defensive
today — but always go through the wrapper so the patch stays in place
and a future test cannot silently break the sweep.

The wrapper also injects a **contention-safe `--max-children` default**
(`cpu_count // 2`). mutmut otherwise forks `cpu_count` workers, fully
subscribing the box; under that load the heavier service modules' covering
tests — each spins up a FastAPI app + an in-memory DB — overshoot mutmut's
per-mutant CPU/wall limit and are recorded as **timeouts**. Because mutmut
buckets a timeout as "killed", a spurious timeout silently masks a real
survivor. Halving the worker count keeps each test near its unloaded
baseline (verified: `catalog_service`'s 203 mutants went 245-timeouts → 0
between 12 and 6 workers on a 12-core box). Override per-run with
`--max-children <n>`, or set `MUTMUT_MAX_CHILDREN` to change the default
(useful on a 2-vCPU CI runner, where even the default 2 workers contend —
cap it at 1, or use a larger runner).

There is no committed mutmut dependency on purpose — it is opt-in via
`uv run --with`. Pin the version so runs are reproducible:

```bash
MUTMUT="uv run --with mutmut==3.5.0 python scripts/mutation/run_mutmut.py"
```

## Full run

```bash
$MUTMUT run          # long; mutates services/ + storage/ + pagination.py
$MUTMUT results      # summary table; killed / survived / no-test / timeout
$MUTMUT show <id>    # the diff for one mutant
```

mutmut copies the repo to `mutants/`, runs the full unit suite **once** to
map each mutant to its covering tests (this stats pass dominates the
wall-clock floor — ~70 s for the default `-m "not integration and not
postgres"` suite), then forks workers. Mutants with no covering test exit
instantly (free); only covered ones cost time.

`mutants/` and `mutmut-stats.json` are git-ignored — they are the working
copy, never committed.

## Scoped re-verify loop

After adding tests for one module, re-check just that module without a
full run:

```bash
rm -f mutants/mutmut-stats.json                          # force fresh stats
$MUTMUT run "soyuz_catalog.services.catalog_service.*"   # stats (~70 s) + only this module's mutants
```

The glob matches mangled mutant names (`<module>.<func>__mutmut_<n>`).
The suite-wide stats pass is the floor; the module's own mutants run on
top.

## PR gate

[`scripts/check-mutation-budget.sh`](../check-mutation-budget.sh) is the
cheap per-PR predecessor of the nightly sweep: it mutates **only** the
`services/` + `storage/` + `pagination.py` modules a branch actually
changes vs `origin/main` (override with `MUTATION_BASE_REF`) and fails if
any introduces a surviving mutant not on the known-equivalent allowlist.
It is deliberately **not** wired into pre-commit — even a scoped run is
minutes, far too slow for a commit hook.

## Reading per-module results

Each mutated source file has a sidecar `mutants/<path>.py.meta` whose
`exit_code_by_key` maps every mutant to an exit code (values observed with
mutmut 3.5.0 here — a process killed by a signal is stored as `-signum`):

| exit code | meaning            |
|----------:|--------------------|
| 0         | **survived** (blind spot — add a test) |
| 1         | killed (a covering test failed) |
| 33        | no covering test (mutant was never exercised) |
| -24       | timeout — `RLIMIT_CPU` fired `SIGXCPU` (signal 24); see below |

### Timeouts are not automatically trustworthy kills

mutmut buckets a timeout as "killed", but a timeout only means *the tests
did not finish in time* — it does **not** prove the mutation was caught. A
mutant whose tests would have **passed** (i.e. a genuine survivor) but which
ran slow under load is recorded as a timeout and silently counted as killed,
masking the blind spot. Two causes:

- **contention** — too many workers oversubscribe the box and inflate the
  heavy service tests past the per-mutant limit. The wrapper's
  `--max-children` cap (see "Why a wrapper") is the first line of defence.
- **a genuinely non-terminating mutation** — e.g. flipping a loop bound into
  an infinite loop. *This* is a legitimate kill.

To tell them apart, re-run the timed-out modules at minimal parallelism,
where contention cannot be the cause:

```bash
$MUTMUT run "soyuz_catalog.services.lineage_service.*" --max-children 1
```

Anything that still times out at `--max-children 1` is a real
(non-terminating) kill; anything that flips to `survived` is a blind spot
the high-parallelism run hid. The first full sweep (4055 mutants) produced
60 such timeouts in the three heaviest modules (`lineage_service`,
`delta_rest_service`, `connection_service`); re-running them at
`--max-children 2` resolved **all 60 to killed, 0 survivors** — they were
pure contention artifacts. Do this re-verify before trusting a fresh
baseline, and before the PR gate's verdict if a changed heavy module times
out.

## Known-equivalent mutants

Some survivors are *equivalent* — the mutation cannot change observable
behaviour, so no test can kill them (`typing.cast` no-ops, cosmetic
error-string content, timing arithmetic). These are recorded in
[`equivalent.txt`](equivalent.txt) with a one-line reason each, so the PR
gate does not flag them.

## Setup gotchas (already handled in the harness)

- **`also_copy`**: only `services/`, `storage/`, and `pagination.py` are
  mutated, so the rest of `soyuz_catalog/` (imported by the mutated code —
  `api/`, `models.py`, `db.py`, the embedded `alembic/` tree) must be
  copied into `mutants/`. That is what `also_copy = soyuz_catalog/` in
  `setup.cfg` does.
- **Slow / external suites**: the `integration` and `postgres` markers are
  deselected by the default pytest addopts in `pyproject.toml`, which the
  copied config carries into the sweep — so the live-server, SDK, Spark,
  and Postgres tests never run per-mutant.
- **Module-global state leaks**: mutmut runs pytest many times in one
  process, so a test that mutates a module global without cleanup fails on
  the 2nd run. soyuz-catalog's autouse `_reset_state` fixture resets the
  DB + settings cache around every test, so the suite is isolation-clean;
  if you add global state, reset it the same way (never mask it).
