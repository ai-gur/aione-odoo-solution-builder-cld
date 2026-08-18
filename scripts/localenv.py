"""Load `.env.local` into the environment.

`LOCAL-DEVELOPMENT.md` tells a developer to copy `.env.example` to `.env.local`
and fill it in, so the tooling has to read it. Without this the workspace
health check reported every path as missing while the file sat there
correctly filled in — the instruction and the behaviour disagreed.

An explicitly exported variable always wins: a developer overriding a value for
one command should not have it silently replaced by the file.
"""

from __future__ import annotations

import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load(path: pathlib.Path | None = None) -> list[str]:
    """Set variables from the file that are not already in the environment.

    Returns the names it set, so a caller can report what came from where.
    """
    env_file = path or (ROOT / ".env.local")
    if not env_file.is_file():
        return []

    applied: list[str] = []
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value
            applied.append(key)
    return applied
