-- 0006 Business facts, requirements and open questions
--
-- Normalisation produces interpretations of what a customer said. The answer
-- itself never changes (0005); these tables hold what the system concluded
-- from it, with the source recorded on every row.
--
-- Three record types stay separate because they mean different things
-- (Discovery §25.8): a fact is something believed true about the business, a
-- requirement is something the solution must do, and an open question is
-- something nobody has answered yet. Collapsing them would let an unanswered
-- question quietly read as a settled fact.
--
-- Derived rows supersede rather than update, so re-running normalisation after
-- a corrected answer leaves the earlier conclusion visible and dated.

BEGIN;

CREATE TABLE discovery.business_facts (
  id                 text PRIMARY KEY CHECK (id LIKE 'fct\_%'),
  tenant_id          text NOT NULL,
  workspace_id       text NOT NULL REFERENCES app.solution_workspaces (id) ON DELETE CASCADE,
  run_id             text NOT NULL REFERENCES discovery.interview_runs (id) ON DELETE CASCADE,

  fact_key           text NOT NULL,
  value              jsonb NOT NULL,

  -- Provenance. Which answers produced this, and which version of which
  -- extractor read them (Discovery §12).
  source_question_keys text[] NOT NULL DEFAULT '{}',
  extraction_method  text NOT NULL DEFAULT 'deterministic',
  extraction_version text NOT NULL,

  confidence         text NOT NULL DEFAULT 'amber' CHECK (confidence IN ('green', 'amber', 'red')),
  verification_state text NOT NULL DEFAULT 'proposed'
                     CHECK (verification_state IN (
                       'proposed', 'confirmed', 'inferred', 'conflicting',
                       'superseded', 'unverified')),

  created_at         timestamptz NOT NULL DEFAULT now(),
  superseded_at      timestamptz
);

CREATE UNIQUE INDEX business_facts_current_idx
  ON discovery.business_facts (run_id, fact_key) WHERE superseded_at IS NULL;
CREATE INDEX business_facts_workspace_idx ON discovery.business_facts (workspace_id);

CREATE TABLE discovery.requirements (
  id                 text PRIMARY KEY CHECK (id LIKE 'req\_%'),
  tenant_id          text NOT NULL,
  workspace_id       text NOT NULL REFERENCES app.solution_workspaces (id) ON DELETE CASCADE,
  run_id             text NOT NULL REFERENCES discovery.interview_runs (id) ON DELETE CASCADE,

  -- Stable, human-facing and stable across revisions: REQ-SAL-001.
  requirement_ref    text NOT NULL,
  domain             text NOT NULL,

  -- Business language, both interface languages. The requirement deliberately
  -- does not name an Odoo module: that decision belongs to the Blueprint
  -- Engine (Discovery §18).
  statement          jsonb NOT NULL,
  rationale          jsonb NOT NULL DEFAULT '{}'::jsonb,
  acceptance_criteria jsonb NOT NULL DEFAULT '[]'::jsonb,

  priority           text NOT NULL DEFAULT 'should'
                     CHECK (priority IN ('must', 'should', 'could', 'wont_this_release')),
  status             text NOT NULL DEFAULT 'proposed'
                     CHECK (status IN ('proposed', 'confirmed', 'rejected', 'superseded')),
  confidence         text NOT NULL DEFAULT 'amber' CHECK (confidence IN ('green', 'amber', 'red')),

  source_question_keys text[] NOT NULL DEFAULT '{}',
  generator_version  text NOT NULL,

  created_at         timestamptz NOT NULL DEFAULT now(),
  superseded_at      timestamptz
);

CREATE UNIQUE INDEX requirements_current_idx
  ON discovery.requirements (run_id, requirement_ref) WHERE superseded_at IS NULL;
CREATE INDEX requirements_workspace_idx ON discovery.requirements (workspace_id);

CREATE TABLE discovery.open_questions (
  id                 text PRIMARY KEY CHECK (id LIKE 'oqs\_%'),
  tenant_id          text NOT NULL,
  workspace_id       text NOT NULL REFERENCES app.solution_workspaces (id) ON DELETE CASCADE,
  run_id             text NOT NULL REFERENCES discovery.interview_runs (id) ON DELETE CASCADE,

  topic_key          text NOT NULL,
  question           jsonb NOT NULL,
  severity           text NOT NULL DEFAULT 'medium'
                     CHECK (severity IN ('low', 'medium', 'high', 'critical')),
  -- A blocking item prevents discovery approval (Discovery §16.4). It is a
  -- property of the item, not a judgement made later at the gate.
  blocking           boolean NOT NULL DEFAULT false,
  owner_role         text,

  source_question_keys text[] NOT NULL DEFAULT '{}',
  generator_version  text NOT NULL,
  state              text NOT NULL DEFAULT 'open'
                     CHECK (state IN ('open', 'answered', 'accepted_risk', 'superseded')),
  resolution         jsonb,

  created_at         timestamptz NOT NULL DEFAULT now(),
  superseded_at      timestamptz
);

CREATE UNIQUE INDEX open_questions_current_idx
  ON discovery.open_questions (run_id, topic_key) WHERE superseded_at IS NULL;
CREATE INDEX open_questions_workspace_idx ON discovery.open_questions (workspace_id);

-- ---------------------------------------------------------------------------
-- Row-level security
-- ---------------------------------------------------------------------------
ALTER TABLE discovery.business_facts ENABLE ROW LEVEL SECURITY;
ALTER TABLE discovery.business_facts FORCE ROW LEVEL SECURITY;
CREATE POLICY facts_in_tenant ON discovery.business_facts
  USING (tenant_id = app.current_tenant_id())
  WITH CHECK (tenant_id = app.current_tenant_id());

ALTER TABLE discovery.requirements ENABLE ROW LEVEL SECURITY;
ALTER TABLE discovery.requirements FORCE ROW LEVEL SECURITY;
CREATE POLICY requirements_in_tenant ON discovery.requirements
  USING (tenant_id = app.current_tenant_id())
  WITH CHECK (tenant_id = app.current_tenant_id());

ALTER TABLE discovery.open_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE discovery.open_questions FORCE ROW LEVEL SECURITY;
CREATE POLICY open_questions_in_tenant ON discovery.open_questions
  USING (tenant_id = app.current_tenant_id())
  WITH CHECK (tenant_id = app.current_tenant_id());

GRANT SELECT, INSERT, UPDATE ON
  discovery.business_facts, discovery.requirements, discovery.open_questions TO app_api;
REVOKE DELETE, TRUNCATE ON
  discovery.business_facts, discovery.requirements, discovery.open_questions FROM app_api;
GRANT SELECT ON
  discovery.business_facts, discovery.requirements, discovery.open_questions
  TO app_worker, app_support;

COMMIT;
