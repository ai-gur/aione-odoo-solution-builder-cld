#!/usr/bin/env python
"""Local development fixture.

One AIOne tenant, two test users, one customer and one workspace, so a
developer can open the interface and see something real without clicking
through setup first.

Sanitized and obviously fake, per TESTING-STANDARDS.md: no production customer
data, ever, including in a demo. Idempotent — running it twice changes nothing.

    python scripts/run.py db-seed-dev
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.db import psql  # noqa: E402

# A Windows console defaults to cp1252 and cannot print Hebrew. Every script
# here may report customer names, so make stdout UTF-8 rather than avoiding
# the alphabet the product is primarily written in.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TENANT = "ten_DEV0000000000000000001"
MANAGER = "usr_DEV0000000000000000001"
CONSULTANT = "usr_DEV0000000000000000002"
CUSTOMER = "cus_DEV0000000000000000001"
WORKSPACE = "wsp_DEV0000000000000000001"

SEED = f"""
INSERT INTO app.tenants (id, name) VALUES ('{TENANT}', 'AIOne')
  ON CONFLICT (id) DO NOTHING;

-- Conflict on the natural key, not the surrogate one: an earlier test run may
-- have created these subjects with different identifiers.
INSERT INTO app.users (id, auth_subject, email, display_name) VALUES
  ('{MANAGER}', 'auth|dev-manager', 'manager@example.test', 'Dana — Account Manager'),
  ('{CONSULTANT}', 'auth|dev-lead', 'lead@example.test', 'Yossi — Team Lead')
  ON CONFLICT (auth_subject) DO NOTHING;

-- These subjects are deliberately distinct from the ones the test suites use.
-- Tests own auth|test-*, and deleting a user cascades to their memberships, so
-- a shared subject means running the tests quietly logs the developer out of
-- their own fixture.
--
-- The Account Manager holds the consultant role too, so one local sign-in can
-- both create a workspace and run its interview. In a real tenant these are
-- different people.
INSERT INTO app.memberships (id, tenant_id, user_id, role_key)
SELECT 'mbr_DEV000000000000000000' || row_number() OVER (), '{TENANT}', u.id, r.role_key
  FROM app.users u
  JOIN (VALUES ('auth|dev-manager', 'account_owner'), ('auth|dev-manager', 'consultant'),
               ('auth|dev-lead', 'solution_owner'), ('auth|dev-lead', 'consultant'))
       AS r(subject, role_key)
    ON r.subject = u.auth_subject
  ON CONFLICT (tenant_id, user_id, role_key) DO NOTHING;

INSERT INTO app.customer_organizations
  (id, tenant_id, legal_name, trading_name, customer_code, countries, industries)
VALUES ('{CUSTOMER}', '{TENANT}', 'דוגמה הפצות בע"מ', 'דוגמה הפצות', 'C0001',
        ARRAY['IL'], ARRAY['wholesale_distribution'])
  ON CONFLICT (id) DO NOTHING;

INSERT INTO app.solution_workspaces
  (id, tenant_id, customer_id, name, business_scope, primary_locale, secondary_locale,
   discovery_mode, state)
VALUES ('{WORKSPACE}', '{TENANT}', '{CUSTOMER}', 'ERP ראשי',
        'הפצה סיטונאית: מכירות, רכש, מלאי וגבולות הנהלת חשבונות',
        'he_IL', 'en_US', 'quick_start', 'discovering')
  ON CONFLICT (id) DO NOTHING;

INSERT INTO app.workspace_state_history
  (tenant_id, workspace_id, from_state, to_state, actor_id, actor_role, reason)
SELECT '{TENANT}', '{WORKSPACE}', NULL, 'discovering', '{MANAGER}', 'account_owner', 'local fixture'
 WHERE NOT EXISTS (
   SELECT 1 FROM app.workspace_state_history WHERE workspace_id = '{WORKSPACE}'
 );
"""

if __name__ == "__main__":
    psql(SEED)
    print("local fixture ready")
    print(f"  tenant    {TENANT}  AIOne")
    print(f"  customer  {CUSTOMER}  דוגמה הפצות בע\"מ")
    print(f"  workspace {WORKSPACE}  ERP ראשי")
    print("  sign in as Dana (Account Manager) or Yossi (Team Lead)")
