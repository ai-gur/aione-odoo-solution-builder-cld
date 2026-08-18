# AIOne Odoo Solution Builder

## Customer Solution Portfolio and Lifecycle Management

**Version:** 0.1  
**Date:** 18 August 2026  
**Status:** Initial design baseline  
**Depends on:** Product Constitution, Discovery Engine, Blueprint Engine, Provisioning Engine and MVP Architecture

## 1. Objective

The Customer Solution Portfolio provides AIOne with one secure administrator portal for managing every customer, their tailored discovery program, approved Odoo solution, software provenance, environments, historical decisions and future changes.

It allows an authorized user to answer, at any time:

- What business did we understand this customer to operate?
- What problems and outcomes defined the implementation?
- What solution did we approve and why?
- What Odoo capabilities, applications and modules were included?
- What was configured or developed specifically for this customer?
- Which environment represents the current accepted baseline?
- What changed, who approved it and what remains unresolved?
- What would be affected if the customer requests a new capability?

## 2. Product model

There is one shared AIOne Solution Builder platform. It does not deploy an independent Solution Builder application for every customer.

Each customer receives one or more isolated **Solution Workspaces** inside the platform. A workspace contains that customer’s tailored discovery, versions, environments, changes and lifecycle history.

```text
AIOne Tenant
  └── Customer Organization
       ├── Solution Workspace: Main ERP
       │    ├── Discovery versions
       │    ├── Blueprint versions
       │    ├── Solution baselines
       │    ├── Manifest versions
       │    ├── Environments
       │    ├── Change requests
       │    └── Audit timeline
       └── Solution Workspace: Additional business or later program
```

A customer may have several workspaces when separate programs have materially different scope, governance or Odoo environments. Workspaces must not be created merely to represent ordinary implementation phases.

## 3. Core entities

### 3.1 Customer Organization

Represents the commercial and legal customer relationship.

Key information:

- internal customer identifier;
- legal and trading names;
- countries and industries;
- commercial owner and solution owner;
- primary contacts and process owners;
- customer status;
- data classification and retention policy;
- contractual and support references;
- active workspaces;
- last review and next recommended review.

### 3.2 Solution Workspace

The long-lived container for one customer solution lifecycle.

Key information:

- stable workspace identifier and display name;
- customer organization;
- business scope and owning sponsor;
- target Odoo edition and release line;
- primary and secondary languages;
- lifecycle state;
- current accepted baseline;
- active working change set;
- related environments;
- software provenance;
- support and review status;
- risk, health and completeness summary.

Workspace states:

- proposed;
- discovering;
- designing;
- sandbox active;
- customer review;
- accepted;
- operating;
- change in progress;
- suspended;
- archived;
- closed.

### 3.3 Customer Solution Baseline

An immutable snapshot of the complete accepted customer solution at a point in time.

A baseline references:

- approved discovery version;
- approved blueprint version;
- approved deployment manifest;
- Odoo capability-catalogue release;
- questionnaire and customer-overlay versions;
- applications, modules and source revisions;
- configuration and security design;
- integrations and data responsibilities;
- gaps, assumptions and accepted deviations;
- relevant environments and validation results;
- customer and AIOne acceptance events;
- custom-code repository releases where applicable.

Only one baseline is Current Accepted for a workspace. Earlier baselines remain immutable and searchable.

### 3.4 Solution Timeline Event

A customer-readable or internal chronological event representing:

- discovery started or approved;
- blueprint proposed, changed or approved;
- manifest compiled or approved;
- sandbox provisioned, validated or released;
- customer feedback;
- change request submitted or completed;
- software release attached;
- environment state change;
- assumption or deviation accepted;
- periodic review;
- access or ownership change.

Timeline events summarize domain events without replacing append-only audit records.

### 3.5 Change Request

A controlled request to change an accepted customer solution.

Required attributes:

- stable change identifier;
- source customer and workspace;
- requester, sponsor and owner;
- business problem and requested outcome;
- urgency and target date;
- affected users and processes;
- initial priority and risk;
- source baseline;
- targeted discovery requirements;
- impact assessment;
- proposed requirements and decisions;
- approval and delivery state;
- resulting baseline when completed.

### 3.6 Software Repository Registration

Records a software repository relevant to a workspace without storing code in the control database.

Required attributes:

- logical repository identifier;
- repository class;
- provider and protected reference;
- owner and visibility;
- permitted customer workspaces;
- default branch and release policy;
- current approved release tag and commit SHA;
- source revision used by each environment;
- security and maintenance status;
- last verification and responsible maintainer.

Repository URL visibility is restricted. Authentication credentials are secret references, never repository records.

## 4. Repository policy

### 4.1 Repository classes

| Class | Purpose | Customer-specific repository required? |
| --- | --- | --- |
| Solution Builder | Shared administrator portal and engines | No, one platform repository |
| Odoo Foundation | Shared Odoo 19 environment and tooling | No, one Foundation repository |
| AIOne Shared Addons | Reusable reviewed AIOne modules and integrations | No, shared repository |
| Customer Custom Code | Code useful only for one customer or contract | Yes, when such code exists |
| External Approved Addon | Third-party source used by a solution | Register pinned source; do not copy unless license and policy require it |

### 4.2 Customer repository decision

A customer-specific private repository is created only when at least one of these applies:

- an isolated custom Odoo module is required;
- an integration contains customer-specific code;
- customer-specific migration code must be maintained;
- contractual ownership or delivery terms require separate source;
- release and access isolation cannot be achieved safely in a shared addon repository.

Ordinary Odoo configuration, questionnaire answers, blueprints and manifests do not justify a customer repository.

### 4.3 Shared-addon eligibility

Code belongs in the shared AIOne addons repository when:

- it solves a reusable capability rather than embedding one customer’s policy;
- tenant and company behavior are configurable;
- it contains no customer identity, credentials or private data;
- AIOne assumes maintenance responsibility;
- licensing permits reuse;
- tests cover general supported behavior;
- the capability catalogue can describe it independently of one customer.

If a customer-funded feature later becomes reusable, moving it requires commercial, licensing, security and architecture review. It is not copied silently.

### 4.4 Repository contents

A customer-specific repository may contain:

- customer-specific Odoo addons;
- integration adapters and contracts;
- migration scripts and mapping definitions;
- automated tests;
- sanitized fixtures;
- technical architecture and runbooks;
- release metadata;
- non-sensitive solution references.

It must not contain:

- questionnaire answers;
- uploaded customer documents;
- production database dumps;
- personal or financial records;
- environment passwords, API keys or private keys;
- raw provisioning logs;
- unredacted evidence;
- populated `.env` files.

### 4.5 Naming and identity

Use an internal customer code rather than a sensitive customer name where practical:

```text
aione-customer-C0127-odoo
```

The portal maps this repository to the customer. Repository names are not the authoritative customer record.

### 4.6 Release policy

- Default branch represents supported source, not environment state.
- Changes use reviewable pull requests.
- Accepted releases receive immutable tags.
- The portal records release tag, commit SHA and artifact digest.
- Environments point to exact revisions, never only a floating branch.
- A release must pass defined tests before it may enter an approved manifest.
- Repository history does not replace blueprint, manifest or audit history.

## 5. Tailored questionnaire management

Each workspace receives an **Interview Program** composed of:

1. A pinned global interview-definition version
2. Activated domains and depth
3. Customer-specific overlay
4. Assigned respondents and ownership
5. Supporting evidence policy
6. Review and escalation rules

The customer overlay may:

- change customer-facing wording without changing meaning;
- add approved customer-specific questions;
- prefill confirmed stable facts;
- disable irrelevant optional topics;
- assign sections to specific roles;
- define additional evidence requirements;
- add targeted follow-ups for an active change request.

The overlay may not:

- remove mandatory safety, finance or security questions;
- weaken approval or completeness rules;
- rewrite historical interview runs;
- convert an unverified claim into a confirmed fact;
- introduce arbitrary executable rules.

When the global interview improves, an existing workspace remains pinned to its historical version. A consultant may adopt a newer version through a reviewed upgrade that shows new, changed and retired information goals.

## 6. Administrator Portal

### 6.1 Portfolio dashboard

Shows all customers and workspaces with:

- customer and workspace name;
- lifecycle and commercial status;
- current Odoo and Foundation release;
- current baseline version;
- active environments and health;
- last customer or consultant activity;
- open change requests;
- blocking questions, deviations or failed validations;
- upcoming review, expiry or maintenance event;
- solution owner and next action.

Filters include owner, industry, Odoo release, capability, module, integration, risk, lifecycle state and last activity.

### 6.2 Customer 360

Provides:

- business and relationship summary;
- contacts and process owners;
- workspaces and current baselines;
- business outcomes and success measures;
- recent activity and unresolved risks;
- environments, repositories and support context;
- change history;
- documents and access controls;
- scheduled reviews.

### 6.3 Solution recap

A generated recap uses only the current accepted baseline and clearly labels later drafts.

It includes:

- business model and scope;
- original problems and intended outcomes;
- To-Be processes;
- Odoo capabilities, applications and modules;
- organization, role and approval design;
- data and integration responsibilities;
- configuration specific to the customer;
- custom development and software releases;
- assumptions, gaps and accepted deviations;
- environment and validation status;
- changes since the preceding baseline.

The recap links every conclusion to its source version.

### 6.4 Questionnaire management

- view all interview programs and runs;
- see active template and overlay versions;
- resume, reassign or request clarification;
- compare historical answers;
- identify facts due for revalidation;
- start targeted discovery for a change;
- preview adoption of a newer global questionnaire version.

### 6.5 Solution and environment management

- view discovery, blueprint, manifest and baseline versions;
- compare any two accepted baselines;
- inspect modules, configuration, integrations and gaps;
- see environments and exact software revisions;
- view validation and deviation status;
- request a new sandbox, rebuild or change analysis according to authority.

### 6.6 Repository registry

- list shared and customer-specific repositories;
- show ownership, access class and maintenance status;
- show which customers and environments consume each release;
- identify unpinned or outdated revisions;
- link releases to blueprint and manifest versions;
- flag repositories containing unsupported or unreviewed code.

The MVP may initially synchronize repository metadata through configured GitHub integration or CI events. It must not require GitHub to store customer discovery data.

## 7. Change lifecycle

### 7.1 Intake

Change sources include:

- customer request;
- consultant recommendation;
- regulatory or localization change;
- Odoo version or addon change;
- validation failure or operational incident;
- new integration or business unit;
- periodic solution review.

### 7.2 Triage

Classify as:

- defect against accepted baseline;
- configuration correction;
- new capability;
- capability expansion;
- process change;
- integration change;
- data or migration change;
- security or compliance change;
- software maintenance;
- training or documentation request.

Defects do not become new requirements merely to hide failure against the accepted baseline.

### 7.3 Targeted discovery

The engine starts from the Current Accepted baseline and asks only what is missing for the proposed change. Existing facts are reused unless stale, contradicted or explicitly affected.

### 7.4 Impact analysis

Impact covers:

- requirements and processes;
- organizational units and roles;
- applications, modules and dependencies;
- configuration and security;
- master data and migration;
- integrations and reports;
- custom code and repository needs;
- environments and regression tests;
- effort, risk and delivery phase;
- assumptions, gaps and customer responsibilities.

### 7.5 Approval and implementation

1. Approve change requirements.
2. Generate a new blueprint version against the source baseline.
3. Compare decisions and affected capabilities.
4. Develop or select software release where required.
5. Compile and approve a new manifest.
6. Provision or update a sandbox under MVP policy.
7. Run new and regression validations.
8. Conduct customer review.
9. Accept the new Customer Solution Baseline.
10. Preserve the prior baseline unchanged.

### 7.6 Change states

- submitted;
- triaging;
- clarification required;
- discovery active;
- impact assessment;
- awaiting approval;
- approved;
- implementation active;
- sandbox validation;
- customer review;
- accepted;
- rejected;
- deferred;
- cancelled;
- superseded.

## 8. Baseline comparison

The portal compares:

- business scope and success measures;
- confirmed facts and assumptions;
- requirements added, changed or removed;
- processes and exceptions;
- blueprint decisions and alternatives;
- applications, modules and source revisions;
- roles, permissions and approvals;
- configuration values under management;
- data ownership and migration;
- integrations and endpoints by non-secret identity;
- custom-code releases;
- validations and accepted deviations;
- environments using each baseline.

Differences are categorized as business, configuration, security, software, data, integration or operational.

## 9. Search and reporting

Authorized AIOne users may search across the portfolio for structured, non-secret information, for example:

- customers using a specific Odoo module or addon;
- customers with serial-number tracking;
- workspaces connected to a particular payment provider;
- customers affected by a withdrawn addon release;
- accepted baselines using an older Foundation revision;
- unresolved high-risk assumptions;
- environments due for review or expiry.

Cross-customer search returns only fields permitted for the user’s AIOne role. Customer users cannot perform portfolio-wide search.

## 10. Storage architecture

| Information | Authoritative storage |
| --- | --- |
| Customer and workspace records | Control-plane PostgreSQL |
| Interview answers and requirements | Control-plane PostgreSQL |
| Documents and evidence | Encrypted object storage plus metadata in PostgreSQL |
| Approved discovery, blueprint, manifest and baseline snapshots | Immutable structured records and artifacts |
| Approvals and audit | Append-only audit storage |
| Environment and run state | PostgreSQL environment registry |
| Credentials | Secret provider |
| Shared platform and addons code | Shared Git repositories |
| Customer-specific code | Conditional private Git repository |
| Release artifacts | Immutable artifact registry or storage |

Git is not the authoritative store for questionnaires, evidence, requirements, approvals or customer history.

## 11. Safety and retention

- Encrypt data in transit and at rest.
- Enforce tenant, customer, workspace and project authorization.
- Use immutable accepted baselines.
- Keep append-only material audit events.
- Use object versioning and integrity checks for evidence and exports.
- Back up control data and support point-in-time recovery.
- Test restoration, not only backup creation.
- Retain or delete evidence by classification, contract and applicable policy.
- Remove customer access when membership ends without deleting historical approvals.
- Keep repository credentials and environment secrets outside portfolio data.
- Export customer solution history through a controlled, audited process.
- Do not expose internal repository or infrastructure metadata to customer users unless explicitly allowed.

## 12. Roles

| Role | Portfolio authority |
| --- | --- |
| AIOne Portfolio Administrator | Manage customers, workspaces, ownership and policies |
| Account Owner | View customer commercial and solution summary |
| Solution Owner | Maintain workspace and coordinate changes |
| Consultant | Conduct discovery and propose blueprint changes |
| Solution Architect | Approve architecture, custom code and repository use |
| Provisioning Operator | Manage approved sandbox operations |
| Repository Maintainer | Manage approved code releases and provenance |
| Customer Sponsor | Review scope, outcomes and accepted baseline |
| Customer Process Owner | Review assigned processes and changes |
| Auditor | Read scoped immutable history and evidence |

Repository access is separate from portal role. A consultant does not automatically receive source-code access.

## 13. Notifications and reviews

The portal supports:

- pending questionnaire or clarification reminders;
- blueprint and change approvals;
- failed provisioning or validation;
- expiring sandbox;
- stale facts or assumptions requiring review;
- repository release affecting customer environments;
- withdrawn addon or security issue;
- periodic solution-health review;
- change request inactivity or blocked ownership.

Review schedules are stored per workspace and may differ by domain. Finance, security or external integration facts may require more frequent confirmation than general business descriptions.

## 14. Analytics

- active customers and workspaces;
- time from change request to accepted baseline;
- changes by type and affected domain;
- reuse of standard versus shared versus customer-specific capabilities;
- customer-specific repository count and maintenance status;
- customers per shared addon release;
- stale or unsupported solution baselines;
- provisioning and validation success by release;
- recurring gaps that should become shared product capabilities;
- customer acceptance and realized success measures.

Analytics must not expose one customer’s confidential details to another.

## 15. MVP scope

The first portfolio release includes:

- customer organization list and Customer 360;
- one or more solution workspaces per customer;
- current accepted solution baseline;
- chronological solution timeline;
- tailored interview program and overlay identity;
- discovery, blueprint, manifest and environment history;
- change-request intake and targeted-discovery workflow;
- baseline comparison;
- repository registry and software-release references;
- conditional customer-repository classification;
- role-based access and audit;
- solution recap export.

Initial Git integration may be metadata-based and manually confirmed. Automatic repository creation, branch protection or pull-request management can follow after core lifecycle behavior is stable.

## 16. Acceptance criteria

The capability is acceptable when:

1. AIOne can list all authorized customers and active workspaces.
2. A customer can have several workspaces without mixing their histories.
3. Each workspace has exactly one Current Accepted baseline or none before acceptance.
4. Accepted baselines are immutable.
5. A solution recap can be regenerated from an accepted baseline.
6. Historical questionnaires retain their exact global template and overlay versions.
7. Updating a global questionnaire does not rewrite customer history.
8. A change request starts from a named accepted baseline.
9. Targeted discovery reuses unaffected facts and asks only necessary questions.
10. Impact analysis identifies process, module, security, data, integration and software consequences.
11. Completing a change produces a new accepted baseline and preserves the old one.
12. Configuration-only customers require no customer Git repository.
13. Customer-specific code requires a registered private repository and pinned release.
14. No customer data, evidence or secret is required in Git.
15. Every environment identifies its blueprint, manifest, catalogue and software revisions.
16. AIOne can identify all workspaces affected by a shared addon release.
17. Customer users cannot view other customers or portfolio-wide repository information.
18. Change, approval and repository-release events appear in audit history.
19. Backups and a controlled customer solution-history export are verified.

## 17. API boundary

The Portfolio domain must expose operations equivalent to:

- create and update customer organization;
- create and manage solution workspace;
- list portfolio and health indicators;
- retrieve Customer 360;
- create immutable solution baseline;
- set current accepted baseline through approval;
- compare baselines;
- generate solution recap;
- create and triage change request;
- start targeted discovery from baseline;
- calculate and approve change impact;
- register repository and software release;
- link release to blueprint, manifest and environment;
- identify affected workspaces by release;
- schedule and complete solution review;
- export scoped solution history.

Exact endpoint and event definitions are deferred to implementation architecture.

## 18. Delivery placement

Portfolio foundations begin before discovery:

- Increment 1 creates Customer Organizations, Solution Workspaces and portfolio authorization.
- Increment 2 attaches Quick Start discovery to a workspace.
- Increment 4 attaches blueprints and creates draft solution-baseline views.
- Increment 5 attaches manifests, environments and software provenance.
- Increment 7 implements accepted baselines, solution recap and customer review.
- Increment 8 implements complete change-request and targeted-discovery lifecycle.
- Repository automation beyond metadata registration follows as a later increment.
