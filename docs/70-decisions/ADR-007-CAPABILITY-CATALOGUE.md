# ADR-007: Verified Odoo Capability Catalogue Releases

**Status:** Accepted  
**Accepted:** 18 August 2026  
**Approved by:** Nir Bar, founding partner, AIOne  
**Date:** 18 August 2026

## Context

Blueprint and provisioning accuracy depends on exact Odoo 19 modules, dependencies and supported configurations. AI memory and marketing descriptions are insufficient.

## Decision

Build immutable catalogue releases from pinned Odoo core, Enterprise, localization and approved-addon source revisions. Parse manifests without executing addon code, enrich capabilities through expert review, and verify releases through tests.

## Rules

- Exact technical identities come from verified source.
- Addons require pinned revision, license, review and maintenance owner.
- Approved blueprints retain their original catalogue release.
- Start with pilot scope rather than all Odoo applications.

## Amendment 1 — one vendor mirror (18 August 2026)

Three Odoo 19.0 checkouts existed on the build machine, 118 commits apart, two of them tracking the moving `19.0` branch. A catalogue built from one would describe code a deployment from another does not contain, which is exactly the unverified technical claim this ADR exists to prevent.

There is now one vendor mirror, pinned by full revision in `catalogue/pinned-sources.json`, held at a detached revision rather than on a branch. A revision change is a catalogue release requiring re-verification, not an edit. `scripts/workspace_health.py` reports drift without correcting it.

## Consequences

- Significant initial verification work
- Explainable and reproducible blueprint decisions
- Catalogue maintenance becomes a product capability

