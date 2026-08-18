"""Catalogue ingestion (Increment 4).

Tests run against synthetic addon trees, never against the real Odoo source:
a test that depends on 658 upstream modules fails when upstream changes, which
teaches the team to ignore it.

The property that matters most here is negative — ingestion must not execute
addon code — so it is proved by trying to make it execute something.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "catalogue" / "ingestion"))

from ingest import (  # noqa: E402
    IngestionRefused,
    collect,
    parse_manifest,
    resolve_dependencies,
    verify_source,
)


def write_module(root: pathlib.Path, name: str, manifest: str) -> pathlib.Path:
    directory = root / name
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "__manifest__.py").write_text(manifest, encoding="utf-8")
    return directory


def make_git_repo(root: pathlib.Path) -> str:
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "add", "."], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(root), "-c", "user.email=t@t.test", "-c", "user.name=Test",
         "commit", "-qm", "fixture"],
        check=True, capture_output=True,
    )
    return subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()


class TestManifestParsing(unittest.TestCase):
    def test_a_literal_manifest_is_read(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = pathlib.Path(raw)
            path = write_module(
                root, "sale_x",
                "{'name': 'Sales', 'version': '19.0.1.0', 'depends': ['base', 'product'],"
                " 'license': 'LGPL-3', 'application': True}",
            ) / "__manifest__.py"
            data, error = parse_manifest(path)
            self.assertIsNone(error)
            self.assertEqual(data["name"], "Sales")
            self.assertEqual(data["depends"], ["base", "product"])

    def test_a_manifest_that_would_execute_code_does_not_run(self) -> None:
        """The central safety property (ADR-007, SECURITY-BASELINE §Supply chain).

        Importing a manifest runs whatever it contains. This one would write a
        file if it were executed; the assertion is that the file never appears.
        """
        with tempfile.TemporaryDirectory() as raw:
            root = pathlib.Path(raw)
            marker = root / "PROOF_OF_EXECUTION"
            hostile = (
                "__import__('pathlib').Path(%r).write_text('executed')\n" % str(marker)
                + "{'name': 'Hostile', 'depends': []}"
            )
            path = write_module(root, "hostile", hostile) / "__manifest__.py"

            data, error = parse_manifest(path)

            self.assertFalse(marker.exists(), "the manifest was executed")
            self.assertIsNone(data)
            self.assertIsNotNone(error)

    def test_a_computed_manifest_is_recorded_not_executed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = pathlib.Path(raw)
            path = write_module(
                root, "computed", "{'name': 'X', 'depends': ['base'] + ['product']}"
            ) / "__manifest__.py"
            data, error = parse_manifest(path)
            self.assertIsNone(data)
            self.assertIn("literal", error)

    def test_a_broken_manifest_is_reported_with_its_line(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = pathlib.Path(raw)
            path = write_module(root, "broken", "{'name': 'X',,}") / "__manifest__.py"
            data, error = parse_manifest(path)
            self.assertIsNone(data)
            self.assertIn("syntax error", error)


class TestCollection(unittest.TestCase):
    def test_modules_record_their_hooks_and_digest(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = pathlib.Path(raw)
            write_module(
                root, "with_hooks",
                "{'name': 'H', 'depends': [], 'post_init_hook': 'setup',"
                " 'uninstall_hook': 'teardown'}",
            )
            modules = collect(root, "odoo_core")
            self.assertEqual(len(modules), 1)
            # Hooks run code at install time, which provisioning treats as
            # elevated risk. A blueprint decision needs to see it beforehand.
            self.assertEqual(sorted(modules[0].hooks), ["post_init_hook", "uninstall_hook"])
            self.assertRegex(modules[0].manifest_digest, r"^sha256:[0-9a-f]{64}$")

    def test_a_duplicate_module_name_refuses_the_build(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = pathlib.Path(raw)
            write_module(root / "a", "sale", "{'name': 'A', 'depends': []}")
            write_module(root / "b", "sale", "{'name': 'B', 'depends': []}")
            with self.assertRaises(IngestionRefused):
                collect(root, "odoo_core")


class TestDependencyGraph(unittest.TestCase):
    def build(self, spec: dict[str, list[str]]):
        with tempfile.TemporaryDirectory() as raw:
            root = pathlib.Path(raw)
            for name, depends in spec.items():
                write_module(root, name, f"{{'name': '{name}', 'depends': {depends!r}}}")
            modules = {m.technical_name: m for m in collect(root, "odoo_core")}
            return resolve_dependencies(modules)

    def test_transitive_dependencies_are_resolved(self) -> None:
        graph = self.build({"base": [], "product": ["base"], "sale": ["product"]})
        self.assertEqual(graph["transitive"]["sale"], ["base", "product"])

    def test_a_missing_dependency_is_reported_not_invented(self) -> None:
        graph = self.build({"sale": ["product"]})
        self.assertEqual(graph["missing"], {"sale": ["product"]})
        self.assertEqual(graph["transitive"]["sale"], [])

    def test_a_cycle_is_detected(self) -> None:
        graph = self.build({"a": ["b"], "b": ["a"]})
        self.assertTrue(graph["cycles"])


class TestSourceVerification(unittest.TestCase):
    def test_a_wrong_revision_refuses(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = pathlib.Path(raw)
            write_module(root, "base", "{'name': 'Base', 'depends': []}")
            make_git_repo(root)
            with self.assertRaises(IngestionRefused) as refused:
                verify_source(root, "0" * 40, "odoo_core")
            self.assertIn("baseline pins", str(refused.exception))

    def test_a_matching_revision_passes(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = pathlib.Path(raw)
            write_module(root, "base", "{'name': 'Base', 'depends': []}")
            revision = make_git_repo(root)
            verify_source(root, revision, "odoo_core")

    def test_an_incomplete_working_tree_refuses(self) -> None:
        """The failure that prompted this guard: a sparse, partial clone has
        the full history but almost no files, so a catalogue built from it
        would describe a source nobody has."""
        with tempfile.TemporaryDirectory() as raw:
            root = pathlib.Path(raw)
            for name in ("base", "product", "sale"):
                write_module(root, name, f"{{'name': '{name}', 'depends': []}}")
            revision = make_git_repo(root)

            # Committed, then removed from the working tree.
            (root / "sale" / "__manifest__.py").unlink()

            with self.assertRaises(IngestionRefused) as refused:
                verify_source(root, revision, "odoo_core")
            self.assertIn("exist at this revision", str(refused.exception))

    def test_a_directory_that_is_not_a_checkout_refuses(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            with self.assertRaises(IngestionRefused):
                verify_source(pathlib.Path(raw), "0" * 40, "odoo_core")


class TestPinnedBaseline(unittest.TestCase):
    def test_the_baseline_is_the_only_place_revisions_are_stated(self) -> None:
        """A revision hard-coded in the ingestion tool could diverge from the
        baseline the manifests and blueprints reference."""
        source = (ROOT / "catalogue" / "ingestion" / "ingest.py").read_text(encoding="utf-8")
        pinned = json.loads((ROOT / "catalogue" / "pinned-sources.json").read_text(encoding="utf-8"))
        for entry in pinned["sources"].values():
            revision = entry.get("revision")
            if revision:
                self.assertNotIn(revision, source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
