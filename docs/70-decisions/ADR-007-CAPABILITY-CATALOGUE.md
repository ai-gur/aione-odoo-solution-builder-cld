# ADR-007: Verified Odoo Capability Catalogue Releases

**Status:** Proposed  
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

## Consequences

- Significant initial verification work
- Explainable and reproducible blueprint decisions
- Catalogue maintenance becomes a product capability

