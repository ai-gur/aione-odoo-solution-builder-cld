"""Domain API.

Increment 0 scope: health, readiness, and identity resolved server-side. No
discovery, blueprint or provisioning behaviour — those arrive with their own
increments and their own approval gates.

Every request carries a correlation identifier, which appears in logs, audit
events and the response header, so one interaction can be followed across the
web tier, this service, workers and eventually a sandbox run.
"""

from __future__ import annotations

import logging
import secrets
import sys
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.responses import JSONResponse

from . import audit, db, identity
from .config import ConfigurationError, Settings, load_settings

logger = logging.getLogger("aione.domain")

CORRELATION_HEADER = "X-Correlation-Id"


def _configure_logging(level: str) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            '{"time":"%(asctime)s","level":"%(levelname)s",'
            '"logger":"%(name)s","message":"%(message)s"}'
        )
    )
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings: Settings = load_settings()
    _configure_logging(settings.log_level)
    app.state.settings = settings
    db.open_pool(settings.database_url)
    logger.info(
        "domain api started environment=%s auth_mode=%s database=%s",
        settings.environment,
        settings.auth_mode,
        settings.safe_database_url,
    )
    try:
        yield
    finally:
        db.close_pool()


app = FastAPI(
    title="AIOne Odoo Solution Builder — Domain API",
    version="0.0.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def correlation_middleware(request: Request, call_next):
    correlation_id = request.headers.get(CORRELATION_HEADER) or "cor_" + secrets.token_hex(8)
    request.state.correlation_id = correlation_id
    response: Response = await call_next(request)
    response.headers[CORRELATION_HEADER] = correlation_id
    return response


@app.exception_handler(ConfigurationError)
async def configuration_error_handler(_: Request, error: ConfigurationError):
    # Configuration errors name the setting, never the value.
    logger.error("configuration error: %s", error)
    return JSONResponse(status_code=500, content={"error": "configuration_error"})


def current_principal(
    request: Request,
    authorization: str | None = Header(default=None),
) -> identity.Principal:
    """Resolve the caller from their credential and the control database.

    Nothing about the caller is taken from the request beyond the credential
    itself. A tenant identifier in a header or body is ignored (ADR-014).
    """
    settings: Settings = request.app.state.settings
    try:
        subject = identity.subject_from_authorization(authorization, settings.auth_mode)
        return identity.resolve_principal(subject)
    except identity.AuthenticationError as error:
        logger.info(
            "authentication failed correlation=%s reason=%s",
            getattr(request.state, "correlation_id", "-"),
            error,
        )
        raise HTTPException(status_code=401, detail={"error": "unauthenticated"}) from error


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness: the process is up. Deliberately does not touch the database,
    so a database outage does not cause the platform to restart the process."""
    return {"status": "ok"}


@app.get("/ready")
def ready(response: Response) -> dict[str, str]:
    """Readiness: dependencies answer and the schema is present."""
    ok, detail = db.check_readiness()
    if not ok:
        response.status_code = 503
        return {"status": "unavailable", "detail": detail}
    return {"status": "ready"}


@app.get("/v1/me")
def me(
    request: Request,
    principal: identity.Principal = Depends(current_principal),
) -> dict[str, object]:
    """The caller's identity and memberships, as resolved server-side."""
    return {
        "userId": principal.user_id,
        "email": principal.email,
        "displayName": principal.display_name,
        "memberships": [
            {
                "tenantId": m.tenant_id,
                "tenantName": m.tenant_name,
                "roleKey": m.role_key,
            }
            for m in principal.memberships
        ],
        "correlationId": request.state.correlation_id,
    }


@app.get("/v1/tenants/{tenant_id}/audit-events")
def list_audit_events(
    tenant_id: str,
    request: Request,
    principal: identity.Principal = Depends(current_principal),
) -> dict[str, object]:
    """Audit events for one tenant.

    The membership check and the database policy are both load-bearing: the
    check produces a clean 403 and an audit trail, and the policy means a bug
    in the check still cannot return another tenant's rows.
    """
    correlation_id = request.state.correlation_id

    if tenant_id not in principal.tenant_ids():
        # Recorded against the tenant that was reached for, which is what an
        # investigation needs to see.
        audit.record(
            tenant_id=tenant_id,
            action="audit.events.list",
            correlation_id=correlation_id,
            outcome="denied",
            actor_id=principal.user_id,
            detail={"reason": "not_a_member"},
        )
        raise HTTPException(status_code=403, detail={"error": "forbidden"})

    with db.transaction(tenant_id=tenant_id, user_id=principal.user_id) as cursor:
        cursor.execute(
            """
            SELECT id, action, actor_id, actor_role, outcome, occurred_at, correlation_id
            FROM audit.events
            ORDER BY occurred_at DESC
            LIMIT 50
            """
        )
        events = [
            {
                "id": row["id"],
                "action": row["action"],
                "actorId": row["actor_id"],
                "actorRole": row["actor_role"],
                "outcome": row["outcome"],
                "occurredAt": row["occurred_at"].isoformat(),
                "correlationId": row["correlation_id"],
            }
            for row in cursor.fetchall()
        ]

    return {"tenantId": tenant_id, "events": events, "correlationId": correlation_id}
