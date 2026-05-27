#!/usr/bin/env python3
"""Pre-commit hook: warn on single-line docstrings for non-trivial defs.

Walks every public function, method, and class in the file paths passed on
the command line and prints a warning when the docstring is a single line.
Trivially-named helpers (private leading-underscore names, dunder methods,
and a small allow-list) are exempt.

This is intentionally a **warning**, not an error — exit code is always 0.
Pre-commit shows the output, the developer reads it, and the build proceeds.
The goal is to nudge contributors toward semantically rich docstrings
(see CLAUDE.md) without blocking trivial helper functions.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ALLOWED_SHORT_NAMES = {
    "__init__",
    "__repr__",
    "__str__",
    "__hash__",
    "__eq__",
}


def is_public(name: str) -> bool:
    """Return True if a symbol name is part of the public surface.

    Args:
        name: The function, method, or class name.

    Returns:
        bool: True for names without a leading underscore.
    """
    return not name.startswith("_")


def is_single_line_docstring(node: ast.AST) -> bool:
    """Return True if ``node`` has a docstring that is exactly one line.

    A docstring is considered single-line if its trimmed body contains no
    newline. ``None`` (no docstring) returns False — that is a separate
    pydoclint concern.

    Args:
        node: An ``ast.FunctionDef``, ``ast.AsyncFunctionDef``, or
            ``ast.ClassDef`` node.

    Returns:
        bool: True if the docstring is a single line of prose.
    """
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return False
    doc = ast.get_docstring(node, clean=True)
    if doc is None:
        return False
    return "\n" not in doc.strip()


def warnings_for_file(path: Path) -> list[str]:
    """Collect docstring-depth warnings for a single file.

    Args:
        path: Path to a Python source file.

    Returns:
        list[str]: One human-readable warning per offending def.
    """
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return []

    warnings: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        name = node.name
        if not is_public(name) and name not in ALLOWED_SHORT_NAMES:
            continue
        if not is_single_line_docstring(node):
            continue
        kind = "class" if isinstance(node, ast.ClassDef) else "def"
        warnings.append(f"{path}:{node.lineno}: {kind} {name}: single-line docstring")
    return warnings


def main(argv: list[str]) -> int:
    """Run the check on every file in ``argv``.

    Args:
        argv: List of file paths from pre-commit.

    Returns:
        int: Always 0 — this hook is informational only.
    """
    all_warnings: list[str] = []
    for raw in argv:
        path = Path(raw)
        if not path.suffix == ".py":
            continue
        all_warnings.extend(warnings_for_file(path))

    if all_warnings:
        sys.stderr.write(
            "⚠️  docstring-depth: the following public defs have single-line "
            "docstrings.\n   See CLAUDE.md for the project docstring style. "
            "This is a warning, not an error.\n",
        )
        for w in all_warnings:
            sys.stderr.write(f"   {w}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
