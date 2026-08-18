# AIOne Odoo Solution Builder

## MVP Application Architecture and Delivery Plan

**Version:** 0.1  
**Date:** 18 August 2026  
**Status:** Initial design baseline  
**Depends on:** Product Constitution, Discovery Engine, Blueprint Engine and Provisioning Engine specifications

## 1. Architectural outcome

The MVP is a standalone, multi-customer AIOne control plane that:

1. conducts adaptive business discovery;
2. stores approved structured requirements;
3. maps requirements to a verified Odoo Enterprise 19 capability catalogue;
4. produces versioned solution blueprints;
5. compiles approved blueprints into deployment manifests;
6. provisions isolated self-hosted Odoo 19 Enterprise sandboxes based on the existing Foundation;
7. validates and releases those sandboxes for customer review.

The control plane and customer Odoo databases are separate security and operational boundaries.

## 2. Recommended MVP stack

| Layer | Recommended technology | Responsibility |
| --- | --- | --- |
| Web application | Next.js with TypeScript | Customer and consultant experiences, server-side rendering and BFF endpoints |
| UI system | Tailwind CSS and shadcn/ui | Accessible, responsive Hebrew RTL and English interface |
| Form engine | React Hook Form with schema validation | Adaptive interviews, review and editing |
| Control database | PostgreSQL, initially through Supabase | Tenants, projects, discovery, blueprints, manifests and audit references |
| Authentication | Supabase Auth or equivalent OIDC provider | User identity, invitations and sessions |
| Object storage | Supabase Storage or compatible S3 storage | Evidence, exports, generated reports and sanitized run artifacts |
| Domain and AI service | Python with FastAPI | Discovery normalization, rule execution, catalogue mapping and AI gateway |
| Background jobs | Python worker with Redis-backed queue | Document processing, blueprint generation, catalogue verification and provisioning orchestration |
| Durable workflow state | PostgreSQL workflow and operation tables | Authoritative job state, idempotency, recovery and audit linkage |
| Odoo sandbox runtime | Docker-based Odoo 19 Foundation topology | Isolated customer sandbox and pinned source runtime |
| Provisioning adapter | Python runner inside the isolated sandbox boundary | Odoo CLI/bootstrap, ORM-backed handlers and validation |
| Observability | OpenTelemetry-compatible traces, structured logs and metrics | End-to-end correlation and operational monitoring |
| Secrets | Managed secret vault or hosting-provider secret store | Scoped runtime credentials referenced by logical name |

Exact library and service versions must be pinned during implementation and updated through controlled dependency review.

## 3. Why this split

### Next.js control plane

Next.js is suitable for the customer and consultant product experience, localization, portals and standard request-response operations. It is not responsible for executing long Odoo installations or infrastructure jobs.

### Python domain and provisioning services

Odoo, document processing, deterministic rule execution and provisioning are best handled in Python. The service uses shared typed contracts rather than duplicating business meaning in the UI.

### PostgreSQL as authority

Durable workflow state lives in PostgreSQL. Redis accelerates queue delivery but is not the authoritative record of a project, approval or provisioning run. A lost queue message can be recovered from database state.

### Docker sandbox first

The MVP supports the known self-hosted Foundation topology first. Future Odoo.sh, partner-hosting or other infrastructure support is added through environment drivers, not by changing the product domain.

## 4. High-level architecture

```text
Customer / Consultant Browser
        |
        v
Next.js Web Application and BFF
        |
        +-----------------------+
        |                       |
        v                       v
PostgreSQL / Auth / Storage   Python Domain API
                                |
                                v
                         Durable Job Queue
                                |
                                v
                       Orchestration Workers
                          |             |
                          v             v
                    AI Gateway     Sandbox Driver
                                        |
                                        v
                          Isolated Odoo 19 Sandbox
                              + PostgreSQL database
```

The text layout is conceptual. Network paths, identities and permissions are defined explicitly in deployment architecture.

## 5. Architectural style

The control plane begins as a **modular monolith with separate worker processes**, not a distributed microservice estate.

Benefits:

- one coherent domain model;
- simpler transactions and versioning;
- fewer deployment and debugging boundaries;
- independent scaling for web, API and workers;
- clear modules that may be separated later when justified.

Required module boundaries:

- Identity and Tenancy
- Customer Engagement
- Discovery
- Evidence
- Requirements
- Capability Catalogue
- Blueprint
- Manifest
- Environment and Provisioning
- Validation and Deviations
- Notifications
- Audit and Reporting
- AI Gateway

Modules communicate through application services and durable domain events. They must not modify another module’s tables directly.

## 6. Repository strategy

Use one product repository for the control plane and provisioning handlers. Keep Odoo core and Enterprise repositories separate, as established by the Foundation.

Recommended workspace:

```text
odoo-solution-builder/
├── AGENTS.md
├── CLAUDE.md
├── README.md
├── .codex/
├── .agents/
│   └── skills/
├── apps/
│   ├── web/                       # Next.js application
│   ├── domain-api/                # FastAPI domain and AI service
│   └── worker/                    # Background and provisioning workers
├── packages/
│   ├── contracts/                 # JSON Schema / generated TS and Python types
│   ├── design-system/             # Shared accessible UI
│   ├── rules/                     # Versioned deterministic rules
│   └── test-fixtures/             # Sanitized domain fixtures
├── provisioning/
│   ├── handlers/                  # Versioned desired-state handlers
│   ├── validators/                # Odoo and business validations
│   ├── drivers/                   # Docker and future hosting drivers
│   ├── schemas/                   # Manifest and operation schemas
│   └── tests/
├── catalogue/
│   ├── schemas/
│   ├── ingestion/
│   ├── verified-releases/
│   └── tests/
├── database/
│   ├── migrations/
│   ├── seeds/
│   └── policies/
├── docs/
│   ├── 00-governance/
│   ├── 10-product/
│   ├── 20-domain/
│   ├── 30-architecture/
│   ├── 40-security/
│   ├── 50-testing/
│   ├── 60-operations/
│   ├── 70-decisions/
│   └── 80-handoff/
├── infrastructure/
│   ├── control-plane/
│   └── sandbox/
├── scripts/
└── tests/
    ├── contract/
    ├── integration/
    └── end-to-end/

workspace/
├── odoo-solution-builder/         # This product
├── odoo-19-enterprise-foundation/ # Existing reusable Foundation
├── odoo/                           # Pinned Odoo core checkout
└── enterprise/                     # Pinned Enterprise checkout
```

The product repository references pinned revisions. It does not copy or commit Odoo core or Enterprise source.

## 7. Authority and shared contracts

The domain model and versioned schemas are authoritative. Both TypeScript and Python types are generated from the same contract definitions where practical.

Contract families:

- interview definitions and answers;
- normalized claims and evidence;
- requirements and acceptance criteria;
- catalogue releases and capabilities;
- blueprint packages and decisions;
- deployment manifests;
- provisioning operations and results;
- validation results and deviations;
- audit event envelopes;
- AI request and structured-output schemas.

Schema changes use explicit versioning and compatibility rules. A worker must reject a payload schema it cannot safely understand.

## 8. Control database model

### 8.1 Identity and tenancy

- `tenants`
- `users`
- `memberships`
- `roles`
- `permissions`
- `customer_access_grants`

### 8.2 Customer engagement

- `customer_organizations`
- `customer_contacts`
- `implementation_projects`
- `project_members`
- `success_measures`
- `project_state_history`

### 8.3 Discovery

- `interview_definitions`
- `interview_definition_versions`
- `question_definitions`
- `interview_runs`
- `interview_sections`
- `question_assignments`
- `answers`
- `answer_revisions`
- `business_facts`
- `assumptions`
- `open_questions`
- `conflicts`
- `discovery_versions`

### 8.4 Evidence and requirements

- `evidence_items`
- `evidence_claims`
- `business_processes`
- `business_roles`
- `organizational_units`
- `approval_rules`
- `requirements`
- `requirement_sources`
- `requirement_dependencies`
- `constraints`

### 8.5 Capability catalogue

- `catalogue_releases`
- `applications`
- `modules`
- `module_dependencies`
- `capabilities`
- `configuration_options`
- `localizations`
- `approved_addons`
- `solution_patterns`
- `catalogue_evidence`
- `provisioning_handler_registrations`
- `validation_rule_registrations`

### 8.6 Blueprint

- `blueprints`
- `blueprint_versions`
- `fit_assessments`
- `blueprint_decisions`
- `decision_alternatives`
- `gaps`
- `implementation_phases`
- `blueprint_reviews`

### 8.7 Provisioning

- `deployment_manifests`
- `manifest_revisions`
- `environments`
- `provisioning_plans`
- `provisioning_runs`
- `configuration_operations`
- `operation_attempts`
- `validation_runs`
- `validation_results`
- `deviations`
- `environment_state_snapshots`

### 8.8 Governance

- `approvals`
- `change_requests`
- `policies`
- `policy_versions`
- `audit_events`
- `outbox_events`
- `notifications`

This is a logical data model. Physical normalization, indexes and partitions will be decided from query and retention requirements.

## 9. Versioning pattern

Mutable working records and immutable approved versions are separate.

Pattern:

1. Users edit a working aggregate.
2. The system validates internal consistency.
3. A version snapshot is generated with a content hash.
4. Review and approvals point to that exact version.
5. Approved content never changes.
6. New information creates a new working revision and version.

This pattern applies to:

- interview definitions;
- discovery packages;
- catalogue releases;
- blueprints;
- deployment manifests;
- provisioning-handler releases;
- validation-rule releases;
- policies.

## 10. Multi-tenancy and authorization

### 10.1 Tenant boundary

Every customer-owned record includes an AIOne tenant and customer/project boundary. Database row-level security is defense in depth, not a substitute for application authorization.

### 10.2 Authorization model

Use role plus relationship and resource-state checks:

- platform role;
- tenant membership;
- customer and project assignment;
- respondent section assignment;
- ownership or review responsibility;
- current workflow state;
- requested action and data sensitivity.

### 10.3 Customer isolation

- Customers cannot enumerate other organizations or projects.
- Evidence access is limited to authorized project members.
- Generated export links are short-lived and scoped.
- Provisioning logs exposed to customers are sanitized views.
- Environment credentials are distributed through invitations or a secret channel.
- Support access is time-bounded and audited where possible.

### 10.4 Service identities

Web, domain API, document worker, AI gateway, catalogue worker and provisioning worker use separate identities and permissions. A compromise of the customer web session must not grant sandbox infrastructure authority.

## 11. Authentication flows

MVP flows:

- AIOne workforce login through configured identity provider;
- customer invitation with verified email;
- project-specific respondent access;
- passwordless or standard secure authentication according to provider policy;
- session revocation and membership removal;
- optional MFA requirement for consultant, architect and provisioning roles;
- step-up authentication before high-impact approval or provisioning authorization.

The architecture remains compatible with future enterprise SSO.

## 12. Discovery rules engine

The rules engine is deterministic and versioned.

Responsibilities:

- question applicability;
- section activation;
- follow-up generation;
- required owner and evidence policies;
- answer validation;
- conflict rules;
- complexity signals;
- confidence, completeness and risk policies;
- domain-specific escalation;
- discovery readiness.

Rules are stored as reviewed definitions or code, not generated and executed as arbitrary AI text.

Rule requirements:

- stable rule key and version;
- typed inputs and outputs;
- pure evaluation where possible;
- explanation of matched conditions;
- unit tests with positive, negative and boundary cases;
- deterministic replay against an immutable discovery snapshot;
- policy for rule deprecation and migration.

## 13. Blueprint decision engine

The decision engine combines deterministic filtering with AI-assisted candidate analysis.

Pipeline:

1. Retrieve approved requirements and context.
2. Retrieve capabilities from the pinned catalogue release.
3. Generate candidate mappings using structured relationships and search.
4. Apply deterministic eligibility, compatibility and dependency filters.
5. Ask the AI gateway for a structured comparative analysis where useful.
6. Validate structured output and supporting catalogue references.
7. Calculate rule-based fit dimensions.
8. Produce proposed decisions, residual gaps and open verification items.
9. Require consultant review.

AI may rank and explain verified candidates. It may not introduce a technical module, field or feature absent from the selected catalogue release.

## 14. AI gateway

All model use goes through one governed gateway.

Permitted MVP tasks:

- interpret short business narratives;
- extract proposed facts and entities from evidence;
- propose clarification questions;
- transform approved facts into draft atomic requirements;
- compare verified capability candidates;
- draft business-facing blueprint explanations;
- summarize validation and deviation information.

Controls:

- purpose-specific prompts and schemas;
- structured outputs validated before persistence;
- minimum required context only;
- allowlisted tools and data sources;
- tenant and project boundaries;
- no raw secret access;
- prompt-injection handling for uploaded documents;
- confidence and human-review policy;
- model, prompt and schema version logging;
- retry and fallback without duplicate writes;
- evaluation datasets and quality thresholds;
- cost and latency budgets;
- kill switch by use case.

AI outputs are stored as proposals with provenance. They do not overwrite original answers or approved records.

## 15. Evidence-processing pipeline

1. Upload directly to scoped object storage using a short-lived request.
2. Record file identity, owner, classification and checksum.
3. Scan the file and quarantine failures.
4. Extract text and structure in an isolated worker.
5. Classify document type and applicability.
6. Send only necessary extracted content through the AI gateway.
7. Produce source-located claims.
8. Compare claims with project facts and answers.
9. Present confirmation and conflicts.
10. Apply retention and deletion policy.

Uploaded documents are untrusted input. Their contents cannot instruct the platform, change rules or grant access.

## 16. Odoo catalogue ingestion

The Catalogue Ingestion service works against pinned local source checkouts or immutable source artifacts.

### 16.1 Automated extraction

- discover installable addon directories;
- parse module manifests without executing arbitrary addon code;
- extract names, versions, licenses, dependencies, data, demo, assets, external dependencies and hooks;
- identify core, Enterprise, localization and approved-addon source;
- calculate source and manifest fingerprints;
- build dependency graph;
- compare against prior catalogue release;
- produce verification work items.

### 16.2 Verified enrichment

Consultants and architects add:

- business capability descriptions;
- configuration options;
- limitations and applicability;
- security and data consequences;
- provisioning handlers;
- validation rules;
- official documentation and source evidence;
- solution patterns.

### 16.3 Release process

- run schema and dependency checks;
- run clean install and selected update tests;
- run handler and validation contract tests;
- review differences;
- approve immutable catalogue release;
- publish release for new blueprint versions.

The first MVP catalogue should cover only the applications required by the first pilot archetype, not all Odoo applications.

## 17. Provisioning execution architecture

### 17.1 Control-plane worker

The worker:

- validates the approved manifest;
- acquires environment lock;
- requests infrastructure allocation;
- passes a signed, time-bound job envelope to the sandbox runner;
- monitors heartbeats and operation results;
- persists authoritative run state;
- schedules validations;
- records deviations and release readiness.

### 17.2 Sandbox runner

For the Docker-based MVP, the runner executes inside the isolated environment boundary and has:

- access to that sandbox only;
- pinned provisioning-handler package;
- Odoo runtime and CLI access;
- scoped database/ORM access;
- short-lived control-plane job authorization;
- no authority over other customer environments;
- no ability to approve its own manifest.

### 17.3 Handler strategy

Use three handler types:

1. **Bootstrap handlers:** database initialization, language activation and module installation using verified Odoo runtime mechanisms.
2. **ORM handlers:** idempotent configuration through Odoo models and external identifiers.
3. **Validation handlers:** read-only or isolated test operations proving technical and business state.

Arbitrary shell, SQL and Python content from a manifest is prohibited. The manifest invokes allowlisted versioned handlers with schema-validated parameters.

### 17.4 Future drivers

Future drivers may support Odoo.sh, partner hosting or cloud Kubernetes. They must preserve manifest, approval, handler and validation contracts even when transport differs.

## 18. Background job reliability

MVP reliability pattern:

- database transaction writes aggregate state and outbox event together;
- relay publishes outbox events to the queue;
- worker claims a durable job record with lease and heartbeat;
- idempotency key prevents duplicate material action;
- worker persists checkpoints after bounded operations;
- expired leases return recoverable jobs for inspection or retry;
- final state is reconciled from database records, not queue acknowledgement alone.

Jobs include:

- evidence extraction;
- requirement proposal;
- blueprint candidate generation;
- catalogue ingestion and verification;
- manifest compilation;
- environment allocation;
- provisioning run;
- validation suite;
- report generation;
- notification delivery.

## 19. API design principles

- Resource-oriented endpoints for domain aggregates
- Commands for state transitions and approvals
- Optimistic concurrency using version or ETag
- Idempotency keys for invitation, compilation and provisioning commands
- Cursor pagination for large audit and catalogue collections
- Localized error messages with stable machine codes
- Explicit schema version in asynchronous envelopes
- No client authority to set approval, confidence or audit fields directly
- Signed short-lived upload and download grants
- Complete authorization at the service layer

The UI does not call worker or sandbox endpoints directly.

## 20. Frontend architecture

### 20.1 Route areas

```text
/app
  /portfolio
  /customers
  /projects/[projectId]
    /overview
    /discovery
    /requirements
    /blueprint
    /manifest
    /sandbox
    /audit
  /catalogue
  /interview-builder
  /administration

/portal
  /projects/[projectId]
    /welcome
    /interview
    /clarifications
    /blueprint-review
    /sandbox-review
```

### 20.2 UI state

- Server state is retrieved through typed API clients.
- Draft forms use local form state and explicit save behavior.
- Autosave is debounced and version-aware.
- Approval and provisioning actions require confirmation and fresh authorization state.
- Background job progress is streamed or polled from authoritative run status.
- Optimistic UI is not used for approvals or provisioning outcomes.

### 20.3 RTL and accessibility

- Direction derives from active interface language and is applied at document and component boundaries.
- Logical CSS properties are used instead of hard-coded left/right behavior.
- Components support keyboard use, visible focus and screen-reader labels.
- Adaptive interview steps announce errors and progress accessibly.
- Tables have responsive alternatives for narrow screens.
- Color never carries confidence or risk meaning by itself.
- Hebrew and English text are tested with realistic content lengths.

## 21. Environments

### Control plane

- local development;
- shared integration;
- staging;
- production.

### Odoo targets in MVP

- automated ephemeral test sandbox;
- project development sandbox;
- customer demonstration sandbox.

Production customer Odoo is excluded.

Each environment has separate credentials, databases, storage namespaces and external endpoints. Staging must not share production secrets or customer evidence by default.

## 22. Deployment topology

Recommended initial topology:

- host the Next.js application on a managed web platform such as Vercel;
- host PostgreSQL, authentication and object storage through Supabase or equivalent managed services;
- host the Python API and worker as Docker services on a platform supporting long-running processes and private networking;
- host Odoo sandboxes on controlled Docker infrastructure with isolated databases and storage;
- use a managed Redis-compatible service for queue transport;
- use a managed secret store appropriate to the worker and sandbox infrastructure.

Vercel functions must not execute long provisioning workflows. They submit commands and return durable job identifiers.

Provider choices remain replaceable through adapters and environment configuration.

## 23. Security architecture

### 23.1 Threat priorities

- cross-customer data exposure;
- provisioning authority escalation;
- credential or secret leakage;
- malicious or compromised document upload;
- prompt injection and AI tool misuse;
- unauthorized blueprint or manifest approval;
- sandbox-to-control-plane lateral movement;
- sandbox-to-sandbox access;
- arbitrary code execution through handlers or manifests;
- supply-chain compromise in Odoo or addon source;
- audit-log tampering.

### 23.2 Required controls

- explicit tenant and project authorization;
- row-level security as defense in depth;
- separate service identities;
- scoped and rotated secrets;
- short-lived signed job envelopes;
- allowlisted handler registry;
- source revision and artifact checksum verification;
- upload scanning and isolated extraction;
- model gateway without secret or direct sandbox authority;
- immutable approvals and checksums;
- structured log redaction;
- network segmentation;
- dependency and container scanning;
- backup and recovery testing;
- append-only or tamper-evident audit retention.

### 23.3 Data classification

At minimum:

- Public
- AIOne Internal
- Customer Confidential
- Sensitive Personal or Financial
- Secret

Classification determines storage, access, AI eligibility, log behavior, export and retention.

## 24. Observability

Every interactive request and background job receives a correlation identifier spanning:

- web request;
- domain command;
- outbox event;
- worker job;
- AI request;
- sandbox operation;
- validation result;
- notification.

Required signals:

- structured application logs;
- provisioning operation logs;
- traces across HTTP, jobs and sandbox adapter;
- metrics for latency, failures, retries, queue depth and model usage;
- audit events for authority and state changes;
- alerting for failed provisioning, stale jobs, authorization anomalies and isolation violations.

Customer-visible status is derived from sanitized domain state, not raw infrastructure logs.

## 25. Testing strategy

### 25.1 Contract tests

- TypeScript and Python consume the same schema fixtures.
- Version compatibility and rejection behavior are tested.
- Every handler and validation rule conforms to its declared contract.

### 25.2 Domain unit tests

- branching and follow-ups;
- conflict detection;
- confidence, completeness, risk and escalation;
- fit classifications and dependency filters;
- approval invalidation;
- manifest compilation;
- idempotency and drift policy.

### 25.3 Integration tests

- PostgreSQL transactions and row-level security;
- authentication and invitation flows;
- object upload and evidence processing;
- outbox, queue and worker recovery;
- AI structured-output validation and fallback;
- catalogue ingestion from pinned fixture addons;
- provisioning against disposable Odoo databases.

### 25.4 Odoo tests

- module installation and update tests;
- Python transaction tests for custom handlers;
- security access and negative-path tests;
- browser tours for critical business scenarios;
- query-count tests for material custom logic;
- Hebrew RTL and English UI smoke tests.

### 25.5 End-to-end golden journeys

At least:

1. Quick Start wholesale distributor to demonstration sandbox
2. Guided professional-services company to validated sandbox
3. Conflict and clarification journey that correctly blocks blueprint approval
4. Failed provisioning operation followed by safe rebuild
5. Manifest rerun proving no duplicate managed records
6. Cross-tenant authorization attack proving isolation

## 26. CI/CD quality gates

For every change:

- formatting and linting;
- TypeScript and Python type checking;
- schema compatibility checks;
- domain and security unit tests;
- database migration validation;
- dependency and secret scanning;
- container and source-artifact checks;
- contract tests;
- affected integration tests.

For release candidates:

- clean control-plane deployment;
- catalogue verification;
- disposable Odoo 19 sandbox provision;
- rerun idempotency test;
- security-negative test suite;
- golden journey tests;
- backup and recovery smoke test;
- release notes and rollback plan.

## 27. Development governance

The project follows the established shared-repository model:

- `AGENTS.md` defines architecture and design authority for Codex;
- `CLAUDE.md` defines implementation responsibilities and constraints;
- `docs/` contains approved authoritative specifications;
- `docs/80-handoff/` contains bounded approved implementation packets;
- architecture changes require an Architecture Decision Record;
- implementation may not silently alter approved domain rules or security boundaries;
- reusable Foundation remains separate from customer and product implementation.

## 28. Architecture Decision Records required before build

Create and approve:

1. ADR-001: Modular monolith and worker-process architecture
2. ADR-002: Next.js and Python service boundary
3. ADR-003: PostgreSQL tenancy and authorization model
4. ADR-004: Shared schema and type-generation approach
5. ADR-005: Durable jobs, outbox and queue design
6. ADR-006: AI gateway, provider abstraction and data policy
7. ADR-007: Odoo catalogue ingestion and release process
8. ADR-008: Docker sandbox driver and runner trust boundary
9. ADR-009: Provisioning handler packaging and execution
10. ADR-010: Secrets and short-lived job authorization
11. ADR-011: Audit-event integrity and retention
12. ADR-012: Evidence processing and malware isolation

## 29. MVP product increments

The delivery sequence is incremental. Each increment must be demonstrable and tested before the next relies on it.

### Increment 0: Foundation and architecture

Deliverables:

- product repository and governance files;
- approved ADRs;
- local control-plane development environment;
- Next.js, Python, PostgreSQL and worker skeletons;
- shared contracts pipeline;
- authentication baseline;
- CI quality gates;
- integration with existing Odoo 19 Foundation workspace.

Exit criteria:

- one command starts the local product dependencies;
- web, API, worker and database health checks pass;
- schema fixture is consumed by TypeScript and Python;
- a worker job completes through the durable queue path;
- no Odoo application is yet configured.

### Increment 1: Tenancy and project workspace

Deliverables:

- AIOne users, customer organizations and project membership;
- customer invitation;
- project lifecycle and dashboard;
- tenant authorization and row-level policies;
- audit-event baseline.

Exit criteria:

- AIOne can create a customer project;
- an invited respondent sees only the assigned project;
- automated cross-tenant tests pass.

### Increment 2: Quick Start Discovery

Deliverables:

- versioned interview definitions;
- Quick Start questions and branching;
- save/resume and respondent assignment;
- facts, assumptions, conflicts and open questions;
- basic requirement proposal and consultant review;
- Hebrew RTL and English interface.

Exit criteria:

- pilot customer completes Quick Start in the intended time range;
- irrelevant branches remain hidden with recorded reason;
- approved immutable discovery package is created.

### Increment 3: Guided Discovery and evidence

Deliverables:

- activated domain sections;
- document upload, scanning and extraction;
- claim confirmation and conflict handling;
- confidence, completeness, complexity and risk policies;
- domain-specific escalation;
- structured requirement review and approval.

Exit criteria:

- representative Guided journey produces traceable requirements;
- material conflicts block approval;
- evidence-derived claims remain proposed until confirmed.

### Increment 4: Odoo catalogue and blueprint MVP

Deliverables:

- catalogue schemas and ingestion pipeline;
- first verified Odoo 19 catalogue release for one pilot archetype;
- candidate mapping and deterministic filters;
- fit assessments, decisions, gaps and phase planning;
- consultant and customer blueprint views;
- blueprint version and approval.

Exit criteria:

- every Must requirement receives a reviewed fit or blocker;
- exact modules resolve from verified manifests;
- approved structured blueprint package is created.

### Increment 5: Manifest and Docker sandbox bootstrap

Deliverables:

- deployment-manifest schema and compiler;
- manifest approval;
- Docker environment driver;
- sandbox runner;
- pinned Odoo core, Enterprise and Foundation runtime;
- environment lifecycle and run tracking;
- secret references and job authorization.

Exit criteria:

- approved blueprint compiles into valid manifest;
- an isolated fresh Odoo 19 Enterprise sandbox boots;
- unauthorized and altered manifests are rejected.

### Increment 6: Configuration handlers and validation

Deliverables:

- module-install handlers;
- language, company and pilot-pattern handlers;
- managed external identity registry;
- current-state comparison and idempotency;
- platform, module, configuration and security validations;
- Hebrew RTL and business smoke tours;
- deviations and rebuild.

Exit criteria:

- pilot manifest provisions the intended sandbox;
- same-manifest rerun creates no duplicates;
- mandatory failure prevents release;
- failed disposable sandbox can be rebuilt reproducibly.

### Increment 7: Customer sandbox review

Deliverables:

- release package and guided review scenarios;
- secure customer access;
- feedback classification;
- change-request flow;
- readiness and traceability reports;
- operational dashboards and alerts.

Exit criteria:

- customer completes defined review scenarios;
- feedback links to blueprint and manifest versions;
- accepted sandbox and unresolved gaps are explicit.

### Increment 8: Comprehensive Discovery baseline

Deliverables:

- workshop-based process editor;
- advanced exception, control and cross-domain review;
- specialist respondent workflows;
- requirements and process traceability enhancements.

Exit criteria:

- one complex domain can be specified through a controlled workshop without breaking the shared discovery model.

## 30. Recommended pilot archetype

Start with one bounded archetype rather than a universal Odoo implementation.

Recommended first pilot: **Israeli B2B wholesale distributor with CRM, Sales, Purchase, Inventory and Accounting boundaries**.

Why:

- directly aligned with AIOne’s target market and the user’s distribution experience;
- exercises products, pricing, customers, suppliers, warehouses and approvals;
- exposes Israeli localization boundaries;
- supports a clear order-to-cash and procure-to-pay demonstration;
- remains simpler than manufacturing or regulated healthcare;
- creates reusable foundations for importers and distributors.

The pilot should initially use demonstration data and accounting-safe configuration approved by an authorized finance consultant.

## 31. Pilot golden journey

1. AIOne creates an Israeli wholesale-distribution project.
2. Customer sponsor completes Quick Start.
3. Sales, inventory and finance owners complete assigned Guided sections.
4. Product list and example quotation are uploaded and reviewed.
5. Conflicts and assumptions are resolved.
6. Consultant approves discovery version.
7. Engine proposes capabilities and exact verified modules.
8. Consultant reviews pricing, approvals, warehouse and accounting boundaries.
9. Customer approves business-facing blueprint.
10. AIOne approves sandbox manifest.
11. Docker driver provisions a fresh Odoo 19 Enterprise sandbox.
12. Handlers install and configure the approved pilot scope.
13. Validations run CRM-to-order, purchase-to-receipt, access and RTL scenarios.
14. Customer receives the sandbox review package.
15. Feedback creates defects, corrections or change requests with traceability.

## 32. Scope explicitly deferred after MVP

- automatic production deployment;
- live cutover orchestration;
- full financial or historical migration execution;
- automatic deployment of AI-generated custom modules;
- broad marketplace-addon selection;
- every Odoo application and vertical;
- Odoo.sh or multiple hosting-provider drivers;
- complex manufacturing;
- payroll processing;
- regulated clinical implementation;
- autonomous customer acceptance;
- commercial estimation and contract generation.

## 33. Delivery assumptions

Indicative sequencing assumes:

- a small focused team with product, Odoo architecture, full-stack and Python capability;
- access to the existing Odoo 19 Foundation, core and Enterprise repositories;
- an approved pilot customer or realistic sanitized pilot dataset;
- finance review for Israeli accounting boundaries;
- iterative demonstrations and acceptance after each increment.

The plan should be estimated only after ADRs, pilot scope and team availability are confirmed. Calendar dates should not be committed from this architecture document alone.

## 34. MVP definition of done

The MVP is complete when:

1. AIOne can create and isolate customer projects.
2. A customer can complete Quick Start or Guided Discovery in Hebrew or English.
3. The system produces reviewed, source-linked requirements.
4. An approved Odoo 19 catalogue release covers the pilot scope.
5. The engine generates explainable fit decisions and an approved blueprint.
6. The blueprint compiles into an approved immutable manifest.
7. The manifest provisions a fresh isolated Odoo 19 Enterprise pilot sandbox.
8. Rerunning the same manifest is idempotent.
9. Mandatory platform, module, configuration, security, business and RTL tests pass.
10. Failed or deviating sandboxes are not released.
11. The customer can complete guided review and submit classified feedback.
12. Every configuration change is traceable to requirement, decision, manifest and approval.
13. Cross-customer authorization and sandbox-isolation tests pass.
14. No production deployment capability is active.

## 35. Immediate next implementation package

Before writing product code, create the **Repository Bootstrap and Architecture Decision Package** containing:

- final product name and repository name;
- `AGENTS.md`, `CLAUDE.md` and README;
- directory structure;
- local development topology;
- ADR-001 through ADR-012 drafts;
- shared contract conventions;
- coding, testing and security standards;
- environment and secret templates;
- Increment 0 stories and acceptance tests;
- integration instructions for the existing Odoo 19 Enterprise Foundation.

That package will be the approved handoff from product architecture into implementation.
