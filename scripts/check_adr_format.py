#!/usr/bin/env python3
"""Pre-commit hook: validate the structural format of ADR files.

Receives ADR file paths as arguments (passed in by pre-commit's `files:`
filter). Each file must:

1. Be named ``NNNN-kebab-case-title.md`` (4-digit zero-padded number).
2. Start with an H1 heading of the form ``# ADR-NNNN: <title>``.
3. Contain the required sections ``Status``, ``Context``, ``Decision``,
   ``Consequences``.

Files named ``README.md`` or ``0000-template.md`` are skipped.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REQUIRED_SECTIONS = ("Context", "Decision", "Consequences")
FILENAME_RE = re.compile(r"^(\d{4})-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
HEADING_RE = re.compile(r"^# ADR-(\d{4}): .+$", re.MULTILINE)


def check(path: Path) -> list[str]:
    """Validate a single ADR file.

    Args:
        path: Path to the ADR file.

    Returns:
        list[str]: Human-readable error messages. Empty list means the file
            is well-formed.
    """
    errors: list[str] = []
    name = path.name
    if name in {"README.md", "0000-template.md"}:
        return errors

    fn_match = FILENAME_RE.match(name)
    if not fn_match:
        errors.append(
            f"{path}: filename must match NNNN-kebab-case-title.md",
        )
        return errors

    text = path.read_text(encoding="utf-8")

    h1_match = HEADING_RE.search(text)
    if not h1_match:
        errors.append(f"{path}: missing '# ADR-NNNN: <title>' H1 heading")
    elif h1_match.group(1) != fn_match.group(1):
        errors.append(
            f"{path}: heading number {h1_match.group(1)} does not match "
            f"filename number {fn_match.group(1)}",
        )

    if "**Status:**" not in text:
        errors.append(f"{path}: missing '**Status:**' line")

    for section in REQUIRED_SECTIONS:
        if f"## {section}" not in text:
            errors.append(f"{path}: missing required section '## {section}'")

    return errors


def main(argv: list[str]) -> int:
    """Run the check on every path in ``argv``.

    Args:
        argv: List of ADR file paths (typically from pre-commit).

    Returns:
        int: Process exit code (0 = pass, 1 = fail).
    """
    all_errors: list[str] = []
    for raw in argv:
        all_errors.extend(check(Path(raw)))
    for err in all_errors:
        sys.stderr.write(f"❌ {err}\n")
    return 1 if all_errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
