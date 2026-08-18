# AIOne Odoo Solution Builder

A standalone AIOne control plane that interviews business customers, produces approved Odoo Enterprise 19 solution blueprints, and provisions validated development or demonstration sandboxes.

## Current scope

The MVP covers:

- Quick Start and Guided business discovery;
- source-linked facts, requirements, assumptions and conflicts;
- a verified Odoo 19 capability catalogue;
- explainable blueprint generation and approval;
- immutable deployment manifests;
- isolated Docker-based Odoo Enterprise 19 sandboxes;
- deterministic configuration and automated validation;
- Hebrew RTL as the primary product experience and English US as secondary.

Production deployment, live migration and automatic deployment of AI-generated custom modules are excluded.

## Architecture

- Next.js and TypeScript for customer and consultant interfaces
- Python and FastAPI for domain, AI and catalogue services
- PostgreSQL as the authoritative control database
- Redis-compatible queue transport with durable job state in PostgreSQL
- Python workers for evidence processing, blueprint generation and provisioning
- Docker-based Odoo 19 Enterprise sandbox runtime based on the existing Foundation
- Shared versioned contracts consumed by TypeScript and Python

The control plane is a modular monolith with separate worker processes. Customer Odoo databases are isolated targets, never the control authority.

## Repository map

```text
apps/web                 Next.js interface and BFF
apps/domain-api          FastAPI domain and AI service
apps/worker              Background workers
packages/contracts       Shared schemas and generated types
packages/design-system   Accessible bilingual UI
packages/rules           Deterministic rules
catalogue                Odoo capability catalogue
provisioning             Sandbox drivers, handlers and validators
database                 Migrations, policies and seeds
docs                     Governance, architecture and handoffs
infrastructure           Control-plane and sandbox deployment
tests                    Contract, integration and end-to-end tests
```

## Authoritative documents

Read in this order:

1. `AGENTS.md`
2. `docs/00-governance/DESIGN-AUTHORITY.md`
3. `docs/10-product/SOURCE-DOCUMENTS.md`
4. `docs/30-architecture/ARCHITECTURE.md`
5. `docs/70-decisions/ADR-INDEX.md`
6. `docs/80-handoff/INCREMENT-0.md`

The full product design specifications named in `SOURCE-DOCUMENTS.md` must be added unchanged before implementation begins.

## Setup status

This package is an implementation bootstrap, not a running application. Increment 0 creates the executable project skeleton and local environment.

## Working rules

- Standard Odoo before Studio, addon, integration or custom code
- No unverified Odoo module or field claims
- No secret values in repository files or manifests
- No production provisioning in the MVP
- No cross-customer database or sandbox access
- Every applied configuration traces to requirement, decision, manifest and approval
- Architecture changes require an ADR or change request

## First pilot

The first end-to-end pilot is an Israeli B2B wholesale distributor covering CRM, Sales, Purchase, Inventory and approved Israeli accounting boundaries.

