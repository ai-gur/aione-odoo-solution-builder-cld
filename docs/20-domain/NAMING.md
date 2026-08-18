# Product, Repository and Namespace Naming

**Version:** 0.1
**Date:** 18 August 2026
**Status:** Proposed
**Resolves:** readiness blocker B8 (the product and repository name was never fixed)
**Authority:** design note under `DESIGN-AUTHORITY.md` — naming sits inside accepted boundaries. It is recorded here because five different names are in circulation and they are about to be baked into package registries, container images and Odoo external identifiers, where renaming is expensive.

## 1. Names in circulation

| Name | Where |
| --- | --- |
| AIOne Odoo Solution Builder | Constitution, README, AGENTS.md — the majority usage |
| AIOne Odoo Builder | `ODOO-SOLUTION-BUILDER-DESIGN.md` style reference |
| `odoo-solution-builder/` | MVP Architecture §6 workspace tree |
| `aione-odoo-solution-builder/` | LOCAL-DEVELOPMENT.md workspace tree |
| `aione-odoo-solution-builder-cld` | The repository in use |

## 2. Decision

### Product name

**AIOne Odoo Solution Builder** in full, on first use and in customer-facing material.
**Solution Builder** as the short form in internal documentation and interface chrome.

"AIOne Odoo Builder" is retired; the design style reference requires the correction.

The Hebrew product name is not translated. It appears as `AIOne Odoo Solution Builder` in Latin script inside Hebrew text, wrapped per the bidirectional rule in the design system §6.3.

### Repository names

| Repository | Purpose |
| --- | --- |
| `aione-odoo-solution-builder-cld` | **The Solution Builder repository.** Control plane, provisioning handlers, catalogue and docs. The single repository for this implementation |
| `odoo-19-enterprise-foundation` | Existing reusable Foundation |
| `aione-odoo-addons` | Shared reviewed AIOne addons (ADR-013) |
| `aione-customer-<code>-odoo` | Conditional per-customer code repository, using the internal customer code rather than a customer name (Portfolio §4.5) |

The `-cld` suffix is historical and carries no meaning in the product. Because nothing in the codebase, documentation or configuration may depend on a repository or directory name — the rule below — renaming the GitHub repository later is a one-time, near-zero-cost change if AIOne ever wants the suffix gone.

MVP Architecture §6 shows `odoo-solution-builder/` in the workspace tree and requires amendment to the repository name above.

The documented workspace topology uses the repository name. A local checkout may sit in a differently named directory; no script, document or configuration file may depend on the local directory name — paths come from the environment variables in `.env.example`.

### Namespaces

| Surface | Convention | Example |
| --- | --- | --- |
| npm packages | `@aione/` scope | `@aione/contracts`, `@aione/design-system` |
| Python distributions | `aione-` prefix | `aione-domain-api`, `aione-provisioning` |
| Python import roots | `aione_` prefix | `aione_domain`, `aione_provisioning` |
| Container images | `aione/solution-builder-<component>` | `aione/solution-builder-worker` |
| Database schemas | `app`, `audit`, `jobs` | — |
| Environment variables | Screaming snake, no product prefix | `DOMAIN_API_BASE_URL` |
| Correlation and job keys | Prefixed ULID per ADR-015 | `run_01J...` |
| Odoo external identifiers for managed records | `aione_sb.<logical_key>` | `aione_sb.company_main` |
| Odoo custom module prefix, if one is ever required | `aione_` | `aione_wholesale_pricing` |

The `aione_sb` external-identifier prefix is the one entry here that is genuinely expensive to change: it is written into customer databases by provisioning handlers and is the identity that makes reruns idempotent (ADR-009, Provisioning §12). It must be fixed before the first handler ships, and it must never collide with an Odoo core, Enterprise, localization or third-party addon prefix.

## 3. Rules

- One canonical product name in customer-facing text. Do not mix the full and short forms in the same document.
- No document, script or CI job may hard-code a local directory path or the `-cld` repository name.
- A customer name never appears in a repository name; use the internal customer code.
- The external-identifier prefix `aione_sb` is reserved and may not be used for anything other than provisioning-managed records.

## 4. Required amendments

| Document | Change |
| --- | --- |
| `ODOO-SOLUTION-BUILDER-DESIGN.md` | "AIOne Odoo Builder" becomes "AIOne Odoo Solution Builder" |
| MVP Architecture §6 | Workspace tree root becomes `aione-odoo-solution-builder/`, and `aione-odoo-addons/` is added |
| `README.md` | State the canonical product and repository name |
