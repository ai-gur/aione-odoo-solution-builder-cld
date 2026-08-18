-- 0009 Requirement topic
--
-- The join between a requirement and the capability catalogue is an explicit
-- key, not a keyword match on the statement (Blueprint §9.1). Normalisation
-- produces it; without a column it never reached the approved snapshot, and
-- every requirement mapped to nothing.

BEGIN;

ALTER TABLE discovery.requirements ADD COLUMN topic text NOT NULL DEFAULT '';
CREATE INDEX requirements_topic_idx ON discovery.requirements (topic);

COMMIT;
