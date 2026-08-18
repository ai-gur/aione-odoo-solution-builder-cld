-- 0011 Archetype decisions between competing capabilities
--
-- Odoo often answers one business need in more than one real way. Purchase
-- approval is the case that forced this (F-05): a threshold checked on the
-- order, or an approval request the order is created from. Both are verified
-- capabilities, and neither is a better implementation of the other — they are
-- different ways for a business to buy.
--
-- Before this table the ranking settled that by sort order, which meant a
-- consulting decision was being made by an alphabetical tie-break and reported
-- as a confident fit. A decision now has to be made by a named person for a
-- named archetype, or it is not made at all and the assessment says so.
--
-- The row is scoped to a capability set, so it is immutable with the set and a
-- blueprint can always be re-read against the decision that applied when it
-- was generated.

BEGIN;

CREATE TABLE catalogue.topic_decisions (
  id                        text PRIMARY KEY CHECK (id LIKE 'tdc\_%'),
  set_id                    text NOT NULL REFERENCES catalogue.capability_sets (id) ON DELETE CASCADE,
  topic                     text NOT NULL,
  preferred_capability_key  text NOT NULL,
  reason                    text NOT NULL,
  -- An unattributed preference is indistinguishable from a sort order, which
  -- is the thing this table exists to remove.
  decided_by                text NOT NULL,
  decided_role              text,
  decided_on                date NOT NULL,
  -- What the rejected capability is still good for. A decision that erases the
  -- alternative loses the reason a later customer might need it.
  alternative_note          text,
  UNIQUE (set_id, topic)
);

GRANT SELECT ON catalogue.topic_decisions TO app_api, app_worker, app_support;

COMMENT ON TABLE catalogue.topic_decisions IS
  'Which capability an archetype prefers when several address one topic, and who decided.';

COMMIT;
