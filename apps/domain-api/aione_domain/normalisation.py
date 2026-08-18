"""Deterministic normalisation: answers to facts, requirements and open questions.

No model is involved. Given the same answers this produces the same output,
every time, and each row records which answers produced it and which version of
this module read them (Discovery §12).

Three deliberate constraints:

1. **Requirements do not name Odoo.** "The system shall require management
   approval for discounts" is a business need; whether that becomes a standard
   approval rule, Studio, or custom code is the Blueprint Engine's decision
   against a verified catalogue (Discovery §18). Deciding it here would smuggle
   an unverified technical claim into the requirement.

2. **Uncertainty stays visible.** Finance answers are amber until a finance
   owner confirms them (Discovery §7.2). An "undecided" answer produces an open
   question, not an assumption.

3. **Nothing is derived from silence.** An unanswered question produces no fact.
   The absence of an answer is not evidence of anything.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from typing import Any, Callable

# Bumped when the output for the same input would change. Rows record the
# version that produced them, so a later correction is explainable.
VERSION = "norm_v1"


@dataclass
class Derived:
    facts: list[dict[str, Any]] = field(default_factory=list)
    requirements: list[dict[str, Any]] = field(default_factory=list)
    open_questions: list[dict[str, Any]] = field(default_factory=list)


def new_id(prefix: str) -> str:
    return f"{prefix}_" + secrets.token_hex(13).upper()


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _int(value: Any) -> int | None:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Facts
# ---------------------------------------------------------------------------

FactRule = Callable[[dict[str, Any]], list[dict[str, Any]]]
FACT_RULES: list[FactRule] = []


def fact_rule(function: FactRule) -> FactRule:
    FACT_RULES.append(function)
    return function


def fact(key: str, value: Any, sources: list[str], *, confidence: str = "amber",
         state: str = "proposed") -> dict[str, Any]:
    return {
        "fact_key": key,
        "value": value,
        "sources": sources,
        "confidence": confidence,
        "verification_state": state,
    }


@fact_rule
def offerings(answers: dict[str, Any]) -> list[dict[str, Any]]:
    selected = _as_list(answers.get("QS-02"))
    if not selected:
        return []
    physical = {"physical_products", "manufactured_products", "rentals"}
    return [
        # Directly stated by the customer, so green.
        fact("offering.types", selected, ["QS-02"], confidence="green", state="confirmed"),
        # Inferred from the above rather than stated, and labelled as such.
        fact(
            "offering.handles_physical_goods",
            bool(physical & set(selected)),
            ["QS-02"],
            state="inferred",
        ),
        fact(
            "offering.delivers_services",
            bool({"services", "projects"} & set(selected)),
            ["QS-02"],
            state="inferred",
        ),
    ]


@fact_rule
def organisation(answers: dict[str, Any]) -> list[dict[str, Any]]:
    group = answers.get("QS-05")
    if not isinstance(group, dict):
        return []
    facts: list[dict[str, Any]] = []
    for field_name, key in (
        ("companies", "organisation.legal_entities"),
        ("countries", "organisation.countries"),
        ("branches", "organisation.branches"),
        ("warehouses", "organisation.warehouses"),
    ):
        count = _int(group.get(field_name))
        if count is not None:
            facts.append(fact(key, count, ["QS-05"], confidence="green", state="confirmed"))
    if (_int(group.get("companies")) or 0) > 1:
        facts.append(fact("organisation.multi_company", True, ["QS-05"], state="inferred"))
    return facts


@fact_rule
def traceability(answers: dict[str, Any]) -> list[dict[str, Any]]:
    selected = set(_as_list(answers.get("QS-08")))
    if not selected:
        return []
    return [
        fact("inventory.tracking", sorted(selected), ["QS-08"], confidence="green", state="confirmed"),
        fact(
            "inventory.requires_traceability",
            bool({"serial_tracking", "lot_tracking", "expiry_dates"} & selected),
            ["QS-08"],
            state="inferred",
        ),
    ]


@fact_rule
def finance(answers: dict[str, Any]) -> list[dict[str, Any]]:
    scope = answers.get("QS-11")
    if not scope:
        return []
    # Amber and unverified regardless of how clearly it was stated: financial
    # policy is not settled until a finance owner confirms it (Discovery §7.2).
    return [fact("finance.scope", scope, ["QS-11"], confidence="amber", state="unverified")]


@fact_rule
def scope_areas(answers: dict[str, Any]) -> list[dict[str, Any]]:
    selected = _as_list(answers.get("QS-06"))
    if not selected:
        return []
    return [fact("scope.business_areas", selected, ["QS-06"], confidence="green", state="confirmed")]


@fact_rule
def migration(answers: dict[str, Any]) -> list[dict[str, Any]]:
    selected = set(_as_list(answers.get("QS-17")))
    if not selected:
        return []
    heavy = {"historical_transactions", "accounting_balances"}
    return [
        fact("data.migration_objects", sorted(selected), ["QS-17"], confidence="green", state="confirmed"),
        fact("data.requires_financial_migration", bool(heavy & selected), ["QS-17"], state="inferred"),
    ]


# ---------------------------------------------------------------------------
# Requirements
#
# The pattern from Discovery §18: the system shall [behaviour] for [scope] when
# [condition], so that [outcome]. Written in customer language, with acceptance
# criteria that can be tested against a sandbox later.
# ---------------------------------------------------------------------------

RequirementRule = Callable[[dict[str, Any]], list[dict[str, Any]]]
REQUIREMENT_RULES: list[RequirementRule] = []


def requirement_rule(function: RequirementRule) -> RequirementRule:
    REQUIREMENT_RULES.append(function)
    return function


def requirement(
    ref: str, domain: str, he: str, en: str, sources: list[str], *,
    topic: str,
    priority: str = "should", confidence: str = "amber",
    rationale_he: str = "", rationale_en: str = "",
    acceptance: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    return {
        "requirement_ref": ref,
        "domain": domain,
        # The join to the capability catalogue is this key, not a keyword match
        # on the statement text. Semantic similarity may suggest candidates; it
        # may not establish fit (Blueprint §9.1).
        "topic": topic,
        "statement": {"he_IL": he, "en_US": en},
        "rationale": {"he_IL": rationale_he, "en_US": rationale_en},
        "acceptance_criteria": acceptance or [],
        "priority": priority,
        "confidence": confidence,
        "sources": sources,
    }


@requirement_rule
def approval_requirements(answers: dict[str, Any]) -> list[dict[str, Any]]:
    selected = [item for item in _as_list(answers.get("QS-16")) if item != "none"]
    if not selected:
        return []

    labels = {
        "discounts": ("הנחות", "discounts"),
        "quotations": ("הצעות מחיר", "quotations"),
        "purchases": ("הזמנות רכש", "purchase orders"),
        "payments": ("תשלומים", "payments"),
        "expenses": ("הוצאות", "expenses"),
        "credit": ("אשראי לקוחות", "customer credit"),
        "refunds": ("זיכויים", "refunds"),
        "stock_adjustments": ("תיקוני מלאי", "stock adjustments"),
    }

    requirements = []
    for index, item in enumerate(selected, start=1):
        he_label, en_label = labels.get(item, (item, item))
        requirements.append(
            requirement(
                f"REQ-APR-{index:03d}",
                "SEC",
                f"המערכת תדרוש אישור מורשה לפני אישור {he_label}, כדי לשמור על בקרה עסקית.",
                f"The system shall require an authorized approval before {en_label} are confirmed, "
                "so that business control is preserved.",
                ["QS-16"],
                topic=f"approval.{item}",
                priority="must",
                rationale_he="הלקוח ציין שפעולה זו מחייבת אישור הנהלה.",
                rationale_en="The customer stated this action requires management approval.",
                acceptance=[
                    {
                        "he_IL": f"משתמש ללא הרשאת אישור אינו יכול לאשר {he_label}.",
                        "en_US": f"A user without approval authority cannot confirm {en_label}.",
                    },
                    {
                        "he_IL": "האישור נרשם עם מבצע הפעולה ומועד.",
                        "en_US": "The approval is recorded with actor and timestamp.",
                    },
                ],
            )
        )
    return requirements


@requirement_rule
def traceability_requirements(answers: dict[str, Any]) -> list[dict[str, Any]]:
    selected = set(_as_list(answers.get("QS-08")))
    requirements = []

    if "serial_tracking" in selected or "lot_tracking" in selected:
        unit_he = "מספר סידורי" if "serial_tracking" in selected else "אצווה"
        unit_en = "serial number" if "serial_tracking" in selected else "lot"
        requirements.append(
            requirement(
                "REQ-INV-001", "INV",
                f"המערכת תאפשר מעקב אחר פריטים לפי {unit_he} מקבלה ועד אספקה ללקוח, "
                "כדי לאפשר איתור וטיפול בפניות.",
                f"The system shall track items by {unit_en} from receipt through delivery, "
                "so that items can be traced when a customer query arises.",
                ["QS-08"],
                topic="inventory.traceability.serial" if "serial_tracking" in selected
                      else "inventory.traceability.lot",
                priority="must", confidence="green",
                rationale_he="הלקוח ציין דרישת מעקב עבור הפריטים הפיזיים.",
                rationale_en="The customer stated a tracking requirement for physical items.",
                acceptance=[{
                    "he_IL": "ניתן לאתר עבור פריט שסופק את מקור הקבלה שלו.",
                    "en_US": "For a delivered item, its receiving source can be traced.",
                }],
            )
        )

    if "expiry_dates" in selected:
        requirements.append(
            requirement(
                "REQ-INV-002", "INV",
                "המערכת תנהל תאריכי תפוגה ותמנע אספקה של פריטים שפג תוקפם.",
                "The system shall manage expiry dates and prevent delivery of expired items.",
                ["QS-08"], topic="inventory.traceability.expiry",
                priority="must", confidence="green",
            )
        )

    if (_int((answers.get("QS-05") or {}).get("warehouses")) or 0) > 1:
        requirements.append(
            requirement(
                "REQ-INV-003", "INV",
                "המערכת תנהל מלאי בכמה מחסנים ותציג זמינות לפי מחסן.",
                "The system shall manage stock across several warehouses and show availability per warehouse.",
                ["QS-05"], topic="inventory.multi_warehouse",
                priority="must", confidence="green",
            )
        )

    return requirements


@requirement_rule
def multi_company_requirements(answers: dict[str, Any]) -> list[dict[str, Any]]:
    companies = _int((answers.get("QS-05") or {}).get("companies")) or 0
    if companies <= 1:
        return []
    return [
        requirement(
            "REQ-ORG-001", "ORG",
            f"המערכת תתמוך ב-{companies} חברות משפטיות עם הפרדת נתונים ודיווח לכל חברה.",
            f"The system shall support {companies} legal companies with separated data and "
            "per-company reporting.",
            ["QS-05"], topic="organisation.multi_company",
            priority="must", confidence="green",
            rationale_he="הלקוח ציין יותר מחברה משפטית אחת.",
            rationale_en="The customer stated more than one legal company.",
            acceptance=[{
                "he_IL": "משתמש המשויך לחברה אחת אינו רואה מסמכים של חברה אחרת.",
                "en_US": "A user assigned to one company cannot see another company's documents.",
            }],
        )
    ]


@requirement_rule
def finance_requirements(answers: dict[str, Any]) -> list[dict[str, Any]]:
    scope = answers.get("QS-11")
    if scope not in ("full_accounting", "invoicing_only"):
        return []
    he = ("המערכת תפיק מסמכי חשבונאות לישויות ישראליות בהתאם לדרישות הדיווח המקומיות."
          if scope == "full_accounting"
          else "המערכת תפיק חשבוניות ללקוחות בהתאם לדרישות הדיווח המקומיות.")
    en = ("The system shall produce accounting documents for Israeli entities according to local "
          "reporting requirements."
          if scope == "full_accounting"
          else "The system shall issue customer invoices according to local reporting requirements.")
    return [
        requirement(
            "REQ-FIN-001", "FIN", he, en, ["QS-11"],
            topic="finance.accounting_israel" if scope == "full_accounting"
                  else "finance.invoicing_israel",
            priority="must",
            # Amber deliberately: the requirement is real, but its exact
            # content is not settled until a finance owner confirms it.
            confidence="amber",
            rationale_he="נדרש אישור בעל תפקיד בתחום הכספים לפני קביעת המדיניות החשבונאית.",
            rationale_en="A finance owner must confirm the accounting policy before it is settled.",
        )
    ]


# ---------------------------------------------------------------------------
# Open questions
# ---------------------------------------------------------------------------

OpenQuestionRule = Callable[[dict[str, Any]], list[dict[str, Any]]]
OPEN_QUESTION_RULES: list[OpenQuestionRule] = []


def open_question_rule(function: OpenQuestionRule) -> OpenQuestionRule:
    OPEN_QUESTION_RULES.append(function)
    return function


def open_question(topic: str, he: str, en: str, sources: list[str], *,
                  severity: str = "medium", blocking: bool = False,
                  owner_role: str | None = None) -> dict[str, Any]:
    return {
        "topic_key": topic,
        "question": {"he_IL": he, "en_US": en},
        "severity": severity,
        "blocking": blocking,
        "owner_role": owner_role,
        "sources": sources,
    }


@open_question_rule
def finance_confirmation(answers: dict[str, Any]) -> list[dict[str, Any]]:
    scope = answers.get("QS-11")
    if not scope:
        return []
    if scope == "undecided":
        return [
            open_question(
                "finance.scope_undecided",
                "טרם הוחלט אם המערכת תנהל הנהלת חשבונות. יש להכריע לפני קביעת תכולת הפתרון.",
                "Whether the system will manage accounting is undecided. This must be settled "
                "before solution scope is fixed.",
                ["QS-11"], severity="high", blocking=True, owner_role="customer_sponsor",
            )
        ]
    if scope in ("full_accounting", "invoicing_only"):
        return [
            open_question(
                "finance.owner_confirmation",
                "נדרש אישור של בעל תפקיד בתחום הכספים לגבולות החשבונאיים והדיווח בישראל.",
                "An authorized finance owner must confirm the Israeli accounting and reporting "
                "boundaries.",
                ["QS-11"], severity="high", blocking=True, owner_role="customer_sponsor",
            )
        ]
    return []


@open_question_rule
def integration_qualification(answers: dict[str, Any]) -> list[dict[str, Any]]:
    group = answers.get("QS-13")
    if not isinstance(group, dict):
        return []
    name = str(group.get("system_name") or "").strip()
    if not name:
        return []
    # Any named integration becomes a technical qualification item
    # (Discovery §6, QS-13).
    return [
        open_question(
            "integration.qualification",
            f"נדרש בירור טכני עבור הממשק למערכת {name}: ממשקים, תדירות, בעלות ותרחישי כשל.",
            f"Technical qualification is required for the {name} integration: interfaces, "
            "frequency, ownership and failure handling.",
            ["QS-13"], severity="high", blocking=False, owner_role="customer_technical_contact",
        )
    ]


@open_question_rule
def migration_qualification(answers: dict[str, Any]) -> list[dict[str, Any]]:
    selected = set(_as_list(answers.get("QS-17")))
    heavy = {"historical_transactions", "accounting_balances"} & selected
    if not heavy:
        return []
    return [
        open_question(
            "data.migration_qualification",
            "העברת יתרות או היסטוריה מחייבת בירור נתונים: היקף, איכות, תקופה והתאמה.",
            "Migrating balances or history requires data qualification: scope, quality, period "
            "and reconciliation.",
            ["QS-17"], severity="high", blocking=True, owner_role="customer_technical_contact",
        )
    ]


@open_question_rule
def manufacturing_escalation(answers: dict[str, Any]) -> list[dict[str, Any]]:
    complexity = answers.get("QS-10")
    if not complexity or complexity == "simple_assembly":
        return []
    # Discovery §6 QS-10: anything beyond simple assembly escalates MRP to
    # Comprehensive discovery while other domains stay where they are.
    return [
        open_question(
            "manufacturing.escalation",
            "מורכבות הייצור מחייבת אפיון מקיף בתחום הייצור בלבד, לפני קביעת פתרון.",
            "Manufacturing complexity requires Comprehensive discovery for manufacturing only, "
            "before a solution is decided.",
            ["QS-10"], severity="high", blocking=True, owner_role="consultant",
        )
    ]


# ---------------------------------------------------------------------------

def derive(answers: dict[str, Any]) -> Derived:
    """Run every rule against the current answers."""
    derived = Derived()
    for rule in FACT_RULES:
        derived.facts.extend(rule(answers))
    for rule in REQUIREMENT_RULES:
        derived.requirements.extend(rule(answers))
    for rule in OPEN_QUESTION_RULES:
        derived.open_questions.extend(rule(answers))
    return derived
