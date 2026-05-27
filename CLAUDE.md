# Claude instructions for soyuz-catalog

This file is read automatically by Claude Code at the start of every session
in this repository. It captures conventions that are not enforceable by
linters but matter for the long-term readability of the codebase.

## Project context

soyuz-catalog is a Python reimplementation of the Unity Catalog REST API.
The OpenAPI spec at `~/git/unitycatalog/api/all.yaml` is the **source of
truth**. UC OSS Java is a *behaviour reference*, not an authority — see
[ADR-0002](docs/adr/0002-spec-is-the-contract.md). When you encounter a
divergence, document it in `DIVERGENCES.md` *and* add a regression test.

When in doubt about stack/conventions, read
[ADR-0001](docs/adr/0001-stack-and-conventions.md) before inventing a new
pattern.

## Docstring style

Every public module, class, and function in `soyuz_catalog/` gets a
docstring. The shape is non-negotiable:

```python
def update_catalog(session: Session, name: str, payload: UpdateCatalog) -> Catalog:
    """Apply a PATCH to a catalog.

    Replace-style semantics: any field present in the request body is written
    to the row, including ``properties={}`` which clears all properties (the
    UC OSS Java implementation treats this as a no-op — see DIVERGENCES.md).
    Fields absent from the body are left untouched.

    Args:
        session: Active SQLAlchemy session.
        name: Current catalog name (path parameter).
        payload: Validated update request.

    Returns:
        Catalog: The updated catalog row.

    Raises:
        NotFoundError: If no catalog with the given name exists.
    """
```

Three rules:

1. **Summary line + blank line + body.** A single-line docstring is only
   acceptable for trivially-named helpers where the name carries the full
   meaning (e.g. `_now_ms`). Anything that touches a domain concept gets a
   body that explains the **why**, the **invariant**, the **edge case**, or
   the **non-obvious decision** — not a re-statement of the function name.
2. **Body explains, signature describes.** Do not waste the body re-typing
   the parameter list as English ("This function takes a session and a
   name..."). The signature already says that. Use the body for the things
   the signature *cannot* say: which exception path is the spec-conformant
   one, why a field is read with `model_fields_set` instead of `is None`,
   which UC OSS bug a branch is the fix for, etc.
3. **Google style, enforced by pydoclint.** Args / Returns / Raises sections
   match the signature exactly. `pydoclint` and `ruff` will fail the build
   if they don't.

Bad (the kind of docstring this project does not want):

```python
def get_catalog(session: Session, name: str) -> Catalog:
    """Get a catalog by name."""
```

Good:

```python
def get_catalog(session: Session, name: str) -> Catalog:
    """Fetch a catalog by name.

    The lookup is by the user-facing ``name`` column rather than the opaque
    ``id``, because every UC REST endpoint addresses catalogs by name and we
    never want a database round-trip just to translate one to the other.

    Args:
        session: Active SQLAlchemy session.
        name: Catalog name.

    Returns:
        Catalog: The matching catalog row.

    Raises:
        NotFoundError: If no catalog with the given name exists.
    """
```

The pre-commit hook `docstring-depth` flags single-line docstrings on public
functions in `soyuz_catalog/` as a soft warning. It is not a hard failure
because helpers like `_now_ms` legitimately do not need a body — but if you
see the warning on a function that touches domain logic, add the body.

## Other house rules

- **Test every divergence.** A `DIVERGENCES.md` entry without a regression
  test in `tests/test_<resource>.py` is a bug, not a feature.
- **Update CHANGELOG.md** under `## [Unreleased]` for any change in
  `soyuz_catalog/`. The pre-commit hook will block the commit otherwise.
- **Keep the REST reference in sync.** Any new endpoint, request/response
  shape, status code, or UC OSS divergence must land in
  `docs/reference/api.md` in the **same** commit that touches
  `soyuz_catalog/api/routes/` or `soyuz_catalog/api/schemas.py`. Same rule
  for `docs/reference/python/services.md`: every new module under
  `soyuz_catalog/services/` gets a `::: <module>` block added to the
  service reference page. These files are curated (not auto-generated from
  the code), so they rot silently if a change forgets them. `models.md`
  and `schemas.md` use mkdocstrings module-level directives and do *not*
  need per-resource edits.
- **Sync SQLAlchemy.** Routes are `def`, not `async def`. Sessions come
  from `get_session_factory()` via the `get_db` dependency.
- **`extra="forbid"` on every request body.** Silently dropping unknown
  fields is the UC OSS Java bug we exist to fix; do not reintroduce it.
- **No `__init__` docstrings.** Document the class instead. (Enforced by
  `allow-init-docstring = false` in `pydoclint`.)
- **Conventional Commits.** Every commit message follows
  ``<type>(<scope>): <subject>`` with a lowercase Angular type
  (`feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`,
  `ci`, `chore`, `revert`). Scope is the resource or subsystem touched
  (`catalog`, `db`, `docs`, `pre-commit`, …). Enforced by
  `conventional-pre-commit` in the `commit-msg` stage. Examples:

  ```text
  feat(catalog): add PATCH endpoint with replace-style properties
  fix(db): rollback session before re-raising IntegrityError
  docs(adr): add ADR-0003 superseding 0001 on async migration
  ```
