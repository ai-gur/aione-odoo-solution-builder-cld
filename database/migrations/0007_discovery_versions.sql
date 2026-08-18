-- 0007 Approved discovery versions
--
-- The first approval gate in the product (Constitution §11 gate 1, Discovery
-- §16.4). An approved discovery version is the immutable input the Blueprint
-- Engine consumes: it may read only an approved version, and later answers
-- create a new version rather than changing this one.
--
-- Immutability is enforced by privilege, not by intention. The API role may
-- INSERT and SELECT here and nothing else — no UPDATE, no DELETE. An approved
-- version that could be edited afterwards would make every downstream
-- traceability claim unprovable.

BEGIN;

CREATE TABLE discovery.discovery_versions (
  id             text PRIMARY KEY CHECK (id LIKE 'dsv\_%'),
  tenant_id      text NOT NULL,
  workspace_id   text NOT NULL REFERENCES app.solution_workspaces (id) ON DELETE CASCADE,
  run_id         text NOT NULL REFERENCES discovery.interview_runs (id) ON DELETE CASCADE,

  version        integer NOT NULL CHECK (version > 0),

  -- The complete snapshot: answers as given, plus the facts, requirements and
  -- open questions derived from them at approval time.
  content        jsonb NOT NULL,
  -- sha256 over the RFC 8785 canonical form of content (ADR-015). Recomputable
  -- by anyone holding the snapshot, in either language.
  content_digest text NOT NULL,

  definition_key     text NOT NULL,
  definition_version integer NOT NULL,

  approved_by    text NOT NULL,
  approved_role  text NOT NULL,
  approved_at    timestamptz NOT NULL DEFAULT now(),

  UNIQUE (workspace_id, version)
);

CREATE INDEX discovery_versions_workspace_idx
  ON discovery.discovery_versions (workspace_id, version DESC);

ALTER TABLE discovery.discovery_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE discovery.discovery_versions FORCE ROW LEVEL SECURITY;
CREATE POLICY discovery_versions_in_tenant ON discovery.discovery_versions
  USING (tenant_id = app.current_tenant_id())
  WITH CHECK (tenant_id = app.current_tenant_id());

GRANT SELECT, INSERT ON discovery.discovery_versions TO app_api;
REVOKE UPDATE, DELETE, TRUNCATE ON discovery.discovery_versions FROM app_api;
GRANT SELECT ON discovery.discovery_versions TO app_worker, app_support;

COMMIT;
