# AIOne Odoo Solution Builder — Design System

**Version:** 0.1
**Date:** 18 August 2026
**Status:** Accepted  
**Accepted:** 18 August 2026  
**Approved by:** Nir Bar, founding partner, AIOne  
**Depends on:** `docs/10-product/ODOO-SOLUTION-BUILDER-PRODUCT-CONSTITUTION.md`, `ODOO-SOLUTION-BUILDER-MVP-ARCHITECTURE-DELIVERY.md` §20, `ODOO-SOLUTION-BUILDER-DISCOVERY-ENGINE.md` §21, `ODOO-SOLUTION-BUILDER-CUSTOMER-PORTFOLIO.md` §6
**Relationship to `docs/10-product/ODOO-SOLUTION-BUILDER-DESIGN.md`:** complements it. The style reference remains the visual direction. This document is the implementable contract. Where they disagree, MVP Architecture §20.3 wins on accessibility and RTL, and this document records the resolution.

## 1. Scope and authority

This document defines the tokens, typography, RTL behavior, accessibility contract and component inventory for both product surfaces:

- `/app` — AIOne consultant, architect, operator and administrator workspace;
- `/portal` — customer sponsor, process owner and reviewer experience, including the interview.

It does not define page layouts, copy or product behavior. It authorizes nothing until its status is Accepted.

### 1.1 Recorded decisions

| Decision | Choice | Date |
| --- | --- | --- |
| Primary action color | Near-black `#0a0a0a` filled. Deep Sapphire is reassigned to the informational state role. Brand gold is never an action color. | 18 Aug 2026 |
| Hebrew type family | Open Sans (already vendored in `assets/fonts/open-sans/`, SIL OFL) | 18 Aug 2026 |
| Authority | Complements the style reference; §20.3 wins on accessibility and RTL | 18 Aug 2026 |

## 2. Principles

1. **Borders, not elevation.** A 1px hairline defines containers. Shadows are reserved for genuinely floating surfaces.
2. **One accent, used rarely.** Brand gold marks brand moments, not interface state.
3. **State is never color alone.** Every state carries an icon shape and a text label (Constitution §10, MVP §20.3).
4. **Hebrew first.** Every component is designed in Hebrew RTL and verified in English LTR, not the reverse.
5. **Logical properties only.** No physical `left`/`right` in component CSS.
6. **Uncertainty is visible.** Confidence, completeness, risk and conflict are distinct, separately rendered signals — never collapsed into one badge.
7. **Density with air.** Compact data surfaces, but no size below the legibility floor in §4.3.

## 3. Color tokens

All ratios are measured against Canvas White `#ffffff` unless stated. AA text = 4.5:1; AA large text and non-text/UI boundary = 3:1.

### 3.1 Neutrals — surfaces and inks

| Token | Value | Ratio | Use |
| --- | --- | ---: | --- |
| `--color-canvas` | `#ffffff` | — | Page and card base |
| `--color-paper` | `#f5f5f5` | — | Alt sections, nested panels, hover fill |
| `--color-ash` | `#e5e5e5` | 1.26:1 | Decorative hairline only — never the sole boundary of a control |
| `--color-smoke` | `#d4d4d4` | 1.45:1 | Emphasis container border, decorative |
| `--color-midnight-ink` | `#0a0a0a` | 19.80:1 | Primary action fill, highest-emphasis text |
| `--color-charcoal` | `#171717` | 18.10:1 | Body text, headings, badge text on tints |
| `--color-graphite` | `#262626` | 15.30:1 | Secondary text, icon strokes |
| `--color-slate` | `#404040` | 10.37:1 | Tertiary text |
| `--color-steel` | `#525252` | 7.81:1 | Muted text, **control borders** |
| `--color-fog` | `#737373` | 4.74:1 | Placeholder and helper text — the lightest permitted text color |
| `--color-silver` | `#a3a3a3` | 2.52:1 | Non-text decoration only. Never text, never a control boundary |

`--color-pebble` (`#c8c8c8`) from the style reference is dropped; it duplicates Smoke and fails every boundary requirement.

### 3.2 Brand

| Token | Value | Ratio | Use |
| --- | --- | ---: | --- |
| `--color-brand-gold` | `#e3aa24` | 2.09:1 | Logo, brand illustration, large decorative fills, fills on dark surfaces. **Never text, links, focus, borders or state.** |
| `--color-gold-ink` | `#8a6508` | 5.32:1 (4.88:1 on Paper) | Gold-toned text, links, icons and active indicators where a brand tone is wanted |
| `--color-brand-black` | `#231f20` | 17.40:1 | Logo lockup only. UI text uses Charcoal |

Rename map from the style reference: `--color-electric-blue` → `--color-brand-gold` (the old name held a gold value and must not survive into code). `--color-deep-sapphire` → `--color-state-info-ink`. `--color-conic-spectrum` exists only as `--gradient-brand-spectrum` and is forbidden on UI elements.

### 3.3 Action

| Token | Value | Use |
| --- | --- | --- |
| `--color-action-fill` | `#0a0a0a` | Primary filled action background |
| `--color-action-fill-hover` | `#262626` | Hover |
| `--color-action-fill-active` | `#404040` | Pressed |
| `--color-action-on-fill` | `#ffffff` | Text on primary fill (19.8:1) |
| `--color-action-disabled-fill` | `#e5e5e5` | Disabled surface |
| `--color-action-disabled-ink` | `#737373` | Disabled label (4.74:1 — disabled controls remain readable) |

One primary filled action per surface. Everything else is outlined or ghost.

### 3.4 Semantic state

Each state has an ink (for standalone text and icons on white), a tint (badge and row background) and a border. **Badge text is always Charcoal on the tint** (14.7–16.3:1); the ink colors the icon and standalone text.

| Role | Ink | Ink ratio | Tint | Border | Product meaning |
| --- | --- | ---: | --- | --- | --- |
| Success | `#15803d` | 5.02:1 | `#dcfce7` | `#bbf7d0` | Green confidence, Passed, Already compliant, Ready, Accepted |
| Caution | `#a16207` | 4.92:1 | `#fef3c7` | `#fde68a` | Amber confidence, Warning, Ready with warnings, Medium deviation, approved assumption |
| Danger | `#b91c1c` | 6.47:1 | `#fee2e2` | `#fecaca` | Red confidence, Failed, Blocking conflict, Critical and High deviation |
| Info | `#1e40af` | 8.72:1 | `#dbeafe` | `#bfdbfe` | In progress, Running, Proposed, informational notice |
| Neutral | `#525252` | 7.81:1 | `#f5f5f5` | `#e5e5e5` | Draft, Skipped, Unable to evaluate, Not applicable, Superseded |

Rules:

- Skipped and Unable to Evaluate use **Neutral, never Success** (Provisioning §21).
- Every state badge renders `icon + label`. The icon shape differs per state (check, triangle, octagon, circle, dash) so the meaning survives monochrome printing and color-vision differences.
- Confidence, completeness and risk render as three separate indicators. No component may merge them.

### 3.5 Supporting accents

| Token | Value | Ratio | Use |
| --- | --- | ---: | --- |
| `--color-accent-violet` | `#7c3aed` | 5.70:1 | Category tags, chart series |
| `--color-accent-orange-ink` | `#c2410c` | 5.18:1 | Category tags, chart series (replaces `#ea580c`, 3.56:1) |
| `--color-accent-green-ink` | `#15803d` | 5.02:1 | Category tags, chart series (replaces `#16a34a`, 3.30:1) |

Accents are categorical only. They never indicate state. One accent per component.

### 3.6 Focus and selection

| Token | Value | Use |
| --- | --- | --- |
| `--color-focus-ring` | `#0a0a0a` | 2px solid outline, 2px offset (19.8:1 against canvas and paper) |
| `--color-focus-ring-inverse` | `#ffffff` | Focus on dark fills |
| `--color-selection-bg` | `#dbeafe` | Text selection and active nav fill |

## 4. Typography

### 4.1 Families

| Token | Latin | Hebrew | Use |
| --- | --- | --- | --- |
| `--font-display` | Satoshi 500 (fallback Inter 500, `letter-spacing:-0.02em`) | **Open Sans 600** | Display headings, 36–48px only |
| `--font-body` | Inter 400/500/600 | **Open Sans 400/600/700** | Everything at 30px and below |
| `--font-mono` | Geist Mono 400/500 | *not applicable* | Technical identifiers, checksums, module names, code |

Rules:

- Hebrew has no weight 500 in the vendored Open Sans set (400 Regular, 600 SemiBold, 700 Bold). **Latin weight 500 maps to Hebrew weight 600.** Never synthesize weights.
- Hebrew has no italics. Emphasis in Hebrew uses weight or color, never oblique. Do not apply `font-style: italic` under `dir="rtl"`.
- Hebrew ignores the Latin display letter-spacing; `letter-spacing` must be `normal` for Hebrew text at every size.
- The mono family is Latin-only. Hebrew must never fall through to it — technical identifiers stay in `<bdi dir="ltr">` (see §6.3).
- Vendored files are static TTF. Increment 0 subsets them to WOFF2 (Hebrew + Latin) and self-hosts; no external font CDN, consistent with the supply-chain rules.

### 4.2 Type scale

| Role | Size | Line height (Latin) | Line height (Hebrew) | Token |
| --- | ---: | ---: | ---: | --- |
| caption | 12px | 1.50 | 1.60 | `--text-caption` |
| body | 14px | 1.43 | 1.55 | `--text-body` |
| body-lg | 16px | 1.50 | 1.60 | `--text-body-lg` |
| body-xl | 18px | 1.56 | 1.65 | `--text-body-xl` |
| subheading | 20px | 1.40 | 1.50 | `--text-subheading` |
| heading-sm | 24px | 1.33 | 1.42 | `--text-heading-sm` |
| heading | 30px | 1.38 | 1.45 | `--text-heading` |
| heading-lg | 36px | 1.11 | 1.20 | `--text-heading-lg` |
| display | 48px | 1.00 | 1.10 | `--text-display` |

Hebrew has no ascender/descender rhythm, so every step gains line height under `dir="rtl"`.

### 4.3 Usage

- 16px is the canonical body size in the customer portal; 14px is permitted in dense consultant tables and lists.
- Display sizes (36–48px) are used for page titles only.
- **12px is the absolute floor.** The 8px, 10px and 11px steps in the style reference are removed — they are illegible in Hebrew and fail practical AA review.
- Numerals are Latin digits in both languages. Data tables use tabular figures (`font-variant-numeric: tabular-nums`).

## 5. Accessibility contract

Two targets apply together:

- **WCAG 2.2 Level AA** — the internal engineering target for both surfaces.
- **IS 5568 part 1, Level AA (42 check criteria)** — the legal requirement for the customer-facing portal under the Equal Rights Regulations, carrying statutory exposure per claim. It is built on WCAG 2.0, so WCAG 2.2 AA covers most of it, but several IS 5568 items are not reachable from WCAG 2.2 alone and are listed explicitly below (items 12–17). Where the Israeli check sheet assigns a stricter level than WCAG — notably 1.2.1 and 2.4.10 — the Israeli level governs.

1. **Contrast.** Text ≥4.5:1 (≥3:1 at 24px+, or 19px+ bold). UI component boundaries and meaningful graphics ≥3:1. The token tables above are the allowlist; no ad-hoc colors.
2. **Focus appearance (2.4.11, 2.4.13).** Every interactive element shows a 2px `--color-focus-ring` outline at 2px offset. Focus is never removed, never clipped by `overflow: hidden`, and never hidden behind sticky headers or the interview progress bar.
3. **Target size (2.5.8).** Minimum 24×24 CSS px for every control, including table row actions and interview option chips. 44×44 recommended in the portal.
4. **No color-only meaning (1.4.1).** Enforced by §3.4.
5. **Dragging alternatives (2.5.7).** Any reorder interaction (requirement ranking, phase planner) provides keyboard and button alternatives.
6. **Forms.** Every field has a persistent visible label — placeholders are never labels. Errors are identified in text, associated programmatically, and announced.
7. **Live regions.** Autosave confirmation, job and provisioning status, and interview progress changes announce politely; blocking validation failures announce assertively.
8. **Motion.** Respect `prefers-reduced-motion`; no animation on state change beyond opacity/transform under 200ms.
9. **Structure.** One `h1` per page, ordered headings, landmark regions, skip-to-content link, and a document `lang` matching the active language.
10. **Tables.** Every data table has a responsive alternative below 768px (stacked card list), header association, and a caption.
11. **Testing.** Automated axe checks plus keyboard-only and screen-reader passes in Hebrew and English on: interview step, evidence upload, approval dialog, provisioning run view, portfolio table.

Additional IS 5568 items that WCAG 2.2 AA conformance does not by itself guarantee:

12. **Text resize and reflow (1.4.4).** No loss of information or function at 200% text size. Verified in Hebrew, where strings run longer than the English equivalents.
13. **Timing is adjustable (2.2.1).** Any session timeout, interview auto-expiry or save-and-resume link expiry must warn before it expires and allow the respondent to extend or cancel it. A silent session expiry mid-interview is a conformance failure, not only a usability one.
14. **Language of parts (3.1.2).** Every change of language inside content carries a `lang` attribute — English module names, product names and quoted source excerpts inside Hebrew text, and Hebrew customer content inside the English interface. This is separate from the direction handling in §6.3; `<bdi>` fixes direction, `lang` fixes pronunciation and is what a screen reader needs.
15. **Multiple ways to reach a page (2.4.5).** Portal and workspace pages are reachable by more than one route, except pages that are a step in, or the result of, a process — the interview steps are exempt on that basis.
16. **Error prevention for consequential actions (3.3.4).** Any action that creates a legal or financial commitment, or changes or deletes user data, is reversible, or validated, or confirmed in a review-before-submit step. This maps directly to the product's approval gates: blueprint approval, manifest authorization, deviation acceptance and provisioning start all render a review-and-confirm step showing exactly what is being approved, including the content hash.
17. **Valid markup and unique identifiers (4.1.1).** Correct nesting, no duplicate attributes, unique `id` values — enforced in CI rather than by review.

**Accessibility statement.** The portal publishes an accessibility statement page (הצהרת נגישות), linked from the footer of every page and reachable in one click. It is a legal requirement independent of technical conformance and must contain all seven required items: the standard and conformance level targeted (naming IS 5568, not only WCAG), the measures implemented, **known limitations with expected fix dates**, the name of the accessibility coordinator, a phone number, an email address, and both the date of the last audit and the date the statement was updated. If there are no known limitations, that is stated explicitly rather than left blank. The statement page is itself audited like any other page.

## 6. RTL and bilingual behavior

### 6.1 Direction

- Direction derives from the active interface language and is applied at the document (`<html dir>`) and at any component embedding content of the other direction.
- Hebrew (`he_IL`) is primary; English US (`en_US`) is secondary.
- **Locale codes:** `he_IL` and `en_US` are canonical in contracts, storage and Odoo. The web layer maps them to BCP-47 (`he-IL`, `en-US`) at the presentation boundary only.

### 6.2 Logical properties

Component CSS uses `padding-inline`, `margin-inline-start/end`, `inset-inline`, `border-inline-start`, `text-align: start/end`, and logical radius (`border-start-start-radius`). Physical `left`/`right` is permitted only in the explicitly non-mirrored cases listed in §6.4.

The classic failure is the visually-hidden pattern: `left: -9999px` on a skip link becomes unreachable rather than hidden under RTL. Use `inset-inline-start` or a clip-based visually-hidden utility.

### 6.3 Bidirectional content

Latin technical strings inside Hebrew sentences — module names (`sale_management`), external identifiers, checksums, URLs, versions, file names — are wrapped in `<bdi dir="ltr">` with the mono family. Never rely on the browser's implicit bidi resolution for these; unwrapped, trailing punctuation relocates and the identifier renders wrong.

### 6.4 Mirroring

| Mirrors under RTL | Does not mirror |
| --- | --- |
| Layout, navigation, sidebars, table column order | Logos and the partner badge |
| Progress bars, breadcrumbs, stepper direction | Charts with a time axis (time always flows left→right) |
| Directional icons (arrows, chevrons, back/forward) | Media transport controls, checkmarks, warning glyphs |
| Text alignment and list markers | Latin technical identifiers and code blocks |

### 6.5 Formatting

Dates render in the active locale with an unambiguous month (no bare numeric `dd/mm`), times carry a timezone, currency is ILS-aware, and file sizes and counts are localized. Sanitized log and audit views keep timestamps in ISO 8601 UTC with a local rendering beside them.

## 7. Spacing, shape and elevation

- **Base unit:** 4px. Scale: 4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 48, 56, 64, 80, 96, 112.
- **Radius vocabulary — exactly five:** `--radius-pill: 9999px`, `--radius-lg: 16px` (feature cards), `--radius-md: 12px` (cards), `--radius-sm: 8px` (buttons), `--radius-xs: 6px` (inputs). The style reference's stray `20px` token is removed.
- **Card padding:** 16px canonical. The 8px figure in the style reference applied to a nested list row, not a card; nested rows use 8px block and 12px inline padding.
- **Layout:** page max-width 1200px; section gap 64px; element gap 8px.
- **Elevation:** `--shadow-subtle` (1px lift, primary buttons), `--shadow-ring` (4px outer ring, floating panels and mockups), `--shadow-md` (dialogs, popovers only). Cards do not carry shadows.

## 8. Component contract

### 8.1 Resolved conflicts from the style reference

| Component | Resolution |
| --- | --- |
| Primary button | `--color-action-fill` `#0a0a0a`, white label, `--radius-sm` 8px, 10px block / 16px inline padding, `--shadow-subtle`. The 9999px variant in the prompt guide is dropped. |
| Secondary button | Canvas background, Charcoal label, 1px `--color-steel` border, 8px radius, 10px block / 16px inline padding. One padding spec only. |
| Ghost button | Transparent, Charcoal label, no border at rest, Paper fill on hover, pill radius permitted for nav items. |
| Destructive button | Danger ink label with Danger border at rest; filled Danger only inside a confirmation dialog. Never offered for MVP-excluded destructive provisioning operations. |
| Input | Canvas background, Charcoal text, 1px `--color-steel` border (7.81:1), `--radius-xs` 6px, 8px block / 12px inline padding; border darkens to Charcoal on hover, focus ring per §5.2. The undefined `#111827` text and the bare `#000000` border are dropped. |
| Card | Canvas background, 1px `--color-ash`, 12px radius, 16px padding, no shadow. |
| Alt panel | `--color-paper` `#f5f5f5`, 16px radius, 16px padding, no border. The undefined `#fafafa` is dropped. |
| Sidebar item | Transparent at rest; active uses `--color-selection-bg` `#dbeafe` plus a 2px `border-inline-start` in Charcoal — fill alone is not a sufficient active indicator. |
| Status badge | Tint background, Charcoal label, state-colored icon, pill radius, 4px block / 10px inline padding. Per §3.4. |
| Logo cloud | Desaturation applies to customer logos only. The Odoo partner badge is exempt — see §9.3. |

### 8.2 Product component inventory (to be specified before the surfaces are built)

**Interview and portal**
Question block per answer type (Discovery §10); one-question-at-a-time flow with section progress; "I don't know" and reassign-to-owner control; save-and-resume state; assigned-to-another-respondent notice; evidence upload row with scan state (queued, scanning, quarantined, extracted); extracted-claim confirmation card with source excerpt; clarification and open-question item; completion summary.

**Consultant workspace**
Portfolio table with health, blockers and next action; Customer 360 header; discovery dashboard by domain; fact and conflict workspace (two claims side by side with sources); requirement editor with acceptance criteria; confidence / completeness / risk triple indicator; escalation notice with trigger and estimated effort; fit-assessment workbench; decision card with alternatives and rationale; gap register row; phase planner; traceability matrix; version comparison and diff; approval dialog with step-up authentication and content-hash display; audit timeline entry.

**Provisioning**
Run header with stage, correlation identifier and authorizer; stage and operation result rows (pending, running, applied, already compliant, skipped, failed, rolled back, manually resolved); validation result row with expected versus observed; deviation item with severity and resolution; sandbox release package view; rebuild confirmation.

**Foundational**
Empty, loading, partial-failure and permission-denied states for every data surface; toast and inline notice; confirmation dialog; pagination and cursor loading; responsive table alternative.

## 9. Brand and partner assets

### 9.1 Canonical values

The vendored logos disagree with each other and with the token: `#e4ab24` (horizontal), `#e3ab24` (stacked), `#e3aa24` (design token). **`#e3aa24` is canonical**; both SVGs are re-exported to match. Brand black is `#231f20` in the lockup only.

### 9.2 Asset inventory

| Asset | File | Use |
| --- | --- | --- |
| AIOne horizontal | `assets/logos/aione/full-horizontal/…full-color.svg` | App header, interview header, documents |
| AIOne stacked | `assets/logos/aione/stacked/…full-color.svg` | Narrow and mobile contexts, splash |
| Odoo wordmark | `assets/logos/odoo/full-horizontal/…full-color.svg` | Technical and consultant contexts referring to the platform |
| Odoo Silver Partner badge | `assets/logos/odoo/partner/…full-color.svg` | Customer-facing trust signal — see §9.3 |

To be produced in Increment 0: monochrome and knockout AIOne variants for dark surfaces, favicon and application icons, and `assets/README.md` recording provenance, the SIL OFL notice for Open Sans, and the basis for Odoo trademark use.

### 9.3 Partner badge rule

The Odoo Silver Partner badge appears on the interview welcome screen and in the portal footer, beside the AIOne logo.

- Rendered **unmodified and in full color** (`#714b67`, `#8f8f8f`, `#5b899e`). It is explicitly exempt from the logo-desaturation rule.
- Minimum height 32px; clear space equal to half the badge height on all sides; never on a tinted or patterned background.
- Accompanied by a caption identifying AIOne as the partner — Hebrew: "AIOne — שותף Odoo Silver"; English: "AIOne — Odoo Silver Partner".
- Never placed so that it implies Odoo authored, endorsed or operates the Solution Builder; never recolored, rotated, outlined, or combined into a composite lockup with the AIOne mark.
- Alt text names the partner status. The badge is not a link unless it points to AIOne's own partner page.

## 10. Implementation

### 10.1 Source of truth

Tokens live in `packages/design-system` as the single source and are emitted to:

1. CSS custom properties on `:root`;
2. Tailwind v4 `@theme`;
3. a typed TypeScript token export for non-CSS consumers.

Hand-written hex values in application code are a review defect.

### 10.2 shadcn/ui mapping

shadcn ships its own semantic variables. The mapping is fixed here so the two systems cannot drift:

| shadcn variable | This system |
| --- | --- |
| `--background` / `--foreground` | `--color-canvas` / `--color-charcoal` |
| `--card` / `--card-foreground` | `--color-canvas` / `--color-charcoal` |
| `--muted` / `--muted-foreground` | `--color-paper` / `--color-steel` |
| `--primary` / `--primary-foreground` | `--color-action-fill` / `--color-action-on-fill` |
| `--secondary` | `--color-paper` |
| `--accent` | `--color-selection-bg` |
| `--destructive` | `--color-state-danger-ink` |
| `--border` / `--input` | `--color-ash` / `--color-steel` |
| `--ring` | `--color-focus-ring` |
| `--radius` | `--radius-sm` (8px) |

### 10.3 CI checks (Increment 0)

- Contrast lint over the emitted token set — the build fails on any text pair below 4.5:1 or boundary pair below 3:1.
- Token-drift check — fails on raw hex values in `apps/web` outside the design-system package.
- RTL smoke test — the Hebrew shell renders `dir="rtl"`, the English shell renders `dir="ltr"`, visible focus present in both.
- axe automated pass on the application shell and one representative form.

## 11. Open items for design authority

1. Dark theme is out of scope for the MVP; the token structure supports adding it later. Confirm.
2. The charting palette (fit dimensions, portfolio analytics) is not yet defined; it must be categorical, AA-compliant and free of state colors.
3. Print and PDF styling for the blueprint, release package and traceability report is undefined; those are customer deliverables and need their own tokens.
4. IS 5568 conformance and the accessibility statement are settled in §5 — they are required, not optional. Two facts are still needed from AIOne: whether AIOne employs 25 or more people (which triggers the duty to appoint a named accessibility coordinator rather than merely providing an enquiry route), and who that coordinator and enquiry contact will be. The statement cannot ship with placeholders.
