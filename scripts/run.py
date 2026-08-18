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


TEST_DATABASE = "aione_control_test"
TEST_DSN = f"postgresql://app_api:local_dev_only@localhost:55432/{TEST_DATABASE}"
TEST_WORKER_DSN = f"postgresql://app_worker:local_dev_only@localhost:55432/{TEST_DATABASE}"


def run(
    command: list[str], *, cwd: pathlib.Path | None = None, env: dict[str, str] | None = None
) -> None:
    printable = " ".join(command)
    print(f"\n> {printable}", flush=True)
    result = subprocess.run(command, cwd=str(cwd or ROOT), env=env)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def test_env() -> dict[str, str]:
    """Environment pointing every suite at the test database.

    Tests clean up after themselves, and a suite that deletes a user cascades
    to their memberships. Sharing a database with local development means that
    cleanup silently empties the developer's fixture, and the symptom appears
    later as a blank screen rather than as a test failure.
    """
    return {
        **os.environ,
        "AIONE_DATABASE": TEST_DATABASE,
        "DATABASE_URL_API": TEST_DSN,
        "DATABASE_URL_WORKER": TEST_WORKER_DSN,
        "APP_ENVIRONMENT": "local",
        "AUTH_MODE": "dev",
    }


def db_test_prepare() -> None:
    """Create, migrate and seed the test database. Safe to re-run."""
    env = test_env()
    run([sys.executable, "scripts/db.py", "create"], env=env)
    run([sys.executable, "scripts/db.py", "migrate"], env=env)
    run([sys.executable, "scripts/seed_interviews.py"], env=env)


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
    db_test_prepare()
    env = test_env()
    run([sys.executable, "-m", "unittest", "discover", "-s", "tests/integration",
         "-p", "test_tenant_isolation.py", "-v"], env=env)
    # Needs no database; it reads the workspace and writes nothing.
    run([sys.executable, "-m", "unittest", "discover", "-s", "tests/integration",
         "-p", "test_workspace_health.py", "-v"], env=env)
    # The job tests need the worker's dependencies.
    run([venv_python("worker"), "-m", "unittest", "discover", "-s", "tests/integration",
         "-p", "test_durable_jobs.py", "-v"], env=env)


def test_api() -> None:
    db_test_prepare()
    run([venv_python("domain-api"), "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=ROOT / "apps" / "domain-api", env=test_env())


def test() -> None:
    test_contract()
    test_catalogue()
    test_integration()
    test_api()


# --- services ---------------------------------------------------------------

def api_dev() -> None:
    run([venv_python("domain-api"), "-m", "uvicorn", "aione_domain.main:app",
         "--reload", "--port", "8000"], cwd=ROOT / "apps" / "domain-api")


def catalogue_ingest() -> None:
    """Build a catalogue draft from the pinned Odoo source."""
    run([sys.executable, "catalogue/ingestion/ingest.py"])


def test_catalogue() -> None:
    run([sys.executable, "-m", "unittest", "discover", "-s", "catalogue/tests", "-v"])


def workspace_health() -> None:
    """Verify the Odoo workspace paths and revisions. Never mutates them."""
    run([sys.executable, "scripts/workspace_health.py"])


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
    "db-test-prepare": db_test_prepare,
    "test": test,
    "test-contract": test_contract,
    "test-integration": test_integration,
    "test-api": test_api,
    "api-dev": api_dev,
    "worker-dev": worker_dev,
    "workspace-health": workspace_health,
    "catalogue-ingest": catalogue_ingest,
    "test-catalogue": test_catalogue,
}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        print("Commands:")
        for name in COMMANDS:
            print(f"  {name}")
        raise SystemExit(2)
    COMMANDS[sys.argv[1]]()
