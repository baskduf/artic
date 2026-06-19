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


def synthesize_reference_summary(brief: dict[str, Any], references: dict[str, Any]) -> str:
    query = query_from_inputs(brief, references)
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
    reference_lines = selected_reference_lines(references)
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
    text = text.replace(f"{POLICY_MARKER}\n{POLICY}", block)
    return text.replace(POLICY, block)


def render_outputs(root: Path, brief: dict[str, Any], references: dict[str, Any]) -> list[str]:
    name = project_name(brief)
    description = f"{project_description(brief)} Artic-generated homepage design system."
    ref_summary = synthesize_reference_summary(brief, references)
    policy = policy_block(brief)

    design = load_template("DESIGN.template.md")
    design = design.replace("{{PROJECT_NAME}}", yaml_double_quoted(name))
    design = design.replace("{{DESIGN_DESCRIPTION}}", yaml_double_quoted(description))
    design = design.replace("{{OVERVIEW}}", overview(brief, references))
    design = replace_policy_text(design, policy)
    write(root / "DESIGN.md", design)

    rules = load_template("design-rules.template.md")
    rules = rules.replace("{{PROJECT_NAME}}", name)
    rules = rules.replace("{{REFERENCE_SYNTHESIS}}", ref_summary)
    rules = replace_policy_text(rules, policy)
    write(root / "docs" / "design-rules.md", rules)

    checklist = load_template("design-qa-checklist.template.md")
    checklist = replace_policy_text(checklist, policy)
    if "Accessibility" not in checklist:
        checklist = checklist.replace("- [ ] Text contrast targets WCAG AA.", "- [ ] Accessibility: text contrast targets WCAG AA, focus states are visible, controls are semantic, and forms are labeled.")
    write(root / "docs" / "design-qa-checklist.md", checklist)

    prompt = load_template("homepage-design-prompt.template.md")
    prompt = prompt.replace("{{PROJECT_NAME}}", name)
    prompt = replace_policy_text(prompt, policy)
    write(root / "docs" / "homepage-design-prompt.md", prompt)

    update_state(root, brief)
    return GENERATED_FILES


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
            "artic_version": str(brief.get("artic_version") or state.get("artic_version") or "0.1.0"),
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
    brief = read_json(root / ".artic" / "brief.json")
    references = read_json(root / ".artic" / "references.json")
    generated = render_outputs(root, brief, references)
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
