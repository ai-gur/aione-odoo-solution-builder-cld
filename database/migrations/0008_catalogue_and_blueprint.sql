-- 0008 Capability catalogue and blueprint
--
-- The catalogue is global platform data, not customer-owned: it describes Odoo,
-- not a business. Blueprints are customer-owned and tenant-scoped.
--
-- A blueprint may be generated only from an approved discovery version
-- (Blueprint §2), and the row carries that reference so the claim is checkable
-- rather than asserted.

BEGIN;

CREATE SCHEMA IF NOT EXISTS catalogue;
GRANT USAGE ON SCHEMA catalogue TO app_api, app_worker, app_support;

CREATE TABLE catalogue.capability_sets (
  id             text PRIMARY KEY CHECK (id LIKE 'cps\_%'),
  scope_key      text NOT NULL,
  baseline_key   text NOT NULL,
  content_digest text NOT NULL,
  loaded_at      timestamptz NOT NULL DEFAULT now(),
  UNIQUE (scope_key, baseline_key, content_digest)
);

CREATE TABLE catalogue.capabilities (
  id                text PRIMARY KEY CHECK (id LIKE 'cap\_%'),
  set_id            text NOT NULL REFERENCES catalogue.capability_sets (id) ON DELETE CASCADE,
  capability_key    text NOT NULL,
  domain            text NOT NULL,
  description       jsonb NOT NULL,
  -- The join to requirements. An explicit key, not a keyword match.
  addresses_topics  text[] NOT NULL DEFAULT '{}',
  modules           text[] NOT NULL DEFAULT '{}',
  edition           text NOT NULL DEFAULT 'community' CHECK (edition IN ('community', 'enterprise')),
  coverage          text NOT NULL DEFAULT 'full' CHECK (coverage IN ('full', 'partial')),
  activation        jsonb NOT NULL DEFAULT '{}'::jsonb,
  security_surfaces text[] NOT NULL DEFAULT '{}',
  evidence          jsonb NOT NULL DEFAULT '[]'::jsonb,
  limitations       jsonb NOT NULL DEFAULT '[]'::jsonb,
  residual_gap      text,
  -- Draft until an AIOne functional reviewer verifies it. A draft capability
  -- may inform a blueprint; it may not carry one to approval (Blueprint §8).
  status            text NOT NULL DEFAULT 'draft'
                    CHECK (status IN ('draft', 'verified', 'deprecated', 'withdrawn')),
  UNIQUE (set_id, capability_key)
);

CREATE INDEX capabilities_topics_idx ON catalogue.capabilities USING gin (addresses_topics);

-- Topics with no capability, recorded deliberately. An absent row would read as
-- "not looked at"; this reads as "looked at, and nothing satisfies it yet".
CREATE TABLE catalogue.unresolved_topics (
  id           text PRIMARY KEY CHECK (id LIKE 'unr\_%'),
  set_id       text NOT NULL REFERENCES catalogue.capability_sets (id) ON DELETE CASCADE,
  topic        text NOT NULL,
  finding      text,
  reason       text NOT NULL,
  candidates   jsonb NOT NULL DEFAULT '[]'::jsonb,
  treatment    text,
  UNIQUE (set_id, topic)
);

-- ---------------------------------------------------------------------------
-- Blueprints
-- ---------------------------------------------------------------------------
CREATE TABLE app.blueprints (
  id                    text PRIMARY KEY CHECK (id LIKE 'bp\_%'),
  tenant_id             text NOT NULL,
  workspace_id          text NOT NULL REFERENCES app.solution_workspaces (id) ON DELETE CASCADE,
  version               integer NOT NULL CHECK (version > 0),

  -- Only an approved discovery version may produce a blueprint.
  discovery_version_id  text NOT NULL REFERENCES discovery.discovery_versions (id),
  capability_set_id     text NOT NULL REFERENCES catalogue.capability_sets (id),
  baseline_key          text NOT NULL,

  state                 text NOT NULL DEFAULT 'draft' CHECK (state IN (
                          'draft', 'under_review', 'changes_requested',
                          'approved', 'superseded', 'withdrawn')),
  generator_version     text NOT NULL,
  content_digest        text,
  created_by            text NOT NULL,
  created_at            timestamptz NOT NULL DEFAULT now(),
  UNIQUE (workspace_id, version)
);

CREATE INDEX blueprints_workspace_idx ON app.blueprints (workspace_id, version DESC);

CREATE TABLE app.fit_assessments (
  id                 text PRIMARY KEY CHECK (id LIKE 'fit\_%'),
  tenant_id          text NOT NULL,
  blueprint_id       text NOT NULL REFERENCES app.blueprints (id) ON DELETE CASCADE,

  requirement_ref    text NOT NULL,
  topic              text NOT NULL,
  classification     text NOT NULL CHECK (classification IN (
                       'standard_fit', 'configuration_fit', 'localization_fit',
                       'studio_fit', 'approved_addon_fit', 'integration_fit',
                       'custom_development_gap', 'process_change_candidate',
                       'partial_fit', 'unsupported', 'unresolved')),
  capability_key     text,
  modules            text[] NOT NULL DEFAULT '{}',
  rationale          jsonb NOT NULL DEFAULT '{}'::jsonb,
  -- Alternatives considered and why they were not selected (Blueprint §12).
  alternatives       jsonb NOT NULL DEFAULT '[]'::jsonb,
  confidence         text NOT NULL DEFAULT 'amber' CHECK (confidence IN ('green', 'amber', 'red')),
  residual_gap       text,
  created_at         timestamptz NOT NULL DEFAULT now(),
  UNIQUE (blueprint_id, requirement_ref)
);

CREATE TABLE app.blueprint_modules (
  id            text PRIMARY KEY CHECK (id LIKE 'bpm\_%'),
  tenant_id     text NOT NULL,
  blueprint_id  text NOT NULL REFERENCES app.blueprints (id) ON DELETE CASCADE,
  technical_name text NOT NULL,
  -- Business-selected modules are justified by a requirement; technical
  -- dependencies are installed because another module requires them
  -- (Blueprint §13). Conflating them hides what the customer actually asked for.
  inclusion     text NOT NULL CHECK (inclusion IN (
                  'business_selected', 'technical_dependency', 'platform_baseline')),
  justified_by  text[] NOT NULL DEFAULT '{}',
  runs_hooks    boolean NOT NULL DEFAULT false,
  UNIQUE (blueprint_id, technical_name)
);

CREATE INDEX blueprint_modules_blueprint_idx ON app.blueprint_modules (blueprint_id);

-- ---------------------------------------------------------------------------
-- Row-level security
-- ---------------------------------------------------------------------------
ALTER TABLE app.blueprints ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.blueprints FORCE ROW LEVEL SECURITY;
CREATE POLICY blueprints_in_tenant ON app.blueprints
  USING (tenant_id = app.current_tenant_id())
  WITH CHECK (tenant_id = app.current_tenant_id());

ALTER TABLE app.fit_assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.fit_assessments FORCE ROW LEVEL SECURITY;
CREATE POLICY fit_assessments_in_tenant ON app.fit_assessments
  USING (tenant_id = app.current_tenant_id())
  WITH CHECK (tenant_id = app.current_tenant_id());

ALTER TABLE app.blueprint_modules ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.blueprint_modules FORCE ROW LEVEL SECURITY;
CREATE POLICY blueprint_modules_in_tenant ON app.blueprint_modules
  USING (tenant_id = app.current_tenant_id())
  WITH CHECK (tenant_id = app.current_tenant_id());

-- The catalogue describes Odoo, not a customer, so it carries no tenant policy.
GRANT SELECT ON catalogue.capability_sets, catalogue.capabilities,
  catalogue.unresolved_topics TO app_api, app_worker, app_support;

GRANT SELECT, INSERT, UPDATE ON app.blueprints TO app_api;
GRANT SELECT, INSERT ON app.fit_assessments, app.blueprint_modules TO app_api;
REVOKE DELETE, TRUNCATE ON app.fit_assessments, app.blueprint_modules FROM app_api;
GRANT SELECT ON app.blueprints, app.fit_assessments, app.blueprint_modules
  TO app_worker, app_support;

COMMIT;
