#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

POLICY = "Reference policy: extract reusable principles only; do not copy logos, trademarks, proprietary illustrations, or exact layouts."
POLICY_MARKER = "<!-- artic-policy: reference-safety-v1 -->"
POLICY_COPY_BY_LOCALE = {
    "en-US": POLICY,
    "ko-KR": "참고 정책: 재사용 가능한 원칙만 추출하고, 로고, 상표, 독점 일러스트, 정확한 레이아웃은 복사하지 않습니다.",
    "ja-JP": "参照ポリシー: 再利用可能な原則のみを抽出し、ロゴ、商標、独自イラスト、正確なレイアウトはコピーしません。",
    "zh-CN": "参考政策：仅提取可复用原则，不复制标志、商标、专有插画或精确布局。",
    "zh-TW": "參考政策：僅萃取可重用原則，不複製標誌、商標、專有插圖或精確版面。",
}
GENERATED_FILES = [
    "DESIGN.md",
    "docs/design-rules.md",
    "docs/design-qa-checklist.md",
    "docs/homepage-design-prompt.md",
]


def read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"missing required input: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object in {path}")
    return payload


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def template_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "templates"


def load_template(name: str) -> str:
    return (template_dir() / name).read_text(encoding="utf-8")


def yaml_double_quoted(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")


def project_name(brief: dict[str, Any]) -> str:
    project = brief.get("project")
    if isinstance(project, dict):
        name = str(project.get("name") or project.get("description") or "Artic Project").strip()
        return name or "Artic Project"
    return "Artic Project"


def project_description(brief: dict[str, Any]) -> str:
    project = brief.get("project")
    if isinstance(project, dict):
        return str(project.get("description") or project.get("primary_goal") or "Project-specific Artic homepage design system.").strip()
    return "Project-specific Artic homepage design system."


def brief_language(brief: dict[str, Any]) -> dict[str, Any]:
    language = brief.get("language")
    return language if isinstance(language, dict) else {"locale": "en-US", "output_language": "English"}


def policy_block(brief: dict[str, Any]) -> str:
    locale = str(brief_language(brief).get("locale") or "en-US")
    return f"{POLICY_MARKER}\n{POLICY_COPY_BY_LOCALE.get(locale, POLICY)}"


def language_block(brief: dict[str, Any]) -> str:
    language = brief_language(brief)
    locale = str(language.get("locale") or "en-US")
    preserve_terms = language.get("preserve_terms", [])
    preserve = ", ".join(str(item) for item in preserve_terms) if isinstance(preserve_terms, list) else str(preserve_terms or "")
    return "\n".join([
        f"<!-- artic-language: {locale} -->",
        "## Language Contract",
        "",
        f"- Locale: {locale}",
        f"- Output language: {language.get('output_language', 'English')}",
        f"- Tone: {language.get('tone', 'clear, professional, product-focused')}",
        f"- Preserve terms: {preserve or 'DESIGN.md, AI-native, Artic'}",
        f"- Bilingual terms: {bool(language.get('bilingual_terms', False))}",
    ])


def query_from_inputs(brief: dict[str, Any], references: dict[str, Any]) -> str:
    if references.get("query"):
        return str(references["query"])
    project_obj = brief.get("project")
    style_obj = brief.get("style")
    implementation_obj = brief.get("implementation")
    project = project_obj if isinstance(project_obj, dict) else {}
    style = style_obj if isinstance(style_obj, dict) else {}
    implementation = implementation_obj if isinstance(implementation_obj, dict) else {}
    parts: list[str] = [
        str(project.get("name", "")),
        " ".join(str(item) for item in project.get("target_users", []) if item),
        str(project.get("primary_goal", "")),
        " ".join(str(item) for item in style.get("desired_impression", []) if item),
        " ".join(str(item) for item in style.get("search_facets", []) if item),
        " ".join(str(item) for item in brief.get("references", []) if item),
        str(implementation.get("stack", "")),
    ]
    return " ".join(part for part in parts if part).strip() or project_name(brief)


def selected_reference_lines(references: dict[str, Any]) -> list[str]:
    selected = references.get("selected_sources", [])
    if not isinstance(selected, list):
        return []
    lines = []
    for row in selected:
        if not isinstance(row, dict):
            continue
        name = row.get("name") or row.get("id") or "reference source"
        source_id = row.get("id") or "unknown"
        reason = row.get("reason") or row.get("application_guidance") or "selected for reusable design patterns"
        targets = row.get("extraction_targets", [])
        target_text = ", ".join(str(item) for item in targets) if isinstance(targets, list) else str(targets or "")
        suffix = f" Extract: {target_text}." if target_text else ""
        lines.append(f"- {name} (`{source_id}`): {reason}.{suffix}")
    return lines


def source_plan_lines(references: dict[str, Any]) -> list[str]:
    plan = references.get("source_plan", [])
    if not isinstance(plan, list):
        return []
    lines: list[str] = []
    for row in plan:
        if not isinstance(row, dict):
            continue
        source_id = row.get("source_id") or "unknown-source"
        role = row.get("role") or "supporting_reference"
        extract = row.get("extract", [])
        avoid = row.get("avoid", [])
        extract_text = ", ".join(str(item) for item in extract) if isinstance(extract, list) else str(extract or "")
        avoid_text = ", ".join(str(item) for item in avoid) if isinstance(avoid, list) else str(avoid or "")
        transform = row.get("transform") or "Transform this source into original, project-specific design rules."
        lines.append(f"- `{source_id}` as **{role}**. Extract: {extract_text}. Transform: {transform} Avoid: {avoid_text}.")
    return lines


def synthesize_reference_summary(brief: dict[str, Any], references: dict[str, Any]) -> str:
    query = query_from_inputs(brief, references)
    reference_lines = selected_reference_lines(references)
    if reference_lines:
        init_synthesis = str(references.get("synthesis") or "").strip()
        lines = ["# Reference Synthesis", "", "## Selected Sources", "", *reference_lines]
        lines += ["", "## Extracted Compatible Patterns", ""]
        if init_synthesis:
            lines.append(init_synthesis)
        lines.extend(
            [
                "- Convert the initialized sources into original token roles, component rules, layout rhythm, accessibility guardrails, and conversion hierarchy.",
                "- Preserve the selected reference set from `@artic init`; do not swap in unrelated sources during `@artic start`.",
                "",
                "## Source Application Plan",
                "",
                *(source_plan_lines(references) or ["- Treat each selected source as a role-bound reference, not a visual clone target."]),
                "",
                "## Conflicts Resolved",
                "",
                "- Prefer project-specific token roles over any single reference brand identity.",
                "- Keep the primary conversion path visually dominant while secondary actions remain quieter.",
                "- Use component/accessibility discipline from the selected systems without copying exact page compositions.",
                "",
                "## Final Direction",
                "",
                f"Use the initialized Artic reference selection as compatible source patterns for `{query}`. Generate project-specific tokens, components, page composition, QA scoring, and implementation guidance from these reusable principles only.",
                "",
                "## Forbidden Copy Elements",
                "",
                "- Do not copy logos, trademarks, proprietary illustrations, exact page compositions, exact palettes as identity, or source copywriting.",
                "- Treat brand-inspired examples as pattern references, not clone targets.",
            ]
        )
        return "\n".join(lines)

    try:
        from synthesize_reference_notes import make_synthesis

        markdown, _payload = make_synthesis(
            query,
            Path(__file__).resolve().parents[1] / "references" / "source-catalog.json",
            Path(__file__).resolve().parents[1] / "references" / "fixtures",
            3,
        )
        return markdown
    except Exception:
        pass

    lines = [
        "Use the initialized Artic references as compatible reusable patterns for this project.",
        "Resolve conflicts in favor of the project goal, target users, accessibility target, and original brand expression.",
    ]
    init_synthesis = str(references.get("synthesis") or "").strip()
    if init_synthesis:
        lines.append(init_synthesis)
    if reference_lines:
        lines.extend(["", "Selected references:", *reference_lines])
    return "\n".join(lines)


def overview(brief: dict[str, Any], references: dict[str, Any]) -> str:
    project_obj = brief.get("project")
    style_obj = brief.get("style")
    implementation_obj = brief.get("implementation")
    project = project_obj if isinstance(project_obj, dict) else {}
    style = style_obj if isinstance(style_obj, dict) else {}
    implementation = implementation_obj if isinstance(implementation_obj, dict) else {}
    audience = ", ".join(str(item) for item in project.get("target_users", []) if item) or "the target audience"
    goal = str(project.get("primary_goal") or "the primary conversion goal")
    impressions = ", ".join(str(item) for item in style.get("desired_impression", []) if item) or "clear, trustworthy, modern"
    stack = str(implementation.get("stack") or "unspecified stack")
    ref_count = len(references.get("selected_sources", [])) if isinstance(references.get("selected_sources"), list) else 0
    return (
        f"{project_name(brief)} is a homepage direction for {audience}. "
        f"The page should drive {goal} with a {impressions} impression, implemented in {stack}. "
        f"The system below turns {ref_count or 'the selected'} Artic reference sources into original tokens, components, layout rules, and QA guardrails."
    )


def replace_policy_text(text: str, block: str) -> str:
    if f"{POLICY_MARKER}\n{POLICY}" in text:
        return text.replace(f"{POLICY_MARKER}\n{POLICY}", block)
    return text.replace(POLICY, block)


def render_outputs(root: Path, brief: dict[str, Any], references: dict[str, Any], intent: dict[str, Any] | None = None) -> list[str]:
    name = project_name(brief)
    description = f"{project_description(brief)} Artic-generated homepage design system."
    ref_summary = synthesize_reference_summary(brief, references)
    policy = policy_block(brief)
    language = language_block(brief)

    design = load_template("DESIGN.template.md")
    design = design.replace("{{PROJECT_NAME}}", yaml_double_quoted(name))
    design = design.replace("{{DESIGN_DESCRIPTION}}", yaml_double_quoted(description))
    design = design.replace("{{OVERVIEW}}", f"{overview(brief, references)}\n\n{language}")
    north_star = str((intent or {}).get("design_north_star") or brief.get("style", {}).get("design_north_star") or "Every visual choice should support the project's primary conversion goal with original, reference-grounded design judgment.")
    design = design.replace("{{DESIGN_NORTH_STAR}}", north_star)
    design = replace_policy_text(design, policy)
    write(root / "DESIGN.md", design)

    rules = load_template("design-rules.template.md")
    rules = rules.replace("{{PROJECT_NAME}}", name)
    rules = rules.replace("{{REFERENCE_SYNTHESIS}}", f"{language}\n\n{ref_summary}")
    rules = replace_policy_text(rules, policy)
    write(root / "docs" / "design-rules.md", rules)

    checklist = load_template("design-qa-checklist.template.md")
    checklist = checklist.replace("# Artic Design QA Checklist\n", f"# Artic Design QA Checklist\n\n{language}\n")
    checklist = replace_policy_text(checklist, policy)
    if "Accessibility" not in checklist:
        checklist = checklist.replace("- [ ] Text contrast targets WCAG AA.", "- [ ] Accessibility: text contrast targets WCAG AA, focus states are visible, controls are semantic, and forms are labeled.")
    write(root / "docs" / "design-qa-checklist.md", checklist)

    prompt = load_template("homepage-design-prompt.template.md")
    prompt = prompt.replace("{{PROJECT_NAME}}", name)
    prompt = prompt.replace("# Homepage Implementation Prompt\n", f"# Homepage Implementation Prompt\n\n{language}\n")
    prompt = replace_policy_text(prompt, policy)
    write(root / "docs" / "homepage-design-prompt.md", prompt)

    update_state(root, brief)
    return GENERATED_FILES


def migrate_legacy_intent(root: Path, brief: dict[str, Any], references: dict[str, Any]) -> dict[str, Any]:
    raw_style = brief.get("style")
    raw_project = brief.get("project")
    style: dict[str, Any] = raw_style if isinstance(raw_style, dict) else {}
    project: dict[str, Any] = raw_project if isinstance(raw_project, dict) else {}
    selected_sources = references.get("selected_sources", []) if isinstance(references.get("selected_sources"), list) else []
    role_sources = [str(row.get("id")) for row in selected_sources if isinstance(row, dict) and row.get("id")]
    search_facets = list(style.get("search_facets", [])) if isinstance(style.get("search_facets"), list) else ["homepage", "trust", "clean-saas"]
    north_star = str(style.get("design_north_star") or f"{project_name(brief)} should use reference-grounded design judgment while keeping layout, copy, and visual identity original.")
    intent = {
        "schema_version": 1,
        "mapper": "artic-llm-first-contract-legacy-migration",
        "selected_preset": style.get("selected_preset") or "clean-saas",
        "project_archetype": "legacy-homepage",
        "audience_context": ", ".join(str(item) for item in project.get("target_users", []) if item),
        "conversion_goal": str(project.get("primary_goal") or "primary conversion goal"),
        "emotional_target": list(style.get("desired_impression", [])) if isinstance(style.get("desired_impression"), list) else [],
        "style_facets": search_facets,
        "search_facets": search_facets,
        "avoid_facets": [],
        "design_principles": [],
        "design_rules": style.get("design_rules") if isinstance(style.get("design_rules"), dict) else {},
        "design_north_star": north_star,
        "reference_roles": [
            {
                "role": f"legacy_reference_{index + 1}",
                "source_ids": [source_id],
                "selection_reason": "Migrated from pre-LLM-first selected_sources.",
            }
            for index, source_id in enumerate(role_sources)
        ],
        "reference_hints": [],
        "catalog_query": str(references.get("query") or " ".join(search_facets)),
        "llm_contract": {
            "role": "Migrated legacy intent; future runs should regenerate this with the LLM-first mapper.",
            "must_preserve": ["design_north_star", "reference_roles", "catalog_query"],
            "must_not": ["copy protected brand assets", "choose exact layouts as clone targets"],
        },
    }
    write(root / ".artic" / "intent.json", json.dumps(intent, indent=2, ensure_ascii=False) + "\n")
    return intent


def update_state(root: Path, brief: dict[str, Any]) -> None:
    state_path = root / ".artic" / "state.json"
    state: dict[str, Any] = {}
    if state_path.exists():
        try:
            loaded = json.loads(state_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                state = loaded
        except json.JSONDecodeError:
            state = {}
    state.update(
        {
            "artic_version": str(brief.get("artic_version") or state.get("artic_version") or "0.1.1"),
            "last_generated_at": datetime.now(timezone.utc).isoformat(),
            "status": "generated",
            "language": brief_language(brief),
        }
    )
    write(state_path, json.dumps(state, indent=2, ensure_ascii=False) + "\n")


def validate_outputs(root: Path) -> subprocess.CompletedProcess[str]:
    validator = Path(__file__).resolve().with_name("validate_artic_outputs.py")
    return subprocess.run(
        [sys.executable, str(validator), "--root", str(root)],
        check=False,
        capture_output=True,
        text=True,
    )


def create_start_outputs(root: Path, *, no_validate: bool = False) -> dict[str, Any]:
    session_path = root / ".artic" / "init-session.json"
    brief_path = root / ".artic" / "brief.json"
    references_path = root / ".artic" / "references.json"
    if session_path.exists() and (not brief_path.exists() or not references_path.exists()):
        from artic_init_session import finalize_session, is_ready, read_session, render_questions

        session = read_session(root)
        if not is_ready(session):
            questions = render_questions(session)
            raise ValueError("init session is still collecting; answer missing fields before @artic start: " + "; ".join(questions))
        finalize_session(root)
    brief = read_json(root / ".artic" / "brief.json")
    references = read_json(root / ".artic" / "references.json")
    intent = read_json(root / ".artic" / "intent.json") if (root / ".artic" / "intent.json").exists() else migrate_legacy_intent(root, brief, references)
    generated = render_outputs(root, brief, references, intent)
    payload: dict[str, Any] = {
        "root": str(root.resolve()),
        "generated_files": generated,
        "validated": False,
    }
    if not no_validate:
        validation = validate_outputs(root)
        payload["validated"] = validation.returncode == 0
        payload["validation_stdout"] = validation.stdout.strip()
        payload["validation_stderr"] = validation.stderr.strip()
        if validation.returncode != 0:
            raise RuntimeError(json.dumps(payload, indent=2, ensure_ascii=False))
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Artic DESIGN.md and design docs from .artic init outputs.")
    parser.add_argument("--root", required=True, help="Project root containing .artic/brief.json and .artic/references.json")
    parser.add_argument("--no-validate", action="store_true", help="Generate files without running validate_artic_outputs.py")
    args = parser.parse_args()
    try:
        payload = create_start_outputs(Path(args.root), no_validate=args.no_validate)
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 1
    except RuntimeError as exc:
        print(str(exc))
        return 1
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
