-- 0005 Discovery: interview definitions, runs and answers
--
-- The invariants this schema exists to hold (Discovery Engine §12, §25):
--
--   An answer preserves the original wording, author, source and timestamp.
--   Normalisation produces a separate interpretation; it never overwrites what
--   the customer actually said. Revising an answer supersedes the old row
--   rather than updating it, so "what did they tell us in March" stays
--   answerable in September.
--
-- Definitions are versioned and immutable once published. A workspace pins the
-- version it started with, so improving the global questionnaire never rewrites
-- a customer's history (Portfolio §5).

BEGIN;

CREATE SCHEMA IF NOT EXISTS discovery;
GRANT USAGE ON SCHEMA discovery TO app_api, app_worker, app_support;

-- ---------------------------------------------------------------------------
-- Versioned definitions. Global to the platform, not tenant-owned.
-- ---------------------------------------------------------------------------
CREATE TABLE discovery.interview_definitions (
  id            text PRIMARY KEY CHECK (id LIKE 'idf\_%'),
  definition_key text NOT NULL,
  version       integer NOT NULL CHECK (version > 0),
  mode          text NOT NULL CHECK (mode IN ('quick_start', 'guided', 'comprehensive')),
  title         jsonb NOT NULL,
  status        text NOT NULL DEFAULT 'draft'
                CHECK (status IN ('draft', 'published', 'superseded', 'withdrawn')),
  -- Digest of the definition and its questions, computed with the shared
  -- canonicalizer (ADR-015). A pinned run can prove which content it used.
  content_digest text,
  published_at  timestamptz,
  created_at    timestamptz NOT NULL DEFAULT now(),
  UNIQUE (definition_key, version)
);

CREATE TABLE discovery.question_definitions (
  id                text PRIMARY KEY CHECK (id LIKE 'qdf\_%'),
  definition_id     text NOT NULL REFERENCES discovery.interview_definitions (id) ON DELETE CASCADE,
  question_key      text NOT NULL,
  order_index       integer NOT NULL,
  domain            text NOT NULL,
  concept           text,

  prompt            jsonb NOT NULL,          -- {"he_IL": "...", "en_US": "..."}
  help_text         jsonb NOT NULL DEFAULT '{}'::jsonb,
  answer_type       text NOT NULL CHECK (answer_type IN (
                      'boolean_tristate', 'single_select', 'multi_select', 'short_text',
                      'long_narrative', 'integer', 'decimal', 'currency_band', 'percentage',
                      'date', 'date_range', 'ranked_list', 'repeating_group', 'matrix',
                      'evidence_reference', 'system_reference')),
  options           jsonb NOT NULL DEFAULT '[]'::jsonb,

  -- Deterministic, reviewed rule (Discovery §11). Never generated text.
  applicability     jsonb NOT NULL DEFAULT '{"always": true}'::jsonb,
  required_policy   text NOT NULL DEFAULT 'optional'
                    CHECK (required_policy IN ('required', 'conditional', 'optional')),

  risk_weight       integer NOT NULL DEFAULT 0,
  complexity_weight integer NOT NULL DEFAULT 0,
  evidence_policy   text NOT NULL DEFAULT 'optional'
                    CHECK (evidence_policy IN ('required', 'optional', 'not_applicable')),

  UNIQUE (definition_id, question_key)
);

CREATE INDEX question_definitions_order_idx
  ON discovery.question_definitions (definition_id, order_index);

-- ---------------------------------------------------------------------------
-- Runs and answers. Tenant-owned, workspace-scoped.
-- ---------------------------------------------------------------------------
CREATE TABLE discovery.interview_runs (
  id            text PRIMARY KEY CHECK (id LIKE 'run\_%'),
  tenant_id     text NOT NULL,
  workspace_id  text NOT NULL REFERENCES app.solution_workspaces (id) ON DELETE CASCADE,
  -- Pinned: a newer questionnaire does not retroactively change this run.
  definition_id text NOT NULL REFERENCES discovery.interview_definitions (id),
  state         text NOT NULL DEFAULT 'draft' CHECK (state IN (
                  'draft', 'invited', 'in_progress', 'waiting_for_others',
                  'clarification_required', 'ready_for_review', 'under_consultant_review',
                  'changes_requested', 'approved_for_blueprint', 'superseded', 'cancelled')),
  started_by    text,
  started_at    timestamptz NOT NULL DEFAULT now(),
  completed_at  timestamptz
);

CREATE INDEX interview_runs_workspace_idx ON discovery.interview_runs (workspace_id);

CREATE TABLE discovery.answers (
  id                 text PRIMARY KEY CHECK (id LIKE 'ans\_%'),
  tenant_id          text NOT NULL,
  run_id             text NOT NULL REFERENCES discovery.interview_runs (id) ON DELETE CASCADE,
  question_key       text NOT NULL,

  -- What the person actually said, exactly. Never rewritten.
  raw_value          jsonb NOT NULL,
  -- The system's structured interpretation, which may be corrected later
  -- without touching raw_value.
  normalized_value   jsonb,

  answered_by        text,
  answer_source      text NOT NULL DEFAULT 'customer'
                     CHECK (answer_source IN ('customer', 'consultant', 'document', 'system')),
  confidence         text NOT NULL DEFAULT 'amber' CHECK (confidence IN ('green', 'amber', 'red')),
  verification_state text NOT NULL DEFAULT 'proposed'
                     CHECK (verification_state IN (
                       'proposed', 'confirmed', 'inferred', 'conflicting',
                       'superseded', 'unverified')),

  -- Revision, not mutation: a new answer supersedes its predecessor and both
  -- rows remain.
  supersedes_id      text REFERENCES discovery.answers (id),
  superseded_at      timestamptz,
  created_at         timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX answers_run_idx ON discovery.answers (run_id, question_key);
-- Exactly one live answer per question per run.
CREATE UNIQUE INDEX answers_current_idx
  ON discovery.answers (run_id, question_key) WHERE superseded_at IS NULL;

-- ---------------------------------------------------------------------------
-- Row-level security
-- ---------------------------------------------------------------------------
ALTER TABLE discovery.interview_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE discovery.interview_runs FORCE ROW LEVEL SECURITY;
CREATE POLICY runs_in_tenant ON discovery.interview_runs
  USING (tenant_id = app.current_tenant_id())
  WITH CHECK (tenant_id = app.current_tenant_id());

ALTER TABLE discovery.answers ENABLE ROW LEVEL SECURITY;
ALTER TABLE discovery.answers FORCE ROW LEVEL SECURITY;
CREATE POLICY answers_in_tenant ON discovery.answers
  USING (tenant_id = app.current_tenant_id())
  WITH CHECK (tenant_id = app.current_tenant_id());

-- Definitions carry no customer content and are readable by any service role.
GRANT SELECT ON discovery.interview_definitions, discovery.question_definitions
  TO app_api, app_worker, app_support;

GRANT SELECT, INSERT, UPDATE ON discovery.interview_runs TO app_api;
-- Answers may be inserted and superseded, never deleted: the record of what a
-- customer said is not a working document.
GRANT SELECT, INSERT, UPDATE ON discovery.answers TO app_api;
REVOKE DELETE, TRUNCATE ON discovery.answers FROM app_api;
GRANT SELECT ON discovery.interview_runs, discovery.answers TO app_worker, app_support;

COMMIT;
