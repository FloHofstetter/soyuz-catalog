#!/usr/bin/env python3
"""Pre-commit hook: enforce CHANGELOG.md updates for source changes.

Fails if any file under ``soyuz_catalog/`` is staged but ``CHANGELOG.md`` is
not also staged with a non-empty ``[Unreleased]`` section. Bypass for trivial
changes is via ``git commit --no-verify``.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

CHANGELOG = Path("CHANGELOG.md")
SOURCE_PREFIX = "soyuz_catalog/"


def staged_files() -> list[str]:
    """Return the list of files staged for the current commit.

    Returns:
        list[str]: Repo-relative paths of staged files.
    """
    out = subprocess.check_output(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        text=True,
    )
    return [line.strip() for line in out.splitlines() if line.strip()]


def unreleased_has_entries() -> bool:
    """Return True if CHANGELOG.md has a non-empty ``[Unreleased]`` section.

    Returns:
        bool: True when the section exists and contains at least one bullet
            point or sub-heading before the next top-level release header.
    """
    if not CHANGELOG.exists():
        return False
    text = CHANGELOG.read_text(encoding="utf-8")
    marker = "## [Unreleased]"
    if marker not in text:
        return False
    after = text.split(marker, 1)[1]
    next_release = after.find("\n## [")
    section = after if next_release == -1 else after[:next_release]
    for line in section.splitlines():
        stripped = line.strip()
        if stripped.startswith(("- ", "* ", "### ")):
            return True
    return False


def main() -> int:
    """Run the check.

    Returns:
        int: Process exit code (0 = pass, 1 = fail).
    """
    files = staged_files()
    source_changed = any(f.startswith(SOURCE_PREFIX) for f in files)
    if not source_changed:
        return 0

    changelog_staged = "CHANGELOG.md" in files
    if not changelog_staged:
        sys.stderr.write(
            "❌ Source files under soyuz_catalog/ were modified but CHANGELOG.md "
            "is not staged.\n   Add an entry under '## [Unreleased]' or commit "
            "with --no-verify if the change is truly user-invisible.\n",
        )
        return 1

    if not unreleased_has_entries():
        sys.stderr.write(
            "❌ CHANGELOG.md is staged but '## [Unreleased]' has no entries.\n"
            "   Add at least one bullet point under it.\n",
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
