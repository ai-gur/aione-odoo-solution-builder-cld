# MVP Architecture Summary

## Style

Modular control-plane monolith with independently deployed web, Python API and Python worker processes.

## Authority

- PostgreSQL stores authoritative business and workflow state.
- Redis-compatible queue transports work but does not define final state.
- Object storage holds evidence and generated artifacts.
- Approved version snapshots are immutable.
- Odoo catalogue releases pin technical capability evidence.

## Main modules

- Identity and Tenancy
- Customer Engagement
- Discovery and Evidence
- Requirements
- Capability Catalogue
- Blueprint
- Manifest
- Environment and Provisioning
- Validation and Deviations
- Notifications
- Audit
- AI Gateway

## Trust boundaries

1. Customer browser to web application
2. Web application to control-plane API
3. Control plane to AI provider through the AI gateway
4. Control plane to isolated evidence workers
5. Control plane worker to one sandbox runner
6. Sandbox runner to one Odoo database and runtime

No sandbox can call another sandbox or approve its own manifest.

## Data flow

```text
Interview answers and evidence
  -> normalized proposals
  -> approved discovery version
  -> fit assessments and decisions
  -> approved blueprint version
  -> approved deployment manifest
  -> provisioning plan and run
  -> validation results and deviations
  -> released sandbox
```

## Deployment

- Next.js may run on Vercel or an equivalent managed web platform.
- PostgreSQL, authentication and storage may run on Supabase or equivalent services.
- Python API and workers require long-running Docker-capable hosting.
- Odoo sandboxes run on controlled Docker infrastructure based on the Foundation.
- Exact providers are adapters, not domain assumptions.

## Initial pilot

Israeli B2B wholesale distribution with CRM, Sales, Purchase, Inventory and approved accounting boundaries.

