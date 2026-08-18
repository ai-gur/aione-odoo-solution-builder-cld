-- 0001 Identity, tenancy and audit baseline
--
-- Implements the Increment 0 data slice and the enforcement mechanism from
-- ADR-014: the API connects as a role that cannot bypass row-level security,
-- and tenant context arrives per transaction through SET LOCAL rather than
-- from anything the client sends.
--
-- Identifiers are prefixed ULIDs stored as text (ADR-015). They are not UUIDs
-- and must not be cast to uuid.

BEGIN;

-- ---------------------------------------------------------------------------
-- Schemas
-- ---------------------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS app;
CREATE SCHEMA IF NOT EXISTS audit;

-- ---------------------------------------------------------------------------
-- Service roles (ADR-014)
--
-- Local development gives these roles LOGIN and a placeholder password so the
-- isolation tests can actually connect as them. Deployed environments create
-- the same roles without passwords and authenticate through the platform's
-- workload identity.
--
-- None of them is a superuser and none carries BYPASSRLS. app_api holding
-- BYPASSRLS would make every policy below decorative, which is the specific
-- failure ADR-014 exists to prevent.
-- ---------------------------------------------------------------------------
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_api') THEN
    CREATE ROLE app_api LOGIN PASSWORD 'local_dev_only' NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_worker') THEN
    CREATE ROLE app_worker LOGIN PASSWORD 'local_dev_only' NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_support') THEN
    CREATE ROLE app_support LOGIN PASSWORD 'local_dev_only' NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS;
  END IF;
END
$$;

GRANT USAGE ON SCHEMA app TO app_api, app_worker, app_support;
GRANT USAGE ON SCHEMA audit TO app_api, app_worker, app_support;

-- ---------------------------------------------------------------------------
-- Tenant context helper
--
-- Returns the tenant set for the current transaction, or NULL when nothing has
-- been set. NULL makes every policy below match no rows, so a request that
-- forgets to establish context reads nothing rather than everything.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION app.current_tenant_id()
RETURNS text
LANGUAGE sql
STABLE
AS $$
  SELECT nullif(current_setting('app.tenant_id', true), '');
$$;

-- ---------------------------------------------------------------------------
-- Tables
-- ---------------------------------------------------------------------------
CREATE TABLE app.tenants (
  id          text PRIMARY KEY CHECK (id LIKE 'ten\_%'),
  name        text NOT NULL,
  created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE app.users (
  id            text PRIMARY KEY CHECK (id LIKE 'usr\_%'),
  auth_subject  text NOT NULL UNIQUE,
  email         text NOT NULL UNIQUE,
  display_name  text NOT NULL,
  created_at    timestamptz NOT NULL DEFAULT now()
);

-- A user's membership of a tenant, carrying the role key from
-- docs/20-domain/ROLES-AND-PERMISSIONS.md.
CREATE TABLE app.memberships (
  id          text PRIMARY KEY CHECK (id LIKE 'mbr\_%'),
  tenant_id   text NOT NULL REFERENCES app.tenants (id) ON DELETE CASCADE,
  user_id     text NOT NULL REFERENCES app.users (id) ON DELETE CASCADE,
  role_key    text NOT NULL,
  created_at  timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, user_id, role_key)
);

CREATE INDEX memberships_tenant_idx ON app.memberships (tenant_id);
CREATE INDEX memberships_user_idx ON app.memberships (user_id);

-- Append-only material events (ADR-011). Separate from troubleshooting logs,
-- and separate from the app schema so its grants can differ.
CREATE TABLE audit.events (
  id              text PRIMARY KEY CHECK (id LIKE 'evt\_%'),
  tenant_id       text NOT NULL,
  actor_id        text,
  actor_role      text,
  action          text NOT NULL,
  subject_type    text,
  subject_id      text,
  subject_version text,
  correlation_id  text NOT NULL,
  outcome         text NOT NULL CHECK (outcome IN ('succeeded', 'denied', 'failed')),
  occurred_at     timestamptz NOT NULL DEFAULT now(),
  detail          jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX events_tenant_time_idx ON audit.events (tenant_id, occurred_at DESC);
CREATE INDEX events_correlation_idx ON audit.events (correlation_id);

-- ---------------------------------------------------------------------------
-- Row-level security
--
-- FORCE applies the policies to the table owner too, so a migration or a
-- console session cannot quietly read across tenants either.
-- ---------------------------------------------------------------------------
ALTER TABLE app.tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.tenants FORCE ROW LEVEL SECURITY;
CREATE POLICY tenants_in_context ON app.tenants
  USING (id = app.current_tenant_id());

ALTER TABLE app.memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.memberships FORCE ROW LEVEL SECURITY;
CREATE POLICY memberships_in_context ON app.memberships
  USING (tenant_id = app.current_tenant_id())
  WITH CHECK (tenant_id = app.current_tenant_id());

ALTER TABLE audit.events ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit.events FORCE ROW LEVEL SECURITY;
CREATE POLICY events_in_context ON audit.events
  USING (tenant_id = app.current_tenant_id())
  WITH CHECK (tenant_id = app.current_tenant_id());

-- app.users is global: a person may belong to several tenants, and the row
-- carries no tenant-owned content. Reaching a user still requires a membership
-- visible in the caller's tenant, which the policies above constrain.

-- ---------------------------------------------------------------------------
-- Grants
--
-- audit.events is INSERT and SELECT only. No application role may UPDATE or
-- DELETE an audit event (ADR-011); append-only is enforced by privilege, not
-- by convention.
-- ---------------------------------------------------------------------------
GRANT SELECT, INSERT, UPDATE, DELETE ON app.tenants, app.users, app.memberships TO app_api;
GRANT SELECT, INSERT ON audit.events TO app_api;
REVOKE UPDATE, DELETE, TRUNCATE ON audit.events FROM app_api;

GRANT SELECT ON app.tenants, app.users, app.memberships TO app_worker;
GRANT SELECT, INSERT ON audit.events TO app_worker;
REVOKE UPDATE, DELETE, TRUNCATE ON audit.events FROM app_worker;

GRANT SELECT ON app.tenants, app.users, app.memberships TO app_support;
GRANT SELECT ON audit.events TO app_support;

COMMIT;
