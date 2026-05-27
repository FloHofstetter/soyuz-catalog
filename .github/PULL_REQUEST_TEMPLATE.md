## Summary

<!-- Briefly describe what this PR does and why. -->

## Test plan

<!-- How did you test this? What edge cases did you consider? -->

- [ ] Unit tests pass (`uv run pytest -m 'not integration'`)
- [ ] Linting passes (`uv run ruff check . && uv run ruff format --check .`)
- [ ] Type check passes (`uv run pyright`)

## Spec conformance

<!-- soyuz-catalog implements the Unity Catalog REST API spec verbatim. -->

- [ ] This PR does **not** touch any spec-defined endpoint *(skip the rest of this section)*
- [ ] Spec-conformance test against `unitycatalog/api/all.yaml` still passes
- [ ] If the change diverges from UC OSS Java behaviour, the divergence is documented in `DIVERGENCES.md` and tracks *toward* the spec, not away from it
- [ ] Drift gate against the generated client (`soyuz-catalog-client/`) still passes — regenerate with `scripts/regen_client.sh` if the OpenAPI schema changed

## Database migrations

<!-- Alembic migrations require a downgrade path and CI verification. -->

- [ ] This PR does **not** include a database migration *(skip the rest of this section)*
- [ ] `alembic check` passes
- [ ] `downgrade()` is implemented, or a `NotImplementedError` is raised with a comment explaining why

## Client regeneration

- [ ] This PR does **not** change the public REST surface *(skip the rest of this section)*
- [ ] `bash scripts/regen_client.sh` was run; resulting diff in `soyuz-catalog-client/` is committed
- [ ] Any downstream consumer was test-bumped against the new client (or a follow-up issue is filed)
