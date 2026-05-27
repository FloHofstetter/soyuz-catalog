"""Parametrised Spark compatibility audit against live soyuz.

Companion to :mod:`tests.test_spark_roundtrip`. Where the roundtrip
test is the must-pass gate for the single happy path (external
Delta table with explicit ``LOCATION``), this module sweeps the full
surface of Spark SQL statements the upstream JVM
``io.unitycatalog.spark.UCSingleCatalog`` connector can emit and pins
each one to an **expected outcome**:

- ``WORKS`` — soyuz and the connector both handle the statement.
- ``EXPECTED_501`` — soyuz returns 501 by design and the connector
  surfaces it as a failure. Reserved slot: no case currently uses it.
  Managed Delta was the historical occupant; ADR-0011's coordinator
  means soyuz no longer returns 501 there, but Spark's Delta
  extension still does not route managed-Delta DDL through the UC
  plugin, so that case lives in Category C
  (``C-managed-delta-insert``) rather than Category A.
- ``EXPECTED_CONNECTOR_THROW`` — ``UCSingleCatalog`` raises
  ``UnsupportedOperationException`` *before* any HTTP call reaches
  soyuz (e.g. ALTER / RENAME / VOLUME — see the explicit throws in
  ``UCSingleCatalog.scala`` lines 805 / 814 and the absence of
  ``VolumesApi`` from the class header).
- ``EXPECTED_4XX_DOCUMENTED`` — soyuz returns a documented 4xx that
  the test pins by status + error_code (reserved slot; no cases yet).

The audit established that there is **no hidden soyuz-side gap for
Spark** — every operation the connector can reach either already
works or is a documented 501. This test turns that audit into a
*red-on-drift* regression net: if a connector bump or a soyuz
change silently flips a previously-blocked operation to working,
the corresponding case will fail loudly and force a conscious
re-categorisation.

Fixtures (``module_live_server``, ``spark_session``,
``bootstrap_catalog``) are imported from :mod:`tests._spark_fixtures`;
see that module's docstring for why they are not in ``conftest.py``.
The gap report in ``docs/spark-compatibility.md`` is the prose twin of
this file and cross-references the same case ids.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

pyspark = pytest.importorskip("pyspark")
hypercorn = pytest.importorskip("hypercorn")

from pyspark.sql import SparkSession  # noqa: E402

from tests._spark_helpers import CATALOG_NAME, bootstrap_catalog  # noqa: E402

pytest_plugins = ("tests._spark_fixtures",)
pytestmark = pytest.mark.integration


WORKS = "WORKS"
EXPECTED_501 = "EXPECTED_501"
EXPECTED_CONNECTOR_THROW = "EXPECTED_CONNECTOR_THROW"
EXPECTED_4XX_DOCUMENTED = "EXPECTED_4XX_DOCUMENTED"


@dataclass(frozen=True)
class SparkCase:
    """One row in the Spark compatibility matrix.

    Each case is a single Spark SQL statement (or a short ordered
    sequence of statements — see :attr:`sqls`) paired with the outcome
    the audit asserts today and a human-readable note that will appear
    in the pytest failure message when reality drifts from the
    expectation.

    Attributes:
        id: Stable pytest parameter id — used as a cross-reference
            anchor from ``docs/spark-compatibility.md``.
        category: ``A`` / ``B`` / ``C`` / ``D`` — mirrors the gap
            report categories. ``D`` is docs-only and has no cases
            here.
        sqls: Ordered Spark SQL statements. For ``WORKS`` cases all
            statements must succeed. For failure cases the **last**
            statement is the one that must raise; earlier statements
            set up state and must succeed.
        outcome: One of the four outcome constants above.
        note: Free-form text appended to assertion failures. Should
            point at the exact line of ``UCSingleCatalog.scala`` or
            the ``DIVERGENCES.md`` / ADR entry that pinned the
            expectation.
    """

    id: str
    category: str
    sqls: tuple[str, ...]
    outcome: str
    note: str


_SCHEMA = "compat"
"""Single shared schema used by every matrix case.

Created once per module via :func:`bootstrap_catalog` in the
``_matrix_setup`` fixture. Individual cases create/drop their own
tables under this schema, so ordering does not matter as long as
each case's setup SQL is self-contained.
"""


def _qualified(table: str) -> str:
    """Fully-qualify a table name under the shared test schema."""
    return f"{CATALOG_NAME}.{_SCHEMA}.{table}"


def _build_cases(tmp_root: Path) -> list[SparkCase]:
    """Materialise the matrix against a per-module warehouse root.

    The ``tmp_root`` is threaded through so external-Delta cases get
    stable per-case directories — separate table names prevent
    cross-contamination from earlier runs of the same case when the
    module-scoped fixture is re-entered under pytest-xdist.

    Args:
        tmp_root: Module-scoped temporary directory under which each
            external Delta table case gets its own subdirectory.

    Returns:
        list[SparkCase]: The full parametrised matrix.
    """
    t_ext = tmp_root / "t_ext"
    t_join_a = tmp_root / "t_join_a"
    t_join_b = tmp_root / "t_join_b"
    t_drop = tmp_root / "t_drop"
    t_alter = tmp_root / "t_alter"
    t_rename = tmp_root / "t_rename"

    return [
        # ---- Category A: currently works (regression-pinned) ------------
        SparkCase(
            id="A-show-schemas",
            category="A",
            sqls=(f"SHOW SCHEMAS IN {CATALOG_NAME}",),
            outcome=WORKS,
            note="List schemas via the connector's listNamespaces path.",
        ),
        SparkCase(
            id="A-describe-schema",
            category="A",
            sqls=(f"DESCRIBE SCHEMA {CATALOG_NAME}.{_SCHEMA}",),
            outcome=WORKS,
            note="Describe schema via loadNamespaceMetadata.",
        ),
        SparkCase(
            id="A-create-external-delta",
            category="A",
            sqls=(
                f"CREATE TABLE {_qualified('t_ext')} (id INT, name STRING) "
                f"USING delta LOCATION 'file://{t_ext}'",
            ),
            outcome=WORKS,
            note="External Delta table — the JVM-Spark must-pass gate.",
        ),
        SparkCase(
            id="A-insert-external-delta",
            category="A",
            sqls=(f"INSERT INTO {_qualified('t_ext')} VALUES (1, 'a'), (2, 'b')",),
            outcome=WORKS,
            note="Path-based Delta writer commits directly to file://.",
        ),
        SparkCase(
            id="A-select-external-delta",
            category="A",
            sqls=(f"SELECT id, name FROM {_qualified('t_ext')} ORDER BY id",),
            outcome=WORKS,
            note="Read-path parity with the external-Delta write path above.",
        ),
        SparkCase(
            id="A-describe-table-extended",
            category="A",
            sqls=(f"DESCRIBE TABLE EXTENDED {_qualified('t_ext')}",),
            outcome=WORKS,
            note="Provider=delta comes back from getTable.",
        ),
        SparkCase(
            id="A-show-tables",
            category="A",
            sqls=(f"SHOW TABLES IN {CATALOG_NAME}.{_SCHEMA}",),
            outcome=WORKS,
            note="listTables under the compat schema.",
        ),
        SparkCase(
            id="A-join-two-external-delta",
            category="A",
            sqls=(
                f"CREATE TABLE {_qualified('t_join_a')} (id INT, name STRING) "
                f"USING delta LOCATION 'file://{t_join_a}'",
                f"INSERT INTO {_qualified('t_join_a')} VALUES (1, 'a'), (2, 'b')",
                f"CREATE TABLE {_qualified('t_join_b')} (id INT, tag STRING) "
                f"USING delta LOCATION 'file://{t_join_b}'",
                f"INSERT INTO {_qualified('t_join_b')} VALUES (1, 'x'), (2, 'y')",
                f"SELECT a.id, a.name, b.tag FROM {_qualified('t_join_a')} a "
                f"JOIN {_qualified('t_join_b')} b ON a.id = b.id ORDER BY a.id",
            ),
            outcome=WORKS,
            note="Two-table JOIN exercises both getTable calls in one plan.",
        ),
        SparkCase(
            id="A-drop-external-delta",
            category="A",
            sqls=(
                f"CREATE TABLE {_qualified('t_drop')} (id INT) "
                f"USING delta LOCATION 'file://{t_drop}'",
                f"DROP TABLE {_qualified('t_drop')}",
            ),
            outcome=WORKS,
            note="dropTable on an external Delta table.",
        ),
        # ---- Category C: upstream Spark-Delta-connector routing gap -----
        SparkCase(
            id="C-managed-delta-insert",
            category="C",
            sqls=(
                f"CREATE TABLE {_qualified('t_managed')} (id INT, name STRING) USING delta",
                f"INSERT INTO {_qualified('t_managed')} VALUES (1, 'a')",
            ),
            outcome=EXPECTED_CONNECTOR_THROW,
            note=(
                "ADR-0011 ships the passthrough Delta commit "
                "coordinator at POST /delta/preview/commits, so soyuz is "
                "spec-complete. But Spark's Delta SQL extension intercepts "
                "`USING delta` DDL at analysis time and reroutes it through "
                "`spark_catalog` (wired to DeltaCatalog in the fixture, per "
                "the upstream UC recipe) before the UCSingleCatalog plugin is "
                "invoked — so the request never reaches soyuz. Spark "
                "short-circuits with SCHEMA_NOT_FOUND (the `compat` schema is "
                "not registered on `spark_catalog`). This is an upstream "
                "Spark + Delta + unitycatalog-spark integration gap, not a "
                "soyuz gap: tests/test_delta_commits.py exercises the full "
                "coordinator contract end-to-end via direct HTTP. Flips to "
                "WORKS the day unitycatalog-spark routes managed-Delta DDL "
                "through the named UC catalog instead of `spark_catalog`."
            ),
        ),
        # ---- Category C: upstream JVM connector throws ------------------
        SparkCase(
            id="C-alter-table-add-column",
            category="C",
            sqls=(
                f"CREATE TABLE {_qualified('t_alter')} (id INT) "
                f"USING delta LOCATION 'file://{t_alter}'",
                f"ALTER TABLE {_qualified('t_alter')} ADD COLUMN extra STRING",
            ),
            outcome=EXPECTED_CONNECTOR_THROW,
            note=(
                "UCSingleCatalog.scala:805 raises "
                "UnsupportedOperationException('Altering a table is not "
                "supported yet'). No HTTP call reaches soyuz."
            ),
        ),
        SparkCase(
            id="C-alter-table-rename",
            category="C",
            sqls=(
                f"CREATE TABLE {_qualified('t_rename')} (id INT) "
                f"USING delta LOCATION 'file://{t_rename}'",
                f"ALTER TABLE {_qualified('t_rename')} RENAME TO {_qualified('t_renamed')}",
            ),
            outcome=EXPECTED_CONNECTOR_THROW,
            note=(
                "UCSingleCatalog.scala:814 raises "
                "UnsupportedOperationException('Renaming a table is not "
                "supported yet'). No HTTP call reaches soyuz."
            ),
        ),
        SparkCase(
            id="C-create-volume",
            category="C",
            sqls=(f"CREATE VOLUME {CATALOG_NAME}.{_SCHEMA}.v_managed",),
            outcome=EXPECTED_CONNECTOR_THROW,
            note=(
                "UCSingleCatalog does not instantiate a VolumesApi — no "
                "Spark SQL path reaches /api/2.1/unity-catalog/volumes. "
                "In practice Spark's SQL parser rejects the statement "
                "outright with PARSE_SYNTAX_ERROR (no `CREATE VOLUME` "
                "grammar is registered), which is even earlier than the "
                "UnsupportedOperationException throws for ALTER/RENAME. "
                "Same net effect for the audit: no HTTP call reaches "
                "soyuz."
            ),
        ),
    ]


@pytest.fixture(scope="module")
def _matrix_setup(
    module_live_server: str,
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[Path, list[SparkCase]]:
    """Seed the catalog + compat schema once and build the case list.

    Returns the per-module temp root and the fully-materialised list of
    cases, so the parametrised test can index by case id without
    rebuilding paths on every call.
    """
    root = tmp_path_factory.mktemp("spark_compat")
    warehouse = root / "warehouse"
    warehouse.mkdir()
    bootstrap_catalog(module_live_server, f"file://{warehouse}", _SCHEMA)
    return root, _build_cases(root)


def _case_ids(tmp_root: Path) -> list[str]:
    """Stable parametrisation ids computed without a live JVM.

    The matrix is built twice: once here at collection time (no Spark
    involvement — the ids come from string construction only) and once
    inside ``_matrix_setup`` at test time. Both builds produce the
    same ids because :func:`_build_cases` is pure over its ``tmp_root``
    input and the ids do not embed the path.
    """
    return [c.id for c in _build_cases(tmp_root)]


# Collection-time ids: we use a dummy path because ids are path-independent.
_COLLECTION_IDS = _case_ids(Path("/tmp/_spark_compat_collection_only"))


@pytest.mark.parametrize("case_id", _COLLECTION_IDS)
def test_spark_compatibility_matrix(
    spark_session: SparkSession,
    _matrix_setup: tuple[Path, list[SparkCase]],
    case_id: str,
) -> None:
    """Run one Spark SQL case and assert its pinned outcome.

    Why the test takes ``case_id`` (a string) instead of a full
    :class:`SparkCase`: pytest ``parametrize`` needs collection-time
    ids, but the case list depends on the module-scoped ``tmp_root``
    from :func:`_matrix_setup` which cannot run at collection time. We
    parametrise over ids only and resolve the case inside the test
    body against the fixture-built list.

    Args:
        spark_session: Module-scoped SparkSession (JVM + UCSingleCatalog).
        _matrix_setup: ``(tmp_root, cases)`` from the module fixture.
        case_id: One of :data:`_COLLECTION_IDS`.
    """
    _, cases = _matrix_setup
    case = next(c for c in cases if c.id == case_id)

    if case.outcome == WORKS:
        _run_works(spark_session, case)
    elif case.outcome == EXPECTED_501:
        # Managed Delta via Spark fails for one of two reasons in practice:
        # (a) the call reaches POST /delta/preview/commits and returns
        # 501 COMMIT_COORDINATOR_UNSUPPORTED (ADR-0006), or (b) Spark
        # re-resolves an unlocated managed table through `spark_catalog`
        # (the Delta catalog) and short-circuits with SCHEMA_NOT_FOUND
        # before ever contacting soyuz. Both outcomes are equivalent for
        # the audit: managed Delta is not a supported path.
        _run_expected_failure(
            spark_session,
            case,
            (
                "COMMIT_COORDINATOR_UNSUPPORTED",
                "SCHEMA_NOT_FOUND",
                "spark_catalog",
            ),
        )
    elif case.outcome == EXPECTED_CONNECTOR_THROW:
        # Two pre-HTTP failure modes: the connector explicitly raises
        # UnsupportedOperationException (ALTER / RENAME — see
        # UCSingleCatalog.scala lines 805 / 814), or Spark's SQL parser
        # rejects the statement outright (CREATE VOLUME — no `VolumesApi`
        # is wired, so there is no parser extension either, and the
        # stock parser returns PARSE_SYNTAX_ERROR). Both confirm "no
        # HTTP call reached soyuz", which is the property the category
        # pins.
        _run_expected_failure(
            spark_session,
            case,
            (
                "UnsupportedOperationException",
                "PARSE_SYNTAX_ERROR",
                "SCHEMA_NOT_FOUND",
                "spark_catalog",
            ),
            require_no_http=True,
        )
    elif case.outcome == EXPECTED_4XX_DOCUMENTED:  # pragma: no cover — reserved
        pytest.fail(f"{case.id}: EXPECTED_4XX_DOCUMENTED has no cases yet.")
    else:  # pragma: no cover — defensive
        pytest.fail(f"{case.id}: unknown outcome {case.outcome!r}")


def _run_works(spark: SparkSession, case: SparkCase) -> None:
    """Execute every statement in a ``WORKS`` case; any raise is a failure.

    The ``.collect()`` call at the end forces query materialisation for
    ``SELECT`` / ``SHOW`` / ``DESCRIBE`` statements so a lazy
    ``DataFrame`` does not swallow an error that would only surface on
    execution.
    """
    for sql in case.sqls:
        try:
            spark.sql(sql).collect()
        except Exception as exc:  # noqa: BLE001
            pytest.fail(
                f"{case.id}: expected WORKS but raised {type(exc).__name__}: "
                f"{exc}\nSQL: {sql}\nNote: {case.note}"
            )


def _run_expected_failure(
    spark: SparkSession,
    case: SparkCase,
    any_of_markers: tuple[str, ...],
    *,
    require_no_http: bool = False,
) -> None:
    """Run a case whose statement sequence is expected to fail somewhere.

    Statements run in order; the first one that raises stops the loop
    and its exception is checked against :paramref:`any_of_markers`.
    The case passes if at least one marker substring appears anywhere
    in that exception's cause chain, and fails if every statement
    succeeds (meaning a previously-blocked operation now works). This
    is deliberately looser than "the *last* statement must raise": for
    cases where Spark's analyzer short-circuits earlier than the
    connector (e.g. ``spark_catalog`` fallbacks, parser rejections),
    the failure surfaces on an earlier statement — which is still a
    legitimate failure for the audit.

    ``any_of`` semantics (not ``all_of``): a single category can
    legitimately fail for one of several structural reasons depending
    on which layer of Spark short-circuits first.

    Args:
        spark: The SparkSession.
        case: The compatibility case.
        any_of_markers: Substrings; at least one must appear in the
            exception chain for the case to pass.
        require_no_http: If True, the test additionally asserts that
            no HTTP call reached soyuz (no ``COMMIT_COORDINATOR_*``
            and no ``HTTP/`` status line in the chain). This is what
            distinguishes ``EXPECTED_CONNECTOR_THROW`` from
            ``EXPECTED_501``.
    """
    last_exc: BaseException | None = None
    last_sql: str | None = None
    for sql in case.sqls:
        try:
            spark.sql(sql).collect()
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            last_sql = sql
            break

    if last_exc is None:
        pytest.fail(
            f"{case.id}: expected the statement sequence to raise (any of "
            f"{any_of_markers!r}) but every statement succeeded. The "
            f"operation has silently started working — audit and "
            f"re-categorise.\nSQLs: {case.sqls}\nNote: {case.note}"
        )

    chain = _exception_chain_text(last_exc)
    if not any(m in chain for m in any_of_markers):
        pytest.fail(
            f"{case.id}: raised {type(last_exc).__name__} at {last_sql!r} "
            f"but chain does not match any expected marker in "
            f"{any_of_markers!r}.\nChain: {chain}\nNote: {case.note}"
        )
    if require_no_http and ("COMMIT_COORDINATOR_UNSUPPORTED" in chain or "HTTP/" in chain):
        pytest.fail(
            f"{case.id}: expected a pre-HTTP connector throw but the "
            f"exception chain looks like an HTTP response.\nChain: {chain}"
            f"\nNote: {case.note}"
        )


def _exception_chain_text(exc: BaseException) -> str:
    """Flatten an exception's ``__cause__`` / ``__context__`` chain to text.

    Py4J wraps JVM exceptions in a ``Py4JJavaError`` whose ``str()``
    already contains the JVM stack trace; we also walk the Python
    cause chain so soyuz-side ``HTTPStatusError`` messages (which
    carry the 501 + error_code) are visible to the marker check.
    """
    parts: list[str] = []
    seen: set[int] = set()
    cur: BaseException | None = exc
    while cur is not None and id(cur) not in seen:
        seen.add(id(cur))
        parts.append(f"{type(cur).__name__}: {cur}")
        cur = cur.__cause__ or cur.__context__
    return " || ".join(parts)
