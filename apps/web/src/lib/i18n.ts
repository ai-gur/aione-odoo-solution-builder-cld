/**
 * Locale definitions and copy.
 *
 * Hebrew is primary and English secondary (Constitution §3.10). Contracts and
 * storage use `he_IL` / `en_US`; the URL and the `lang` attribute use BCP-47
 * (ADR-015), and the mapping lives here so it exists in exactly one place.
 */

export const LOCALES = ["he", "en"] as const;
export type Locale = (typeof LOCALES)[number];
export const DEFAULT_LOCALE: Locale = "he";

export function isLocale(value: string): value is Locale {
  return (LOCALES as readonly string[]).includes(value);
}

/** Text direction for a locale. Drives `dir` on <html> and every logical property. */
export function directionOf(locale: Locale): "rtl" | "ltr" {
  return locale === "he" ? "rtl" : "ltr";
}

/** The canonical contract code for a URL locale. */
export function contractLocale(locale: Locale): "he_IL" | "en_US" {
  return locale === "he" ? "he_IL" : "en_US";
}

type Copy = {
  productName: string;
  productShort: string;
  skipToContent: string;
  signedInAs: string;
  notSignedIn: string;
  signIn: string;
  signOut: string;
  chooseTestUser: string;
  memberships: string;
  noMemberships: string;
  role: string;
  tenant: string;
  overview: string;
  workspaces: string;
  catalogue: string;
  administration: string;
  serviceHealth: string;
  apiReachable: string;
  apiUnreachable: string;
  partnerCaption: string;
  languageSwitch: string;
  incrementNotice: string;
  identityResolvedServerSide: string;
  correlationId: string;
};

const he: Copy = {
  productName: "AIOne Odoo Solution Builder",
  productShort: "Solution Builder",
  skipToContent: "דילוג לתוכן הראשי",
  signedInAs: "מחובר בתור",
  notSignedIn: "לא מחובר",
  signIn: "כניסה",
  signOut: "יציאה",
  chooseTestUser: "בחירת משתמש בדיקה",
  memberships: "שיוכים",
  noMemberships: "אין שיוכים פעילים",
  role: "תפקיד",
  tenant: "ארגון",
  overview: "סקירה",
  workspaces: "מרחבי פתרון",
  catalogue: "קטלוג יכולות",
  administration: "ניהול",
  serviceHealth: "מצב השירות",
  apiReachable: "שירות הדומיין זמין",
  apiUnreachable: "שירות הדומיין אינו זמין",
  partnerCaption: "AIOne — שותף Odoo Silver",
  languageSwitch: "English",
  incrementNotice:
    "שלב 0: שלד המערכת. גילוי, תכנון פתרון והקמת סביבות יתווספו בשלבים הבאים.",
  identityResolvedServerSide: "הזהות נקבעת בשרת מול מסד הבקרה, ולא מתוך הבקשה.",
  correlationId: "מזהה מעקב",
};

const en: Copy = {
  productName: "AIOne Odoo Solution Builder",
  productShort: "Solution Builder",
  skipToContent: "Skip to main content",
  signedInAs: "Signed in as",
  notSignedIn: "Not signed in",
  signIn: "Sign in",
  signOut: "Sign out",
  chooseTestUser: "Choose a test user",
  memberships: "Memberships",
  noMemberships: "No active memberships",
  role: "Role",
  tenant: "Tenant",
  overview: "Overview",
  workspaces: "Solution workspaces",
  catalogue: "Capability catalogue",
  administration: "Administration",
  serviceHealth: "Service health",
  apiReachable: "Domain service reachable",
  apiUnreachable: "Domain service unreachable",
  partnerCaption: "AIOne — Odoo Silver Partner",
  languageSwitch: "עברית",
  incrementNotice:
    "Increment 0: application skeleton. Discovery, blueprinting and provisioning arrive in later increments.",
  identityResolvedServerSide:
    "Identity is resolved server-side against the control database, never from the request.",
  correlationId: "Correlation id",
};

const DICTIONARIES: Record<Locale, Copy> = { he, en };

export function copyFor(locale: Locale): Copy {
  return DICTIONARIES[locale];
}

export function otherLocale(locale: Locale): Locale {
  return locale === "he" ? "en" : "he";
}
