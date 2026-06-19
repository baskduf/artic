#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from validate_artic_strategy import read_json as read_strategy_json
from validate_artic_strategy import validate_strategy_payload

POLICY = "Reference policy: extract reusable principles only; do not copy logos, trademarks, proprietary illustrations, or exact layouts."
POLICY_MARKER = "<!-- artic-policy: reference-safety-v1 -->"
POLICY_ID = "artic-policy: reference-safety-v1"
POLICY_COPY_BY_LOCALE = {
    "en-US": POLICY,
    "ko-KR": "참고 정책: 재사용 가능한 원칙만 추출하고, 로고, 상표, 독점 일러스트, 정확한 레이아웃은 복사하지 않습니다.",
    "ja-JP": "参照ポリシー: 再利用可能な原則のみを抽出し、ロゴ、商標、独自イラスト、正確なレイアウトはコピーしません。",
    "zh-CN": "参考政策：仅提取可复用原则，不复制标志、商标、专有插画或精确布局。",
    "zh-TW": "參考政策：僅萃取可重用原則，不複製標誌、商標、專有插圖或精確版面。",
}
GENERATED_FILES = [
    "docs/artic-strategy.md",
    "DESIGN.md",
    "docs/design-rules.md",
    "docs/design-qa-checklist.md",
    "docs/homepage-design-prompt.md",
]
FORBIDDEN_COPY_ELEMENTS = ["logos", "trademarks", "proprietary illustrations", "exact layouts", "source copywriting"]


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


def project_description(brief: dict[str, Any], strategy: dict[str, Any] | None = None) -> str:
    summary = (strategy or {}).get("project_summary")
    if isinstance(summary, str) and summary.strip():
        return summary.strip()
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


def as_markdown(value: Any, *, indent: int = 0) -> str:
    prefix = "  " * indent
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        lines: list[str] = []
        for item in value:
            rendered = as_markdown(item, indent=indent + 1)
            if "\n" in rendered:
                lines.append(f"{prefix}- {rendered.replace(chr(10), chr(10) + prefix + '  ')}")
            else:
                lines.append(f"{prefix}- {rendered}")
        return "\n".join(lines)
    if isinstance(value, dict):
        lines = []
        for key, item in value.items():
            rendered = as_markdown(item, indent=indent + 1)
            if "\n" in rendered:
                lines.append(f"{prefix}- **{key}**:\n{rendered}")
            else:
                lines.append(f"{prefix}- **{key}**: {rendered}")
        return "\n".join(lines)
    return str(value)


RISK_LABELS = {
    "en": {
        "heading": "Risk / Readiness Summary",
        "summary_line": "Risk Summary: risk/quality readiness details follow.",
        "core_quality_requirements": "Core quality requirements",
        "known_missing_information": "Known missing information",
        "safe_assumptions": "Safe assumptions",
        "unsafe_assumptions": "Unsafe assumptions",
        "placeholder_fallback_boundary": "Placeholder/fallback boundary",
        "implementation_stop_conditions": "Implementation stop conditions / Stop Conditions",
        "completion_acceptance_criteria": "Completion/acceptance criteria",
        "status_ready": "Strategy/preview can proceed.",
        "status_blocked": "Strategy/preview can proceed, but implementation is blocked until missing inputs are resolved.",
        "none": "None declared.",
        "check_intent": "requested product photo/3D/map/payment trust intent is satisfied or explicitly blocked",
        "check_placeholder": "placeholder is not accepted as production substitute for quality-critical requirement",
    },
    "ko": {
        "heading": "위험/준비 상태 요약",
        "summary_line": "위험 요약: 리스크와 품질 기준에 따른 준비 상태를 정리합니다.",
        "core_quality_requirements": "핵심 품질 요구사항",
        "known_missing_information": "알려진 누락 정보",
        "safe_assumptions": "안전한 가정",
        "unsafe_assumptions": "위험한 가정",
        "placeholder_fallback_boundary": "플레이스홀더/대체 경계",
        "implementation_stop_conditions": "구현 중단 조건",
        "completion_acceptance_criteria": "완료/수용 기준",
        "status_ready": "전략/프리뷰는 진행할 수 있습니다.",
        "status_blocked": "전략/프리뷰는 진행할 수 있지만, 누락된 정보가 해결될 때까지 구현은 차단됩니다.",
        "none": "명시된 항목 없음.",
        "check_intent": "요청된 제품 사진/3D/지도/결제 신뢰 의도가 충족되었거나 명시적으로 차단됨",
        "check_placeholder": "플레이스홀더는 품질 핵심 요구사항의 프로덕션 대체물로 인정되지 않음",
    },
}


RISK_SECTION_KEYS = [
    "core_quality_requirements",
    "known_missing_information",
    "safe_assumptions",
    "unsafe_assumptions",
    "placeholder_fallback_boundary",
    "implementation_stop_conditions",
    "completion_acceptance_criteria",
]


def risk_readiness(brief: dict[str, Any]) -> dict[str, Any]:
    value = brief.get("risk_readiness")
    return value if isinstance(value, dict) and value else {}


def risk_labels(brief: dict[str, Any]) -> dict[str, str]:
    locale = str(brief_language(brief).get("locale") or "en-US")
    return RISK_LABELS["ko"] if locale.startswith("ko") else RISK_LABELS["en"]


def risk_items(risk: dict[str, Any], key: str) -> list[str]:
    aliases = {
        "core_quality_requirements": ["quality_critical_requirements", "core_requirements"],
        "known_missing_information": ["missing_information", "missing_inputs", "blockers"],
        "placeholder_fallback_boundary": ["placeholder_boundary", "fallback_boundary"],
        "implementation_stop_conditions": ["stop_conditions", "implementation_blockers"],
        "completion_acceptance_criteria": ["acceptance_criteria", "completion_criteria"],
    }
    raw = risk.get(key)
    if raw is None:
        for alias in aliases.get(key, []):
            raw = risk.get(alias)
            if raw is not None:
                break
    if raw is None or raw == "":
        return []
    if isinstance(raw, list):
        items: list[str] = []
        for item in raw:
            rendered = as_markdown(item).strip()
            if rendered:
                items.append(rendered)
        return items
    return [as_markdown(raw).strip()]


def risk_readiness_block(brief: dict[str, Any], *, checklist: bool = False) -> str:
    risk = risk_readiness(brief)
    if not risk:
        return ""
    labels = risk_labels(brief)
    implementation_blocked = bool(risk.get("implementation_blocked")) or risk.get("ready_for_implementation") is False
    readiness = risk.get("readiness")
    if isinstance(readiness, dict) and str(readiness.get("implementation") or "").lower() == "blocked":
        implementation_blocked = True
    lines = [f"## {labels['heading']}", "", f"- {labels['summary_line']}", f"- {labels['status_blocked'] if implementation_blocked else labels['status_ready']}"]
    if "ready_for_strategy" in risk:
        lines.append(f"- ready_for_strategy: {bool(risk.get('ready_for_strategy'))}")
    if "implementation_blocked" in risk:
        lines.append(f"- implementation_blocked: {bool(risk.get('implementation_blocked'))}")
    lines.append("")
    for key in RISK_SECTION_KEYS:
        lines.extend([f"### {labels[key]}", ""])
        items = risk_items(risk, key)
        if items:
            prefix = "- [ ]" if checklist else "-"
            lines.extend(f"{prefix} {item}" for item in items)
        else:
            lines.append(f"- {labels['none']}")
        lines.append("")
    if checklist:
        lines.extend([
            "### Intent-matched QA gates",
            "",
            f"- [ ] {labels['check_intent']}.",
            f"- [ ] {labels['check_placeholder']}.",
            "",
        ])
    return "\n".join(lines).rstrip()


def role_lines(strategy: dict[str, Any]) -> list[str]:
    roles = strategy.get("reference_roles", [])
    lines: list[str] = []
    if not isinstance(roles, list):
        return lines
    for role in roles:
        if not isinstance(role, dict):
            continue
        lines.append(
            "- Reference (`{}`) as **{}** — {} Extract: {} Transform: translate into project-specific rules. Avoid: {}".format(
                role.get("source_id", "unknown"),
                role.get("role", "reference"),
                role.get("why_selected", "selected for reusable principles"),
                as_markdown(role.get("extract", "reusable patterns")),
                as_markdown(role.get("avoid", "protected expression")),
            )
        )
    return lines


def strategy_doc(brief: dict[str, Any], strategy: dict[str, Any]) -> str:
    policy = policy_block(brief)
    risk_block = risk_readiness_block(brief)
    parts = [
        f"# Artic Strategy: {project_name(brief)}",
        "",
        language_block(brief),
        "",
        policy,
        "",
    ]
    if risk_block:
        parts.extend([risk_block, ""])
    parts.extend([
        "## Project Summary",
        "",
        as_markdown(strategy.get("project_summary", "")),
        "",
        "## Design North Star",
        "",
        as_markdown(strategy.get("design_north_star", "")),
        "",
        "## Target User Interpretation",
        "",
        as_markdown(strategy.get("target_user_interpretation", "")),
        "",
        "## Conversion Strategy",
        "",
        as_markdown(strategy.get("conversion_strategy", "")),
        "",
        "## Reference Roles",
        "",
        *(role_lines(strategy) or ["- No reference roles supplied."]),
        "",
        "## Source Application Plan",
        "",
        *(role_lines(strategy) or ["- No reference roles supplied."]),
        "",
        "## Conflict Resolution",
        "",
        as_markdown(strategy.get("conflict_resolution", "")),
        "",
        "## Visual System",
        "",
        as_markdown(strategy.get("visual_system", "")),
        "",
        "## Component Rules",
        "",
        as_markdown(strategy.get("component_rules", "")),
        "",
        "## Accessibility",
        "",
        as_markdown(strategy.get("accessibility", "")),
        "",
        "## Implementation Guidance",
        "",
        as_markdown(strategy.get("implementation_guidance", "")),
        "",
        "## Forbidden Copy Elements",
        "",
        as_markdown(strategy.get("forbidden_copy_elements", FORBIDDEN_COPY_ELEMENTS)),
        "",
    ])
    return "\n".join(parts)


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
    locale = str(brief_language(brief).get("locale") or "en-US")
    if locale.startswith("ko"):
        return (
            f"{project_name(brief)}는 {audience}를 위한 홈페이지 방향입니다. "
            f"이 페이지는 {impressions} 인상으로 {goal}을 이끌어야 하며, 구현 스택은 {stack}입니다. "
            f"아래 시스템은 {ref_count or '선택된'}개의 Artic 레퍼런스 소스를 원본 그대로 복제하지 않고 토큰, 컴포넌트, 레이아웃 규칙, QA 가드레일로 변환합니다."
        )
    return (
        f"{project_name(brief)} is a homepage direction for {audience}. "
        f"The page should drive {goal} with a {impressions} impression, implemented in {stack}. "
        f"The system below turns {ref_count or 'the selected'} Artic reference sources into original tokens, components, layout rules, and QA guardrails."
    )


def replace_policy_text(text: str, block: str) -> str:
    if f"{POLICY_MARKER}\n{POLICY}" in text:
        return text.replace(f"{POLICY_MARKER}\n{POLICY}", block)
    return text.replace(POLICY, block)


def validate_runtime_inputs(intent: dict[str, Any], references: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ("mapper", "design_north_star", "reference_roles", "design_rules", "catalog_query"):
        if key not in intent:
            errors.append(f"ERROR: intent missing key: {key}")
    roles = intent.get("reference_roles", [])
    if not isinstance(roles, list) or len(roles) < 1:
        errors.append("ERROR: intent reference_roles must include at least 1 role assignment")
    for role in roles if isinstance(roles, list) else []:
        if not isinstance(role, dict):
            errors.append("ERROR: intent reference role must be an object")
            continue
        for key in ("role", "source_ids", "selection_reason"):
            if key not in role:
                errors.append(f"ERROR: intent reference role missing key: {key}")

    selected = references.get("selected_sources", [])
    if not isinstance(selected, list) or len(selected) < 1:
        errors.append("ERROR: references selected_sources must include at least 1 candidate")
    source_plan = references.get("source_plan", [])
    if not isinstance(source_plan, list) or len(source_plan) < 1:
        errors.append("ERROR: references source_plan must include at least 1 source plan")
    return errors


def validate_strategy_sources(strategy: dict[str, Any], references: dict[str, Any]) -> list[str]:
    selected = references.get("selected_sources", [])
    if not isinstance(selected, list):
        return ["ERROR: references selected_sources must be a list before validating strategy sources"]
    allowed_ids = {str(row.get("id")) for row in selected if isinstance(row, dict) and row.get("id")}
    if not allowed_ids:
        return ["ERROR: references selected_sources must include source ids before validating strategy sources"]
    errors: list[str] = []
    roles = strategy.get("reference_roles", [])
    for index, role in enumerate(roles if isinstance(roles, list) else [], start=1):
        if not isinstance(role, dict):
            continue
        source_id = str(role.get("source_id") or "").strip()
        if source_id and source_id not in allowed_ids:
            errors.append(f"ERROR: strategy reference_roles[{index}].source_id references unselected source: {source_id}")
    return errors


def render_outputs(root: Path, brief: dict[str, Any], references: dict[str, Any], strategy: dict[str, Any], intent: dict[str, Any] | None = None) -> list[str]:
    name = project_name(brief)
    description = f"{project_description(brief, strategy)} Artic-generated homepage design system."
    policy = policy_block(brief)
    language = language_block(brief)
    risk_block = risk_readiness_block(brief)
    risk_checklist_block = risk_readiness_block(brief, checklist=True)
    strategy_markdown = strategy_doc(brief, strategy)

    design = load_template("DESIGN.template.md")
    design = design.replace("{{PROJECT_NAME}}", yaml_double_quoted(name))
    design = design.replace("{{DESIGN_DESCRIPTION}}", yaml_double_quoted(description))
    overview_text = "\n\n".join([
        overview(brief, references),
        as_markdown(strategy.get("project_summary", "")),
        language,
        "### Target User Interpretation",
        as_markdown(strategy.get("target_user_interpretation", "")),
        "### Conversion Strategy",
        as_markdown(strategy.get("conversion_strategy", "")),
        "### Reference Roles",
        "\n".join(role_lines(strategy)),
    ])
    design = design.replace("{{OVERVIEW}}", overview_text)
    design = design.replace("{{DESIGN_NORTH_STAR}}", as_markdown(strategy.get("design_north_star", "")))
    design = design.replace("Use role-based color tokens. Primary is reserved for the highest-value conversion action. Secondary supports navigation or lower-emphasis actions. Accent is for sparse emphasis only, not a second brand palette.", as_markdown(strategy.get("visual_system", "")) or "Use role-based color tokens and preserve contrast.")
    design = design.replace("Buttons, cards, forms, navigation, proof sections, feature cards, and final CTA blocks must use the tokens above.", as_markdown(strategy.get("component_rules", "")) or "Buttons, cards, forms, navigation, proof sections, feature cards, and final CTA blocks must use the tokens above.")
    design = design.replace("Target WCAG AA contrast, visible keyboard focus, semantic buttons/links, labeled form controls, and plain-language validation copy.", as_markdown(strategy.get("accessibility", "")) or "Target WCAG AA contrast, visible keyboard focus, semantic buttons/links, labeled form controls, and plain-language validation copy.")
    design = design.replace("Recommended homepage sequence: hero with one primary promise, proof immediately near the hero, feature/job sections, trust or comparison section, conversion area, FAQ, and final CTA.", as_markdown(strategy.get("implementation_guidance", "")) or "Recommended homepage sequence: hero, proof, feature sections, trust, conversion area, FAQ, and final CTA.")
    design = design.replace("Do not use generic gradient blobs, random glassmorphism, off-token colors, multiple primary CTAs in one viewport, low-contrast muted copy, centered long paragraphs, or exact reference layouts.", "Do not copy " + ", ".join(str(item) for item in strategy.get("forbidden_copy_elements", FORBIDDEN_COPY_ELEMENTS)) + ". " + as_markdown(strategy.get("conflict_resolution", "")))
    design = replace_policy_text(design, policy)
    if risk_block:
        design += f"\n\n{risk_block}\n"
    write(root / "DESIGN.md", design)
    write(root / "docs" / "artic-strategy.md", strategy_markdown)

    rules = load_template("design-rules.template.md")
    rules = rules.replace("{{PROJECT_NAME}}", name)
    rules = rules.replace("{{REFERENCE_SYNTHESIS}}", strategy_markdown)
    rules = replace_policy_text(rules, policy)
    if risk_block:
        rules += f"\n\n{risk_block}\n"
    write(root / "docs" / "design-rules.md", rules)

    checklist = load_template("design-qa-checklist.template.md")
    checklist = checklist.replace("# Artic Design QA Checklist\n", f"# Artic Design QA Checklist\n\n{language}\n")
    checklist = replace_policy_text(checklist, policy)
    if "Accessibility" not in checklist:
        checklist = checklist.replace("- [ ] Text contrast targets WCAG AA.", "- [ ] Accessibility: text contrast targets WCAG AA, focus states are visible, controls are semantic, and forms are labeled.")
    if risk_checklist_block:
        checklist += f"\n\n{risk_checklist_block}\n"
    checklist += "\n## Strategy Gates\n\n- [ ] Visual hierarchy follows the strategy north star.\n- [ ] Brand coherence follows the visual_system field.\n- [ ] Conversion clarity follows the conversion_strategy field.\n- [ ] Mobile quality follows implementation_guidance.\n- [ ] Accessibility follows the accessibility field.\n- [ ] Reference safety forbids logos, trademarks, proprietary illustrations, exact layouts, and source copywriting.\n"
    write(root / "docs" / "design-qa-checklist.md", checklist)

    prompt = load_template("homepage-design-prompt.template.md")
    prompt = prompt.replace("{{PROJECT_NAME}}", name)
    prompt = prompt.replace("# Homepage Implementation Prompt\n", f"# Homepage Implementation Prompt\n\n{language}\n")
    prompt = prompt.replace("Rules:\n", f"Strategy source: `docs/artic-strategy.md`.\n\nRules:\n")
    prompt = replace_policy_text(prompt, policy)
    if risk_block:
        prompt += f"\n\n{risk_block}\n"
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
        "mapper": "artic-internal-normalized-input-legacy-migration",
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
            {"role": f"legacy_reference_{index + 1}", "source_ids": [source_id], "selection_reason": "Migrated from pre-strategy selected_sources."}
            for index, source_id in enumerate(role_sources)
        ],
        "reference_hints": [],
        "catalog_query": str(references.get("query") or " ".join(search_facets)),
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
    state.update({"artic_version": str(brief.get("artic_version") or state.get("artic_version") or "0.4.1"), "last_generated_at": datetime.now(timezone.utc).isoformat(), "status": "generated", "language": brief_language(brief), "strategy_path": ".artic/strategy.json"})
    write(state_path, json.dumps(state, indent=2, ensure_ascii=False) + "\n")


def validate_outputs(root: Path) -> subprocess.CompletedProcess[str]:
    validator = Path(__file__).resolve().with_name("validate_artic_outputs.py")
    return subprocess.run([sys.executable, str(validator), "--root", str(root)], check=False, capture_output=True, text=True)


def write_strategy_prompt(root: Path, brief: dict[str, Any], references: dict[str, Any], intent: dict[str, Any] | None) -> Path:
    prompt = load_template("strategy-prompt.template.md")
    prompt += "\n\n## Current Brief Summary\n\n```json\n" + json.dumps(brief, indent=2, ensure_ascii=False) + "\n```\n"
    prompt += "\n## Current References Summary\n\n```json\n" + json.dumps(references, indent=2, ensure_ascii=False) + "\n```\n"
    if intent is not None:
        prompt += "\n## Internal Normalized Input (intent.json)\n\n```json\n" + json.dumps(intent, indent=2, ensure_ascii=False) + "\n```\n"
    prompt += "\nWrite the completed JSON to `.artic/strategy.json`, then rerun `@artic start`.\n"
    path = root / ".artic" / "strategy-prompt.md"
    write(path, prompt)
    return path


def stage_ready_session(root: Path) -> tuple[Path, dict[str, Any], dict[str, Any], dict[str, Any], tempfile.TemporaryDirectory[str]]:
    from artic_init_session import finalize_session

    tempdir = tempfile.TemporaryDirectory(prefix="artic-start-")
    staged_root = Path(tempdir.name)
    (staged_root / ".artic").mkdir(parents=True, exist_ok=True)
    shutil.copy2(root / ".artic" / "init-session.json", staged_root / ".artic" / "init-session.json")
    finalize_session(staged_root)
    brief = read_json(staged_root / ".artic" / "brief.json")
    references = read_json(staged_root / ".artic" / "references.json")
    intent = read_json(staged_root / ".artic" / "intent.json") if (staged_root / ".artic" / "intent.json").exists() else migrate_legacy_intent(staged_root, brief, references)
    return staged_root, brief, references, intent, tempdir


def commit_staged_ready_session(root: Path, staged_root: Path) -> None:
    for rel in [
        ".artic/brief.json",
        ".artic/references.json",
        ".artic/intent.json",
        ".artic/state.json",
        "docs/artic-brief.md",
        ".artic/init-session.json",
    ]:
        source = staged_root / rel
        if source.exists():
            destination = root / rel
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)


def create_start_outputs(root: Path, *, no_validate: bool = False) -> dict[str, Any]:
    session_path = root / ".artic" / "init-session.json"
    brief_path = root / ".artic" / "brief.json"
    references_path = root / ".artic" / "references.json"
    strategy_path = root / ".artic" / "strategy.json"
    staged_root: Path | None = None
    staged_tempdir: tempfile.TemporaryDirectory[str] | None = None
    if session_path.exists():
        from artic_init_session import is_ready, read_session, render_questions
        session = read_session(root)
        status = str(session.get("status") or "")
        if status == "collecting" or not is_ready(session):
            missing = ", ".join(str(item) for item in session.get("missing", []))
            questions = " | ".join(render_questions(session))
            raise ValueError("cannot run @artic start before init is ready" + (f": missing {missing}" if missing else "") + (f". Next questions: {questions}" if questions else ""))
        if not strategy_path.exists() and (status == "ready" or not brief_path.exists() or not references_path.exists()):
            answers = session.get("answers") if isinstance(session.get("answers"), dict) else {}
            prompt_brief = {"answers": answers, "language": session.get("language", {}), "risk_readiness": session.get("risk_readiness", {})}
            prompt_references = {"selected_sources": [], "source_plan": [], "note": "@artic start requires the agent-authored strategy before finalizing init outputs."}
            prompt_path = write_strategy_prompt(root, prompt_brief, prompt_references, None)
            raise ValueError(json.dumps({
                "error": "missing_strategy",
                "message": "Public Artic agent must create .artic/strategy.json before runtime generation.",
                "strategy_prompt": str(prompt_path.relative_to(root)),
                "generated_files": [str(prompt_path.relative_to(root))],
            }, ensure_ascii=False))
        if status == "ready" or not brief_path.exists() or not references_path.exists():
            staged_root, brief, references, intent, staged_tempdir = stage_ready_session(root)
        else:
            brief = read_json(brief_path)
            references = read_json(references_path)
            intent = read_json(root / ".artic" / "intent.json") if (root / ".artic" / "intent.json").exists() else migrate_legacy_intent(root, brief, references)
    else:
        brief = read_json(brief_path)
        references = read_json(references_path)
        intent = read_json(root / ".artic" / "intent.json") if (root / ".artic" / "intent.json").exists() else migrate_legacy_intent(root, brief, references)

    if not strategy_path.exists():
        prompt_path = write_strategy_prompt(root, brief, references, intent)
        raise ValueError(json.dumps({
            "error": "missing_strategy",
            "message": "Public Artic agent must create .artic/strategy.json before runtime generation.",
            "strategy_prompt": str(prompt_path.relative_to(root)),
            "generated_files": [str(prompt_path.relative_to(root))],
        }, ensure_ascii=False))

    strategy = read_strategy_json(strategy_path)
    strategy_errors = validate_strategy_payload(strategy)
    if strategy_errors:
        raise ValueError(json.dumps({"error": "invalid_strategy", "errors": strategy_errors}, ensure_ascii=False))
    input_errors = validate_runtime_inputs(intent, references)
    if input_errors:
        raise ValueError(json.dumps({"error": "invalid_runtime_inputs", "errors": input_errors}, ensure_ascii=False))
    strategy_source_errors = validate_strategy_sources(strategy, references)
    if strategy_source_errors:
        raise ValueError(json.dumps({"error": "invalid_strategy_sources", "errors": strategy_source_errors}, ensure_ascii=False))
    if staged_root is not None:
        commit_staged_ready_session(root, staged_root)

    generated = render_outputs(root, brief, references, strategy, intent)
    payload: dict[str, Any] = {
        "root": str(root.resolve()),
        "generated_files": generated,
        "validated": False,
        "strategy_path": str(strategy_path.relative_to(root)),
        "strategy_validated": True,
        "strategy": {"design_north_star": str(strategy.get("design_north_star") or "")},
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
    parser = argparse.ArgumentParser(description="Compile Artic strategy.json into DESIGN.md and design docs.")
    parser.add_argument("--root", required=True, help="Project root containing .artic/brief.json, .artic/references.json, and .artic/strategy.json")
    parser.add_argument("--no-validate", action="store_true", help="Skip final output validation only; strategy validation always runs")
    args = parser.parse_args()
    try:
        payload = create_start_outputs(Path(args.root), no_validate=args.no_validate)
    except ValueError as exc:
        message = str(exc)
        try:
            print(json.dumps(json.loads(message), ensure_ascii=False))
        except json.JSONDecodeError:
            print(json.dumps({"error": message}, ensure_ascii=False))
        return 1
    except RuntimeError as exc:
        print(str(exc))
        return 1
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
