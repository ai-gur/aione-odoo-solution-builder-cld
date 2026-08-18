#!/usr/bin/env python
"""Extract capability evidence from pinned Odoo source.

The catalogue has two halves (Blueprint §8). This produces the half that can be
read from source and checked by anyone: which models a module defines, which
security groups it declares, how many access rules it ships, which
configuration settings it adds. Facts, with a file reference for each.

The other half — what a capability lets a business *do* — is written by a
person and stays draft until an AIOne consultant verifies it. This tool never
writes that half, because a capability description is a claim about Odoo
behaviour, and the constitution forbids asserting those without evidence.

Nothing here executes addon code. Python is read with `ast`, XML with a parser
that resolves no entities, CSV as text.

    python scripts/run.py catalogue-evidence
"""

from __future__ import annotations

import ast
import csv
import io
import json
import pathlib
import sys
import xml.etree.ElementTree as ElementTree
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from localenv import load as load_local_env  # noqa: E402

load_local_env()

PILOT = ROOT / "catalogue" / "pilot-scope.json"
RELEASES = ROOT / "catalogue" / "verified-releases"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# A malformed or hostile XML file must not be able to exhaust memory during a
# catalogue build. Odoo's own view files sit far below this.
MAX_XML_BYTES = 8 * 1024 * 1024


def python_models(module_root: pathlib.Path) -> dict[str, list[dict[str, Any]]]:
    """Models a module defines or extends, read without importing anything."""
    defined: list[dict[str, Any]] = []
    extended: list[dict[str, Any]] = []

    for path in sorted(module_root.rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (SyntaxError, UnicodeDecodeError, OSError):
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for statement in node.body:
                if not isinstance(statement, ast.Assign) or len(statement.targets) != 1:
                    continue
                target = statement.targets[0]
                if not isinstance(target, ast.Name) or target.id not in ("_name", "_inherit"):
                    continue
                try:
                    value = ast.literal_eval(statement.value)
                except ValueError:
                    # A computed model name is evidence we cannot read; skipping
                    # it is honest, inventing one would not be.
                    continue
                names = value if isinstance(value, list) else [value]
                for name in names:
                    if not isinstance(name, str):
                        continue
                    entry = {
                        "model": name,
                        "evidence": f"{path.relative_to(module_root).as_posix()}:{statement.lineno}",
                    }
                    (defined if target.id == "_name" else extended).append(entry)

    def unique(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: dict[str, dict[str, Any]] = {}
        for entry in entries:
            seen.setdefault(entry["model"], entry)
        return sorted(seen.values(), key=lambda e: e["model"])

    return {"defines": unique(defined), "extends": unique(extended)}


def xml_records(module_root: pathlib.Path, model: str) -> list[dict[str, Any]]:
    """Records of one model declared in a module's XML data."""
    found: list[dict[str, Any]] = []

    for path in sorted(module_root.rglob("*.xml")):
        try:
            if path.stat().st_size > MAX_XML_BYTES:
                continue
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        # Entity declarations are refused outright rather than resolved.
        if "<!ENTITY" in text or "<!DOCTYPE" in text:
            continue

        try:
            root = ElementTree.fromstring(text)
        except ElementTree.ParseError:
            continue

        for record in root.iter("record"):
            if record.get("model") != model:
                continue
            name = None
            for field in record.findall("field"):
                if field.get("name") == "name":
                    name = (field.text or "").strip() or field.get("eval")
            found.append({
                "xmlId": record.get("id"),
                "name": name,
                "evidence": path.relative_to(module_root).as_posix(),
            })

    return sorted(found, key=lambda entry: entry["xmlId"] or "")


def access_rules(module_root: pathlib.Path) -> dict[str, Any]:
    """Model access rights shipped by the module."""
    path = module_root / "security" / "ir.model.access.csv"
    if not path.is_file():
        return {"count": 0, "models": [], "evidence": None}

    try:
        rows = list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8"))))
    except (OSError, UnicodeDecodeError, csv.Error):
        return {"count": 0, "models": [], "evidence": None, "unreadable": True}

    models = sorted({
        (row.get("model_id:id") or row.get("model_id/id") or "").strip()
        for row in rows
        if (row.get("model_id:id") or row.get("model_id/id"))
    })
    return {
        "count": len(rows),
        "models": models,
        "evidence": "security/ir.model.access.csv",
    }


def config_settings(module_root: pathlib.Path) -> list[dict[str, Any]]:
    """Settings the module adds to res.config.settings.

    These are the switches a provisioning handler would set, so knowing which
    exist — and which module owns each — is what lets a configuration decision
    name a real field rather than a plausible one.
    """
    settings: list[dict[str, Any]] = []

    for path in sorted(module_root.rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (SyntaxError, UnicodeDecodeError, OSError):
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            inherits: list[str] = []
            for statement in node.body:
                if isinstance(statement, ast.Assign) and len(statement.targets) == 1:
                    target = statement.targets[0]
                    if isinstance(target, ast.Name) and target.id == "_inherit":
                        try:
                            value = ast.literal_eval(statement.value)
                        except ValueError:
                            continue
                        inherits = value if isinstance(value, list) else [value]
            if "res.config.settings" not in inherits:
                continue

            for statement in node.body:
                if not isinstance(statement, ast.Assign) or len(statement.targets) != 1:
                    continue
                target = statement.targets[0]
                if not isinstance(target, ast.Name) or target.id.startswith("_"):
                    continue
                call = statement.value
                if not isinstance(call, ast.Call):
                    continue
                field_type = getattr(call.func, "attr", None)
                if not field_type:
                    continue
                settings.append({
                    "field": target.id,
                    "type": field_type,
                    "evidence": f"{path.relative_to(module_root).as_posix()}:{statement.lineno}",
                })

    return sorted(settings, key=lambda entry: entry["field"])


def describe(module: dict[str, Any], source_roots: dict[str, pathlib.Path]) -> dict[str, Any]:
    module_root = source_roots[module["source"]] / module["path"]

    models = python_models(module_root)
    groups = xml_records(module_root, "res.groups")
    return {
        "technicalName": module["technicalName"],
        "source": module["source"],
        "manifestDigest": module["manifestDigest"],
        "models": models,
        "securityGroups": groups,
        "accessRules": access_rules(module_root),
        "configSettings": config_settings(module_root),
        # Everything above is read from source. Nothing here says what the
        # module lets a business do: that is authored and verified separately
        # (Blueprint §8), and this flag is what stops it being assumed.
        "capabilityDescriptions": [],
        "verification": {
            "evidenceExtracted": True,
            "expertReviewed": False,
            "status": "draft",
        },
    }


def main() -> int:
    pilot = json.loads(PILOT.read_text(encoding="utf-8"))
    release_path = RELEASES / f"{pilot['baselineKey']}.json"
    if not release_path.is_file():
        print(f"no release at {release_path.relative_to(ROOT)}; run catalogue-ingest first",
              file=sys.stderr)
        return 1

    release = json.loads(release_path.read_text(encoding="utf-8"))
    by_name = {module["technicalName"]: module for module in release["modules"]}

    import os

    source_roots = {
        "odoo_core": pathlib.Path(os.environ["ODOO_CORE_PATH"]),
        "odoo_enterprise": pathlib.Path(os.environ["ODOO_ENTERPRISE_PATH"]),
    }

    wanted = [name for names in pilot["domains"].values() for name in names]
    missing = [name for name in wanted if name not in by_name]
    if missing:
        print(f"not in the release: {', '.join(missing)}", file=sys.stderr)
        return 1

    evidence = [describe(by_name[name], source_roots) for name in sorted(set(wanted))]

    output = RELEASES / f"{pilot['scopeKey']}-evidence.json"
    document = {
        "kind": "CapabilityEvidence",
        "schemaVersion": "1.0.0",
        "scopeKey": pilot["scopeKey"],
        "baselineKey": pilot["baselineKey"],
        "modules": evidence,
    }
    output.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"evidence for {len(evidence)} pilot modules\n")
    for entry in evidence:
        print(
            f"  {entry['technicalName']:<18}"
            f" models {len(entry['models']['defines']):>3} defined,"
            f" {len(entry['models']['extends']):>3} extended"
            f" | groups {len(entry['securityGroups']):>2}"
            f" | acl {entry['accessRules']['count']:>3}"
            f" | settings {len(entry['configSettings']):>3}"
        )
    print(f"\nwritten to {output.relative_to(ROOT)}")
    print("every record is draft until an AIOne consultant verifies it")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
