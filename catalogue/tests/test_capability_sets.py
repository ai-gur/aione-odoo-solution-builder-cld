"""Capability records, checked against the pinned baseline they claim.

A capability record is a technical claim about Odoo. Unlike the ingestion and
evidence tests, these run against the real catalogue files, because the point
is to catch a claim that has drifted from the source it cites — a module that
does not exist at the pinned revision, an edition that understates what a
customer must license, a topic listed as unresolved that some capability
quietly answers.

Verification provenance is checked here too. `status: verified` is what lets a
fit assessment reach green, so a record that claims it must name the reviewer
and the date. The database enforces the same rule (migration 0010); this
catches it before anything is loaded.
"""

from __future__ import annotations

import datetime
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
CAPABILITIES = ROOT / "catalogue" / "capabilities"
RELEASES = ROOT / "catalogue" / "verified-releases"

# Enterprise is the stronger claim: one Enterprise module makes the whole
# capability Enterprise, because the customer cannot install part of it.
EDITION_OF_SOURCE = {"odoo_core": "community", "odoo_enterprise": "enterprise"}


def capability_files() -> list[pathlib.Path]:
    return sorted(CAPABILITIES.glob("*.json"))


def baseline(key: str) -> dict[str, dict]:
    path = RELEASES / f"{key}.json"
    if not path.exists():
        raise AssertionError(f"capability set cites baseline {key}, which has no release file")
    release = json.loads(path.read_text(encoding="utf-8"))
    return {module["technicalName"]: module for module in release["modules"]}


class CapabilitySetTestCase(unittest.TestCase):
    """Every check runs over every capability file, naming the offender."""

    def documents(self):
        for path in capability_files():
            yield path, json.loads(path.read_text(encoding="utf-8"))

    def test_there_is_at_least_one_capability_set(self) -> None:
        self.assertTrue(capability_files(), "no capability files found")


class TestClaims(CapabilitySetTestCase):
    def test_every_module_exists_at_the_pinned_revision(self) -> None:
        for path, document in self.documents():
            modules = baseline(document["baselineKey"])
            for capability in document["capabilities"]:
                for module in capability["modules"]:
                    self.assertIn(
                        module, modules,
                        f"{path.name}: {capability['capabilityKey']} names {module}, "
                        f"which does not exist in {document['baselineKey']}",
                    )

    def test_the_declared_edition_covers_every_module_it_names(self) -> None:
        """Understating the edition understates what the customer must buy."""
        for path, document in self.documents():
            modules = baseline(document["baselineKey"])
            for capability in document["capabilities"]:
                editions = {
                    EDITION_OF_SOURCE[modules[m]["source"]] for m in capability["modules"]
                }
                required = "enterprise" if "enterprise" in editions else "community"
                self.assertEqual(
                    capability["edition"], required,
                    f"{path.name}: {capability['capabilityKey']} declares "
                    f"{capability['edition']} but its modules require {required}",
                )

    def test_partial_coverage_records_what_is_missing(self) -> None:
        for path, document in self.documents():
            for capability in document["capabilities"]:
                gap = capability.get("residualGap")
                if capability["coverage"] == "partial":
                    self.assertTrue(
                        gap, f"{path.name}: {capability['capabilityKey']} is partial "
                             "but records no residual gap",
                    )
                else:
                    self.assertIsNone(
                        gap, f"{path.name}: {capability['capabilityKey']} claims full "
                             "coverage and a residual gap at once",
                    )

    def test_every_capability_cites_evidence(self) -> None:
        for path, document in self.documents():
            for capability in document["capabilities"]:
                self.assertTrue(
                    capability.get("evidence"),
                    f"{path.name}: {capability['capabilityKey']} cites no evidence",
                )
                self.assertTrue(
                    capability.get("addressesTopics"),
                    f"{path.name}: {capability['capabilityKey']} addresses no topic, "
                    "so no requirement can ever reach it",
                )

    def test_capability_keys_are_unique(self) -> None:
        for path, document in self.documents():
            keys = [c["capabilityKey"] for c in document["capabilities"]]
            self.assertEqual(len(keys), len(set(keys)), f"{path.name}: duplicate capability key")

    def test_a_topic_is_never_both_addressed_and_unresolved(self) -> None:
        """Otherwise the same requirement is answered and open at once, and
        which one wins depends on load order."""
        for path, document in self.documents():
            addressed = {
                topic for c in document["capabilities"] for topic in c["addressesTopics"]
            }
            for unresolved in document.get("unresolvedTopics", []):
                self.assertNotIn(
                    unresolved["topic"], addressed,
                    f"{path.name}: {unresolved['topic']} is listed unresolved and "
                    "addressed by a capability",
                )

    def test_every_unresolved_topic_says_why_and_what_next(self) -> None:
        for path, document in self.documents():
            for unresolved in document.get("unresolvedTopics", []):
                self.assertTrue(unresolved.get("reason"), f"{path.name}: {unresolved['topic']}")
                self.assertTrue(unresolved.get("treatment"), f"{path.name}: {unresolved['topic']}")

    def test_an_answered_candidate_carries_the_evidence_for_its_answer(self) -> None:
        """Ruling a candidate out is itself a technical claim. 'We checked and
        it cannot do this' has to be as checkable as 'it can'."""
        for path, document in self.documents():
            for unresolved in document.get("unresolvedTopics", []):
                for candidate in unresolved.get("candidatesRequiringVerification", []):
                    if "answer" not in candidate:
                        continue
                    where = f"{path.name}: {unresolved['topic']} / {candidate['modules']}"
                    self.assertTrue(candidate.get("evidence"), f"{where} answers with no evidence")
                    datetime.date.fromisoformat(candidate["answeredOn"])

    def test_a_capability_naming_an_enterprise_module_is_reachable(self) -> None:
        """Every module a capability names must be in the pilot scope, so its
        evidence was actually extracted rather than assumed."""
        scope = json.loads((ROOT / "catalogue" / "pilot-scope.json").read_text(encoding="utf-8"))
        in_scope = {name for names in scope["domains"].values() for name in names}
        for path, document in self.documents():
            if document["scopeKey"] != scope["scopeKey"]:
                continue
            for capability in document["capabilities"]:
                for module in capability["modules"]:
                    self.assertIn(
                        module, in_scope,
                        f"{path.name}: {capability['capabilityKey']} names {module}, "
                        "which is outside the pilot scope and therefore unevidenced",
                    )


class TestVerificationProvenance(CapabilitySetTestCase):
    def test_a_verified_capability_names_its_reviewer_and_date(self) -> None:
        for path, document in self.documents():
            for capability in document["capabilities"]:
                if capability["status"] != "verified":
                    continue
                verification = capability.get("verification") or {}
                where = f"{path.name}: {capability['capabilityKey']}"
                self.assertTrue(
                    verification.get("reviewer"),
                    f"{where} is verified but names no reviewer; a green assessment "
                    "would then rest on nobody",
                )
                self.assertTrue(verification.get("note"), f"{where} records no what-was-confirmed")
                datetime.date.fromisoformat(verification["date"])  # raises if not a real date

    def test_a_draft_capability_claims_no_verification(self) -> None:
        for path, document in self.documents():
            for capability in document["capabilities"]:
                if capability["status"] == "draft":
                    self.assertIsNone(
                        capability.get("verification"),
                        f"{path.name}: {capability['capabilityKey']} is draft but "
                        "carries a verification record",
                    )

    def test_verification_never_silently_widens_coverage(self) -> None:
        """Reviewing a capability confirms what it says. A reviewer who wants
        to claim more edits the record, and that shows up as a new digest."""
        for path, document in self.documents():
            for capability in document["capabilities"]:
                if capability["status"] == "verified" and capability["coverage"] == "partial":
                    self.assertTrue(
                        capability.get("residualGap"),
                        f"{path.name}: {capability['capabilityKey']} was verified as "
                        "partial and must still record its gap",
                    )


if __name__ == "__main__":
    unittest.main(verbosity=2)
