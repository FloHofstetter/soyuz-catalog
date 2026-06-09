#!/usr/bin/env python
"""Run mutmut against soyuz-catalog with the trampoline KeyError patch applied.

mutmut 3.x rewrites every target function into a *trampoline* that reads
``os.environ['MUTANT_UNDER_TEST']`` with a hard index. Tests that swap
``os.environ`` wholesale (e.g. ``monkeypatch.setattr(os, "environ", {})``)
turn that index into a ``KeyError`` and abort the whole run. This wrapper
rewrites the trampoline template to read the variable defensively *before*
``mutmut.file_mutation`` imports it — that module binds ``trampoline_impl``
by value and parses it into a CST at import time, so the patch has to land
first. Every written mutant then carries the patched trampoline.

soyuz-catalog's current suite does not swap ``os.environ`` wholesale, so the
patch is defensive rather than load-bearing today; it is kept in place so
a future test that does swap the environment cannot silently break the
sweep.

All command-line arguments are forwarded verbatim to the mutmut CLI, so
this is a drop-in replacement for ``mutmut``::

    uv run --with mutmut==3.5.0 python scripts/mutation/run_mutmut.py run
    uv run --with mutmut==3.5.0 python scripts/mutation/run_mutmut.py results
    uv run --with mutmut==3.5.0 python scripts/mutation/run_mutmut.py run "<glob>"

On top of the trampoline patch, the wrapper injects a *contention-safe*
``--max-children`` default into ``run`` invocations. mutmut's default is
``os.cpu_count()``, which fully subscribes the box; under that load the
heavier service modules' covering tests (each spins up a FastAPI app + an
in-memory DB) overshoot mutmut's per-mutant CPU/wall limit
(``(estimated_test_time + 1) * 30`` CPU-seconds, ``* 15`` wall) and get
recorded as *timeouts*. mutmut buckets a timeout as "killed", so a spurious
timeout silently masks a genuine survivor — a real blind spot would never
surface. Capping workers at ``cpu_count // 2`` (verified: catalog_service's
203 mutants go 245-timeouts→0 between 12 and 6 workers on a 12-core box)
keeps each test run near its unloaded baseline. Pass ``--max-children``
explicitly to override; set ``MUTMUT_MAX_CHILDREN`` to change the default.

See ``scripts/mutation/README.md`` for the full workflow, including the
scoped re-verify loop and how to read per-module ``.meta`` exit codes.
"""

from __future__ import annotations

import os
import sys

_HARD_INDEX = "os.environ['MUTANT_UNDER_TEST']"
_SAFE_GET = "os.environ.get('MUTANT_UNDER_TEST', '')"


def _default_max_children() -> int:
    """Return the contention-safe worker count: ``cpu_count // 2`` (min 1).

    ``MUTMUT_MAX_CHILDREN`` overrides it wholesale. The halving leaves
    headroom for the main process, the OS, and the per-test fixture setup
    so wall time stays close to the unloaded baseline mutmut measured its
    timeout against — see the module docstring for why a fully-subscribed
    box turns real kills into masked survivors.

    Returns:
        int: Worker count to pass as ``--max-children``.
    """
    override = os.environ.get("MUTMUT_MAX_CHILDREN")
    if override:
        return max(1, int(override))
    return max(1, (os.cpu_count() or 2) // 2)


def _inject_max_children(argv: list[str]) -> list[str]:
    """Add a ``--max-children`` default to a ``run`` invocation if absent.

    Only ``run`` accepts the flag, so leave every other subcommand
    (``results``, ``show``, …) untouched. An explicit ``--max-children``
    the caller passed always wins.

    Args:
        argv: ``sys.argv[1:]`` — the arguments destined for the mutmut CLI.

    Returns:
        list[str]: ``argv`` with ``--max-children <n>`` appended when the
        subcommand is ``run`` and the caller did not already set it.
    """
    if not argv or argv[0] != "run" or "--max-children" in argv:
        return argv
    return [*argv, "--max-children", str(_default_max_children())]


def _patch_trampoline_template() -> None:
    """Rewrite the trampoline's env lookup to a defensive ``.get`` form.

    Must run before ``mutmut.file_mutation`` is imported: that module does
    ``from mutmut.trampoline_templates import trampoline_impl`` and builds
    its CST from the value at import time, so a later patch is ignored.

    Raises:
        SystemExit: if the upstream template no longer contains the hard
            index this patch targets — fail loudly so a mutmut upgrade
            can't silently reintroduce the ``KeyError``.
    """
    import mutmut.trampoline_templates as templates

    if _HARD_INDEX not in templates.trampoline_impl:
        raise SystemExit(
            "mutmut trampoline template changed shape: "
            f"{_HARD_INDEX!r} not found. Re-derive the patch in "
            "scripts/mutation/run_mutmut.py against the installed mutmut."
        )
    templates.trampoline_impl = templates.trampoline_impl.replace(_HARD_INDEX, _SAFE_GET)


def main() -> None:
    """Apply the trampoline patch, inject the worker cap, then hand to mutmut."""
    _patch_trampoline_template()

    sys.argv[1:] = _inject_max_children(sys.argv[1:])

    from mutmut.__main__ import cli

    cli()


if __name__ == "__main__":
    main()
