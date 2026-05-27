"""Detect drift between upstream Unity Catalog ``all.yaml`` and a committed baseline.

This is the recurring half of the spec-conformance check: the regression
suite already covers "soyuz ⊆ spec"; this script covers the opposite
direction. A weekly GitHub Actions workflow (see
``.github/workflows/spec-drift.yml``) fetches upstream ``all.yaml``, invokes
this script, and opens a GitHub issue whenever upstream has grown new paths,
methods, or schemas since the baseline snapshot was last refreshed.

Snapshot-based, not live-subset: the interesting signal here is *upstream
additions*, and schemas have no natural implemented/deferred mapping
against soyuz routes — so a committed baseline is the only comparison that
works for them too. The review loop is:

1. Script flags drift, opens an issue with the delta.
2. A maintainer reviews the delta (adds routes to soyuz, records the
   divergence, or both) and regenerates the baseline with
   ``--write-baseline``.
3. Committing the new baseline closes out the drift.

The script is deliberately offline: the workflow handles the ``curl`` fetch
so the script stays trivially unit-testable.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from soyuz_catalog._openapi_utils import HTTP_METHODS, normalise_path

REPO_ROOT = Path(__file__).resolve().parent.parent
BASELINE_PATH = REPO_ROOT / "tests" / "data" / "uc_spec_baseline.json"
UPSTREAM_URL = "https://raw.githubusercontent.com/unitycatalog/unitycatalog/main/api/all.yaml"


def extract_snapshot(spec: dict[str, Any]) -> dict[str, Any]:
    """Reduce an OpenAPI document to the surface we track for drift.

    The snapshot intentionally discards everything except the path/method
    tuples and the schema names, because richer fields (descriptions,
    examples, field types) change often enough that diffing them would
    bury the "did a new endpoint appear" signal we actually care about.
    Path parameters are normalised via :func:`normalise_path` so upstream
    renaming ``{name}`` to ``{catalog_name}`` does not register as drift.

    Args:
        spec: Parsed OpenAPI document.

    Returns:
        dict: ``{"paths": sorted list of [path, method] pairs,
        "schemas": sorted list of schema names}``. Lists (not sets) so the
        snapshot round-trips cleanly through JSON.
    """
    paths: set[tuple[str, str]] = set()
    for path, methods in (spec.get("paths") or {}).items():
        if not isinstance(methods, dict):
            continue
        for method in methods:
            if method in HTTP_METHODS:
                paths.add((normalise_path(path), method))
    schemas = sorted((spec.get("components") or {}).get("schemas", {}).keys())
    return {
        "paths": sorted([list(pm) for pm in paths]),
        "schemas": schemas,
    }


def diff_snapshots(baseline: dict[str, Any], current: dict[str, Any]) -> dict[str, list[Any]]:
    """Compute added/removed paths and schemas between two snapshots.

    "Added" means present in ``current`` but not ``baseline``; "removed" is
    the reverse. Both directions are reported because an upstream removal
    is equally interesting — it usually means an endpoint was renamed or
    the spec was cleaned up, and soyuz should follow.

    Args:
        baseline: Previously committed snapshot (the "known good" state).
        current: Snapshot computed from freshly fetched upstream spec.

    Returns:
        dict: Four sorted lists under ``added_paths``, ``removed_paths``,
        ``added_schemas``, ``removed_schemas``.
    """
    base_paths = {tuple(pm) for pm in baseline.get("paths", [])}
    curr_paths = {tuple(pm) for pm in current.get("paths", [])}
    base_schemas = set(baseline.get("schemas", []))
    curr_schemas = set(current.get("schemas", []))
    return {
        "added_paths": sorted([list(pm) for pm in curr_paths - base_paths]),
        "removed_paths": sorted([list(pm) for pm in base_paths - curr_paths]),
        "added_schemas": sorted(curr_schemas - base_schemas),
        "removed_schemas": sorted(base_schemas - curr_schemas),
    }


def render_report(diff: dict[str, list[Any]], *, source: str, captured_at: str) -> str:
    """Render a drift diff as a GitHub-issue-ready markdown body.

    The format is tuned for the workflow's ``gh issue create --body-file``
    step: a single H2 header, four H3 sub-sections (each omitted when
    empty), and bullet lists of the changed items. Keeping the shape
    stable lets the workflow deduplicate issues by title+label without
    parsing the body.

    Args:
        diff: Output of :func:`diff_snapshots`.
        source: URL the upstream spec was fetched from.
        captured_at: ISO date string of when the baseline was captured.

    Returns:
        str: Markdown body, newline-terminated.
    """
    lines = [
        "## Upstream spec drift detected",
        "",
        f"Source: {source}",
        f"Baseline captured: {captured_at}",
        "",
    ]
    sections = [
        ("New paths", diff["added_paths"], lambda pm: f"`{pm[1].upper()} {pm[0]}`"),
        (
            "Removed paths",
            diff["removed_paths"],
            lambda pm: f"`{pm[1].upper()} {pm[0]}`",
        ),
        ("New schemas", diff["added_schemas"], lambda s: f"`{s}`"),
        ("Removed schemas", diff["removed_schemas"], lambda s: f"`{s}`"),
    ]
    for title, items, fmt in sections:
        if not items:
            continue
        lines.append(f"### {title}")
        lines.extend(f"- {fmt(item)}" for item in items)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def has_drift(diff: dict[str, list[Any]]) -> bool:
    """Return ``True`` if any of the four diff buckets is non-empty."""
    return any(diff.values())


def load_yaml(path: Path) -> dict[str, Any]:
    """Parse a YAML file into a dict, raising on non-mapping top level.

    Args:
        path: Filesystem path to a YAML document.

    Returns:
        dict: Parsed document.

    Raises:
        ValueError: If the document does not parse to a mapping.
    """
    data = yaml.safe_load(path.read_text())
    if not isinstance(data, dict):
        raise ValueError(f"spec at {path} did not parse to a mapping")
    return data


def main(argv: list[str] | None = None) -> int:
    """Command-line entry point for spec-drift detection.

    Exit codes: ``0`` = no drift, ``1`` = drift detected, ``2`` = unable to
    read or parse the upstream spec. The workflow branches on the exit code
    to decide whether to open a GitHub issue.

    Args:
        argv: Optional argument vector (defaults to ``sys.argv[1:]`` via
            argparse). Present so unit tests can invoke ``main`` directly.

    Returns:
        int: Process exit code.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--spec",
        type=Path,
        required=True,
        help="Path to the fetched upstream all.yaml",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=BASELINE_PATH,
        help="Path to the committed baseline snapshot",
    )
    parser.add_argument(
        "--source",
        default=UPSTREAM_URL,
        help="URL recorded in the baseline as the source of truth",
    )
    parser.add_argument(
        "--write-baseline",
        action="store_true",
        help="Regenerate the baseline in place from the current upstream spec",
    )
    args = parser.parse_args(argv)

    try:
        spec = load_yaml(args.spec)
    except (OSError, yaml.YAMLError, ValueError) as exc:
        print(f"error: failed to load spec at {args.spec}: {exc}", file=sys.stderr)
        return 2

    current = extract_snapshot(spec)

    if args.write_baseline:
        payload = {
            "source": args.source,
            "captured_at": date.today().isoformat(),
            **current,
        }
        args.baseline.parent.mkdir(parents=True, exist_ok=True)
        args.baseline.write_text(json.dumps(payload, indent=2) + "\n")
        print(f"wrote baseline to {args.baseline}", file=sys.stderr)
        return 0

    if not args.baseline.exists():
        print(
            f"error: baseline {args.baseline} missing — bootstrap with --write-baseline",
            file=sys.stderr,
        )
        return 2

    baseline = json.loads(args.baseline.read_text())
    diff = diff_snapshots(baseline, current)
    if not has_drift(diff):
        return 0

    report = render_report(
        diff,
        source=baseline.get("source", args.source),
        captured_at=baseline.get("captured_at", "unknown"),
    )
    sys.stdout.write(report)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
