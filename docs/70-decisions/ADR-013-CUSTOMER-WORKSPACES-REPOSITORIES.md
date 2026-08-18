# ADR-013: Customer Workspaces and Conditional Repositories

**Status:** Proposed  
**Date:** 18 August 2026

## Context

AIOne needs to manage many customers over years, recap accepted solutions and process later changes. Git is appropriate for software code but poor as the authoritative store for questionnaires, evidence, approvals and customer history.

## Decision

Operate one shared Solution Builder platform. Give each customer one or more isolated Solution Workspaces with immutable Customer Solution Baselines. Store discovery, requirements, blueprints, manifests, approvals and history in the control plane and object storage.

Create a private customer Git repository only when customer-specific code, integrations or migration software must be maintained separately. Configuration-only customers have no customer repository. Shared reusable code belongs in the reviewed AIOne addons repository.

## Rules

- Every environment links to exact blueprint, manifest, catalogue and software revisions.
- Customer-specific repositories contain code, tests and technical documentation only.
- Customer evidence, database dumps, personal data and secrets are prohibited in Git.
- Repository releases use immutable tags, commit SHAs and artifact digests.
- Change requests start from a named accepted baseline and produce a new baseline.
- Historical baselines are never overwritten.

## Consequences

- The administrator portal, not GitHub, is the authoritative customer record.
- Standard customers require less repository administration.
- Customer-specific code gains clear ownership, access and release isolation.
- The platform requires a repository and software-provenance registry.
