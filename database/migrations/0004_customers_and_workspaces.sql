-- 0004 Customer organizations and solution workspaces
--
-- The Solution Workspace is the bounded engagement aggregate (Constitution
-- §7.1 as amended, ADR-013). It owns discovery, requirements, blueprints,
-- manifests, environments, baselines and approvals — everything that follows
-- attaches here, which is why this table settles what "stored under the
-- customer's account" means.
--
-- Roles come from docs/20-domain/ROLES-AND-PERMISSIONS.md and states from
-- docs/20-domain/ENUMS.md. Both are constrained here rather than trusted from
-- application code, because a bad role key written once outlives whichever
-- release wrote it.

BEGIN;

CREATE TABLE app.customer_organizations (
  id                  text PRIMARY KEY CHECK (id LIKE 'cus\_%'),
  tenant_id           text NOT NULL REFERENCES app.tenants (id) ON DELETE CASCADE,
  legal_name          text NOT NULL,
  trading_name        text,
  -- An internal code, so a repository or an export never has to carry the
  -- customer's name (Portfolio §4.5).
  customer_code       text NOT NULL,
  countries           text[] NOT NULL DEFAULT ARRAY['IL'],
  industries          text[] NOT NULL DEFAULT '{}',
  status              text NOT NULL DEFAULT 'active'
                      CHECK (status IN ('prospect', 'active', 'dormant', 'closed')),
  data_classification text NOT NULL DEFAULT 'customer_confidential'
                      CHECK (data_classification IN (
                        'public', 'aione_internal', 'customer_confidential',
                        'sensitive_personal_or_financial', 'secret')),
  created_at          timestamptz NOT NULL DEFAULT now(),
  updated_at          timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, customer_code)
);

CREATE INDEX customer_organizations_tenant_idx ON app.customer_organizations (tenant_id);

CREATE TABLE app.solution_workspaces (
  id                    text PRIMARY KEY CHECK (id LIKE 'wsp\_%'),
  tenant_id             text NOT NULL REFERENCES app.tenants (id) ON DELETE CASCADE,
  customer_id           text NOT NULL REFERENCES app.customer_organizations (id) ON DELETE RESTRICT,
  name                  text NOT NULL,
  business_scope        text,

  state                 text NOT NULL DEFAULT 'proposed'
                        CHECK (state IN (
                          'proposed', 'discovering', 'clarification_required', 'designing',
                          'blueprint_review', 'approved_for_sandbox', 'provisioning',
                          'validation_failed', 'sandbox_active', 'customer_review',
                          'revision_required', 'accepted', 'operating',
                          'change_in_progress', 'suspended', 'archived', 'closed')),

  target_odoo_version   text NOT NULL DEFAULT '19.0',
  target_odoo_edition   text NOT NULL DEFAULT 'enterprise'
                        CHECK (target_odoo_edition IN ('enterprise', 'community')),
  primary_locale        text NOT NULL DEFAULT 'he_IL' CHECK (primary_locale IN ('he_IL', 'en_US')),
  secondary_locale      text CHECK (secondary_locale IN ('he_IL', 'en_US')),

  discovery_mode        text CHECK (discovery_mode IN ('quick_start', 'guided', 'comprehensive')),

  -- Set by baseline.accept; cleared by nothing. A workspace without one has
  -- never been accepted, which is a different thing from having been accepted
  -- and then changed.
  current_baseline_id   text,

  created_at            timestamptz NOT NULL DEFAULT now(),
  updated_at            timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, customer_id, name)
);

CREATE INDEX solution_workspaces_tenant_idx ON app.solution_workspaces (tenant_id);
CREATE INDEX solution_workspaces_customer_idx ON app.solution_workspaces (customer_id);

-- Membership of a workspace, distinct from membership of the tenant. Being an
-- AIOne consultant does not put a person on every engagement, and a customer
-- respondent belongs to exactly one.
CREATE TABLE app.workspace_members (
  id            text PRIMARY KEY CHECK (id LIKE 'wsm\_%'),
  tenant_id     text NOT NULL REFERENCES app.tenants (id) ON DELETE CASCADE,
  workspace_id  text NOT NULL REFERENCES app.solution_workspaces (id) ON DELETE CASCADE,
  user_id       text NOT NULL REFERENCES app.users (id) ON DELETE CASCADE,
  role_key      text NOT NULL CHECK (role_key IN (
                  'platform_administrator', 'account_owner', 'solution_owner',
                  'consultant', 'solution_architect', 'provisioning_operator',
                  'repository_maintainer', 'auditor',
                  'customer_sponsor', 'customer_process_owner', 'customer_technical_contact')),
  created_at    timestamptz NOT NULL DEFAULT now(),
  UNIQUE (workspace_id, user_id, role_key)
);

CREATE INDEX workspace_members_workspace_idx ON app.workspace_members (workspace_id);
CREATE INDEX workspace_members_user_idx ON app.workspace_members (user_id);

-- Every state change, with who caused it. The portfolio timeline reads from
-- here; audit events remain the authority for proof.
CREATE TABLE app.workspace_state_history (
  id            bigserial PRIMARY KEY,
  tenant_id     text NOT NULL,
  workspace_id  text NOT NULL REFERENCES app.solution_workspaces (id) ON DELETE CASCADE,
  from_state    text,
  to_state      text NOT NULL,
  actor_id      text,
  actor_role    text,
  reason        text,
  occurred_at   timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX workspace_state_history_workspace_idx
  ON app.workspace_state_history (workspace_id, occurred_at DESC);

-- ---------------------------------------------------------------------------
-- Row-level security
-- ---------------------------------------------------------------------------
ALTER TABLE app.customer_organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.customer_organizations FORCE ROW LEVEL SECURITY;
CREATE POLICY customers_in_tenant ON app.customer_organizations
  USING (tenant_id = app.current_tenant_id())
  WITH CHECK (tenant_id = app.current_tenant_id());

ALTER TABLE app.solution_workspaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.solution_workspaces FORCE ROW LEVEL SECURITY;
CREATE POLICY workspaces_in_tenant ON app.solution_workspaces
  USING (tenant_id = app.current_tenant_id())
  WITH CHECK (tenant_id = app.current_tenant_id());

ALTER TABLE app.workspace_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.workspace_members FORCE ROW LEVEL SECURITY;
-- Readable within the tenant, or by the person the row is about — the same
-- bootstrap the tenant memberships need in migration 0002.
CREATE POLICY workspace_members_readable ON app.workspace_members
  FOR SELECT
  USING (tenant_id = app.current_tenant_id() OR user_id = app.current_user_id());
CREATE POLICY workspace_members_writable ON app.workspace_members
  FOR ALL
  USING (tenant_id = app.current_tenant_id())
  WITH CHECK (tenant_id = app.current_tenant_id());

ALTER TABLE app.workspace_state_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.workspace_state_history FORCE ROW LEVEL SECURITY;
CREATE POLICY workspace_history_in_tenant ON app.workspace_state_history
  USING (tenant_id = app.current_tenant_id())
  WITH CHECK (tenant_id = app.current_tenant_id());

-- History is append-only for the same reason audit events are: a corrected
-- history is not a history.
GRANT SELECT, INSERT, UPDATE, DELETE ON
  app.customer_organizations, app.solution_workspaces, app.workspace_members TO app_api;
GRANT SELECT, INSERT ON app.workspace_state_history TO app_api;
REVOKE UPDATE, DELETE, TRUNCATE ON app.workspace_state_history FROM app_api;
GRANT USAGE, SELECT ON SEQUENCE app.workspace_state_history_id_seq TO app_api;

GRANT SELECT ON app.customer_organizations, app.solution_workspaces,
  app.workspace_members, app.workspace_state_history TO app_worker, app_support;

COMMIT;
