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
├── aione-odoo-solution-builder-cld/ # This product
├── AIOne Internal Odoo 19e/         # The Foundation (FOUNDATION-VERSION 1.1.0)
└── AIOne Odoo Vendor/odoo/
    ├── odoo/                        # Pinned Odoo core checkout
    └── enterprise/                  # Pinned Enterprise checkout
```

**One vendor mirror, pinned by revision.** `catalogue/pinned-sources.json` records the
exact core and Enterprise revisions every catalogue release and manifest is built
against. Both delivery routes — a remote server and an offline on-premise package —
resolve to those revisions, so a blueprint approved against a baseline describes the
system either way (ADR-007, ADR-008).

The Foundation holds no Odoo source of its own. It mounts core and Enterprise
read-only and executes `odoo-bin` from the mount, so the pinned revisions are the code
that actually runs.

Paths are supplied through `ODOO_FOUNDATION_PATH`, `ODOO_CORE_PATH` and
`ODOO_ENTERPRISE_PATH`. Verify them with:

```text
python scripts/run.py workspace-health
```

The check is strictly non-mutating: it never fetches or checks out, because reading a
workspace must not change it. A drifted revision is reported rather than corrected —
moving a baseline is a catalogue release, not an edit.

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

The canonical command interface, decided 18 August 2026 under the
developer-experience clause below:

```text
python scripts/run.py bootstrap
python scripts/run.py stack-up
python scripts/run.py stack-down
python scripts/run.py db-migrate
python scripts/run.py db-status
python scripts/run.py db-reset
python scripts/run.py test
python scripts/run.py test-contract
python scripts/run.py test-integration
python scripts/run.py test-api
python scripts/run.py api-dev
python scripts/run.py worker-dev
```

Sandbox commands (`sandbox-up`, `sandbox-test`, `sandbox-down`) join the same
interface when the Docker sandbox driver arrives in Increment 5.

**Why not `make`.** `make` is absent from a stock Windows installation, and the
first developers on this project are on Windows. Installing it would add a
system-level dependency, and per-machine prerequisites are exactly what a
bootstrap command exists to avoid. Python is already a hard requirement — the
domain service and workers are written in it — so the commands live in
`scripts/run.py` and need nothing that running the product does not already
need. A Makefile wrapper was tried and removed: two entry points must be kept
in sync, and the second one earns nothing.

Command names may change through a further accepted developer-experience decision, but README and CI must use one canonical interface.

