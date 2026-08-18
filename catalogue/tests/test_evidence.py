"""Capability evidence extraction (Increment 4).

Synthetic addon trees again: a test that depends on upstream Odoo fails when
upstream changes and teaches the team to ignore it.

The properties under test are what make the evidence trustworthy — it is read
without executing anything, every fact carries a file reference, and a fact
that cannot be read is omitted rather than guessed.
"""

from __future__ import annotations

import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "catalogue" / "ingestion"))

from extract_evidence import (  # noqa: E402
    access_rules,
    config_settings,
    python_models,
    xml_records,
)


def write(root: pathlib.Path, relative: str, content: str) -> pathlib.Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


class TestModelExtraction(unittest.TestCase):
    def test_defined_and_extended_models_are_separated(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = pathlib.Path(raw)
            write(root, "models/order.py", (
                "from odoo import models\n"
                "class Order(models.Model):\n"
                "    _name = 'wholesale.order'\n"
                "class Partner(models.Model):\n"
                "    _inherit = 'res.partner'\n"
            ))
            models = python_models(root)
            self.assertEqual([m["model"] for m in models["defines"]], ["wholesale.order"])
            self.assertEqual([m["model"] for m in models["extends"]], ["res.partner"])

    def test_every_model_carries_a_file_and_line_reference(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = pathlib.Path(raw)
            write(root, "models/order.py", "class O:\n    _name = 'a.b'\n")
            entry = python_models(root)["defines"][0]
            self.assertEqual(entry["evidence"], "models/order.py:2")

    def test_a_computed_model_name_is_omitted_rather_than_guessed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = pathlib.Path(raw)
            write(root, "models/dynamic.py", (
                "PREFIX = 'wholesale'\n"
                "class Dynamic:\n"
                "    _name = PREFIX + '.thing'\n"
            ))
            self.assertEqual(python_models(root)["defines"], [])

    def test_a_file_that_would_execute_code_is_never_run(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = pathlib.Path(raw)
            marker = root / "PROOF_OF_EXECUTION"
            write(root, "models/hostile.py", (
                f"import pathlib\npathlib.Path({str(marker)!r}).write_text('executed')\n"
                "class X:\n    _name = 'x.y'\n"
            ))
            models = python_models(root)
            self.assertFalse(marker.exists(), "module source was executed")
            # Reading the file is still fine: the model is found by parsing.
            self.assertEqual([m["model"] for m in models["defines"]], ["x.y"])

    def test_a_syntactically_broken_file_is_skipped_not_fatal(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = pathlib.Path(raw)
            write(root, "models/broken.py", "class X(:\n")
            write(root, "models/good.py", "class Y:\n    _name = 'y.z'\n")
            self.assertEqual([m["model"] for m in python_models(root)["defines"]], ["y.z"])


class TestSecurityEvidence(unittest.TestCase):
    def test_groups_are_read_from_xml_with_their_file(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = pathlib.Path(raw)
            write(root, "security/groups.xml", (
                "<odoo>"
                "<record id='group_wholesale_manager' model='res.groups'>"
                "<field name='name'>Wholesale Manager</field></record>"
                "<record id='other' model='ir.ui.view'><field name='name'>v</field></record>"
                "</odoo>"
            ))
            groups = xml_records(root, "res.groups")
            self.assertEqual(len(groups), 1)
            self.assertEqual(groups[0]["xmlId"], "group_wholesale_manager")
            self.assertEqual(groups[0]["name"], "Wholesale Manager")
            self.assertEqual(groups[0]["evidence"], "security/groups.xml")

    def test_xml_declaring_entities_is_refused(self) -> None:
        """Addon source is treated as untrusted input (SECURITY-BASELINE
        §Supply chain), so entity expansion is never attempted."""
        with tempfile.TemporaryDirectory() as raw:
            root = pathlib.Path(raw)
            write(root, "security/bomb.xml", (
                "<!DOCTYPE odoo [<!ENTITY a 'aaaaaaaaaa'>]>"
                "<odoo><record id='x' model='res.groups'>"
                "<field name='name'>&a;</field></record></odoo>"
            ))
            self.assertEqual(xml_records(root, "res.groups"), [])

    def test_access_rules_are_counted_with_their_models(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = pathlib.Path(raw)
            write(root, "security/ir.model.access.csv", (
                "id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink\n"
                "a,Order user,model_wholesale_order,base.group_user,1,1,1,0\n"
                "b,Order manager,model_wholesale_order,base.group_system,1,1,1,1\n"
            ))
            rules = access_rules(root)
            self.assertEqual(rules["count"], 2)
            self.assertEqual(rules["models"], ["model_wholesale_order"])

    def test_a_module_without_access_rules_reports_zero(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            rules = access_rules(pathlib.Path(raw))
            self.assertEqual(rules["count"], 0)
            self.assertIsNone(rules["evidence"])


class TestConfigSettings(unittest.TestCase):
    def test_settings_fields_are_found_with_their_type(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = pathlib.Path(raw)
            write(root, "wizard/res_config_settings.py", (
                "from odoo import fields, models\n"
                "class Settings(models.TransientModel):\n"
                "    _inherit = 'res.config.settings'\n"
                "    group_discount_per_line = fields.Boolean('Discounts')\n"
                "    default_warehouse_id = fields.Many2one('stock.warehouse')\n"
            ))
            settings = config_settings(root)
            self.assertEqual(
                [(s["field"], s["type"]) for s in settings],
                [("default_warehouse_id", "Many2one"), ("group_discount_per_line", "Boolean")],
            )

    def test_fields_on_other_models_are_not_reported_as_settings(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = pathlib.Path(raw)
            write(root, "models/order.py", (
                "from odoo import fields, models\n"
                "class Order(models.Model):\n"
                "    _name = 'wholesale.order'\n"
                "    note = fields.Char()\n"
            ))
            self.assertEqual(config_settings(root), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
