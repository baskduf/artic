#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import tarfile
import zipfile
from pathlib import Path

FORBIDDEN_PARTS = {"__pycache__"}
FORBIDDEN_SUFFIXES = (".pyc", ".pyo", ".pyd")
REQUIRED_PLUGIN_FILES = [
    "skills/artic/SKILL.md",
    "skills/artic/references/source-catalog.json",
    "skills/artic/scripts/artic_init.py",
    "skills/artic/scripts/artic_version.py",
    "skills/artic/scripts/artic_update.py",
    "skills/artic/scripts/search_reference_catalog.py",
    "skills/artic/scripts/synthesize_reference_notes.py",
    "skills/artic/scripts/validate_artic_outputs.py",
    "plugins/claude-artic/.claude-plugin/plugin.json",
    "plugins/codex-artic/.codex-plugin/plugin.json",
]


def archive_names(path: Path) -> list[str]:
    if path.suffix == ".whl" or path.suffix == ".zip":
        with zipfile.ZipFile(path) as zf:
            return zf.namelist()
    if path.name.endswith(".tar.gz") or path.suffix in {".tgz", ".tar"}:
        with tarfile.open(path) as tf:
            return tf.getnames()
    raise ValueError(f"unsupported archive type: {path}")


def normalize(name: str) -> str:
    parts = name.split("/")
    if parts and parts[0].startswith("artic-"):
        parts = parts[1:]
    return "/".join(parts)


def forbidden_entries(names: list[str]) -> list[str]:
    bad: list[str] = []
    for name in names:
        parts = set(name.split("/"))
        if parts & FORBIDDEN_PARTS or name.endswith(FORBIDDEN_SUFFIXES):
            bad.append(name)
    return bad


def require_payload(names: list[str], archive: Path) -> list[str]:
    normalized = {normalize(name) for name in names}
    missing = [required for required in REQUIRED_PLUGIN_FILES if required not in normalized]
    if missing:
        return [f"{archive}: missing required payload {item}" for item in missing]
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Artic release archives for marketplace readiness.")
    parser.add_argument("archives", nargs="+", help="Archive paths to inspect")
    parser.add_argument("--require-payload", action="store_true", help="Require skill/plugin payload files")
    args = parser.parse_args()

    findings: list[str] = []
    for raw in args.archives:
        archive = Path(raw)
        if not archive.exists() or archive.stat().st_size == 0:
            findings.append(f"{archive}: missing or empty")
            continue
        try:
            names = archive_names(archive)
        except Exception as exc:  # noqa: BLE001 - CLI validator should report all archive failures plainly.
            findings.append(f"{archive}: cannot inspect archive: {exc}")
            continue
        bad = forbidden_entries(names)
        findings.extend(f"{archive}: forbidden bytecode/cache entry {name}" for name in bad)
        if args.require_payload:
            findings.extend(require_payload(names, archive))

    if findings:
        print("\n".join(findings))
        return 1
    print(f"Validated {len(args.archives)} archive(s): no bytecode/cache entries found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
