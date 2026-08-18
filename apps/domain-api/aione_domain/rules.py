"""Deterministic applicability rules.

Discovery Engine §11: branching is evaluated from reviewed, versioned rules —
never from generated text, and never from a model's opinion about whether a
question is relevant. Given the same answers, the same questions appear, every
time, and the engine can explain which condition matched.

The language is intentionally small. Every operator here is one an Odoo
consultant could read in a review:

    {"always": true}
    {"answered": "QS-02"}
    {"answer_includes": {"question": "QS-02", "any_of": ["physical", "manufactured"]}}
    {"answer_equals": {"question": "QS-11", "value": "full_accounting"}}
    {"answer_at_least": {"question": "QS-05", "field": "warehouses", "value": 2}}
    {"all": [...]}, {"any": [...]}, {"not": {...}}

Anything unrecognised evaluates to False and is reported, rather than being
skipped silently: a typo in a rule must hide a question loudly, not admit one
quietly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

Answers = Mapping[str, Any]


@dataclass(frozen=True)
class Evaluation:
    applicable: bool
    # Human-readable trace of what decided it. The consultant review workspace
    # shows this, and "why am I being asked this" must always have an answer.
    reason: str


class RuleError(ValueError):
    """The rule is malformed. Raised at load time, not at interview time."""


def _value_of(answers: Answers, question_key: str, field: str | None = None) -> Any:
    if question_key not in answers:
        return None
    value = answers[question_key]
    if field is None:
        return value
    if isinstance(value, Mapping):
        return value.get(field)
    return None


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def evaluate(rule: Any, answers: Answers) -> Evaluation:
    """Evaluate one rule against the answers given so far."""
    if not isinstance(rule, Mapping) or len(rule) != 1:
        return Evaluation(False, f"malformed rule: {rule!r}")

    (operator, operand), = rule.items()

    if operator == "always":
        return Evaluation(bool(operand), "always")

    if operator == "answered":
        answered = _value_of(answers, str(operand)) is not None
        return Evaluation(answered, f"{operand} {'answered' if answered else 'unanswered'}")

    if operator == "answer_includes":
        question = str(operand.get("question", ""))
        wanted = set(operand.get("any_of", []))
        given = set(str(item) for item in _as_list(_value_of(answers, question)))
        overlap = given & wanted
        return Evaluation(
            bool(overlap),
            f"{question} includes {sorted(overlap)}" if overlap
            else f"{question} includes none of {sorted(wanted)}",
        )

    if operator == "answer_equals":
        question = str(operand.get("question", ""))
        expected = operand.get("value")
        actual = _value_of(answers, question, operand.get("field"))
        return Evaluation(actual == expected, f"{question} == {expected!r} (is {actual!r})")

    if operator == "answer_at_least":
        question = str(operand.get("question", ""))
        threshold = operand.get("value", 0)
        actual = _value_of(answers, question, operand.get("field"))
        try:
            meets = actual is not None and float(actual) >= float(threshold)
        except (TypeError, ValueError):
            meets = False
        return Evaluation(meets, f"{question} >= {threshold} (is {actual!r})")

    if operator == "all":
        results = [evaluate(item, answers) for item in operand]
        failed = [r for r in results if not r.applicable]
        return Evaluation(not failed, "all matched" if not failed else f"blocked by {failed[0].reason}")

    if operator == "any":
        results = [evaluate(item, answers) for item in operand]
        matched = [r for r in results if r.applicable]
        return Evaluation(bool(matched), matched[0].reason if matched else "no branch matched")

    if operator == "not":
        inner = evaluate(operand, answers)
        return Evaluation(not inner.applicable, f"not ({inner.reason})")

    return Evaluation(False, f"unknown operator {operator!r}")


def validate(rule: Any, known_questions: set[str]) -> None:
    """Check a rule at load time, so a typo fails the seed rather than the
    interview."""
    if not isinstance(rule, Mapping) or len(rule) != 1:
        raise RuleError(f"rule must be a single-operator object: {rule!r}")

    (operator, operand), = rule.items()

    if operator == "always":
        if not isinstance(operand, bool):
            raise RuleError("always takes a boolean")
        return

    if operator in {"all", "any"}:
        if not isinstance(operand, list) or not operand:
            raise RuleError(f"{operator} takes a non-empty list")
        for item in operand:
            validate(item, known_questions)
        return

    if operator == "not":
        validate(operand, known_questions)
        return

    if operator == "answered":
        question = str(operand)
    elif operator in {"answer_includes", "answer_equals", "answer_at_least"}:
        if not isinstance(operand, Mapping):
            raise RuleError(f"{operator} takes an object")
        question = str(operand.get("question", ""))
    else:
        raise RuleError(f"unknown operator {operator!r}")

    if question not in known_questions:
        raise RuleError(f"rule references unknown question {question!r}")
