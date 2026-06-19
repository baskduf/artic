#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from pathlib import Path

REQUIRED_FILES = [
    ".artic/brief.json", ".artic/references.json", ".artic/state.json",
    "docs/artic-brief.md", "DESIGN.md", "docs/design-rules.md",
    "docs/design-qa-checklist.md", "docs/homepage-design-prompt.md",
]
REQUIRED_DESIGN_SECTIONS = [
    "## Overview", "## Colors", "## Typography", "## Layout", "## Page Composition",
    "## Visual Hierarchy", "## Responsive Behavior", "## Elevation & Depth", "## Shapes",
    "## Components", "## Motion", "## Accessibility", "## Anti-Patterns", "## Do's and Don'ts",
]
REQUIRED_COLOR_TOKENS = ("primary", "secondary", "accent", "surface", "neutral", "text", "muted", "border")
REQUIRED_TYPE_TOKENS = ("h1", "h2", "h3", "body-md", "caption")
REQUIRED_SPACING_TOKENS = ("xs", "sm", "md", "lg", "xl", "section")
REQUIRED_COMPONENT_TOKENS = ("button-primary", "button-secondary", "card", "form-field", "proof-strip")
REQUIRED_QA_TERMS = ("Visual hierarchy", "Brand coherence", "Conversion clarity", "Mobile quality", "Accessibility", "Reference safety")
POLICY_FRAGMENT = "extract reusable principles only"
POLICY_MARKER = "<!-- artic-policy: reference-safety-v1 -->"


def has_reference_safety(text: str) -> bool:
    return POLICY_MARKER in text or POLICY_FRAGMENT in text


def frontmatter_and_body(design: str) -> tuple[str, str | None]:
    if not design.startswith("---\n"):
        return "", None
    closing = design.find("\n---\n", 4)
    if closing < 0:
        return "", None
    return design[4:closing], design[closing + 5:]


def has_yaml_key(frontmatter: str, key: str) -> bool:
    return re.search(rf"^\s*{re.escape(key)}\s*:", frontmatter, re.MULTILINE) is not None


def yaml_section(frontmatter: str, section: str) -> str:
    lines = frontmatter.splitlines()
    collected: list[str] = []
    in_section = False
    for line in lines:
        if re.match(rf"^{re.escape(section)}\s*:", line):
            in_section = True
            collected.append(line.split(":", 1)[1])
            continue
        if in_section:
            if line and not line.startswith(" "):
                break
            collected.append(line)
    return "\n".join(collected)


def section_has_token(frontmatter: str, section: str, token: str) -> bool:
    section_text = yaml_section(frontmatter, section)
    if not section_text.strip():
        return False
    return re.search(rf"(?:^|[{{,\s]){re.escape(token)}\s*:", section_text, re.MULTILINE) is not None


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
            for key in ("artic_version", "project", "style", "references", "implementation", "language", "copy_policy"):
                if key not in brief:
                    errors.append(f"ERROR: brief missing key: {key}")
            policy_value = str(brief.get("copy_policy", ""))
            if "reference-safety-v1" not in policy_value and POLICY_FRAGMENT not in policy_value:
                errors.append("ERROR: brief copy_policy does not include reference safety phrase")
            language = brief.get("language")
            if isinstance(language, dict):
                for key in ("locale", "output_language", "tone", "preserve_terms", "bilingual_terms"):
                    if key not in language:
                        errors.append(f"ERROR: brief language missing key: {key}")
            elif "language" in brief:
                errors.append("ERROR: brief language must be an object")
            facets = brief.get("style", {}).get("search_facets", [])
            if brief.get("style") and (not isinstance(facets, list) or len(facets) < 3):
                errors.append("ERROR: brief style.search_facets must include at least 3 normalized facets")

    references_path = root / ".artic" / "references.json"
    if references_path.exists():
        try:
            references = json.loads(references_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"ERROR: invalid .artic/references.json: {exc}")
        else:
            selected = references.get("selected_sources", [])
            if not isinstance(selected, list) or len(selected) < 3:
                errors.append("ERROR: references selected_sources must include at least 3 candidates")
            for row in selected:
                for key in ("id", "reason"):
                    if key not in row:
                        errors.append(f"ERROR: reference candidate missing key: {key}")

    design_path = root / "DESIGN.md"
    if design_path.exists():
        design = design_path.read_text(encoding="utf-8")
        if not design.startswith("---\n"):
            errors.append("ERROR: DESIGN.md must start with YAML front matter")
            frontmatter, body = "", None
        else:
            frontmatter, body = frontmatter_and_body(design)
            if body is None:
                errors.append("ERROR: DESIGN.md YAML front matter must have a closing delimiter")
            else:
                for required in ("version", "name", "description", "colors", "typography", "components"):
                    if not has_yaml_key(frontmatter, required):
                        errors.append(f"ERROR: DESIGN.md front matter missing key: {required}")
                for token in REQUIRED_COLOR_TOKENS:
                    if not section_has_token(frontmatter, "colors", token):
                        errors.append(f"ERROR: colors missing quality token: {token}")
                for token in REQUIRED_TYPE_TOKENS:
                    if not section_has_token(frontmatter, "typography", token):
                        errors.append(f"ERROR: typography missing quality token: {token}")
                for token in REQUIRED_SPACING_TOKENS:
                    if not section_has_token(frontmatter, "spacing", token):
                        errors.append(f"ERROR: spacing missing quality token: {token}")
                for token in REQUIRED_COMPONENT_TOKENS:
                    if not section_has_token(frontmatter, "components", token):
                        errors.append(f"ERROR: components missing quality token: {token}")
        last_index = -1
        for section in REQUIRED_DESIGN_SECTIONS:
            idx = design.find(section)
            if idx < 0:
                errors.append(f"ERROR: DESIGN.md missing section: {section}")
            elif idx < last_index:
                errors.append(f"ERROR: DESIGN.md section out of order: {section}")
            last_index = max(last_index, idx)
        if not has_reference_safety(design):
            errors.append("ERROR: DESIGN.md missing reference safety phrase")

    combined_docs = ""
    for rel in ("docs/design-rules.md", "docs/design-qa-checklist.md", "docs/homepage-design-prompt.md"):
        path = root / rel
        if path.exists():
            text = path.read_text(encoding="utf-8")
            combined_docs += "\n" + text
            if not has_reference_safety(text):
                errors.append(f"ERROR: {rel} missing reference safety phrase")
    checklist = root / "docs" / "design-qa-checklist.md"
    if checklist.exists():
        text = checklist.read_text(encoding="utf-8")
        for term in REQUIRED_QA_TERMS:
            if term not in text:
                errors.append(f"ERROR: docs/design-qa-checklist.md missing scoring term: {term}")
    if combined_docs and not has_reference_safety(combined_docs):
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
