"""Database access with per-transaction tenant context.

This module is the only place that opens a transaction, and it is the only
place that sets tenant context. Both facts are deliberate: ADR-014 requires
that policy context be established from server-verified identity on every
request, and a second code path that opens transactions is a second place to
forget.

`SET LOCAL` rather than a session-level `SET`, because the pool reuses sessions
across requests and a session-level setting would hand one request's tenant to
the next one. The integration suite proves it does not.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Iterator

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

logger = logging.getLogger(__name__)

_pool: ConnectionPool | None = None


def open_pool(database_url: str, *, min_size: int = 1, max_size: int = 8) -> ConnectionPool:
    global _pool
    if _pool is None:
        _pool = ConnectionPool(
            conninfo=database_url,
            min_size=min_size,
            max_size=max_size,
            kwargs={"row_factory": dict_row},
            open=True,
        )
    return _pool


def close_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


def get_pool() -> ConnectionPool:
    if _pool is None:
        raise RuntimeError("Connection pool is not open; call open_pool during startup.")
    return _pool


@contextmanager
def transaction(
    tenant_id: str | None = None, user_id: str | None = None
) -> Iterator[psycopg.Cursor]:
    """Open a transaction, optionally scoped to one tenant and one user.

    Passing no tenant is not a way to see everything — the policies match no
    rows when context is unset, so an unscoped transaction reads nothing from
    tenant-owned tables. That is the intended failure mode for a code path that
    forgets to resolve identity.
    """
    with get_pool().connection() as connection:
        with connection.transaction():
            with connection.cursor() as cursor:
                # Parameterised via set_config: these values reach here from a
                # database lookup rather than from the request, but SET LOCAL
                # built by string interpolation would be an injection point the
                # first time that stops being true.
                if tenant_id is not None:
                    cursor.execute(
                        "SELECT set_config('app.tenant_id', %s::text, true)", (tenant_id,)
                    )
                if user_id is not None:
                    cursor.execute(
                        "SELECT set_config('app.user_id', %s::text, true)", (user_id,)
                    )
                yield cursor


def check_readiness() -> tuple[bool, str]:
    """Confirm the database answers and the schema is present."""
    try:
        with get_pool().connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT count(*) AS n FROM information_schema.tables "
                    "WHERE table_schema IN ('app', 'audit')"
                )
                row = cursor.fetchone()
                tables = row["n"] if row else 0
                if tables == 0:
                    return False, "schema not migrated"
                return True, "ready"
    except Exception as error:  # noqa: BLE001 - reported, never raised to the client
        logger.warning("readiness check failed: %s", type(error).__name__)
        return False, "database unavailable"
