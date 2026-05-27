<!-- markdownlint-disable MD030 -->
# Concepts

These pages explain *why* soyuz-catalog is shaped the way it is. The
top-of-page section is the linear reading path for someone new to the
project; the section below it is the per-topic deep-dive set, pulled
in by reference from walkthroughs and reference pages.

## Reading order

Read these in order for the mental model. About 30 minutes total.

<div class="grid cards" markdown>

-   :material-numeric-1-circle:{ .lg .middle } **[Origin and relationship to Unity Catalog](origin.md)**

    ---

    What soyuz is, what Unity Catalog is, and why a second
    implementation exists.

-   :material-numeric-2-circle:{ .lg .middle } **[Architecture](architecture.md)**

    ---

    Request lifecycle, layer boundaries, where to look in the source
    tree.

-   :material-numeric-3-circle:{ .lg .middle } **[Spec is the contract](spec-is-the-contract.md)**

    ---

    How the OpenAPI document is treated as authoritative, and what
    that means for divergences.

-   :material-numeric-4-circle:{ .lg .middle } **[Securables and naming](securables-and-naming.md)**

    ---

    The hierarchy, three- vs four-part names, opaque IDs, rename
    semantics.

-   :material-numeric-5-circle:{ .lg .middle } **[Permissions model](permissions-model.md)**

    ---

    Direct + inherited grants, why soyuz computes but does not
    enforce.

-   :material-numeric-6-circle:{ .lg .middle } **[Extensions over the spec](extensions-over-spec.md)**

    ---

    The index of over-the-spec features.

-   :material-numeric-7-circle:{ .lg .middle } **[Stack and interchangeability](stack.md)**

    ---

    Which libraries soyuz uses, why, and what could be swapped.

</div>

## Topic deep-dives

Pull these in when you touch the corresponding feature. They are not
required reading for the mental model but are the canonical home for
each topic the rest of the docs refer to.

<div class="grid cards" markdown>

-   :material-source-branch:{ .lg .middle } **[Lineage](lineage.md)**

    ---

    The OpenLineage ingestion + traversal model in depth.

-   :material-source-commit:{ .lg .middle } **[Delta commit handling](delta-commits.md)**

    ---

    The passthrough coordinator pattern.

-   :material-key-variant:{ .lg .middle } **[Credentials](credentials.md)**

    ---

    Storage Credentials vs Temporary Credentials, and the
    metadata-only stance.

-   :material-format-list-checks:{ .lg .middle } **[Table constraints](table-constraints.md)**

    ---

    `PRIMARY KEY` / `FOREIGN KEY` / `CHECK` / `NOT NULL` declarations,
    why declared-only and never enforced.

-   :material-clipboard-text-clock:{ .lg .middle } **[Audit log](audit-log.md)**

    ---

    What gets written on every mutation, the proxy-attached identity
    model, and where the trail stops being enough.

-   :material-file-multiple:{ .lg .middle } **[Volume files](volume-files.md)**

    ---

    The over-the-spec single-node file IO routes, and when to reach
    for a real object store instead.

-   :material-page-next:{ .lg .middle } **[Pagination](pagination.md)**

    ---

    The keyset cursor every list endpoint uses, why not offset, and
    the gotchas.

</div>

## Reference material

The concept pages link out to:

- **ADRs** for hard design decisions ([Decisions index](../adr/README.md)).
- **REST API reference** for wire-level details ([api.md](../reference/api.md)).
- **Spec coverage map** for the full implementation status
  ([spec-coverage.md](../reference/spec-coverage.md)).
- **Divergences** for documented behaviour differences from the Java
  reference ([divergences.md](../divergences.md)).
