#!/usr/bin/env python
"""Odoo manifest ingestion.

Builds the factual half of a catalogue release: exact module names, versions,
licences, dependencies and hooks, read from the source at a pinned revision
(ADR-007). The interpretive half — what a module lets a business *do* — is
added by expert review afterwards and is not this tool's job.

Two rules shape the implementation.

**Manifests are parsed, never executed.** An `__manifest__.py` is a Python
file, and importing one runs whatever it contains. This reads it with `ast`
and evaluates only literal structures, so a hostile or merely careless addon
cannot run code during catalogue ingestion (ADR-007, SECURITY-BASELINE
§Supply chain).

**A release refuses to build from a source it cannot vouch for.** If the
checkout is at the wrong revision, or its working tree is incomplete, the run
stops. A catalogue that silently describes 5 modules out of 658 would be worse
than no catalogue: every downstream claim would be true of a source nobody
has.
"""

from __future__ import annotations

import ast
import hashlib
import json
import pathlib
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages" / "contracts" / "python"))

from aione_contracts import canonical_bytes  # noqa: E402

PINNED = ROOT / "catalogue" / "pinned-sources.json"
RELEASES = ROOT / "catalogue" / "verified-releases"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


class IngestionRefused(Exception):
    """The source cannot be vouched for, so no release is produced."""


@dataclass
class Module:
    technical_name: str
    source: str
    relative_path: str
    manifest_digest: str
    name: str = ""
    version: str = ""
    category: str = ""
    licence: str = ""
    summary: str = ""
    depends: list[str] = field(default_factory=list)
    installable: bool = True
    auto_install: Any = False
    application: bool = False
    external_dependencies: dict[str, Any] = field(default_factory=dict)
    # Hooks run arbitrary code at install or uninstall time, which the
    # provisioning engine treats as elevated risk (Provisioning §19.7). Recorded
    # here so a blueprint decision can see it before a handler runs.
    hooks: list[str] = field(default_factory=list)
    countries: list[str] = field(default_factory=list)
    parse_error: str | None = None


HOOK_KEYS = ("pre_init_hook", "post_init_hook", "uninstall_hook", "post_load")


def git(path: pathlib.Path, *args: str) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(path), *args], capture_output=True, text=True, encoding="utf-8"
    )
    return result.stdout.strip() if result.returncode == 0 else None


def verify_source(path: pathlib.Path, expected_revision: str, label: str) -> None:
    """Refuse to ingest a source that cannot be vouched for."""
    if not path.is_dir():
        raise IngestionRefused(f"{label}: {path} does not exist")

    actual = git(path, "rev-parse", "HEAD")
    if actual is None:
        raise IngestionRefused(f"{label}: {path} is not a git checkout, so its revision is unknown")
    if actual != expected_revision:
        raise IngestionRefused(
            f"{label}: checked out {actual[:12]}, baseline pins {expected_revision[:12]}. "
            "Build the release from the pinned revision, or publish a new baseline."
        )

    in_git = len([
        line for line in (git(path, "ls-tree", "-r", "--name-only", "HEAD") or "").splitlines()
        if line.endswith("__manifest__.py")
    ])
    on_disk = len(list(path.rglob("__manifest__.py")))

    if on_disk < in_git:
        sparse = git(path, "config", "core.sparseCheckout") == "true"
        partial = git(path, "config", "remote.origin.partialclonefilter")
        detail = []
        if sparse:
            detail.append("the working tree is a sparse checkout")
        if partial:
            detail.append(f"the clone is partial ({partial}), so file contents live on the remote")
        raise IngestionRefused(
            f"{label}: {on_disk} manifests present, {in_git} exist at this revision"
            + (f" — {', '.join(detail)}" if detail else "")
            + ". A catalogue built from an incomplete tree would describe a source nobody has."
        )


def parse_manifest(path: pathlib.Path) -> tuple[dict[str, Any] | None, str | None]:
    """Read a manifest without executing it.

    `ast.literal_eval` accepts only literals — dicts, lists, strings, numbers,
    booleans. A manifest that computes its values fails here and is recorded as
    unparseable rather than being run to find out what it means.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        return None, f"unreadable: {type(error).__name__}"

    try:
        tree = ast.parse(text, mode="eval")
    except SyntaxError as error:
        return None, f"syntax error at line {error.lineno}"

    try:
        value = ast.literal_eval(tree)
    except ValueError:
        return None, "manifest is not a literal structure; it would have to be executed to read"

    if not isinstance(value, dict):
        return None, f"manifest is a {type(value).__name__}, expected a dict"
    return value, None


def read_module(manifest_path: pathlib.Path, source: str, root: pathlib.Path) -> Module:
    raw = manifest_path.read_bytes()
    module = Module(
        technical_name=manifest_path.parent.name,
        source=source,
        relative_path=str(manifest_path.parent.relative_to(root)).replace("\\", "/"),
        manifest_digest="sha256:" + hashlib.sha256(raw).hexdigest(),
    )

    data, error = parse_manifest(manifest_path)
    if data is None:
        module.parse_error = error
        return module

    def text(key: str) -> str:
        value = data.get(key, "")
        return value if isinstance(value, str) else ""

    module.name = text("name")
    module.version = text("version")
    module.category = text("category")
    module.licence = text("license")
    module.summary = text("summary")
    module.depends = [d for d in data.get("depends", []) if isinstance(d, str)]
    module.installable = bool(data.get("installable", True))
    module.auto_install = data.get("auto_install", False)
    module.application = bool(data.get("application", False))
    external = data.get("external_dependencies", {})
    module.external_dependencies = external if isinstance(external, dict) else {}
    module.hooks = [key for key in HOOK_KEYS if key in data]
    module.countries = [c for c in data.get("countries", []) if isinstance(c, str)]
    return module


def collect(root: pathlib.Path, source: str) -> list[Module]:
    modules = [
        read_module(manifest, source, root)
        for manifest in sorted(root.rglob("__manifest__.py"))
    ]
    # A module directory appearing twice in one source would make "which code
    # is this" unanswerable.
    seen: dict[str, str] = {}
    for module in modules:
        if module.technical_name in seen:
            raise IngestionRefused(
                f"{source}: {module.technical_name} appears at both "
                f"{seen[module.technical_name]} and {module.relative_path}"
            )
        seen[module.technical_name] = module.relative_path
    return modules


def resolve_dependencies(modules: dict[str, Module]) -> dict[str, Any]:
    """Transitive dependencies, missing references and cycles."""
    transitive: dict[str, list[str]] = {}
    missing: dict[str, list[str]] = {}
    cycles: list[list[str]] = []

    def walk(name: str, seen: set[str], stack: list[str]) -> set[str]:
        module = modules.get(name)
        if module is None:
            return set()
        result: set[str] = set()
        for dependency in module.depends:
            if dependency not in modules:
                missing.setdefault(name, []).append(dependency)
                continue
            if dependency in stack:
                cycle = stack[stack.index(dependency):] + [dependency]
                if cycle not in cycles:
                    cycles.append(cycle)
                continue
            if dependency in seen:
                result.add(dependency)
                result |= set(transitive.get(dependency, []))
                continue
            seen.add(dependency)
            result.add(dependency)
            result |= walk(dependency, seen, stack + [dependency])
        return result

    for name in modules:
        transitive[name] = sorted(walk(name, set(), [name]))

    return {"transitive": transitive, "missing": missing, "cycles": cycles}


def build(core_path: pathlib.Path, enterprise_path: pathlib.Path) -> dict[str, Any]:
    document = json.loads(PINNED.read_text(encoding="utf-8"))
    sources = document["sources"]

    verify_source(core_path, sources["odoo_core"]["revision"], "odoo_core")
    verify_source(enterprise_path, sources["odoo_enterprise"]["revision"], "odoo_enterprise")

    modules = collect(core_path, "odoo_core") + collect(enterprise_path, "odoo_enterprise")
    by_name = {module.technical_name: module for module in modules}
    graph = resolve_dependencies(by_name)

    unparseable = [m.technical_name for m in modules if m.parse_error]

    release = {
        "kind": "CatalogueRelease",
        "schemaVersion": "1.0.0",
        "baselineKey": document["baselineKey"],
        "sources": {
            "odoo_core": sources["odoo_core"]["revision"],
            "odoo_enterprise": sources["odoo_enterprise"]["revision"],
        },
        "status": "draft",
        "modules": [
            {
                "technicalName": m.technical_name,
                "source": m.source,
                "path": m.relative_path,
                "name": m.name,
                "version": m.version,
                "category": m.category,
                "licence": m.licence,
                "summary": m.summary,
                "application": m.application,
                "installable": m.installable,
                "autoInstall": m.auto_install if isinstance(m.auto_install, bool) else True,
                "depends": m.depends,
                "transitiveDepends": graph["transitive"].get(m.technical_name, []),
                "externalDependencies": m.external_dependencies,
                "hooks": m.hooks,
                "countries": m.countries,
                "manifestDigest": m.manifest_digest,
                "parseError": m.parse_error,
            }
            for m in sorted(modules, key=lambda m: m.technical_name)
        ],
        "summary": {
            "moduleCount": len(modules),
            "applicationCount": sum(1 for m in modules if m.application),
            "withHooks": sum(1 for m in modules if m.hooks),
            "withExternalDependencies": sum(1 for m in modules if m.external_dependencies),
            "unparseable": unparseable,
            "missingDependencies": graph["missing"],
            "dependencyCycles": graph["cycles"],
        },
    }

    release["contentDigest"] = "sha256:" + hashlib.sha256(canonical_bytes(release)).hexdigest()
    return release


def main() -> int:
    import os

    core = os.environ.get("ODOO_CORE_PATH", "").strip()
    enterprise = os.environ.get("ODOO_ENTERPRISE_PATH", "").strip()
    if not core or not enterprise:
        print("ODOO_CORE_PATH and ODOO_ENTERPRISE_PATH must be set", file=sys.stderr)
        return 2

    try:
        release = build(pathlib.Path(core), pathlib.Path(enterprise))
    except IngestionRefused as error:
        print(f"ingestion refused\n  {error}", file=sys.stderr)
        return 1

    RELEASES.mkdir(parents=True, exist_ok=True)
    output = RELEASES / f"{release['baselineKey']}.json"
    output.write_text(json.dumps(release, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    summary = release["summary"]
    print(f"catalogue draft {release['baselineKey']}")
    print(f"  modules              {summary['moduleCount']}")
    print(f"  applications         {summary['applicationCount']}")
    print(f"  with install hooks   {summary['withHooks']}")
    print(f"  external deps        {summary['withExternalDependencies']}")
    print(f"  unparseable          {len(summary['unparseable'])}")
    print(f"  missing dependencies {len(summary['missingDependencies'])}")
    print(f"  dependency cycles    {len(summary['dependencyCycles'])}")
    print(f"  digest               {release['contentDigest'][:23]}…")
    print(f"\nwritten to {output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
