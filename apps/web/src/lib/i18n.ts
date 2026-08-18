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
  noWorkspaces: string;
  localeNotice: string;
  stateLabel: Record<string, string>;
  modeLabel: Record<string, string>;
  interview: string;
  question: string;
  progressLabel: string;
  save: string;
  saved: string;
  answeredEarlier: string;
  optional: string;
  required: string;
  whyThisQuestion: string;
  allAnswered: string;
  notApplicableHere: string;
  startInterview: string;
  backToWorkspaces: string;
  review: string;
  reviewIntro: string;
  facts: string;
  requirements: string;
  openQuestions: string;
  blocking: string;
  advisory: string;
  noneYet: string;
  recalculate: string;
  basedOn: string;
  saidBy: string;
  priorityLabel: Record<string, string>;
  confidenceLabel: Record<string, string>;
  verificationLabel: Record<string, string>;
  acceptance: string;
  ownerLabel: string;
  toInterview: string;
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
  noWorkspaces: "אין עדיין מרחבי פתרון",
  localeNotice: "קוד השפה בחוזים ובאחסון:",
  stateLabel: {
    proposed: "הוצע",
    discovering: "באפיון",
    clarification_required: "נדרשת הבהרה",
    designing: "בתכנון פתרון",
    blueprint_review: "בבדיקת תכנון",
    approved_for_sandbox: "אושר להקמת סביבה",
    provisioning: "בהקמה",
    validation_failed: "בדיקות נכשלו",
    sandbox_active: "סביבה פעילה",
    customer_review: "בבדיקת הלקוח",
    revision_required: "נדרש עדכון",
    accepted: "התקבל",
    operating: "בתפעול",
    change_in_progress: "שינוי בביצוע",
    suspended: "מושהה",
    archived: "בארכיון",
    closed: "סגור",
  },
  modeLabel: {
    quick_start: "היכרות מהירה",
    guided: "אפיון מודרך",
    comprehensive: "אפיון מקיף",
  },
  interview: "ריאיון אפיון",
  question: "שאלה",
  progressLabel: "שאלות שנענו",
  save: "שמירה והמשך",
  saved: "נשמר",
  answeredEarlier: "נענה קודם",
  optional: "לא חובה",
  required: "חובה",
  whyThisQuestion: "מדוע שאלה זו מוצגת",
  allAnswered: "כל השאלות הרלוונטיות נענו. אפשר להעביר את האפיון לבדיקת יועץ.",
  notApplicableHere: "לא רלוונטי לפי התשובות עד כה",
  startInterview: "התחלת ריאיון",
  backToWorkspaces: "חזרה למרחבי הפתרון",
  review: "בדיקת אפיון",
  reviewIntro:
    "מה שהמערכת הסיקה מהתשובות. כל שורה מציגה את המקור שממנו נגזרה, וניתן לתקן תשובה ולחשב מחדש.",
  facts: "עובדות עסקיות",
  requirements: "דרישות",
  openQuestions: "שאלות פתוחות",
  blocking: "חוסם אישור",
  advisory: "לידיעה",
  noneYet: "טרם נגזרו פריטים. יש לענות על שאלות ולחשב מחדש.",
  recalculate: "חישוב מחדש",
  basedOn: "נגזר מ",
  saidBy: "תשובת הלקוח",
  priorityLabel: { must: "חובה", should: "רצוי", could: "אפשרי", wont_this_release: "לא בגרסה זו" },
  confidenceLabel: { green: "ודאות גבוהה", amber: "דורש הנחה מאושרת", red: "דורש הכרעה" },
  verificationLabel: {
    confirmed: "אושר על ידי הלקוח",
    inferred: "הוסק על ידי המערכת",
    unverified: "טרם אומת",
    proposed: "מוצע",
    conflicting: "סתירה",
    superseded: "הוחלף",
  },
  acceptance: "קריטריוני קבלה",
  ownerLabel: "אחראי",
  toInterview: "למסך הריאיון",
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
  noWorkspaces: "No solution workspaces yet",
  localeNotice: "Locale code used in contracts and storage:",
  stateLabel: {
    proposed: "Proposed",
    discovering: "Discovering",
    clarification_required: "Clarification required",
    designing: "Designing",
    blueprint_review: "Blueprint review",
    approved_for_sandbox: "Approved for sandbox",
    provisioning: "Provisioning",
    validation_failed: "Validation failed",
    sandbox_active: "Sandbox active",
    customer_review: "Customer review",
    revision_required: "Revision required",
    accepted: "Accepted",
    operating: "Operating",
    change_in_progress: "Change in progress",
    suspended: "Suspended",
    archived: "Archived",
    closed: "Closed",
  },
  modeLabel: {
    quick_start: "Quick Start",
    guided: "Guided",
    comprehensive: "Comprehensive",
  },
  interview: "Discovery interview",
  question: "Question",
  progressLabel: "Questions answered",
  save: "Save and continue",
  saved: "Saved",
  answeredEarlier: "Answered earlier",
  optional: "Optional",
  required: "Required",
  whyThisQuestion: "Why this question appears",
  allAnswered: "Every applicable question is answered. Discovery can go to consultant review.",
  notApplicableHere: "Not applicable given the answers so far",
  startInterview: "Start interview",
  backToWorkspaces: "Back to workspaces",
  review: "Discovery review",
  reviewIntro:
    "What the system concluded from the answers. Every row shows the source it came from, and correcting an answer and recalculating updates it.",
  facts: "Business facts",
  requirements: "Requirements",
  openQuestions: "Open questions",
  blocking: "Blocks approval",
  advisory: "Advisory",
  noneYet: "Nothing derived yet. Answer questions and recalculate.",
  recalculate: "Recalculate",
  basedOn: "Derived from",
  saidBy: "Customer answer",
  priorityLabel: { must: "Must", should: "Should", could: "Could", wont_this_release: "Won't, this release" },
  confidenceLabel: { green: "High confidence", amber: "Needs an approved assumption", red: "Needs resolution" },
  verificationLabel: {
    confirmed: "Confirmed by the customer",
    inferred: "Inferred by the system",
    unverified: "Not yet verified",
    proposed: "Proposed",
    conflicting: "Conflicting",
    superseded: "Superseded",
  },
  acceptance: "Acceptance criteria",
  ownerLabel: "Owner",
  toInterview: "Go to the interview",
};

const DICTIONARIES: Record<Locale, Copy> = { he, en };

export function copyFor(locale: Locale): Copy {
  return DICTIONARIES[locale];
}

export function otherLocale(locale: Locale): Locale {
  return locale === "he" ? "en" : "he";
}
