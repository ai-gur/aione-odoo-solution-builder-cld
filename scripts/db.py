#!/usr/bin/env python
"""Migration runner and database checks for the local control plane.

Plain SQL migrations applied through psql in the Postgres container. No ORM
migration DSL, deliberately: this schema's security-relevant parts are roles,
grants, RLS policies and FORCE flags, and those read far more clearly as SQL
than as generated migration objects. It also means the file reviewed is exactly
the file executed.

Usage:
    python scripts/db.py migrate     apply pending migrations
    python scripts/db.py status      show applied migrations
    python scripts/db.py reset       drop and recreate the database
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
COMPOSE_FILE = ROOT / "infrastructure" / "control-plane" / "compose.yaml"
MIGRATIONS_DIR = ROOT / "database" / "migrations"
DATABASE = "aione_control"

LEDGER_SQL = """
CREATE TABLE IF NOT EXISTS public.schema_migrations (
  filename    text PRIMARY KEY,
  applied_at  timestamptz NOT NULL DEFAULT now()
);
"""


def run_psql(
    sql: str,
    *,
    database: str = DATABASE,
    user: str = "postgres",
    password: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run SQL in the Postgres container and return the completed process.

    Callers that expect failure — the isolation tests — inspect the result
    themselves rather than having it raised for them.
    """
    command = ["docker", "compose", "-f", str(COMPOSE_FILE), "exec", "-T"]
    if password is not None:
        command += ["-e", f"PGPASSWORD={password}"]
    command += [
        "postgres", "psql",
        "-v", "ON_ERROR_STOP=1",
        "-U", user,
        "-d", database,
        "-t", "-A",
        "-f", "-",
    ]
    return subprocess.run(
        command, input=sql, capture_output=True, text=True, encoding="utf-8"
    )


def psql(
    sql: str,
    *,
    database: str = DATABASE,
    user: str = "postgres",
    password: str | None = None,
) -> str:
    """Run SQL and return stdout, failing loudly on error."""
    result = run_psql(sql, database=database, user=user, password=password)
    if result.returncode != 0:
        sys.stderr.write(result.stdout)
        sys.stderr.write(result.stderr)
        raise SystemExit(f"psql failed with exit code {result.returncode}")
    return result.stdout.strip()


def applied() -> set[str]:
    psql(LEDGER_SQL)
    rows = psql("SELECT filename FROM public.schema_migrations ORDER BY filename;")
    return {line.strip() for line in rows.splitlines() if line.strip()}


def migrate() -> None:
    done = applied()
    pending = [p for p in sorted(MIGRATIONS_DIR.glob("*.sql")) if p.name not in done]
    if not pending:
        print("no pending migrations")
        return
    for path in pending:
        print(f"applying {path.name}")
        sql = path.read_text(encoding="utf-8")
        # The ledger insert rides in the same psql invocation as the migration,
        # so a failed migration cannot be recorded as applied.
        sql += (
            "\nINSERT INTO public.schema_migrations (filename) VALUES "
            f"('{path.name}') ON CONFLICT DO NOTHING;\n"
        )
        psql(sql)
    print(f"applied {len(pending)} migration(s)")


def status() -> None:
    done = applied()
    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        print(f"{'applied' if path.name in done else 'pending':>8}  {path.name}")


def reset() -> None:
    psql(f'DROP DATABASE IF EXISTS "{DATABASE}" WITH (FORCE);', database="postgres")
    psql(f'CREATE DATABASE "{DATABASE}";', database="postgres")
    print(f"recreated {DATABASE}")


COMMANDS = {"migrate": migrate, "status": status, "reset": reset}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in COMMANDS:
        raise SystemExit(f"usage: python scripts/db.py [{'|'.join(COMMANDS)}]")
    COMMANDS[sys.argv[1]]()
