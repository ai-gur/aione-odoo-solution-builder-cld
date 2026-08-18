# Deferred Decisions Register

**Version:** 0.1
**Date:** 18 August 2026
**Status:** Accepted  
**Accepted:** 18 August 2026  
**Approved by:** Nir Bar, founding partner, AIOne  
**Purpose:** Decisions consciously postponed, with the point at which each must be settled. A deferred decision is not an open risk to be rediscovered later; it is recorded here so that the increment which depends on it cannot start unnoticed.

Each entry names the decision, why it is safe to defer now, and the **trigger** — the concrete event that ends the deferral. When a trigger is reached, the entry becomes an ADR, a change request or a specification amendment.

| # | Decision | Deferred because | Trigger | Owner |
| --- | --- | --- | --- | --- |
| D-01 | **Data residency, processor arrangements and privacy position** — where control-plane data and evidence are hosted, and the Israeli Privacy Protection Law and GDPR position for customer confidential data | No real customer data exists yet. Increment 0 uses sanitized local fixtures only, so nothing is stored that the decision would govern | First storage of real customer discovery, evidence or contact data — that is, the start of Increment 1, or any pilot using a real customer | Product owner |
| D-02 | **Onboarding of existing Odoo customers** — reverse discovery from a running database and adoption of an existing environment as an accepted baseline | Every approved specification starts from a blank interview and ends at a fresh sandbox. The capability has no spec | Before the tenancy model is treated as final, or the first attempt to bring a live AIOne customer into the portal | Product owner |
| D-03 | **Dark theme** | Light-only is sufficient for the MVP and the token structure already supports adding it | First request for a dark interface, or any customer-facing accessibility requirement that implies it | Design authority |
| D-04 | **Charting palette** for fit dimensions and portfolio analytics | No chart ships before Increment 4 | First analytics or scoring visualization | Design authority |
| D-05 | **Print and PDF styling** for blueprint, release package and traceability reports | Those are customer deliverables that arrive with Increments 4 and 7 | First generated customer-facing document | Design authority |
| D-06 | **Accessibility coordinator appointment** — whether AIOne's headcount triggers the duty to appoint a named רכז נגישות, and who the contact is | The accessibility statement page ships with the customer portal, not with the skeleton | Before the portal is exposed to any real customer | Product owner |
| D-07 | **Production provisioning scope** | Explicitly excluded from the MVP by the constitution and every engine specification | Any request to deploy to a live customer environment. Requires a new ADR and a security review, never an implementation decision | Design authority |
| D-08 | **Odoo.sh and alternative hosting drivers** | ADR-008 commits to one Docker driver first and keeps the driver contract provider-neutral | A customer environment that cannot run on AIOne-controlled Docker infrastructure | Design authority |

## Rules

- An entry may be added only with a trigger. "Later" is not a trigger.
- Reaching a trigger blocks the dependent work until the decision is recorded, in the form the change-control section of `DESIGN-AUTHORITY.md` requires.
- Removing an entry requires naming the record that superseded it.
