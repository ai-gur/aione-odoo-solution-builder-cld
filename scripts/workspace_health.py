#!/usr/bin/env python
"""Odoo workspace health check (Increment 0, story I0-08).

Verifies that the configured Odoo Foundation, core and Enterprise paths exist
and records the revision each one is actually at, comparing it against
`catalogue/pinned-sources.json`.

Strictly non-mutating. It never fetches, checks out, or writes to a workspace
repository. Reading a workspace must not change it, and a health check that
quietly runs `git fetch` would move the very thing it is reporting on.

A drifted revision is reported, not corrected: whether to move the baseline is
a catalogue release decision, and every technical claim already published is
true of the pinned revision rather than of whatever is checked out today.

    python scripts/run.py workspace-health
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PINNED = ROOT / "catalogue" / "pinned-sources.json"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OK = "ok"
MISSING = "missing"
DRIFTED = "drifted"
UNPINNED = "unpinned"


def git(path: pathlib.Path, *args: str) -> str | None:
    """Read-only git. Returns None when the directory is not a checkout."""
    result = subprocess.run(
        ["git", "-C", str(path), *args],
        capture_output=True, text=True, encoding="utf-8",
    )
    return result.stdout.strip() if result.returncode == 0 else None


def check(name: str, source: dict) -> dict:
    env_var = source["envPath"]
    configured = os.environ.get(env_var, "").strip()

    if not configured:
        return {
            "source": name, "status": MISSING, "envPath": env_var,
            "detail": f"{env_var} is not set. Copy .env.example to .env.local and fill it in.",
        }

    path = pathlib.Path(configured)
    if not path.is_dir():
        return {
            "source": name, "status": MISSING, "envPath": env_var, "path": str(path),
            "detail": f"{env_var} points at a directory that does not exist.",
        }

    actual = git(path, "rev-parse", "HEAD")
    if actual is None:
        return {
            "source": name, "status": UNPINNED, "envPath": env_var, "path": str(path),
            "detail": "Not a git checkout, so its revision cannot be recorded.",
        }

    branch = git(path, "rev-parse", "--abbrev-ref", "HEAD")
    dirty = bool(git(path, "status", "--porcelain"))
    expected = source.get("revision")

    entry = {
        "source": name,
        "envPath": env_var,
        "path": str(path),
        "revision": actual,
        "expected": expected,
        # A detached HEAD is the healthy state for a pinned vendor mirror: on a
        # branch, a pull silently changes what the product describes.
        "branch": branch,
        "detached": branch == "HEAD",
        "dirty": dirty,
    }

    if expected and actual != expected:
        entry["status"] = DRIFTED
        entry["detail"] = (
            f"Checked out {actual[:12]}, baseline pins {expected[:12]}. "
            "Moving the baseline is a catalogue release, not an edit."
        )
    else:
        entry["status"] = OK

    return entry


def main() -> int:
    if not PINNED.exists():
        print(f"missing {PINNED.relative_to(ROOT)}", file=sys.stderr)
        return 2

    document = json.loads(PINNED.read_text(encoding="utf-8"))
    results = [check(name, source) for name, source in document["sources"].items()]

    print(f"baseline {document['baselineKey']}\n")
    width = max(len(item["source"]) for item in results)
    for item in results:
        marker = {OK: "ok      ", MISSING: "MISSING ", DRIFTED: "DRIFTED ", UNPINNED: "UNPINNED"}[
            item["status"]
        ]
        print(f"  {marker} {item['source']:<{width}}  {item.get('revision', '-')[:12]}")
        if item["status"] != OK:
            print(f"           {item['detail']}")
        elif item.get("dirty"):
            print("           working tree has uncommitted changes")
        elif item.get("branch") and not item.get("detached"):
            print(
                f"           on branch {item['branch']}: a pull here would move the baseline "
                "without a catalogue release"
            )

    failures = [item for item in results if item["status"] in (MISSING, DRIFTED, UNPINNED)]
    if failures:
        print(f"\n{len(failures)} source(s) need attention")
        return 1

    print("\nall sources match the pinned baseline")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
