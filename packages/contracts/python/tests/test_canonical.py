"""Canonicalization and digest tests.

The fixture file is shared with the TypeScript suite. If these pass here and
there, the two implementations agree byte for byte, which is the property
ADR-015 actually needs.
"""

from __future__ import annotations

import json
import math
import pathlib
import unittest

from aione_contracts.canonical import CanonicalizationError, canonicalize
from aione_contracts.digest import digest, digests_match, document_digest

FIXTURE_PATH = (
    pathlib.Path(__file__).resolve().parents[2] / "fixtures" / "canonicalization.json"
)
FIXTURES = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


class TestCanonicalize(unittest.TestCase):
    def test_shared_fixtures(self) -> None:
        for case in FIXTURES["cases"]:
            with self.subTest(case=case["name"]):
                self.assertEqual(canonicalize(case["value"]), case["canonical"])

    def test_rejects_non_finite_numbers(self) -> None:
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value):
                with self.assertRaises(CanonicalizationError):
                    canonicalize({"n": value})

    def test_rejects_numbers_outside_the_safe_integer_range(self) -> None:
        # These are the values where Python and JavaScript would disagree about
        # the canonical form, and therefore about the digest.
        for unsafe in FIXTURES["rejected"]["unsafeNumbers"]:
            with self.subTest(value=unsafe):
                with self.assertRaises(CanonicalizationError):
                    canonicalize({"n": unsafe})

    def test_rejects_non_json_values(self) -> None:
        with self.assertRaises(CanonicalizationError):
            canonicalize({"when": object()})

    def test_booleans_are_not_treated_as_integers(self) -> None:
        self.assertEqual(canonicalize({"flag": True}), '{"flag":true}')
        self.assertEqual(canonicalize({"flag": False}), '{"flag":false}')

    def test_stable_regardless_of_insertion_order(self) -> None:
        first = canonicalize({"a": 1, "b": {"c": 2, "d": 3}})
        second = canonicalize({"b": {"d": 3, "c": 2}, "a": 1})
        self.assertEqual(first, second)

    def test_error_names_the_path(self) -> None:
        with self.assertRaises(CanonicalizationError) as raised:
            canonicalize({"spec": {"modules": [1, object()]}})
        self.assertIn("spec.modules[1]", str(raised.exception))


class TestDigest(unittest.TestCase):
    def test_digest_shape(self) -> None:
        self.assertRegex(digest({"a": 1}), r"^sha256:[0-9a-f]{64}$")

    def test_digest_differs_on_any_change(self) -> None:
        self.assertNotEqual(digest({"a": 1}), digest({"a": 2}))
        self.assertNotEqual(digest({"a": 1}), digest({"a": "1"}))

    def test_document_digest_ignores_excluded_fields(self) -> None:
        exclusions = FIXTURES["digestExclusions"]
        self.assertEqual(
            document_digest(exclusions["document"], exclusions["kind"]),
            document_digest(exclusions["equivalentDocument"], exclusions["kind"]),
        )

    def test_unknown_kind_is_refused(self) -> None:
        with self.assertRaises(KeyError):
            document_digest({"a": 1}, "UnknownKind")

    def test_digests_match(self) -> None:
        self.assertTrue(digests_match("sha256:abc", "sha256:abc"))
        self.assertFalse(digests_match("sha256:abc", "sha256:abd"))


if __name__ == "__main__":
    unittest.main()
