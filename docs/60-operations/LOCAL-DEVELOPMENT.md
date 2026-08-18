# Local Development Topology

## Goal

One documented command should start the control-plane dependencies after Increment 0. The exact command is selected during implementation, but the topology is fixed.

## Processes

- Next.js web application
- Python FastAPI domain service
- Python background worker
- PostgreSQL control database
- Redis-compatible queue transport
- S3-compatible local object storage or managed development bucket
- Optional local mail capture
- Existing Odoo 19 Enterprise Foundation sandbox stack

## Workspace requirements

Keep repositories separate:

```text
workspace/
├── aione-odoo-solution-builder/     # This product
├── odoo-19-enterprise-foundation/   # Reusable Foundation
├── aione-odoo-addons/               # Shared reviewed AIOne addons (ADR-013)
├── odoo/                            # Pinned Odoo core checkout
└── enterprise/                      # Pinned Enterprise checkout
```

Four repositories are recorded by the workspace health command: Foundation, AIOne addons, Odoo core and Enterprise. Their paths are supplied through `ODOO_FOUNDATION_PATH`, `AIONE_ADDONS_PATH`, `ODOO_CORE_PATH` and `ODOO_ENTERPRISE_PATH`.

Paths are supplied through `.env.local`, which is never committed.

## Local secret policy

- `.env.example` documents names only.
- Developers create local values in `.env.local` or an approved local secret mechanism.
- Tests use generated disposable secrets.
- No production key is required for ordinary local tests.
- AI-dependent tests use mocks by default and a separate explicitly enabled integration suite.

## Sandbox policy

- Use a disposable Odoo database per integration run where practical.
- Pin Odoo and Enterprise revisions.
- Keep sandbox files and databases outside git.
- Do not expose Odoo database-management endpoints publicly.
- Clean up only resources carrying the exact test run identifier.

## Expected developer commands

Increment 0 should implement commands equivalent to:

```text
make bootstrap
make dev
make check
make test
make test-contract
make test-integration
make sandbox-up
make sandbox-test
make sandbox-down
```

Command names may change through an accepted developer-experience decision, but README and CI must use one canonical interface.

