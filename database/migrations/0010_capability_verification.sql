-- 0010 Capability verification provenance
--
-- A capability moves from draft to verified when an AIOne functional reviewer
-- confirms that its statement holds against the pinned revision (ADR-007:
-- "enrich capabilities through expert review"). Before this migration the
-- status said that had happened but not who did it or when, which is the same
-- unattributable claim the catalogue exists to prevent: a blueprint reaching
-- green rests on that review, and a reader must be able to ask the reviewer.
--
-- The constraint is the point. A verified row that names nobody cannot be
-- written, so the provenance cannot be lost by a loader that forgets to carry
-- it.

BEGIN;

ALTER TABLE catalogue.capabilities
  ADD COLUMN verified_by   text,
  ADD COLUMN verified_role text,
  ADD COLUMN verified_on   date,
  ADD COLUMN verification_note text;

ALTER TABLE catalogue.capabilities
  ADD CONSTRAINT capabilities_verified_names_its_reviewer
    CHECK (status <> 'verified' OR (verified_by IS NOT NULL AND verified_on IS NOT NULL));

COMMENT ON COLUMN catalogue.capabilities.verified_by IS
  'The functional reviewer who confirmed this capability against the pinned revision.';
COMMENT ON COLUMN catalogue.capabilities.verification_note IS
  'What the reviewer confirmed, and anything the verification deliberately did not cover.';

COMMIT;
