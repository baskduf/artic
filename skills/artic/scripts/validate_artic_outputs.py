#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from pathlib import Path

from validate_artic_strategy import validate_root as validate_strategy_root

REQUIRED_FILES = [
    ".artic/brief.json", ".artic/intent.json", ".artic/references.json", ".artic/strategy.json", ".artic/state.json",
    "docs/artic-brief.md", "DESIGN.md", "docs/artic-strategy.md", "docs/design-rules.md",
    "docs/design-qa-checklist.md", "docs/homepage-design-prompt.md",
]
REQUIRED_DESIGN_SECTIONS = [
    "## Overview", "## Design North Star", "## Colors", "## Typography", "## Layout", "## Page Composition",
    "## Visual Hierarchy", "## Responsive Behavior", "## Elevation & Depth", "## Shapes",
    "## Components", "## Motion", "## Accessibility", "## Anti-Patterns", "## Do's and Don'ts",
]
REQUIRED_COLOR_TOKENS = ("primary", "secondary", "accent", "surface", "neutral", "text", "muted", "border")
REQUIRED_TYPE_TOKENS = ("h1", "h2", "h3", "body-md", "caption")
REQUIRED_SPACING_TOKENS = ("xs", "sm", "md", "lg", "xl", "section")
REQUIRED_COMPONENT_TOKENS = ("button-primary", "button-secondary", "card", "form-field", "proof-strip")
REQUIRED_QA_TERMS = ("Visual hierarchy", "Brand coherence", "Conversion clarity", "Mobile quality", "Accessibility", "Reference safety")
RISK_SECTIONS_EN = (
    "Risk / Readiness Summary",
    "Core quality requirements",
    "Known missing information",
    "Safe assumptions",
    "Unsafe assumptions",
    "Placeholder/fallback boundary",
    "Implementation stop conditions",
    "Completion/acceptance criteria",
)
RISK_SECTIONS_KO = (
    "위험/준비 상태 요약",
    "핵심 품질 요구사항",
    "알려진 누락 정보",
    "안전한 가정",
    "위험한 가정",
    "플레이스홀더/대체 경계",
    "구현 중단 조건",
    "완료/수용 기준",
)
RISK_DOCS = ("DESIGN.md", "docs/artic-strategy.md", "docs/design-rules.md", "docs/design-qa-checklist.md", "docs/homepage-design-prompt.md")
POLICY_FRAGMENT = "extract reusable principles only"
POLICY_MARKER = "<!-- artic-policy: reference-safety-v1 -->"
LANGUAGE_MARKER_PREFIX = "<!-- artic-language:"


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
    brief_locale = "en-US"
    declared_risk_readiness = False
    risk_implementation_blocked = False
    for rel in REQUIRED_FILES:
        if not (root / rel).exists():
            errors.append(f"ERROR: missing required file: {rel}")

    errors.extend(validate_strategy_root(root))

    strategy_doc_path = root / "docs" / "artic-strategy.md"
    if strategy_doc_path.exists():
        strategy_doc = strategy_doc_path.read_text(encoding="utf-8")
        for required in ("## Design North Star", "## Reference Roles", "## Conflict Resolution", "## Implementation Guidance"):
            if required not in strategy_doc:
                errors.append(f"ERROR: docs/artic-strategy.md missing section: {required}")
        if not has_reference_safety(strategy_doc):
            errors.append("ERROR: docs/artic-strategy.md missing reference safety phrase")

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
                brief_locale = str(language.get("locale") or "")
                if not brief_locale:
                    errors.append("ERROR: brief language.locale is required")
                if not str(language.get("output_language") or ""):
                    errors.append("ERROR: brief language.output_language is required")
                preserve_terms = language.get("preserve_terms", [])
                if isinstance(preserve_terms, list):
                    for term in ("DESIGN.md", "Artic"):
                        if term not in preserve_terms:
                            errors.append(f"ERROR: brief language.preserve_terms missing required term: {term}")
            elif "language" in brief:
                errors.append("ERROR: brief language must be an object")
            facets = brief.get("style", {}).get("search_facets", [])
            if brief.get("style") and (not isinstance(facets, list) or len(facets) < 3):
                errors.append("ERROR: brief style.search_facets must include at least 3 normalized facets")
            style = brief.get("style", {})
            if isinstance(style, dict) and not style.get("design_north_star"):
                errors.append("ERROR: brief style.design_north_star is required for LLM-first Artic output")
            risk_readiness = brief.get("risk_readiness")
            risk_implementation_blocked = False
            if isinstance(risk_readiness, dict) and risk_readiness:
                declared_risk_readiness = True
                readiness = risk_readiness.get("readiness")
                risk_implementation_blocked = (
                    bool(risk_readiness.get("implementation_blocked"))
                    or risk_readiness.get("ready_for_implementation") is False
                    or (isinstance(readiness, dict) and str(readiness.get("implementation") or "").lower() == "blocked")
                )
            elif "risk_readiness" in brief and risk_readiness not in ({}, None):
                errors.append("ERROR: brief risk_readiness must be an object when provided")

    intent_path = root / ".artic" / "intent.json"
    if intent_path.exists():
        try:
            intent = json.loads(intent_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"ERROR: invalid .artic/intent.json: {exc}")
        else:
            for key in ("mapper", "design_north_star", "reference_roles", "design_rules", "catalog_query"):
                if key not in intent:
                    errors.append(f"ERROR: intent missing key: {key}")
            roles = intent.get("reference_roles", [])
            if not isinstance(roles, list) or len(roles) < 1:
                errors.append("ERROR: intent reference_roles must include at least 1 role assignment")
            for role in roles if isinstance(roles, list) else []:
                for key in ("role", "source_ids", "selection_reason"):
                    if key not in role:
                        errors.append(f"ERROR: intent reference role missing key: {key}")

    references_path = root / ".artic" / "references.json"
    if references_path.exists():
        try:
            references = json.loads(references_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"ERROR: invalid .artic/references.json: {exc}")
        else:
            selected = references.get("selected_sources", [])
            if not isinstance(selected, list) or len(selected) < 1:
                errors.append("ERROR: references selected_sources must include at least 1 candidate")
            selected_ids = {str(row.get("id")) for row in selected if isinstance(row, dict) and row.get("id")}
            for row in selected:
                for key in ("id", "reason"):
                    if key not in row:
                        errors.append(f"ERROR: reference candidate missing key: {key}")
            source_plan = references.get("source_plan", [])
            if not isinstance(source_plan, list) or len(source_plan) < 1:
                errors.append("ERROR: references source_plan must include at least 1 source plan")
            planned_ids = {str(row.get("source_id")) for row in source_plan if isinstance(row, dict) and row.get("source_id")}
            for row in source_plan if isinstance(source_plan, list) else []:
                for key in ("source_id", "role", "extract", "transform", "avoid"):
                    if key not in row:
                        errors.append(f"ERROR: source plan missing key: {key}")
                source_id = str(row.get("source_id"))
                if selected_ids and source_id not in selected_ids:
                    errors.append(f"ERROR: source plan references unselected source: {source_id}")
            role_assignments = references.get("role_assignments", [])
            if not isinstance(role_assignments, list):
                errors.append("ERROR: references role_assignments must be a list")
                role_assignments = []
            for role in role_assignments:
                if not isinstance(role, dict):
                    errors.append("ERROR: role assignment must be an object")
                    continue
                selected_source_ids = role.get("selected_source_ids", [])
                if not isinstance(selected_source_ids, list):
                    errors.append("ERROR: role assignment selected_source_ids must be a list")
                    selected_source_ids = []
                for source_id in selected_source_ids:
                    if selected_ids and source_id not in selected_ids:
                        errors.append(f"ERROR: role assignment references unselected source: {source_id}")
                    if planned_ids and source_id not in planned_ids:
                        errors.append(f"ERROR: role assignment missing source plan: {source_id}")

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
        if design.count(POLICY_MARKER) > 1:
            errors.append("ERROR: DESIGN.md has duplicate reference safety policy markers")
        if brief_locale and brief_locale != "en-US" and f"<!-- artic-language: {brief_locale} -->" not in design:
            errors.append(f"ERROR: localized outputs missing language marker: {brief_locale} in DESIGN.md")

    combined_docs = ""
    for rel in ("docs/artic-strategy.md", "docs/design-rules.md", "docs/design-qa-checklist.md", "docs/homepage-design-prompt.md"):
        path = root / rel
        if path.exists():
            text = path.read_text(encoding="utf-8")
            combined_docs += "\n" + text
            if not has_reference_safety(text):
                errors.append(f"ERROR: {rel} missing reference safety phrase")
            if brief_locale and brief_locale != "en-US" and f"<!-- artic-language: {brief_locale} -->" not in text:
                errors.append(f"ERROR: localized outputs missing language marker: {brief_locale} in {rel}")
    if declared_risk_readiness:
        required_risk_sections = RISK_SECTIONS_KO if brief_locale.startswith("ko") else RISK_SECTIONS_EN
        for rel in RISK_DOCS:
            path = root / rel
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8")
            for section in required_risk_sections:
                if section not in text:
                    errors.append(f"ERROR: {rel} missing risk_readiness section: {section}")
            if risk_implementation_blocked:
                blocked_terms = [
                    "implementation is blocked until missing inputs are resolved",
                    "누락된 정보가 해결될 때까지 구현은 차단됩니다",
                ]
                if not any(term in text for term in blocked_terms):
                    errors.append(f"ERROR: {rel} missing risk_readiness implementation block notice")
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
