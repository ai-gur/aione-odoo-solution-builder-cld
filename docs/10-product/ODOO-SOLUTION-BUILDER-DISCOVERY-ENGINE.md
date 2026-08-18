# AIOne Odoo Solution Builder

## Discovery Model and Interview Engine

**Version:** 0.1  
**Date:** 18 August 2026  
**Status:** Initial design baseline  
**Depends on:** `ODOO-SOLUTION-BUILDER-PRODUCT-CONSTITUTION.md`

## 1. Objective

The Discovery Engine obtains the minimum reliable understanding of a customer required to create an explainable Odoo Enterprise 19 blueprint and provision an appropriate sandbox.

It must minimize customer effort without hiding uncertainty. It uses progressive discovery: start simply, ask relevant follow-ups, and escalate only the topics that materially affect configuration, risk or implementation scope.

## 2. Discovery outcomes

Every completed discovery produces:

- confirmed and inferred business facts;
- organizational structure;
- business capabilities and processes;
- atomic requirements and acceptance criteria;
- constraints and dependencies;
- business roles and approval needs;
- existing systems and integration needs;
- data-migration scope;
- problems, objectives and success measures;
- assumptions, conflicts and open questions;
- complexity, confidence, completeness and risk assessments;
- sufficient structured input for blueprint generation.

## 3. Experience principles

1. Use customer language, not Odoo terminology, during initial discovery.
2. Ask one clear question at a time in customer self-service mode.
3. Explain why sensitive or demanding information is needed.
4. Show progress by relevant sections, not by a misleading fixed question count.
5. Save after every answer and allow pause and resume.
6. Do not ask the customer to repeat information already supplied.
7. Allow “I don’t know” and route the question to an appropriate owner.
8. Separate required questions from optional enrichment.
9. Confirm extracted or inferred information before treating it as verified.
10. Make skipped sections and their reasons visible to the consultant.
11. Support professional Hebrew with complete RTL and English US.
12. Meet WCAG 2.2 AA interaction and content requirements.

## 4. Discovery modes

### 4.1 Quick Start

**Goal:** Obtain enough information to recommend a preliminary Odoo footprint and create a demonstration sandbox.

**Target effort:** 10–15 minutes.  
**Typical respondent:** Owner, CEO, COO or senior manager.  
**Expected questions:** 12–18, depending on branching.  
**Permitted output:** Initial blueprint and demonstration sandbox with visible assumptions.  
**Not sufficient for:** Production scope approval, complex permissions, accounting design, migration execution or custom-development approval.

### 4.2 Guided Discovery

**Goal:** Obtain a reliable operational understanding for a typical small or mid-market implementation.

**Target effort:** 35–60 minutes, optionally split between people.  
**Typical respondents:** Sponsor plus relevant process owners.  
**Expected questions:** 35–70, depending on business scope.  
**Permitted output:** Reviewable solution blueprint and validated sandbox.

### 4.3 Comprehensive Discovery

**Goal:** Specify complex, multi-company, regulated, integrated or operationally critical implementations.

**Target effort:** 2–4 structured workshops plus evidence review.  
**Typical respondents:** Sponsor, process owners, finance, IT, security and data owners.  
**Expected questions:** Determined by scoped processes and exceptions, not a fixed count.  
**Permitted output:** Detailed implementation architecture and phased sandbox program.

## 5. Shared discovery domains

All three modes write into these shared domains:

| Code | Domain | Purpose |
| --- | --- | --- |
| ORG | Organization | Legal entities, branches, sites, departments and ownership |
| STR | Strategy | Problems, objectives, priorities, KPIs and scope |
| CUS | Customers | Customer types, channels, terms and service expectations |
| OFF | Offerings | Products, services, subscriptions, projects and bundles |
| CRM | Marketing and CRM | Lead sources, qualification, pipeline and activities |
| SAL | Sales | Quotations, pricing, contracts, approvals and orders |
| PUR | Purchasing | Suppliers, purchase flows, approvals and replenishment |
| INV | Inventory and Logistics | Warehouses, stock, traceability, fulfillment and returns |
| MRP | Manufacturing | Bills of materials, work centers, planning and quality |
| SRV | Projects and Services | Delivery, projects, timesheets, planning and field service |
| SUP | Support | Tickets, SLAs, warranties, repairs and customer service |
| FIN | Finance | Accounting, invoicing, tax, payments, expenses and controls |
| HCM | People | Employees, roles, attendance, leave and recruitment |
| DOC | Documents | Files, knowledge, signatures, retention and templates |
| WEB | Digital Channels | Website, eCommerce, portals and online appointments |
| DAT | Data | Master data, history, quality, ownership and migration |
| INT | Integrations | External systems, APIs, identity, devices and messaging |
| SEC | Security | Access, segregation of duties, privacy, audit and continuity |
| REP | Reporting | Operational reports, dashboards, KPIs and exports |
| AUT | Automation and AI | Repetitive decisions, automation opportunities and controls |
| IMP | Implementation | Timeline, phasing, resources, training and acceptance |

## 6. Quick Start interview

The Quick Start interview should feel conversational. The following are canonical information goals; localized wording may adapt to the respondent.

### QS-01 Business identity

**Question:** In one or two sentences, what does your company do?  
**Answer type:** Short narrative plus optional website.  
**Produces:** Industry candidates, business-model candidates and terminology.  
**Follow-up:** Confirm the system’s concise interpretation.

### QS-02 Offerings

**Question:** What do you sell or deliver?  
**Options:** Physical products, services, projects, subscriptions, manufactured products, digital products, rentals, combination.  
**Branching:** Activates relevant OFF, INV, MRP, SRV and SAL branches.

### QS-03 Customers and channels

**Question:** Who buys from you and how do they buy?  
**Options:** Businesses, consumers, government, internal group companies; sales team, store, website, marketplace, tender, recurring agreement, other.  
**Produces:** Customer segments, sales channels and portal/eCommerce candidates.

### QS-04 Scale

**Question:** Approximately how large is the operation?  
**Fields:** Employees, expected Odoo users, monthly orders or transactions, annual revenue band optional.  
**Purpose:** Configuration sizing and complexity signals, not infrastructure sizing by itself.

### QS-05 Organization footprint

**Question:** How many legal companies, branches, countries, stores, warehouses and operating sites need to be included?  
**Branching:** Multi-company, multi-currency, localization and warehouse discovery.

### QS-06 Required business areas

**Question:** Which activities should the new system manage?  
**Options:** CRM, sales, purchasing, inventory, manufacturing, projects, timesheets, field service, support, accounting, expenses, HR, documents, signatures, website, eCommerce, marketing, subscriptions, appointments, reporting.  
**Behavior:** Recommend likely missing areas but require confirmation before adding them to scope.

### QS-07 Current working method

**Question:** What do you use today to run these activities?  
**Options:** Another ERP, CRM, accounting system, spreadsheets, paper, separate applications, mostly informal processes.  
**Follow-up:** Capture names only for systems relevant to scope.

### QS-08 Inventory trigger

**Applicability:** Physical, manufactured or rental items selected.  
**Question:** Do you purchase, store, track or deliver physical items?  
**Fields:** Warehouses, serial or lot tracking, expiry dates, dropshipping, imports, returns.  
**Behavior:** Any complex selection escalates INV in Guided Discovery.

### QS-09 Service delivery trigger

**Applicability:** Services or projects selected.  
**Question:** How do you plan and record delivery?  
**Options:** Tasks, projects, appointments, shifts, field visits, timesheets, milestones, informal follow-up.  
**Behavior:** Activates project, planning, field service and timesheet candidates.

### QS-10 Manufacturing trigger

**Applicability:** Manufactured products selected.  
**Question:** Is production simple assembly or does it require work centers, routing, subcontracting, quality or maintenance?  
**Behavior:** Anything beyond simple assembly creates mandatory Comprehensive discovery for MRP while allowing unrelated domains to remain Guided.

### QS-11 Finance and Israel

**Question:** Should Odoo issue invoices and manage accounting for Israeli entities?  
**Options:** Full accounting, invoicing only, external accountant/system, undecided.  
**Follow-up:** Currency, VAT, withholding, payment providers and current accounting system at a high level.  
**Safety:** Financial policy remains unverified until confirmed by an authorized finance owner.

### QS-12 Digital presence

**Question:** Do you need a website, online store, customer portal or online appointment booking?  
**Branching:** Activates WEB and related payment/integration topics.

### QS-13 Integrations

**Question:** Which systems must continue exchanging information with Odoo?  
**Input:** System name, purpose and direction of exchange.  
**Behavior:** Any named integration becomes an open technical qualification item.

### QS-14 Main problems

**Question:** What are the three most important problems you want the new system to solve?  
**Input:** Ranked narrative.  
**Produces:** Problem statements and candidate requirements.

### QS-15 Success

**Question:** Six months after launch, what measurable improvement would tell you the project succeeded?  
**Input:** Outcome, optional baseline and target.  
**Produces:** Success measures and benefit hypotheses.

### QS-16 Approvals

**Question:** Which transactions or decisions require management approval?  
**Examples:** Discounts, quotations, purchases, payments, expenses, credit, refunds, stock adjustments.  
**Behavior:** Creates initial approval-rule candidates; detailed thresholds require Guided Discovery.

### QS-17 Data

**Question:** What existing information must be brought into the new system?  
**Options:** Customers, suppliers, products, prices, stock, open documents, accounting balances, historical transactions, employees, projects, files.  
**Behavior:** Historical or financial migration creates a mandatory data-qualification follow-up.

### QS-18 Supporting material

**Question:** Would you like to upload examples that help us understand the business?  
**Examples:** Product list, quotation, invoice, process document, report, organization chart or system export.  
**Behavior:** Upload is optional; extracted claims always require review.

## 7. Guided Discovery structure

Guided Discovery starts with all verified Quick Start information. Each activated domain uses a compact sequence:

1. Scope screen
2. Normal flow
3. Important variations and exceptions
4. People and approvals
5. Data and documents
6. Reporting and success
7. Problems and desired change
8. Review of generated requirements

### 7.1 Mandatory core sections

Every Guided Discovery includes:

- ORG: company structure, locations, currencies and languages;
- STR: objectives, priorities, scope exclusions and success measures;
- OFF: offering types and commercial model;
- CUS: customer types and channels;
- SEC: user groups, sensitive information and access principles;
- DAT: required master data and migration boundaries;
- INT: systems that remain in the target architecture;
- IMP: timeline, ownership, training and acceptance.

### 7.2 Conditional operational sections

#### CRM and Sales

Activated when leads, quotations, contracts or sales orders are in scope.

Information goals:

- lead sources and ownership;
- qualification stages and loss reasons;
- opportunity stages and required activities;
- quotation types, validity and templates;
- price lists, currencies, discounts and promotions;
- contract, subscription and renewal behavior;
- sales approval rules;
- order confirmation, delivery and invoicing triggers;
- commissions, targets and sales reporting;
- exceptions such as tenders, samples, consignment or backorders.

#### Purchasing

Activated when the company buys goods or services through Odoo.

Information goals:

- requisition and purchase initiation;
- supplier selection and price comparison;
- purchase agreements and minimum quantities;
- approval thresholds and budget controls;
- expected delivery and receipt;
- three-way matching requirements;
- imports, landed costs and foreign currency;
- subcontracting and service purchases;
- supplier performance and reporting.

#### Inventory and Logistics

Activated by physical-item handling.

Information goals:

- warehouse and location structure;
- receipt, putaway, picking, packing and delivery;
- ownership and consignment;
- units of measure and packaging;
- serial, lot and expiry tracking;
- replenishment and procurement rules;
- routes, dropshipping and cross-docking;
- stock counts and adjustment controls;
- returns, repairs and scrap;
- shipping providers and delivery documents;
- volume, peaks and mobile scanning.

#### Projects and Services

Activated by project or service delivery.

Information goals:

- project types, templates and stages;
- task assignment and dependencies;
- planning, appointments and field visits;
- timesheet rules and approvals;
- billable units, retainers and milestones;
- materials and expenses used in delivery;
- service reports and customer signatures;
- profitability and utilization measures;
- recurring work and service agreements.

#### Support

Activated by post-sale service, tickets, warranties or repairs.

Information goals:

- intake channels and ticket classification;
- assignment and escalation;
- service levels and operating calendars;
- entitlements, warranties and contracts;
- knowledge and response templates;
- links to customers, products, assets and orders;
- field service, repair and replacement flows;
- closure, satisfaction and performance reporting.

#### Finance

Activated when Odoo invoicing, accounting, payments or financial controls are in scope.

Information goals:

- legal entities, fiscal positions and currencies;
- chart-of-accounts and Israeli localization approach;
- customer and supplier invoicing triggers;
- payment terms, methods and providers;
- bank accounts and reconciliation;
- credit limits and collection;
- expenses and employee reimbursements;
- analytic accounting, budgets and profitability;
- tax, withholding and required documents;
- period close, approvals and external accountant interaction;
- reporting and audit requirements.

Finance answers must be confirmed by an authorized finance owner before being classified Green.

#### Manufacturing

Guided Discovery may qualify simple assembly. Work-center routing, planning constraints, quality, maintenance, engineering changes, subcontracting or regulated traceability escalate MRP to Comprehensive Discovery.

#### People

Activated when HR capabilities are in scope.

Information goals:

- employee structure and contracts at a requirements level;
- recruitment and onboarding;
- attendance, leave, planning and expenses;
- equipment and document management;
- manager and HR access boundaries;
- Israeli payroll integration or external payroll boundary;
- reporting and retention.

#### Documents and Digital Channels

Activated when documents, signatures, website, eCommerce, portal, appointments or marketing are in scope.

Information goals include content ownership, templates, approvals, access, retention, multilingual needs, catalogue behavior, checkout, payments, fulfillment, customer self-service and consent.

### 7.3 Cross-domain review

After conditional sections, the engine runs a cross-domain review for:

- order-to-cash consistency;
- procure-to-pay consistency;
- inventory-to-accounting consistency;
- project-to-invoice consistency;
- support entitlement consistency;
- roles and segregation of duties;
- shared master data;
- approval conflicts;
- reporting-source availability;
- integration ownership;
- data-migration feasibility.

## 8. Comprehensive Discovery structure

Comprehensive Discovery is workshop-based and process-centered. It reuses all prior facts and focuses on decisions, exceptions and controls.

### Workshop 1: Strategy, scope and operating model

- business objectives and measurable outcomes;
- organizational and legal structure;
- business capabilities and value streams;
- customer and offering models;
- implementation scope, exclusions and phases;
- constraints, risks and decision governance.

### Workshop 2: End-to-end processes

For every in-scope process:

- trigger and intended outcome;
- participants and ownership;
- normal flow;
- decisions and business rules;
- inputs, outputs and documents;
- exceptions, failure handling and escalations;
- approvals and segregation of duties;
- volumes, peaks and performance expectations;
- As-Is problems and To-Be design intent;
- controls, KPIs and acceptance scenarios.

### Workshop 3: Data, integrations, security and reporting

- canonical master-data ownership;
- migration objects, history, quality and reconciliation;
- integration contracts, frequency, direction and failure handling;
- identity, access, privacy and audit;
- reporting definitions, source data and reconciliation;
- operational continuity, monitoring and support.

### Workshop 4: Solution validation and delivery

- requirement catalogue review;
- fit and gap review;
- process-change candidates;
- custom-development boundaries;
- implementation phases and dependencies;
- test scenarios and acceptance criteria;
- training, cutover and operational readiness.

Additional specialist workshops may be opened only for activated complexity areas such as advanced manufacturing, multi-company finance or high-volume logistics.

## 9. Question model

Each Question Definition must include:

```yaml
question_key: SAL.PRICING.010
version: 1
domain: SAL
concept: pricing_model
mode_minimum: guided
prompt:
  he_IL: "כיצד נקבע המחיר ללקוח?"
  en_US: "How is the customer price determined?"
help_text: {}
answer_type: multi_select
options: []
required_policy: conditional
applicability_rule: "scope.sales == true"
branch_rules: []
normalization_rule: pricing_model_v1
requirement_templates: []
risk_weight: 2
complexity_weight: 2
evidence_policy: optional
allowed_respondent_roles:
  - customer_process_owner
  - aione_consultant
review_policy: consultant_review
```

The example is conceptual. The persistence and rule-expression syntax will be selected during technical architecture.

## 10. Supported answer types

- Boolean and tri-state: Yes, No, Unknown
- Single select
- Multi-select
- Short text
- Long narrative
- Integer and decimal
- Currency and amount band
- Percentage
- Date and date range
- Duration and frequency
- Ranked list
- Repeating structured group
- Matrix
- File or evidence reference
- Process sequence
- Person or business-role reference
- Organizational-unit reference
- Existing-system reference

Free text may supplement structured input but should not replace it when deterministic configuration depends on the answer.

## 11. Branching and follow-up rules

Rules may evaluate:

- prior normalized answers;
- customer facts;
- activated scope domains;
- business model and industry;
- respondent role;
- evidence availability;
- confidence and verification state;
- complexity and risk flags;
- contradictions or missing dependencies;
- selected interview mode.

Rule actions may:

- show, hide or defer a question;
- activate or deactivate a domain;
- request a different respondent;
- require evidence;
- generate a clarification;
- propose a fact or requirement;
- mark a topic for consultant review;
- escalate a domain to a deeper discovery mode;
- block blueprint approval.

Hidden questions are not treated as answered. The engine records whether a question was not applicable, deferred or skipped with justification.

## 12. Answer normalization

The original answer is immutable. Normalization creates structured interpretations without replacing source wording.

Example:

> “We have a main warehouse in Petah Tikva and a small returns area in the office.”

May produce proposed facts:

- warehouse count: 1;
- internal location candidate: Returns;
- site: Petah Tikva;
- returns process: present;
- clarification: whether the office returns area belongs to the same warehouse.

Each normalized claim records:

- source answer or evidence;
- extraction method and version;
- exact supporting excerpt where applicable;
- normalized value;
- confidence;
- verification state;
- reviewer and review timestamp;
- relationships to other claims;
- conflict status.

## 13. Document-assisted discovery

Supported initial document classes:

- organization chart;
- product, service or price list;
- quotation, order, invoice or purchase order;
- process document or work instruction;
- customer or supplier export;
- inventory export;
- report or dashboard sample;
- role or permissions matrix;
- existing-system export schema.

Processing lifecycle:

1. Upload and classify document.
2. Scan and safely extract text and structure.
3. Identify candidate facts, entities and requirements.
4. Link each claim to a document location or excerpt.
5. Compare claims with existing answers.
6. Present confirmations, conflicts and follow-up questions.
7. Require human confirmation before high-impact claims become verified.

The engine must not treat a document as current merely because it was uploaded. Document date, owner, authority and applicability must be captured where material.

## 14. Conflict detection

A conflict exists when two active claims that apply to the same context cannot both be true.

Examples:

- sponsor states there is one company, while accounting evidence shows two legal entities;
- sales says discounts need no approval, while finance states discounts over 10% require approval;
- product file uses serial tracking, while interview answer says no traceability is needed;
- two owners provide different invoicing triggers.

Conflict handling:

1. Preserve both claims and their sources.
2. Determine whether market, company, date, product or process context resolves the difference.
3. If unresolved, create an Open Question with an assigned owner.
4. Calculate impact and blocking status.
5. Prevent affected decisions from becoming Green.
6. Record the final resolution and why one claim superseded or contextualized another.

## 15. Complexity assessment

Complexity is evaluated per domain and for the project overall.

Initial complexity signals include:

- multiple legal entities or countries;
- more than one active localization;
- multi-currency accounting;
- several warehouses or complex routes;
- lots, serial numbers, expiry or regulated traceability;
- advanced manufacturing;
- high transaction volume or material seasonal peaks;
- extensive approval matrices;
- several material integrations;
- historical or financial migration;
- custom pricing or contract logic;
- sensitive or regulated information;
- complex segregation of duties;
- major process differences between units;
- substantial custom-development expectations.

Complexity does not automatically block a sandbox. It determines the required discovery depth and permissible assumptions.

## 16. Confidence, completeness and risk engine

### 16.1 Confidence

Confidence is calculated for individual facts, requirements and decisions using:

- source authority;
- direct answer versus inference;
- respondent relevance;
- supporting evidence;
- consistency with other sources;
- recency and applicability;
- reviewer confirmation.

Recommended states:

- **Green:** verified by an appropriate owner or authoritative evidence, with no unresolved conflict;
- **Amber:** plausible and usable only with an explicit, approved assumption;
- **Red:** missing, conflicting, insufficiently authoritative or unsuitable for configuration.

### 16.2 Completeness

Completeness is rule-based, not merely a percentage of questions answered.

A domain is complete when:

- all mandatory information goals for its scope and mode are satisfied;
- required owners have responded or confirmed;
- blocking conflicts are resolved;
- required evidence is present;
- resulting requirements contain acceptance criteria;
- dependencies on other domains are addressed.

### 16.3 Risk

Risk considers likelihood and impact of an incorrect discovery conclusion. High-impact topics include accounting, access control, destructive migration, legal entities, inventory valuation, traceability and external integrations.

### 16.4 Provisioning readiness

A project may proceed to blueprint generation when requirements can be proposed transparently. It may proceed to blueprint approval only when:

- all mandatory scoped domains meet completeness policy;
- no blocking Red item remains;
- Amber assumptions have named owners and explicit approval;
- critical cross-domain consistency checks pass;
- the discovery review has been approved by an AIOne consultant.

## 17. Escalation between discovery modes

Escalation is domain-specific. A customer may complete Quick Start overall while Finance moves to Guided and Manufacturing moves to Comprehensive.

### Quick Start to Guided triggers

- the customer requests more than a demonstration sandbox;
- critical facts remain Amber or Red;
- approvals require thresholds or conditional logic;
- more than one legal entity, warehouse or material sales channel exists;
- an external integration is required;
- accounting, migration or access design is in scope;
- requirements contain important exceptions;
- the customer or consultant requests deeper review.

### Guided to Comprehensive triggers

- advanced manufacturing or logistics;
- multiple entities with shared operations or intercompany flows;
- regulated or high-risk processes;
- complex accounting or consolidation;
- extensive integrations or identity architecture;
- high-volume performance requirements;
- substantial historical migration;
- major process divergence between business units;
- significant custom-development gaps;
- unresolved conflicts with high business impact.

The engine must state the trigger and estimated additional effort before escalating.

## 18. Requirement generation

Requirements may be proposed from answers, facts, processes, documents and detected dependencies. They remain proposed until reviewed.

Requirement pattern:

> The system shall [capability or behavior] for [actor or scope] when [condition], so that [business outcome], subject to [control or constraint].

Each generated requirement must:

- express one testable need;
- use customer business language;
- identify source and rationale;
- avoid prematurely prescribing an Odoo module;
- include measurable or observable acceptance criteria;
- distinguish current-state fact from desired future behavior;
- identify relevant exceptions;
- record confidence and review status.

Example:

> The system shall require Sales Manager approval when a salesperson proposes a discount above 10%, so that commercial margin is controlled. Approval must be recorded before quotation confirmation.

This requirement does not yet decide whether standard approvals, Studio, automation or custom development will implement it.

## 19. Discovery review experience

The consultant review workspace must present:

- project summary and scope;
- progress by domain;
- facts awaiting confirmation;
- conflicts and open questions;
- generated requirements grouped by process;
- assumptions and their impact;
- complexity, confidence, completeness and risk;
- source traceability;
- topics recommended for deeper discovery;
- readiness blockers;
- change history.

The consultant can confirm, revise, reject, merge or split proposed requirements. Any material manual change requires a reason and creates an audit event.

## 20. Discovery lifecycle

| State | Meaning |
| --- | --- |
| Draft | Interview run created but not issued |
| Invited | One or more respondents were invited |
| In Progress | Answers are being collected |
| Waiting for Others | Assigned questions require other respondents |
| Clarification Required | Conflicts or missing critical information exist |
| Ready for Review | Automated discovery checks passed |
| Under Consultant Review | Requirements and conclusions are being reviewed |
| Changes Requested | Additional customer or consultant input is required |
| Approved for Blueprint | A specific discovery version is approved |
| Superseded | A newer approved discovery version replaces it |
| Cancelled | The run was intentionally abandoned |

## 21. Core screens

### Customer-facing

1. Welcome, purpose and estimated effort
2. Respondent role and consent
3. Business profile
4. Adaptive interview section
5. Upload supporting material
6. Questions assigned to others
7. Review of interpreted facts
8. Open clarifications
9. Completion summary

### Consultant-facing

1. Discovery portfolio
2. Project discovery dashboard
3. Interview builder and template versions
4. Respondent and assignment manager
5. Answer and evidence review
6. Fact and conflict workspace
7. Process and requirement editor
8. Readiness and escalation report
9. Discovery approval

## 22. Notifications and collaboration

The MVP supports:

- respondent invitation;
- save-and-resume link;
- question assignment to another person;
- reminder for incomplete required items;
- notification of clarification requests;
- consultant notification when review is ready;
- notification when an approved answer changes.

Notification channels are an implementation decision. The domain must remain channel-independent.

## 23. Privacy and security requirements

- Collect only information necessary for discovery and implementation.
- Clearly label optional financial and sensitive questions.
- Restrict customer access to their own organization and assigned projects.
- Restrict respondents to authorized sections and evidence.
- Encrypt data in transit and at rest.
- Scan uploads and isolate processing.
- Keep secrets and production credentials outside discovery records.
- Record material access, export, change and approval events.
- Apply retention and deletion policy by project and evidence class.
- Do not use customer content to train shared models without explicit lawful authorization.

## 24. Analytics and quality measures

The product should measure:

- median customer effort by discovery mode;
- completion and abandonment by question and section;
- number of questions avoided through branching;
- percentage of extracted claims accepted, corrected or rejected;
- conflicts detected before blueprint approval;
- requirements changed during blueprint review;
- domains escalated and their triggers;
- time from project creation to approved discovery;
- sandbox configuration failures attributable to missing discovery;
- customer and consultant satisfaction.

These measures improve the interview without optimizing merely for fewer questions.

## 25. Discovery acceptance criteria

The Discovery Engine is acceptable for MVP when:

1. A project can start in any of the three modes.
2. A deeper mode reuses all applicable prior answers.
3. Questions appear or disappear deterministically according to versioned rules.
4. Multiple respondents can own different sections.
5. Every answer preserves source, author, time and original value.
6. Document claims remain proposed until reviewed.
7. The system detects and presents material conflicts.
8. Facts, assumptions, constraints and requirements are separate record types.
9. Every requirement links to its discovery source and acceptance criteria.
10. Confidence, completeness, risk and complexity are assessed separately.
11. Escalation is domain-specific and explainable.
12. Blocking Red items prevent approval.
13. Approved Amber assumptions are explicit and traceable.
14. A consultant can approve a specific immutable discovery version.
15. The approved output can be consumed by the Blueprint Engine without parsing a narrative report.

## 26. Initial API boundary

The Discovery Engine must expose operations equivalent to:

- create project discovery;
- recommend discovery mode;
- start or resume interview run;
- retrieve next relevant question set;
- submit and revise answer;
- assign question or section;
- attach and classify evidence;
- review extracted claims;
- calculate progress and readiness;
- list conflicts and open questions;
- generate proposed requirements;
- review and revise requirements;
- request clarification;
- create immutable discovery version;
- approve discovery version;
- export structured discovery package.

Exact protocol and endpoint design are deferred to technical architecture.

## 27. Next design package

The next package should define the **Blueprint Engine and Odoo Capability Catalogue**, including:

- catalogue taxonomy and sources;
- requirement-to-capability mapping;
- fit assessment rules;
- decision explainability;
- standard/configuration/localization/Studio/addon/integration/custom hierarchy;
- blueprint structure and versions;
- gap and phase planning;
- blueprint approval gates;
- structured handoff to the Deployment Manifest compiler.
