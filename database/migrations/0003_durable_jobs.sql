-- 0003 Durable jobs, transactional outbox and effects
--
-- ADR-005: PostgreSQL holds authoritative job state; the queue is transport.
-- A lost or duplicated Redis message must not change what happened, so every
-- fact a decision depends on lives here.
--
-- Role-scoped policies rather than a shared one. The worker must see jobs
-- across tenants — it claims work before it knows whose work it is — while the
-- API must never see another tenant's jobs. Writing that as two policies with
-- TO clauses keeps the distinction in the database rather than in the hope
-- that application code sets context correctly.

BEGIN;

CREATE SCHEMA IF NOT EXISTS jobs;
GRANT USAGE ON SCHEMA jobs TO app_api, app_worker, app_support;

CREATE TABLE jobs.jobs (
  id                text PRIMARY KEY CHECK (id LIKE 'job\_%'),
  tenant_id         text NOT NULL,
  job_type          text NOT NULL,
  payload           jsonb NOT NULL DEFAULT '{}'::jsonb,

  -- Retried deliveries reuse this identity, which is what makes a repeat
  -- harmless (ADR-005). Unique per tenant, not globally: two customers may
  -- legitimately submit the same logical request.
  idempotency_key   text NOT NULL,

  state             text NOT NULL DEFAULT 'pending'
                    CHECK (state IN ('pending', 'running', 'succeeded', 'failed', 'blocked')),
  attempts          integer NOT NULL DEFAULT 0,
  max_attempts      integer NOT NULL DEFAULT 3,

  -- Lease, not a lock: a worker that dies stops renewing, and the job becomes
  -- claimable again once the lease expires. Nothing has to notice the death.
  lease_owner       text,
  lease_expires_at  timestamptz,
  heartbeat_at      timestamptz,

  last_error        text,
  correlation_id    text NOT NULL,
  created_at        timestamptz NOT NULL DEFAULT now(),
  updated_at        timestamptz NOT NULL DEFAULT now(),
  completed_at      timestamptz,

  UNIQUE (tenant_id, idempotency_key)
);

CREATE INDEX jobs_claimable_idx ON jobs.jobs (state, lease_expires_at)
  WHERE state IN ('pending', 'running');
CREATE INDEX jobs_tenant_idx ON jobs.jobs (tenant_id, created_at DESC);

-- The outbox is written in the same transaction as the state change it
-- describes. Either both are committed or neither is, which is the property
-- that makes "the queue lost it" recoverable rather than fatal.
CREATE TABLE jobs.outbox (
  id              bigserial PRIMARY KEY,
  tenant_id       text NOT NULL,
  job_id          text NOT NULL REFERENCES jobs.jobs (id) ON DELETE CASCADE,
  topic           text NOT NULL,
  correlation_id  text NOT NULL,
  created_at      timestamptz NOT NULL DEFAULT now(),
  published_at    timestamptz
);

CREATE INDEX outbox_unpublished_idx ON jobs.outbox (created_at) WHERE published_at IS NULL;

-- Material effects of a job. The unique key is what makes a second delivery
-- observable as "already done" rather than as a second effect, and it is what
-- the duplicate-delivery test asserts against.
CREATE TABLE jobs.job_effects (
  id          bigserial PRIMARY KEY,
  tenant_id   text NOT NULL,
  job_id      text NOT NULL REFERENCES jobs.jobs (id) ON DELETE CASCADE,
  effect_key  text NOT NULL,
  detail      jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at  timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, effect_key)
);

-- ---------------------------------------------------------------------------
-- Row-level security
-- ---------------------------------------------------------------------------
ALTER TABLE jobs.jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs.jobs FORCE ROW LEVEL SECURITY;
ALTER TABLE jobs.outbox ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs.outbox FORCE ROW LEVEL SECURITY;
ALTER TABLE jobs.job_effects ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs.job_effects FORCE ROW LEVEL SECURITY;

-- The API sees only its own tenant's work.
CREATE POLICY jobs_tenant_scoped ON jobs.jobs
  TO app_api
  USING (tenant_id = app.current_tenant_id())
  WITH CHECK (tenant_id = app.current_tenant_id());

CREATE POLICY outbox_tenant_scoped ON jobs.outbox
  TO app_api
  USING (tenant_id = app.current_tenant_id())
  WITH CHECK (tenant_id = app.current_tenant_id());

CREATE POLICY effects_tenant_scoped ON jobs.job_effects
  TO app_api
  USING (tenant_id = app.current_tenant_id());

-- The worker claims work before it knows whose work it is, so it sees the
-- queue across tenants. It gains nothing else: this role holds no access to
-- discovery, blueprint or approval data.
CREATE POLICY jobs_worker ON jobs.jobs TO app_worker USING (true) WITH CHECK (true);
CREATE POLICY outbox_worker ON jobs.outbox TO app_worker USING (true) WITH CHECK (true);
CREATE POLICY effects_worker ON jobs.job_effects TO app_worker USING (true) WITH CHECK (true);

CREATE POLICY jobs_support ON jobs.jobs TO app_support USING (true);

GRANT SELECT, INSERT ON jobs.jobs TO app_api;
GRANT SELECT, INSERT ON jobs.outbox TO app_api;
GRANT USAGE, SELECT ON SEQUENCE jobs.outbox_id_seq TO app_api;
GRANT SELECT ON jobs.job_effects TO app_api;

GRANT SELECT, INSERT, UPDATE ON jobs.jobs TO app_worker;
GRANT SELECT, INSERT, UPDATE ON jobs.outbox TO app_worker;
GRANT USAGE, SELECT ON SEQUENCE jobs.outbox_id_seq TO app_worker;
GRANT SELECT, INSERT ON jobs.job_effects TO app_worker;
GRANT USAGE, SELECT ON SEQUENCE jobs.job_effects_id_seq TO app_worker;

GRANT SELECT ON jobs.jobs, jobs.outbox, jobs.job_effects TO app_support;

COMMIT;
