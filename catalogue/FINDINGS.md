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

**Consequence for the pilot.** `REQ-APR-001` resolves to one of: a verified
Enterprise approvals capability if review confirms it can gate a sales order;
Studio or an automation rule; or a custom-development gap. The decision needs
an Odoo functional reviewer, and until then the fit assessment is `unresolved`
rather than a guess. This is the case Blueprint §27 describes: produce a sound
design direction and refuse to invent the module.

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
