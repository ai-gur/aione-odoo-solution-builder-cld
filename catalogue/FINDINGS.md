# Catalogue findings

Facts established from the pinned source that change what the Blueprint Engine
may claim. Each is checkable against `odoo19-baseline-2026-08-17` and the
evidence file for the pilot scope.

## F-01 — Standard Sales has no discount-approval capability

**Evidence.** `sale` declares four security groups: `group_auto_done_setting`
(Lock Confirmed Sales), `group_discount_per_so_line` (Discount on lines),
`group_proforma_sales`, `group_warning_sale`. Its configuration settings
include `group_discount_per_so_line` and `module_sale_margin`. None of them
requires an approval before a discounted quotation is confirmed.

**Why it matters.** Normalisation generates `REQ-APR-001` — "the system shall
require an authorized approval before discounts are confirmed" — from a
customer answering QS-16. The obvious blueprint decision would be "standard
Odoo discount approval". That capability does not exist in the pilot module
set, and asserting it would be exactly the fabricated technical claim the
constitution forbids.

**What exists instead.** Four Enterprise modules mention approvals at this
revision: `approvals`, `approvals_purchase`, `approvals_purchase_stock`,
`documents_approvals`, all OEEL-1. `approvals_purchase` covers purchase
requests; none of them is wired to sales-order discounts out of the box.

**The Enterprise candidate is now eliminated.** `approvals` contains no
reference to `sale.order` anywhere in the module. `approval.category` is a
request object of its own, not a generic approval attached to another model,
so there is nothing to point at a quotation. The only bridges to a business
document at this revision are `approvals_purchase`,
`approvals_purchase_stock` and `documents_approvals`; there is no
`approvals_sale`. The Enterprise approvals framework cannot gate confirmation
of a discounted sales order.

**Consequence for the pilot.** `REQ-APR-001` stays `unresolved`, but for a
narrower reason than before: the question was asked and one candidate was
ruled out on evidence. What remains is a choice between an automation rule on
`sale.order`, Studio, and custom development, and that choice belongs to an
Odoo functional reviewer. This is the case Blueprint §27 describes: produce a
sound design direction and refuse to invent the module.

## F-02 — Israeli localization is two modules and adds no models

**Evidence.** `l10n_il` defines no models, extends only
`account.chart.template`, ships no access rules and adds no configuration
settings. `l10n_il_reports` is the only other `l10n_il*` module at this
revision. `l10n_il` is core and LGPL-3; `l10n_il_reports` is Enterprise and
OEEL-1.

**Split edition.** The chart of accounts is available on Community; the local
reports are not. A capability naming both modules is an Enterprise capability,
because a customer cannot install half of it. The pilot capability record
declared `community` until verification on 18 August 2026; the check now runs
on every test run, deriving the required edition from the module sources in the
pinned release rather than from what the record asserts.

**Why it matters.** The pilot scope assumed an Israeli accounting boundary.
The localization supplies a chart of accounts and reports; it does not supply
invoice-numbering rules, tax-authority reporting behaviour or document formats
beyond what those two modules contain. Any requirement implying more needs a
finance reviewer and probably an addon or custom work, and normalisation
already holds finance answers at amber until that review happens.

## F-03 — Installing Sales pulls six modules that run install hooks

**Evidence.** `sale_management` depends on `sale` and `digest`, and resolves to
22 modules transitively. Six declare install or uninstall hooks: `account`,
`account_payment`, `base`, `http_routing`, `mail`, `sale`.

**Why it matters.** A hook runs arbitrary code at install time. Provisioning
treats that as elevated risk (Provisioning §19.7), so the blueprint should show
it before an operator authorizes a run rather than after a sandbox behaves
unexpectedly.

## F-04 — 206 of 1440 modules declare hooks; 14 declare external packages

**Evidence.** Release summary at this baseline.

**Why it matters.** External packages (`phonenumbers`, `python-ldap`, `zeep`,
`geoip2` and others) must exist in the sandbox image before installation, so
they belong in the manifest's preflight rather than being discovered when a
module fails to install. `website` requires `geoip2`, which matters as soon as
the pilot adds a customer portal.

## F-05 — Enterprise approvals approves a request, not an order

**Evidence.** `approvals_purchase` adds `approval_type` `'purchase'` ("Create
RFQ's") to `approval.category` and `action_create_purchase_orders` to
`approval.request`. Its `purchase.order` override does one thing: it logs
state changes into the approval request's chatter. Cancelling an approved
request removes the draft orders it created, or flags them for manual action
if they have moved on.

**Why it matters.** A customer who says "purchases above ₪50,000 need my
approval" can mean either of two things, and Odoo answers them differently.
`purchase`'s `po_double_validation` is a second validation on the order
itself, above a single amount per company. The Enterprise approvals workflow
approves a *request* — with a minimum number of approvers, optionally in
sequence — and the RFQ is created from it afterwards. Neither is a
substitute for the other, and the difference is a change to how the business
buys, not a configuration detail.

**Consequence.** Both are capability records against `approval.purchases`. A
requirement that reaches them gets both, ranked equally, with the choice
stated as a decision for the review rather than settled by the catalogue.
