"""Odoo workspace health check (Increment 0, story I0-08).

Needs no database. What matters here is that the check reports honestly:
a missing path is named, a drifted revision is reported rather than corrected,
and nothing in a workspace repository is written to.
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "workspace_health.py"
PINNED = ROOT / "catalogue" / "pinned-sources.json"


def run_check(env_overrides: dict[str, str]) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, **env_overrides}
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True, text=True, encoding="utf-8", env=env, cwd=str(ROOT),
    )


def make_repo(directory: pathlib.Path) -> str:
    """A throwaway git checkout, so the test never touches a real workspace."""
    subprocess.run(["git", "init", "-q", str(directory)], check=True)
    (directory / "README").write_text("fixture", encoding="utf-8")
    for command in (
        ["git", "-C", str(directory), "add", "."],
        ["git", "-C", str(directory), "-c", "user.email=t@t.test",
         "-c", "user.name=Test", "commit", "-qm", "fixture"],
    ):
        subprocess.run(command, check=True, capture_output=True)
    return subprocess.run(
        ["git", "-C", str(directory), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()


class TestPinnedSources(unittest.TestCase):
    def test_the_baseline_records_a_full_revision_for_every_source(self) -> None:
        document = json.loads(PINNED.read_text(encoding="utf-8"))
        for name, source in document["sources"].items():
            with self.subTest(source=name):
                self.assertRegex(
                    source["revision"], r"^[0-9a-f]{40}$",
                    f"{name} must pin a full revision; an abbreviation can become ambiguous",
                )
                self.assertTrue(source["envPath"])

    def test_the_enterprise_licence_key_is_not_recorded_here(self) -> None:
        """The key is a secret resolved by reference (ADR-010). A baseline file
        is committed, so a key in it would be a key in the repository."""
        raw = PINNED.read_text(encoding="utf-8").lower()
        for forbidden in ("licence_key", "license_key", "enterprise_code", "subscription_code"):
            self.assertNotIn(forbidden, raw)


class TestWorkspaceHealth(unittest.TestCase):
    def test_unset_paths_are_reported_by_name(self) -> None:
        result = run_check({
            "ODOO_CORE_PATH": "", "ODOO_ENTERPRISE_PATH": "", "ODOO_FOUNDATION_PATH": "",
        })
        self.assertEqual(result.returncode, 1)
        self.assertIn("MISSING", result.stdout)
        # The developer is told which setting to fix, not merely that something failed.
        self.assertIn("ODOO_CORE_PATH", result.stdout)

    def test_a_path_that_does_not_exist_is_reported(self) -> None:
        result = run_check({"ODOO_CORE_PATH": str(ROOT / "does-not-exist")})
        self.assertEqual(result.returncode, 1)
        self.assertIn("does not exist", result.stdout)

    def test_a_drifted_revision_is_reported_and_not_corrected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = pathlib.Path(raw) / "core"
            repo.mkdir()
            revision = make_repo(repo)

            result = run_check({"ODOO_CORE_PATH": str(repo)})
            self.assertEqual(result.returncode, 1)
            self.assertIn("DRIFTED", result.stdout)
            self.assertIn("catalogue release", result.stdout)

            after = subprocess.run(
                ["git", "-C", str(repo), "rev-parse", "HEAD"],
                capture_output=True, text=True, check=True,
            ).stdout.strip()
            self.assertEqual(after, revision, "the check must not move a workspace repository")

    def test_the_check_makes_no_change_to_a_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = pathlib.Path(raw) / "core"
            repo.mkdir()
            make_repo(repo)
            before = subprocess.run(
                ["git", "-C", str(repo), "status", "--porcelain", "-b"],
                capture_output=True, text=True, check=True,
            ).stdout

            run_check({"ODOO_CORE_PATH": str(repo)})

            after = subprocess.run(
                ["git", "-C", str(repo), "status", "--porcelain", "-b"],
                capture_output=True, text=True, check=True,
            ).stdout
            self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main(verbosity=2)
