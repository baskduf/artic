#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

REQUIRED_FILES = [
    ".artic/brief.json", ".artic/references.json", ".artic/state.json",
    "docs/artic-brief.md", "DESIGN.md", "docs/design-rules.md",
    "docs/design-qa-checklist.md", "docs/homepage-design-prompt.md",
]
REQUIRED_DESIGN_SECTIONS = [
    "## Overview", "## Colors", "## Typography", "## Layout",
    "## Elevation & Depth", "## Shapes", "## Components", "## Do's and Don'ts",
]
POLICY_FRAGMENT = "extract reusable principles only"

def validate(root: Path) -> list[str]:
    errors: list[str] = []
    for rel in REQUIRED_FILES:
        if not (root / rel).exists():
            errors.append(f"ERROR: missing required file: {rel}")

    brief_path = root / ".artic" / "brief.json"
    if brief_path.exists():
        try:
            brief = json.loads(brief_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"ERROR: invalid .artic/brief.json: {exc}")
        else:
            for key in ("artic_version", "project", "style", "references", "implementation", "copy_policy"):
                if key not in brief:
                    errors.append(f"ERROR: brief missing key: {key}")
            if POLICY_FRAGMENT not in str(brief.get("copy_policy", "")):
                errors.append("ERROR: brief copy_policy does not include reference safety phrase")

    references_path = root / ".artic" / "references.json"
    if references_path.exists():
        try:
            json.loads(references_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"ERROR: invalid .artic/references.json: {exc}")

    design_path = root / "DESIGN.md"
    if design_path.exists():
        design = design_path.read_text(encoding="utf-8")
        if not design.startswith("---\n"):
            errors.append("ERROR: DESIGN.md must start with YAML front matter")
        last_index = -1
        for section in REQUIRED_DESIGN_SECTIONS:
            idx = design.find(section)
            if idx < 0:
                errors.append(f"ERROR: DESIGN.md missing section: {section}")
            elif idx < last_index:
                errors.append(f"ERROR: DESIGN.md section out of order: {section}")
            last_index = max(last_index, idx)
        if POLICY_FRAGMENT not in design:
            errors.append("ERROR: DESIGN.md missing reference safety phrase")

    combined_docs = ""
    for rel in ("docs/design-rules.md", "docs/design-qa-checklist.md", "docs/homepage-design-prompt.md"):
        path = root / rel
        if path.exists():
            combined_docs += "\n" + path.read_text(encoding="utf-8")
    if combined_docs and POLICY_FRAGMENT not in combined_docs:
        errors.append("ERROR: generated docs missing reference safety phrase")
    return errors

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    args = parser.parse_args()
    errors = validate(Path(args.root))
    if errors:
        print("Artic validation failed:")
        print("\n".join(errors))
        return 1
    print("Artic validation passed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
