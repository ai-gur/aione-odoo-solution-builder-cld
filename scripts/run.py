#!/usr/bin/env python
"""Canonical developer commands.

`LOCAL-DEVELOPMENT.md` requires one command interface used by both the README
and CI. A Makefile alone cannot be that interface here: `make` is not present
on a stock Windows developer machine, and this project's first developers are
on Windows. So the commands live in Python, which every contributor already
has because the domain service is written in it, and the Makefile delegates
here for people who prefer typing `make`.

    python scripts/run.py <command>
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
COMPOSE = ["docker", "compose", "-f", str(ROOT / "infrastructure" / "control-plane" / "compose.yaml")]


def venv_python(app: str) -> str:
    """Interpreter for an app's virtual environment, on either platform."""
    base = ROOT / "apps" / app / ".venv"
    candidate = base / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not candidate.exists():
        raise SystemExit(
            f"{app} has no virtual environment yet. Run: python scripts/run.py bootstrap"
        )
    return str(candidate)


def run(command: list[str], *, cwd: pathlib.Path | None = None) -> None:
    printable = " ".join(command)
    print(f"\n> {printable}", flush=True)
    result = subprocess.run(command, cwd=str(cwd or ROOT))
    if result.returncode != 0:
        raise SystemExit(result.returncode)


# --- stack ------------------------------------------------------------------

def stack_up() -> None:
    run([*COMPOSE, "up", "-d"])
    print("\npostgres 55432 | redis 56379 | storage 59000 (console 59001) | mail 58125")


def stack_down() -> None:
    run([*COMPOSE, "down"])


def stack_ps() -> None:
    run([*COMPOSE, "ps"])


# --- database ---------------------------------------------------------------

def db_migrate() -> None:
    run([sys.executable, "scripts/db.py", "migrate"])


def db_status() -> None:
    run([sys.executable, "scripts/db.py", "status"])


def db_reset() -> None:
    run([sys.executable, "scripts/db.py", "reset"])
    db_migrate()
    db_seed()


def db_seed() -> None:
    """Load versioned interview definitions. Idempotent."""
    run([sys.executable, "scripts/seed_interviews.py"])


def db_seed_dev() -> None:
    """Load the local fixture: one tenant, customer and workspace."""
    db_seed()
    run([sys.executable, "scripts/seed_dev.py"])


# --- tests ------------------------------------------------------------------

def test_contract_ts() -> None:
    run(["node", "--test", "packages/contracts/ts/test/canonical.test.ts"])


def test_contract_py() -> None:
    env_python = sys.executable
    run(
        [env_python, "-m", "unittest", "discover", "-s", "tests"],
        cwd=ROOT / "packages" / "contracts" / "python",
    )


def test_contract() -> None:
    test_contract_ts()
    test_contract_py()


def test_integration() -> None:
    run([sys.executable, "-m", "unittest", "discover", "-s", "tests/integration",
         "-p", "test_tenant_isolation.py", "-v"])
    # The job tests need the worker's dependencies.
    run([venv_python("worker"), "-m", "unittest", "discover", "-s", "tests/integration",
         "-p", "test_durable_jobs.py", "-v"])


def test_api() -> None:
    run([venv_python("domain-api"), "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=ROOT / "apps" / "domain-api")


def test() -> None:
    test_contract()
    test_integration()
    test_api()


# --- services ---------------------------------------------------------------

def api_dev() -> None:
    run([venv_python("domain-api"), "-m", "uvicorn", "aione_domain.main:app",
         "--reload", "--port", "8000"], cwd=ROOT / "apps" / "domain-api")


def worker_dev() -> None:
    run([venv_python("worker"), "-m", "aione_worker"], cwd=ROOT / "apps" / "worker")


def bootstrap() -> None:
    run(["pnpm", "install"])
    run(["uv", "sync"], cwd=ROOT / "packages" / "contracts" / "python")
    run(["uv", "sync"], cwd=ROOT / "apps" / "domain-api")
    run(["uv", "sync"], cwd=ROOT / "apps" / "worker")
    print("\nNext: python scripts/run.py stack-up && python scripts/run.py db-migrate")


COMMANDS = {
    "bootstrap": bootstrap,
    "stack-up": stack_up,
    "stack-down": stack_down,
    "stack-ps": stack_ps,
    "db-migrate": db_migrate,
    "db-status": db_status,
    "db-reset": db_reset,
    "db-seed": db_seed,
    "db-seed-dev": db_seed_dev,
    "test": test,
    "test-contract": test_contract,
    "test-integration": test_integration,
    "test-api": test_api,
    "api-dev": api_dev,
    "worker-dev": worker_dev,
}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        print("Commands:")
        for name in COMMANDS:
            print(f"  {name}")
        raise SystemExit(2)
    COMMANDS[sys.argv[1]]()
