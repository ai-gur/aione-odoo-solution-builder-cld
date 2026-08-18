# AIOne Odoo Solution Builder

## Deployment Manifest and Sandbox Provisioning Engine

**Version:** 0.1  
**Date:** 18 August 2026  
**Status:** Initial design baseline  
**Depends on:** Product Constitution, Discovery Engine and Blueprint Engine specifications  
**Target:** Odoo Enterprise 19 development and sandbox environments

## 1. Objective

The Provisioning Engine converts an approved structured blueprint into a reproducible, isolated and validated Odoo Enterprise 19 sandbox.

The engine operates from an immutable Deployment Manifest. It separates infrastructure creation, Odoo database initialization, module installation, supported configuration, baseline data loading and validation into explicit operations with known prerequisites and outcomes.

The MVP provisions development and demonstration sandboxes only. It does not deploy to production or execute irreversible production migration.

## 2. Provisioning principles

1. **Approved desired state:** Only an approved blueprint can produce an executable manifest.
2. **Immutable input:** An approved manifest cannot be edited. Changes create a new version.
3. **Fresh-environment preference:** The MVP favors rebuilding disposable sandboxes over repairing an unknown environment.
4. **Idempotent operations:** Safe reruns converge on the declared state without duplicate records.
5. **Current-state inspection:** Every operation checks the environment before writing.
6. **Dependency ordering:** Operations run only after declared prerequisites succeed.
7. **Least privilege:** Provisioning identities receive only the access required for the current operation class.
8. **No embedded secrets:** The manifest contains secret references, never secret values.
9. **Verifiable completion:** An operation is not complete until its validation passes.
10. **Traceability:** Every change maps back to a manifest item, blueprint decision, requirement and approval.
11. **Fail explicitly:** Unknown, conflicting or unsupported states produce deviations rather than silent workarounds.
12. **No core modification:** Odoo core and Enterprise source remain unmodified.

## 3. System boundary

The Provisioning Engine is part of the AIOne control plane and is not installed as the controlling authority inside a customer database.

Conceptual components:

| Component | Responsibility |
| --- | --- |
| Manifest Compiler | Converts an approved blueprint into an immutable desired-state package |
| Policy Validator | Confirms approval, environment and operation eligibility |
| Environment Driver | Creates or resolves isolated compute, database, storage and routing |
| Odoo Bootstrap Adapter | Initializes the target Odoo 19 Enterprise database |
| Odoo Configuration Adapter | Executes supported Odoo configuration operations |
| State Inspector | Reads current module, configuration, record and security state |
| Plan Resolver | Builds the dependency-ordered execution plan |
| Secret Broker | Resolves short-lived or scoped credentials by reference |
| Operation Runner | Executes, retries and records configuration operations |
| Validation Runner | Executes technical and business validation suites |
| Deviation Manager | Records and resolves differences from desired state |
| Artifact Store | Retains manifests, reports, logs and validation evidence |
| Audit Service | Records append-only material events |

The exact infrastructure provider and transport are deferred. All adapters must implement the same declared contracts.

## 4. Deployment Manifest

### 4.1 Purpose

The Deployment Manifest is the executable contract between approved solution design and a named target environment.

It describes desired state, not a free-form script. The compiler selects only operations supported by the pinned provisioning-handler catalogue.

### 4.2 Manifest identity

Every manifest contains:

- manifest identifier and semantic schema version;
- immutable manifest revision;
- customer and implementation-project identifiers;
- approved blueprint identifier and version;
- approved discovery-version reference;
- Odoo capability-catalogue release;
- provisioning-handler catalogue release;
- target Odoo edition, branch and verified source revisions;
- target environment identifier and environment type;
- compiler version and compilation timestamp;
- authorizer and approval references;
- canonical content checksum;
- status and expiry where policy requires.

### 4.3 Manifest sections

```yaml
apiVersion: aione.odoo/v1alpha1
kind: OdooSandboxManifest
metadata:
  manifestId: manifest_example
  revision: 1
  projectId: project_example
  blueprintId: blueprint_example
  blueprintVersion: 1
  catalogueRelease: odoo19_catalogue_2026_08
  handlerRelease: provisioners_2026_08
  checksum: pending
spec:
  target: {}
  sourceRevisions: {}
  environment: {}
  secrets: []
  database: {}
  languages: []
  organizations: []
  modules: {}
  configuration: []
  security: []
  baselineData: []
  demonstrationData: {}
  integrations: []
  validations: []
  policies: {}
  traceability: {}
approvals: []
```

This is a conceptual schema. Formal JSON Schema or equivalent will be defined during implementation architecture.

### 4.4 Target section

Defines:

- Odoo edition: Enterprise;
- Odoo version: 19.0;
- deployment topology profile;
- supported operating and database versions;
- expected base image or runtime identity;
- locale, timezone and default language;
- sandbox expiry and retention policy;
- demonstration or development classification.

### 4.5 Source revisions

Pins:

- Odoo core source revision;
- Odoo Enterprise source revision;
- AIOne custom-addon revision;
- approved third-party addon revisions;
- Foundation release;
- container or runtime artifact digest where used.

Floating branch names are insufficient for an executable approved manifest.

### 4.6 Secret declarations

A secret declaration includes:

- stable logical name;
- secret-provider reference;
- purpose and consuming operation classes;
- expected type;
- environment scope;
- rotation and expiry metadata;
- whether the value must already exist;
- validation that does not disclose the value.

The manifest never stores passwords, API keys, database credentials, private keys or tokens.

### 4.7 Organization declarations

Defines desired legal companies, languages, currencies, countries, websites, warehouses and other approved organizational structures using stable manifest references.

Every created record uses a deterministic external identity or registry mapping so reruns can find the same record.

### 4.8 Module declarations

Separates:

- platform baseline modules;
- business-selected modules;
- localization modules;
- approved addons;
- transitive technical dependencies;
- demonstration-only modules or data.

Each declared module includes:

- exact technical name;
- source and pinned revision;
- reason and linked blueprint decisions;
- direct versus transitive classification;
- required installation phase;
- expected installed state;
- update and uninstall policy;
- validation rules.

### 4.9 Configuration declarations

Each item references a versioned handler and contains structured, schema-validated desired state. The manifest does not embed arbitrary Python, SQL or server-action code.

### 4.10 Validation declarations

Defines mandatory and advisory checks, their parameters, expected outcome, blocking policy and traceability to acceptance criteria.

## 5. Manifest compilation

Compilation lifecycle:

1. Load the approved blueprint and catalogue releases.
2. Confirm the blueprint approval is valid and current.
3. Resolve exact modules and transitive dependencies from verified manifests.
4. Resolve capabilities into supported configuration handlers.
5. Resolve business roles into reviewed security declarations.
6. Resolve organization and baseline-data references.
7. Select validations for every provisioned decision and critical platform invariant.
8. Order declarations by logical prerequisites without yet inspecting a live environment.
9. Validate schemas, policies, compatibility and traceability.
10. Generate canonical serialization and checksum.
11. Request manifest approval for the named environment.
12. Freeze the approved revision.

Compilation fails when:

- a blueprint decision lacks an approved handler;
- an exact module or source revision cannot be resolved;
- dependencies conflict;
- required validations do not exist;
- an unapproved addon is included;
- a secret value rather than a reference is detected;
- target environment type is outside MVP policy;
- blocking blueprint assumptions or gaps apply to the requested sandbox.

## 6. Environment model

Each Environment contains:

- stable environment identifier;
- customer and implementation project;
- environment type: development or sandbox in MVP;
- infrastructure provider and driver;
- region and data-residency classification;
- Odoo and database endpoints by protected reference;
- source and runtime revisions;
- current manifest revision;
- lifecycle state;
- creation, expiry and last-validation timestamps;
- backup and snapshot policy;
- access policy and authorized users;
- health and deviation summary.

No environment may be shared between unrelated customer projects.

## 7. Environment lifecycle

| State | Meaning |
| --- | --- |
| Requested | Approved manifest targets a not-yet-created environment |
| Allocating | Infrastructure resources are being created |
| Bootstrapping | Odoo runtime and database are being initialized |
| Configuring | Modules and configuration operations are running |
| Validating | Mandatory checks are running |
| Ready | All mandatory checks passed |
| Ready with Warnings | Blocking checks passed; advisory issues remain |
| Failed | Provisioning or mandatory validation failed |
| Suspended | Access or runtime is temporarily disabled |
| Expired | Retention period ended and review is required |
| Rebuilding | A replacement sandbox is being created |
| Archived | Required artifacts retained but runtime is inactive |
| Destroyed | Runtime resources were intentionally removed under policy |

Destructive lifecycle transitions are out of automatic MVP behavior unless separately authorized by explicit environment policy.

## 8. Provisioning plan

The Plan Resolver compares the manifest desired state with inspected current state and creates a Provisioning Plan.

The plan contains:

- immutable manifest reference;
- environment-state snapshot and timestamp;
- ordered stages and operations;
- operations already compliant;
- required writes;
- unsupported or conflicting states;
- locks and concurrency requirements;
- expected restart or maintenance events;
- estimated effort and timeout classes;
- rollback, compensation or rebuild strategy;
- required approvals;
- validation sequence.

The plan must be reviewed when it contains any operation classified as destructive, irreversible, unknown-state or manually authorized.

## 9. Standard provisioning stages

### Stage 0: Preflight

- verify manifest signature, checksum and approval;
- confirm environment ownership and type;
- verify pinned source artifacts are accessible;
- verify Odoo core and Enterprise compatibility;
- confirm approved addon revisions;
- confirm secret references can be resolved;
- confirm required capacity and environment policy;
- acquire project and environment execution lock;
- create audit event and run identifier.

### Stage 1: Infrastructure allocation

- allocate isolated compute, database, storage and routing;
- apply environment labels and ownership;
- configure protected network access;
- initialize logging, health and backup facilities;
- record immutable infrastructure references.

### Stage 2: Odoo bootstrap

- start pinned Odoo 19 Enterprise runtime;
- initialize a fresh database using an approved bootstrap mechanism;
- set database-level locale and base configuration;
- create or secure the initial administrative path;
- verify base module and runtime health;
- create a pre-configuration snapshot where supported.

The exact Odoo bootstrap adapter must be verified against the selected deployment topology. The specification does not assume an undocumented public database-creation API.

### Stage 3: Platform baseline

- apply the reusable Foundation baseline;
- activate approved languages;
- establish configuration registry and external identifiers;
- install required platform modules;
- apply baseline mail, audit and technical policies;
- verify baseline health.

### Stage 4: Business and localization modules

- install business-selected applications;
- install localization modules;
- install approved addons;
- verify transitive dependencies;
- run module installation tests;
- record actual module state and source revisions.

Modules are installed in dependency-safe batches. A module failure blocks dependent configuration.

### Stage 5: Organizational configuration

- create or reconcile legal companies;
- configure languages, currencies, countries and timezones;
- create approved warehouses, websites, teams and departments;
- apply company-specific baseline settings;
- validate company boundaries and access context.

### Stage 6: Business configuration

- apply capability configuration operations;
- create approved sequences, stages, tags, terms, policies and templates;
- apply workflow, approval and reporting settings;
- create integration placeholders without exposing live credentials;
- record current-state and result for every item.

### Stage 7: Security configuration

- create approved custom privileges and groups where required;
- map implied groups;
- apply model access and record rules from approved modules;
- assign sandbox users to approved roles;
- validate company and record visibility;
- test prohibited actions and bypass paths.

Security changes require their own validation stage and cannot be considered successful merely because records were created.

### Stage 8: Baseline and demonstration data

- load approved configuration data;
- load sanitized baseline master data;
- optionally load clearly marked demonstration data;
- preserve external identifiers and origin metadata;
- prevent demonstration data from being mistaken for migration output.

### Stage 9: Integration stubs and sandbox connectivity

- configure approved sandbox endpoints or stubs;
- resolve sandbox-only credentials;
- verify authentication and error handling;
- prevent accidental use of production endpoints unless separately authorized;
- run contract-level checks where possible.

### Stage 10: Validation and release

- run platform, module, configuration, security and business validations;
- produce deviation report;
- block release on failed mandatory checks;
- issue readiness report;
- grant approved consultant and customer access only after release authorization.

## 10. Configuration operation contract

Every handler implements behavior equivalent to:

```text
validate_input(desired_state)
inspect(environment, desired_state) -> current_state
compare(current_state, desired_state) -> compliant | change_required | conflict
plan(current_state, desired_state) -> operation_plan
apply(environment, operation_plan) -> operation_result
validate(environment, desired_state) -> validation_result
compensate(environment, operation_result) -> compensation_result
```

Required handler metadata:

- handler key and semantic version;
- supported Odoo and catalogue releases;
- input and output schemas;
- operation class and sensitivity;
- required privileges;
- supported scope: database, company or record set;
- prerequisites and conflicts;
- idempotency key strategy;
- transaction boundary;
- retry classification;
- timeout and performance class;
- validation rule;
- compensation or rebuild policy;
- source owner and automated test status.

## 11. Operation classes

| Class | Examples | Default policy |
| --- | --- | --- |
| Inspect | Read module, record or setting state | Safe and repeatable |
| Install | Install approved module and dependencies | Requires pinned source and tests |
| Configure | Set supported database or company option | Current-state check required |
| Upsert | Create or update a managed record | Stable identity required |
| Assign | Add approved group, role or relationship | Additive behavior reviewed |
| Load | Import approved baseline or demo package | Origin and duplicate policy required |
| Validate | Assert technical or business state | No mutation beyond test fixtures |
| Connect | Configure sandbox integration | Secret reference and endpoint policy required |
| Restart | Restart runtime where required | Coordinated maintenance event |
| Remove | Remove managed configuration or data | Restricted and normally excluded from MVP automation |
| Uninstall | Uninstall module | High risk and excluded by default |

The manifest may express desired absence, but destructive reconciliation requires a separate policy and authorization. In the MVP, rebuild is preferred.

## 12. Managed identity and external identifiers

Every managed Odoo record must be resolvable across reruns.

Preferred identity order:

1. Stable module external identifier for addon-owned data
2. Provisioning registry key mapped to an Odoo external identifier
3. Verified immutable natural key only where safe

Names alone are not sufficient identity. The engine must not update the first record returned by an ambiguous search.

Managed records store or reference:

- project and manifest ownership;
- stable logical key;
- source blueprint decision;
- last applied manifest revision;
- content fingerprint where appropriate;
- management policy: controlled, mergeable or observe-only.

Odoo XML/CSV data packages should use external identifiers. `noupdate` behavior must be chosen explicitly because it changes whether later module updates may reapply data.

## 13. Idempotency

An operation is idempotent when repeating it with the same desired state produces no additional business change.

Required mechanisms:

- deterministic operation key;
- stable managed-record identity;
- desired-state fingerprint;
- pre-write current-state comparison;
- uniqueness and duplicate detection;
- write only changed managed fields;
- relationship reconciliation policy;
- stored applied revision and result;
- safe handling of interrupted runs.

Examples:

- activating Hebrew when already active returns Already Compliant;
- creating a sales team with the same managed identity updates only controlled fields;
- rerunning group assignment does not duplicate a many-to-many relation;
- installing an already installed compatible module validates it rather than reinstalling it.

## 14. Ownership and drift policy

Each managed field or record is classified:

- **Controlled:** Provisioning owns the declared value and reports drift.
- **Mergeable:** Provisioning ensures required elements exist but preserves approved user additions.
- **Observe-only:** Provisioning validates or reports but never changes the value.
- **Unmanaged:** Outside the manifest boundary.

The policy prevents a rerun from overwriting legitimate customer changes simply because the original sandbox value differs.

## 15. Transactions and failure isolation

Operations should use the Odoo ORM and its normal security model whenever possible.

Transaction rules:

- validate before write;
- use one transaction for a coherent bounded operation;
- use savepoints to isolate independently recoverable items;
- batch creates and writes where appropriate;
- avoid manual commits inside ordinary business operations;
- retry only errors classified as transient;
- treat validation, access and integrity errors as non-transient until corrected;
- preserve original failure and correlation identifiers in sanitized logs.

Direct SQL is prohibited when ORM behavior is available. If verified performance or platform needs require SQL, handlers use parameterized Odoo-supported SQL utilities and receive architecture and security review.

## 16. Retry policy

Errors are classified as:

- transient infrastructure;
- transient database concurrency;
- dependency unavailable;
- invalid desired state;
- unsupported current state;
- access or policy denied;
- business validation failed;
- module installation failed;
- unknown.

Only transient classes retry automatically. Retries use bounded attempts, backoff and the same idempotency key. Unknown errors do not retry indefinitely.

Dependent operations remain blocked until the prerequisite is successful or manually resolved through an audited action.

## 17. Rollback, compensation and rebuild

Not all Odoo configuration changes are safely reversible. The engine declares one strategy per operation:

- transaction rollback before commit;
- compensating operation;
- snapshot restore;
- environment rebuild from the last approved manifest;
- manual recovery procedure.

The MVP default for a materially failed fresh sandbox is:

1. preserve logs and validation evidence;
2. mark the environment Failed;
3. correct the blueprint, manifest, handler or environment cause;
4. provision a replacement sandbox from an approved manifest;
5. archive or remove the failed runtime only under explicit retention policy.

Module uninstall and broad data deletion are not generic rollback mechanisms.

## 18. Concurrency and locking

- Only one mutating Provisioning Run may target an environment at a time.
- Manifest compilation and read-only inspection may occur concurrently when version boundaries are respected.
- Operations acquire narrower logical locks where supported.
- A stale lock requires an audited recovery procedure.
- Concurrent customer or consultant changes during provisioning are blocked or detected as drift before release.

## 19. Odoo 19 module installation rules

1. Use exact technical module names from the approved catalogue release.
2. Resolve `depends` from verified Odoo manifests.
3. Verify external Python and binary dependencies before installation.
4. Respect pinned core, Enterprise, localization and addon revisions.
5. Install dependency-safe groups and record actual resolved state.
6. Run installation and post-install tests according to module policy.
7. Treat pre-init, post-init and uninstall hooks as elevated-risk behavior requiring catalogue evidence.
8. Keep demonstration data explicitly controlled.
9. Do not mark a module successful until registry loading and mandatory validation succeed.
10. Do not modify source to force a failed module to install during a run.

## 20. Validation architecture

Validation is layered.

### 20.1 Infrastructure validation

- runtime and database health;
- storage and routing availability;
- expected runtime and source revisions;
- backup or snapshot readiness;
- network and endpoint policy.

### 20.2 Odoo platform validation

- database loads without registry failure;
- base and Enterprise runtime are healthy;
- expected languages and timezone behavior;
- no unexpected module states;
- scheduled workers and mail behavior follow sandbox policy;
- no production endpoint or credential is unintentionally configured.

### 20.3 Module validation

- selected modules installed;
- dependencies installed at compatible revisions;
- excluded modules not accidentally selected except documented technical dependencies;
- install/update test suites pass where required;
- module manifests and source checksums match the approved catalogue.

### 20.4 Configuration validation

- companies and organizational structures match desired state;
- company-specific settings are applied in correct context;
- managed records and external identifiers resolve uniquely;
- configuration options hold expected values;
- sequences, stages, terms and templates exist as declared;
- demonstration data is labeled and isolated.

### 20.5 Security validation

- approved users have intended groups and company access;
- model create, read, write and delete permissions match the design;
- record rules enforce company and ownership boundaries;
- restricted fields are unavailable to unauthorized roles;
- portal users cannot reach internal records;
- negative tests verify prohibited actions;
- alternate RPC, import and batch paths do not bypass critical controls.

### 20.6 Business-process validation

Tests are generated or selected from blueprint acceptance criteria, for example:

- create lead, progress opportunity and produce quotation;
- confirm an approved order and verify delivery/invoice trigger;
- receive stock and verify traceability behavior;
- record project time and verify billable outcome;
- submit transaction above an approval threshold and verify blocking;
- verify customer portal visibility.

### 20.7 User-interface and RTL validation

- Hebrew is available and renders RTL correctly;
- English US is available where required;
- key forms and lists are usable in both languages;
- critical tours execute in the intended interface;
- accessibility checks cover keyboard, focus, labels, contrast and error messaging.

### 20.8 Performance validation

- agreed smoke volumes complete within policy;
- critical operations avoid obvious query explosion;
- query-count assertions exist for custom handlers or modules where relevant;
- installation and startup remain within defined timeout classes.

## 21. Validation result model

Every result contains:

- rule key and version;
- run and environment;
- linked manifest declaration, decision and acceptance criterion;
- mandatory or advisory classification;
- exact inspected scope;
- expected and observed result;
- status: passed, failed, warning, skipped or unable to evaluate;
- sanitized evidence and timestamps;
- executor identity and tool version;
- remediation guidance;
- retest history.

Skipped and Unable to Evaluate are not equivalent to Passed.

## 22. Deviation management

A Deviation is created when:

- current state conflicts with desired state;
- an operation applies a different result than declared;
- a mandatory validation fails;
- user changes introduce controlled drift;
- actual module or source revision differs;
- environment characteristics no longer match the manifest;
- an operation requires unsupported manual intervention.

Deviation severity:

- Critical: security, isolation, data integrity or unusable environment;
- High: mandatory business behavior or module state incorrect;
- Medium: material configuration mismatch with workaround;
- Low: advisory or cosmetic difference.

Allowed resolutions:

- correct environment to match manifest;
- approve a new blueprint and manifest revision;
- accept a bounded deviation with owner, reason and expiry;
- rebuild environment;
- close as false positive after rule correction and evidence.

The engine never edits an approved manifest to match accidental environment state.

## 23. Provisioning Run model

Each run records:

- run identifier and correlation key;
- manifest, plan and environment snapshots;
- requester and authorizer;
- handler, rule and adapter releases;
- start, heartbeat and completion timestamps;
- current stage and overall state;
- operations and attempts;
- validation results and deviations;
- sanitized logs and artifact references;
- final readiness decision;
- cancellation, interruption or recovery history.

Run states:

- planned;
- awaiting authorization;
- queued;
- running;
- paused;
- blocked;
- cancelling;
- cancelled;
- failed;
- completed with warnings;
- completed;
- superseded.

## 24. Logging and audit

Logs serve troubleshooting; audit events prove authority and change history. They are separate.

Logs must:

- use structured event fields and correlation identifiers;
- identify handler, stage and environment;
- redact secrets and sensitive payloads;
- avoid unnecessary customer personal data;
- retain enough context to reproduce failures;
- use controlled retention.

Audit events include:

- manifest compilation and approval;
- provisioning authorization;
- secret-resolution request without secret value;
- environment creation and lifecycle change;
- every mutating operation outcome;
- manual override or deviation acceptance;
- readiness release;
- access grant;
- rebuild, archive or destruction authorization.

## 25. Access and segregation of duties

Recommended platform roles:

| Role | Authority |
| --- | --- |
| Blueprint Approver | Approves business and technical solution version |
| Manifest Compiler | Produces candidate manifest, cannot approve it |
| Manifest Approver | Authorizes manifest for a named environment |
| Provisioning Operator | Starts and monitors approved runs |
| Environment Administrator | Manages infrastructure, not business approval |
| Validation Reviewer | Reviews results and deviations |
| Customer Reviewer | Accesses released sandbox and acceptance tasks |

Tenant policy may prohibit the same person from approving the blueprint and manifest or from authorizing and accepting a deviation.

## 26. Sandbox release package

When mandatory validation passes, the engine produces:

- environment access instructions;
- purpose, scope and expiry;
- blueprint and manifest version;
- installed application summary;
- configured process summary;
- demonstration-data notice;
- known gaps, warnings and accepted deviations;
- test accounts and business roles through secure delivery;
- customer review scenarios;
- support and feedback route;
- validation and traceability report.

Credentials are delivered through an approved secret or invitation flow, never embedded in the report.

## 27. Customer review and acceptance

The released sandbox contains guided scenarios derived from blueprint acceptance criteria.

Feedback is classified as:

- defect against approved blueprint;
- configuration correction;
- discovery correction;
- new requirement;
- usability or training issue;
- accepted behavior;
- deferred enhancement.

Feedback that changes approved scope or desired state creates a Change Request and, when material, new discovery, blueprint and manifest versions.

## 28. Example operation

Conceptual declaration:

```yaml
- operationKey: org.company.main
  handler: odoo.company.upsert
  handlerVersion: 1.0.0
  scope: database
  desired:
    logicalId: company.main
    name: Example Israel Ltd
    countryRef: base.il
    currencyRef: base.ILS
  ownership:
    name: controlled
    countryRef: controlled
    currencyRef: observe_after_accounting_activation
  traceability:
    decisions: [BP-ORG-001]
    requirements: [REQ-ORG-001]
  validations:
    - company.exists_and_unique
    - company.country_and_currency
```

Execution behavior:

1. Resolve `company.main` through managed external identity.
2. If absent, create it using the verified handler.
3. If present, compare only fields under provisioning ownership.
4. If controlled fields differ and policy allows, plan the update.
5. If an observe-only or protected accounting state conflicts, create a deviation.
6. Validate uniqueness, country, currency and company context.

The example is illustrative and does not establish final field names or mutability rules without verification against the pinned Odoo 19 source and localization.

## 29. Recovery scenarios

### Interrupted run

- retain run and operation state;
- verify environment and transaction outcome;
- reinspect current state;
- resume only operations proven incomplete or noncompliant;
- use the same manifest and idempotency keys.

### Module installation failure

- stop dependent stages;
- preserve registry and module logs;
- classify source, dependency, configuration or environment cause;
- do not modify source during the run;
- correct through a new approved artifact or rebuild.

### Validation failure

- leave environment unreleased;
- create deviations linked to expected behavior;
- allow bounded corrective run only from approved manifest logic;
- otherwise revise blueprint/manifest or rebuild.

### Drift after release

- inspect controlled and mergeable fields;
- report impact;
- avoid overwriting customer changes automatically;
- reconcile through explicit consultant action or a new manifest.

## 30. Operational metrics

Measure:

- time from approved blueprint to ready sandbox;
- compilation and preflight failure rates;
- operation success, retry and failure by handler;
- percentage already compliant on rerun;
- module installation failures by source revision;
- validation failures by category;
- deviations caused by missing discovery or blueprint errors;
- rebuild rate;
- average recovery time;
- drift after release;
- customer scenario acceptance rate.

Metrics must not reward suppressing validations or classifying failures as warnings.

## 31. Provisioning acceptance criteria

The Provisioning Engine is acceptable for MVP when:

1. Only an approved blueprint produces a candidate manifest.
2. Only an approved manifest can start a mutating run.
3. The manifest pins source, catalogue and handler releases.
4. The manifest contains secret references and rejects secret values.
5. Module dependencies resolve from verified manifests.
6. Every configuration item maps to a versioned handler and validation.
7. Current state is inspected before every write.
8. A second run of the same manifest creates no duplicate managed records.
9. Ambiguous record identity blocks the operation.
10. Unsupported destructive changes do not run automatically.
11. Failed prerequisites block dependents.
12. Transient retries are bounded and idempotent.
13. Mandatory validations cover platform, modules, configuration and security.
14. Business smoke tests link to blueprint acceptance criteria.
15. Hebrew RTL and English behavior are tested where in scope.
16. A failed validation prevents Sandbox Ready status.
17. Deviations are explicit and never rewrite the approved manifest.
18. Logs do not expose secrets.
19. Every applied change is traceable to approval and requirement.
20. A materially failed disposable sandbox can be rebuilt reproducibly.

## 32. Initial API boundary

The Provisioning domain must expose operations equivalent to:

- compile manifest from approved blueprint;
- validate and compare manifest revisions;
- approve manifest for environment;
- create or resolve sandbox environment;
- inspect environment current state;
- generate provisioning plan;
- authorize and start run;
- retrieve run progress and logs;
- pause or cancel at safe boundaries;
- execute or retry eligible operation;
- run validation suite;
- list and resolve deviations;
- release sandbox for review;
- request rebuild;
- export readiness and traceability reports.

Exact protocol and infrastructure adapter design are deferred.

## 33. Next design package

The next package should define the **MVP Application Architecture and Delivery Plan**, including:

- control-plane technology architecture;
- service and aggregate boundaries;
- persistence and event model;
- AI gateway and deterministic rule engine;
- Odoo source and capability-catalogue ingestion;
- provisioning adapter architecture;
- authentication, tenancy and permissions;
- deployment topology and environments;
- observability and operations;
- repository structure;
- phased implementation backlog and release acceptance.
