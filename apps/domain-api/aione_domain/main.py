"""Domain API.

Increment 0 scope: health, readiness, and identity resolved server-side. No
discovery, blueprint or provisioning behaviour — those arrive with their own
increments and their own approval gates.

Every request carries a correlation identifier, which appears in logs, audit
events and the response header, so one interaction can be followed across the
web tier, this service, workers and eventually a sandbox run.
"""

from __future__ import annotations

import json
import logging
import secrets
import sys
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.responses import JSONResponse

from . import audit, authorization, db, discovery, identity, workspaces
from .config import ConfigurationError, Settings, load_settings

logger = logging.getLogger("aione.domain")

CORRELATION_HEADER = "X-Correlation-Id"


def _serialise(row: dict) -> dict:
    """Render a database row as JSON. Timestamps become RFC 3339 (ADR-015)."""
    return {
        key: (value.isoformat() if isinstance(value, datetime) else value)
        for key, value in row.items()
    }


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


@app.post("/v1/tenants/{tenant_id}/jobs", status_code=202)
def submit_job(
    tenant_id: str,
    request: Request,
    body: dict,
    principal: identity.Principal = Depends(current_principal),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> dict[str, object]:
    """Submit a durable job.

    Returns 202 with a job identifier rather than a result: long work never
    runs inside a request (ADR-002). The job row and its outbox event are
    written in one transaction, so the queue can never carry an event for work
    the database does not know about (ADR-005).

    Resubmitting with the same Idempotency-Key returns the original job instead
    of creating a second one.
    """
    correlation_id = request.state.correlation_id

    if tenant_id not in principal.tenant_ids():
        audit.record(
            tenant_id=tenant_id,
            action="job.submit",
            correlation_id=correlation_id,
            outcome="denied",
            actor_id=principal.user_id,
            detail={"reason": "not_a_member"},
        )
        raise HTTPException(status_code=403, detail={"error": "forbidden"})

    job_type = str(body.get("jobType", "")).strip()
    if job_type != "health.echo":
        # Increment 0 registers one example handler. An unknown type is
        # refused here rather than accepted and blocked later, so the caller
        # learns immediately.
        raise HTTPException(status_code=400, detail={"error": "unsupported_job_type"})

    key = (idempotency_key or "").strip() or f"auto_{correlation_id}"
    job_id = "job_" + secrets.token_hex(13).upper()

    with db.transaction(tenant_id=tenant_id, user_id=principal.user_id) as cursor:
        cursor.execute(
            """
            INSERT INTO jobs.jobs (id, tenant_id, job_type, payload, idempotency_key, correlation_id)
            VALUES (%s, %s, %s, %s::jsonb, %s, %s)
            ON CONFLICT (tenant_id, idempotency_key) DO NOTHING
            RETURNING id
            """,
            (job_id, tenant_id, job_type, json.dumps(body.get("payload", {})), key, correlation_id),
        )
        created = cursor.fetchone()

        if created is None:
            cursor.execute(
                "SELECT id, state FROM jobs.jobs WHERE tenant_id = %s AND idempotency_key = %s",
                (tenant_id, key),
            )
            existing = cursor.fetchone()
            return {
                "jobId": existing["id"],
                "state": existing["state"],
                "duplicate": True,
                "correlationId": correlation_id,
            }

        # Same transaction as the insert above: both commit or neither does.
        cursor.execute(
            """
            INSERT INTO jobs.outbox (tenant_id, job_id, topic, correlation_id)
            VALUES (%s, %s, %s, %s)
            """,
            (tenant_id, job_id, "job.submitted", correlation_id),
        )

    audit.record(
        tenant_id=tenant_id,
        action="job.submit",
        correlation_id=correlation_id,
        outcome="succeeded",
        actor_id=principal.user_id,
        subject_type="job",
        subject_id=job_id,
        detail={"jobType": job_type},
    )

    return {"jobId": job_id, "state": "pending", "duplicate": False, "correlationId": correlation_id}


@app.get("/v1/tenants/{tenant_id}/jobs/{job_id}")
def job_status(
    tenant_id: str,
    job_id: str,
    request: Request,
    principal: identity.Principal = Depends(current_principal),
) -> dict[str, object]:
    """Authoritative job state, read from the database and never from the
    queue (ADR-005)."""
    if tenant_id not in principal.tenant_ids():
        raise HTTPException(status_code=403, detail={"error": "forbidden"})

    with db.transaction(tenant_id=tenant_id, user_id=principal.user_id) as cursor:
        cursor.execute(
            """
            SELECT id, job_type, state, attempts, max_attempts, last_error,
                   correlation_id, created_at, completed_at
              FROM jobs.jobs
             WHERE id = %s
            """,
            (job_id,),
        )
        job = cursor.fetchone()
        if job is None:
            raise HTTPException(status_code=404, detail={"error": "not_found"})

        cursor.execute(
            "SELECT count(*) AS n FROM jobs.job_effects WHERE job_id = %s", (job_id,)
        )
        effects = cursor.fetchone()["n"]

    return {
        "jobId": job["id"],
        "jobType": job["job_type"],
        "state": job["state"],
        "attempts": job["attempts"],
        "maxAttempts": job["max_attempts"],
        "lastError": job["last_error"],
        "effectCount": effects,
        "correlationId": job["correlation_id"],
        "createdAt": job["created_at"].isoformat(),
        "completedAt": job["completed_at"].isoformat() if job["completed_at"] else None,
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


# ---------------------------------------------------------------------------
# Customers and solution workspaces (Increment 1)
# ---------------------------------------------------------------------------


def authorize(
    principal: identity.Principal, tenant_id: str, authority: str, correlation_id: str
) -> str:
    """Check an authority, audit the denial, and return the role used.

    Every route goes through here, so a denial is always recorded and always
    recorded the same way. The role that permitted the action is returned
    because history and approval rows must name it (Constitution §5) — "they
    were an administrator" is not an answer.
    """
    try:
        return authorization.require(principal, tenant_id, authority)
    except authorization.AuthorizationError as error:
        audit.record(
            tenant_id=tenant_id,
            action=authority,
            correlation_id=correlation_id,
            outcome="denied",
            actor_id=principal.user_id,
            detail={"reason": error.reason},
        )
        raise HTTPException(status_code=403, detail={"error": "forbidden"}) from error


@app.post("/v1/tenants/{tenant_id}/customers", status_code=201)
def create_customer(
    tenant_id: str,
    request: Request,
    body: dict,
    principal: identity.Principal = Depends(current_principal),
) -> dict[str, object]:
    correlation_id = request.state.correlation_id
    role = authorize(principal, tenant_id, "customer.manage", correlation_id)

    legal_name = str(body.get("legalName", "")).strip()
    customer_code = str(body.get("customerCode", "")).strip()
    if not legal_name or not customer_code:
        raise HTTPException(
            status_code=400, detail={"error": "legalName_and_customerCode_required"}
        )

    try:
        customer = workspaces.create_customer(
            tenant_id=tenant_id,
            user_id=principal.user_id,
            legal_name=legal_name,
            customer_code=customer_code,
            trading_name=(body.get("tradingName") or None),
            countries=body.get("countries") or None,
        )
    except workspaces.ConflictError as error:
        raise HTTPException(status_code=409, detail={"error": str(error)}) from error

    audit.record(
        tenant_id=tenant_id,
        action="customer.created",
        correlation_id=correlation_id,
        outcome="succeeded",
        actor_id=principal.user_id,
        actor_role=role,
        subject_type="customer",
        subject_id=customer["id"],
        detail={"customerCode": customer_code},
    )
    return {"customer": _serialise(customer), "correlationId": correlation_id}


@app.get("/v1/tenants/{tenant_id}/customers")
def list_customers(
    tenant_id: str,
    request: Request,
    principal: identity.Principal = Depends(current_principal),
) -> dict[str, object]:
    correlation_id = request.state.correlation_id
    authorize(principal, tenant_id, "customer.read", correlation_id)
    rows = workspaces.list_customers(tenant_id=tenant_id, user_id=principal.user_id)
    return {"customers": [_serialise(row) for row in rows], "correlationId": correlation_id}


@app.post("/v1/tenants/{tenant_id}/workspaces", status_code=201)
def create_workspace(
    tenant_id: str,
    request: Request,
    body: dict,
    principal: identity.Principal = Depends(current_principal),
) -> dict[str, object]:
    correlation_id = request.state.correlation_id
    role = authorize(principal, tenant_id, "workspace.create", correlation_id)

    customer_id = str(body.get("customerId", "")).strip()
    name = str(body.get("name", "")).strip()
    if not customer_id or not name:
        raise HTTPException(status_code=400, detail={"error": "customerId_and_name_required"})

    try:
        workspace = workspaces.create_workspace(
            tenant_id=tenant_id,
            user_id=principal.user_id,
            actor_role=role,
            customer_id=customer_id,
            name=name,
            business_scope=(body.get("businessScope") or None),
            primary_locale=str(body.get("primaryLocale") or "he_IL"),
            discovery_mode=(body.get("discoveryMode") or None),
        )
    except workspaces.ConflictError as error:
        raise HTTPException(status_code=409, detail={"error": str(error)}) from error

    audit.record(
        tenant_id=tenant_id,
        action="workspace.created",
        correlation_id=correlation_id,
        outcome="succeeded",
        actor_id=principal.user_id,
        actor_role=role,
        subject_type="workspace",
        subject_id=workspace["id"],
        detail={"name": name},
    )
    return {"workspace": _serialise(workspace), "correlationId": correlation_id}


@app.get("/v1/tenants/{tenant_id}/workspaces")
def list_workspaces(
    tenant_id: str,
    request: Request,
    principal: identity.Principal = Depends(current_principal),
    customer_id: str | None = None,
) -> dict[str, object]:
    correlation_id = request.state.correlation_id
    authorize(principal, tenant_id, "workspace.read", correlation_id)
    rows = workspaces.list_workspaces(
        tenant_id=tenant_id, user_id=principal.user_id, customer_id=customer_id
    )
    return {"workspaces": [_serialise(row) for row in rows], "correlationId": correlation_id}


@app.post("/v1/tenants/{tenant_id}/workspaces/{workspace_id}/transition")
def transition_workspace(
    tenant_id: str,
    workspace_id: str,
    request: Request,
    body: dict,
    principal: identity.Principal = Depends(current_principal),
) -> dict[str, object]:
    correlation_id = request.state.correlation_id
    to_state = str(body.get("toState", "")).strip()

    # Confirming an engagement is complete is the Account Manager's decision
    # about the customer relationship, not a general workspace edit
    # (ROLES-AND-PERMISSIONS.md §4).
    authority = "workspace.complete" if to_state == "operating" else "workspace.manage"
    role = authorize(principal, tenant_id, authority, correlation_id)

    try:
        workspace = workspaces.transition(
            tenant_id=tenant_id,
            user_id=principal.user_id,
            actor_role=role,
            workspace_id=workspace_id,
            to_state=to_state,
            reason=(body.get("reason") or None),
        )
    except workspaces.TransitionError as error:
        audit.record(
            tenant_id=tenant_id,
            action="workspace.transition",
            correlation_id=correlation_id,
            outcome="failed",
            actor_id=principal.user_id,
            actor_role=role,
            subject_type="workspace",
            subject_id=workspace_id,
            detail={"from": error.current, "to": error.requested},
        )
        raise HTTPException(
            status_code=409,
            detail={"error": "illegal_transition", "from": error.current, "to": error.requested},
        ) from error
    except workspaces.ConflictError as error:
        raise HTTPException(status_code=404, detail={"error": str(error)}) from error

    audit.record(
        tenant_id=tenant_id,
        action="workspace.transition",
        correlation_id=correlation_id,
        outcome="succeeded",
        actor_id=principal.user_id,
        actor_role=role,
        subject_type="workspace",
        subject_id=workspace_id,
        detail={"to": to_state},
    )
    return {"workspace": _serialise(workspace), "correlationId": correlation_id}


@app.get("/v1/tenants/{tenant_id}/workspaces/{workspace_id}/history")
def workspace_history(
    tenant_id: str,
    workspace_id: str,
    request: Request,
    principal: identity.Principal = Depends(current_principal),
) -> dict[str, object]:
    correlation_id = request.state.correlation_id
    authorize(principal, tenant_id, "workspace.read", correlation_id)
    rows = workspaces.workspace_history(
        tenant_id=tenant_id, user_id=principal.user_id, workspace_id=workspace_id
    )
    return {"history": [_serialise(row) for row in rows], "correlationId": correlation_id}


# ---------------------------------------------------------------------------
# Discovery interviews (Increment 2)
# ---------------------------------------------------------------------------


@app.post("/v1/tenants/{tenant_id}/workspaces/{workspace_id}/interviews", status_code=201)
def start_interview(
    tenant_id: str,
    workspace_id: str,
    request: Request,
    body: dict | None = None,
    principal: identity.Principal = Depends(current_principal),
) -> dict[str, object]:
    """Start or resume the workspace's interview.

    Resuming is the default. Starting a second run would ask the customer for
    information they have already given, which Discovery §3.6 forbids.
    """
    correlation_id = request.state.correlation_id
    role = authorize(principal, tenant_id, "discovery.conduct", correlation_id)
    mode = str((body or {}).get("mode") or "quick_start")

    try:
        run = discovery.start_run(
            tenant_id=tenant_id, user_id=principal.user_id,
            workspace_id=workspace_id, mode=mode,
        )
    except discovery.DiscoveryError as error:
        raise HTTPException(status_code=409, detail={"error": str(error)}) from error

    if not run["resumed"]:
        audit.record(
            tenant_id=tenant_id, action="discovery.run.started",
            correlation_id=correlation_id, outcome="succeeded",
            actor_id=principal.user_id, actor_role=role,
            subject_type="interview_run", subject_id=run["id"],
            detail={"mode": mode, "workspaceId": workspace_id},
        )

    return {"run": _serialise(run), "correlationId": correlation_id}


@app.get("/v1/tenants/{tenant_id}/interviews/{run_id}")
def get_interview(
    tenant_id: str,
    run_id: str,
    request: Request,
    locale: str = "he_IL",
    principal: identity.Principal = Depends(current_principal),
) -> dict[str, object]:
    """The interview plan: every question, whether it applies, and why."""
    correlation_id = request.state.correlation_id
    authorize(principal, tenant_id, "discovery.conduct", correlation_id)

    try:
        plan = discovery.question_plan(
            tenant_id=tenant_id, user_id=principal.user_id, run_id=run_id, locale=locale
        )
    except discovery.DiscoveryError as error:
        raise HTTPException(status_code=404, detail={"error": str(error)}) from error

    return {**plan, "correlationId": correlation_id}


@app.post("/v1/tenants/{tenant_id}/interviews/{run_id}/answers")
def submit_answer(
    tenant_id: str,
    run_id: str,
    request: Request,
    body: dict,
    principal: identity.Principal = Depends(current_principal),
) -> dict[str, object]:
    """Record an answer. A second answer to the same question supersedes the
    first; neither row is lost."""
    correlation_id = request.state.correlation_id
    role = authorize(principal, tenant_id, "discovery.conduct", correlation_id)

    question_key = str(body.get("questionKey", "")).strip()
    if not question_key or "value" not in body:
        raise HTTPException(status_code=400, detail={"error": "questionKey_and_value_required"})

    try:
        answer = discovery.submit_answer(
            tenant_id=tenant_id, user_id=principal.user_id, run_id=run_id,
            question_key=question_key, raw_value=body["value"],
            answer_source=str(body.get("source") or "customer"),
            confidence=str(body.get("confidence") or "amber"),
        )
    except discovery.DiscoveryError as error:
        raise HTTPException(status_code=409, detail={"error": str(error)}) from error

    audit.record(
        tenant_id=tenant_id, action="discovery.answer.recorded",
        correlation_id=correlation_id, outcome="succeeded",
        actor_id=principal.user_id, actor_role=role,
        subject_type="answer", subject_id=answer["id"],
        # The answer's content is customer data and stays in the discovery
        # tables; audit records that it happened, not what was said.
        detail={"questionKey": question_key, "revision": answer["revision"]},
    )

    return {"answer": _serialise(answer), "correlationId": correlation_id}


@app.post("/v1/tenants/{tenant_id}/interviews/{run_id}/normalise")
def normalise_interview(
    tenant_id: str,
    run_id: str,
    request: Request,
    principal: identity.Principal = Depends(current_principal),
) -> dict[str, object]:
    """Re-derive facts, requirements and open questions from current answers.

    Deterministic: the same answers produce the same conclusions. Re-running
    after a corrected answer supersedes the conclusions that no longer hold
    rather than deleting them, so a reviewer can see that the system once
    believed something different and why.
    """
    correlation_id = request.state.correlation_id
    role = authorize(principal, tenant_id, "discovery.conduct", correlation_id)

    try:
        counts = discovery.normalise(
            tenant_id=tenant_id, user_id=principal.user_id, run_id=run_id
        )
    except discovery.DiscoveryError as error:
        raise HTTPException(status_code=404, detail={"error": str(error)}) from error

    audit.record(
        tenant_id=tenant_id, action="discovery.normalised",
        correlation_id=correlation_id, outcome="succeeded",
        actor_id=principal.user_id, actor_role=role,
        subject_type="interview_run", subject_id=run_id, detail=counts,
    )
    return {**counts, "correlationId": correlation_id}


@app.get("/v1/tenants/{tenant_id}/interviews/{run_id}/derived")
def interview_derived(
    tenant_id: str,
    run_id: str,
    request: Request,
    principal: identity.Principal = Depends(current_principal),
) -> dict[str, object]:
    """Facts, requirements and open questions currently derived from a run."""
    correlation_id = request.state.correlation_id
    authorize(principal, tenant_id, "discovery.conduct", correlation_id)
    view = discovery.derived_view(
        tenant_id=tenant_id, user_id=principal.user_id, run_id=run_id
    )
    return {**view, "correlationId": correlation_id}


@app.get("/v1/tenants/{tenant_id}/interviews/{run_id}/answers/{question_key}/history")
def answer_history(
    tenant_id: str,
    run_id: str,
    question_key: str,
    request: Request,
    principal: identity.Principal = Depends(current_principal),
) -> dict[str, object]:
    """Every version of one answer — what was said, by whom, and when."""
    correlation_id = request.state.correlation_id
    authorize(principal, tenant_id, "discovery.conduct", correlation_id)
    rows = discovery.answer_history(
        tenant_id=tenant_id, user_id=principal.user_id,
        run_id=run_id, question_key=question_key,
    )
    return {"history": [_serialise(row) for row in rows], "correlationId": correlation_id}
