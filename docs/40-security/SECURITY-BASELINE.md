# Security Baseline

## Critical assets

- Customer discovery, evidence and requirements
- Approved blueprints and manifests
- Tenant and project membership
- Odoo core, Enterprise and addon source revisions
- Provisioning authority and environment credentials
- Customer sandbox databases and files
- Approval and audit history

## Required controls

### Identity and access

- Deny access unless tenant, project, role and state checks allow it.
- Require step-up authentication for manifest approval and provisioning authorization.
- Use separate identities for web, API, AI, evidence and provisioning services.
- Review inactive users, expired invitations and support access.

### Application

- Validate all boundary input against versioned schemas.
- Use optimistic concurrency for mutable drafts.
- Make approved versions immutable.
- Require idempotency for externally repeatable commands.
- Prevent clients from directly setting approval, audit or calculated risk fields.

### Data

- Classify Public, Internal, Customer Confidential, Sensitive and Secret data.
- Encrypt data in transit and at rest.
- Use scoped object paths and short-lived download grants.
- Keep secrets outside PostgreSQL domain records where practical and outside all manifests.
- Use sanitized non-production fixtures.

### AI

- Use only the governed gateway.
- No secrets, unrestricted database access or provisioning authority.
- Uploaded content cannot alter system instructions.
- Persist output as a proposal with provenance and reviewer state.

### Provisioning

- Verify manifest checksum, approval and expiry.
- Use allowlisted handlers and one-environment runner authority.
- Pin and verify source revisions and artifacts.
- Do not configure production endpoints in demonstration sandboxes.
- Run negative security validations before release.

### Supply chain

- Lock dependencies and review updates.
- Scan containers and dependencies.
- Verify third-party addon source, license and pinned revision.
- Do not execute module manifests during catalogue parsing.

### Logging and audit

- Redact credentials, tokens and sensitive payloads.
- Keep audit separate from troubleshooting logs.
- Audit approvals, provisioning, deviations, exports and access changes.

## Required security tests

- Cross-tenant API and database access
- Project membership removal
- Customer access to internal consultant records
- Approval spoofing and stale-version approval
- Altered manifest and invalid checksum
- Expired or wrong-environment job authorization
- Arbitrary handler and parameter rejection
- Sandbox-to-sandbox and sandbox-to-control-plane access
- Prompt injection in uploaded evidence
- Secret leakage in logs, errors and AI requests
- Odoo ACL, record-rule, company and RPC bypass paths

## Stop conditions

Do not release an increment when:

- a Critical or High isolation defect remains;
- secrets appear in repository history or logs;
- an approval can be bypassed;
- a sandbox runner can target more than one authorized environment;
- cross-tenant negative tests are missing or failing.

