#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REQUIRED_INPUTS = [
    "DESIGN.md",
    "docs/homepage-design-prompt.md",
    ".artic/brief.json",
    ".artic/references.json",
]
POLICY_FALLBACK = "Reference policy: extract reusable principles only; do not copy logos, trademarks, proprietary illustrations, or exact layouts."
POLICY_BY_LOCALE = {
    "ko-KR": "참고 정책: 재사용 가능한 원칙만 추출하고, 로고, 상표, 독점 일러스트, 정확한 레이아웃은 복사하지 않습니다.",
}


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


def required_missing(root: Path) -> list[str]:
    return [rel for rel in REQUIRED_INPUTS if not (root / rel).exists()]


def frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        return ""
    end = text.find("\n---\n", 4)
    if end == -1:
        return ""
    return text[4:end]


def yaml_value(block: str, key: str, default: str) -> str:
    match = re.search(rf"^\s*{re.escape(key)}\s*:\s*[\"']?([^\n\"']+)[\"']?\s*$", block, re.MULTILINE)
    return match.group(1).strip() if match else default


def yaml_section_value(block: str, section: str, token: str, default: str) -> str:
    lines = block.splitlines()
    in_section = False
    for line in lines:
        if re.match(rf"^{re.escape(section)}\s*:", line):
            in_section = True
            continue
        if in_section and line and not line.startswith(" "):
            break
        if in_section:
            match = re.match(rf"^\s+{re.escape(token)}\s*:\s*[\"']?([^\n\"']+)[\"']?\s*$", line)
            if match:
                return match.group(1).strip()
    return default


def safe_css_color(value: str, fallback: str) -> str:
    candidate = value.strip()
    safe_patterns = [
        r"#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?(?:[0-9a-fA-F]{2})?",
        r"(?:rgb|rgba|hsl|hsla)\([0-9.%,\s]+\)",
        r"[a-zA-Z]+",
    ]
    if any(re.fullmatch(pattern, candidate) for pattern in safe_patterns):
        return candidate
    return fallback


def markdown_section(text: str, heading: str) -> str:
    marker = f"## {heading}"
    start = text.find(marker)
    if start == -1:
        return ""
    next_heading = text.find("\n## ", start + len(marker))
    end = next_heading if next_heading != -1 else len(text)
    section = text[start + len(marker):end]
    return " ".join(line.strip(" #") for line in section.splitlines() if line.strip())


def selected_source_names(references: dict[str, Any]) -> list[str]:
    selected = references.get("selected_sources", [])
    if not isinstance(selected, list):
        return []
    names: list[str] = []
    for row in selected:
        if not isinstance(row, dict):
            continue
        name = str(row.get("name") or row.get("id") or "reference source").strip()
        if name:
            names.append(name)
    return names


def brief_locale(brief: dict[str, Any]) -> str:
    language = brief.get("language")
    if isinstance(language, dict):
        return str(language.get("locale") or "en-US")
    return "en-US"


def has_3d_runtime_reference(brief: dict[str, Any], references: dict[str, Any]) -> bool:
    roles = references.get("role_assignments", [])
    if isinstance(roles, list):
        for role in roles:
            if isinstance(role, dict) and "3d_runtime" == str(role.get("role")):
                return True
    style = brief.get("style")
    facets = style.get("search_facets", []) if isinstance(style, dict) else []
    return isinstance(facets, list) and any("3d" in str(item).lower() or "webgl" in str(item).lower() for item in facets)


def localized_copy(locale: str) -> dict[str, str]:
    if locale.startswith("ko"):
        return {
            "preview_badge": "Artic 미리보기 · DESIGN.md 기반 생성",
            "for_label": "대상",
            "headline_suffix": "홈페이지 방향",
            "drive": "목표 이끌기",
            "view_logic": "디자인 논리 보기",
            "north_star": "Design north star",
            "accessibility": "접근성 목표",
            "reference_roles": "레퍼런스 역할",
            "promise_title": "1. 약속",
            "promise_body": "프로젝트 고유의 약속과 가장 중요한 전환 경로를 먼저 보여줍니다.",
            "proof_title": "2. 증거",
            "proof_body": "신뢰 근거를 hero 가까이에 배치해 첫 CTA를 뒷받침합니다.",
            "system_title": "3. 시스템",
            "system_body": "토큰, 간격 리듬, 시맨틱 컨트롤, 독창적 구성을 Artic 문서에서 가져옵니다.",
            "reference_title": "레퍼런스 기반, 복제 아님",
            "reference_body": "이 정적 미리보기는 Artic start 산출물에서 생성됩니다. 기본 동작은 .artic/show/index.html만 작성하고 앱 소스 파일은 건드리지 않습니다.",
            "policy_title": "참고 정책",
            "generated": "생성 시각",
            "root": "루트",
            "model_label": "3D 모델 자리표시자",
            "model_body": "실제 GLB/이미지/모델은 사용자가 허용한 소유 에셋 또는 라이선스 확인 가능한 공개 에셋만 연결합니다. 이 영역은 회전, 줌, 포커스, poster fallback, reduced motion 상태를 검토하기 위한 구조입니다.",
            "interaction_title": "상호작용 영역",
            "interaction_body": "드래그/탭/키보드 포커스로 석고상을 만지는 경험을 설계하고, 로딩 실패 시 정적 포스터와 설명 텍스트를 제공합니다.",
        }
    return {
        "preview_badge": "Artic Preview · generated from DESIGN.md",
        "for_label": "For",
        "headline_suffix": "homepage direction",
        "drive": "Drive",
        "view_logic": "View design logic",
        "north_star": "Design north star",
        "accessibility": "accessibility target",
        "reference_roles": "reference roles",
        "promise_title": "1. Promise",
        "promise_body": "Lead with one clear project-specific promise and one dominant conversion path.",
        "proof_title": "2. Proof",
        "proof_body": "Place evidence close to the hero so trust supports the first CTA.",
        "system_title": "3. System",
        "system_body": "Use tokens, spacing rhythm, semantic controls, and original composition from the Artic docs.",
        "reference_title": "Reference-informed, not reference-copied",
        "reference_body": "This static preview is generated from Artic start outputs. It intentionally writes only .artic/show/index.html and leaves app source files untouched.",
        "policy_title": "Reference policy",
        "generated": "Generated",
        "root": "Root",
        "model_label": "3D model placeholder",
        "model_body": "Attach only user-owned or license-verifiable public GLB/image/model assets when allowed. This zone is for rotation, zoom, focus, poster fallback, and reduced-motion review.",
        "interaction_title": "Interaction zone",
        "interaction_body": "Design drag, tap, and keyboard focus affordances for the central 3D object, with a static poster and description fallback when loading fails.",
    }


def project_name(brief: dict[str, Any], design_frontmatter: str) -> str:
    project = brief.get("project")
    if isinstance(project, dict):
        value = str(project.get("name") or project.get("description") or "").strip()
        if value:
            return value
    return yaml_value(design_frontmatter, "name", "Artic Preview")


def render_html(root: Path, brief: dict[str, Any], references: dict[str, Any], design_text: str) -> str:
    fm = frontmatter(design_text)
    name = project_name(brief, fm)
    description = yaml_value(fm, "description", "Artic-generated homepage preview")
    primary = safe_css_color(yaml_section_value(fm, "colors", "primary", "#1F4FD8"), "#1F4FD8")
    accent = safe_css_color(yaml_section_value(fm, "colors", "accent", "#7C3AED"), "#7C3AED")
    surface = safe_css_color(yaml_section_value(fm, "colors", "surface", "#FFFFFF"), "#FFFFFF")
    neutral = safe_css_color(yaml_section_value(fm, "colors", "neutral", "#F6F8FB"), "#F6F8FB")
    text = safe_css_color(yaml_section_value(fm, "colors", "text", "#111827"), "#111827")
    muted = safe_css_color(yaml_section_value(fm, "colors", "muted", "#6B7280"), "#6B7280")
    border = safe_css_color(yaml_section_value(fm, "colors", "border", "#DDE3EA"), "#DDE3EA")

    raw_project = brief.get("project")
    project = raw_project if isinstance(raw_project, dict) else {}
    audience = ", ".join(str(item) for item in project.get("target_users", []) if item) or "the target audience"
    goal = str(project.get("primary_goal") or "the primary conversion")
    raw_style = brief.get("style")
    style = raw_style if isinstance(raw_style, dict) else {}
    north_star = markdown_section(design_text, "Design North Star") or str(style.get("design_north_star", ""))
    overview = markdown_section(design_text, "Overview") or description
    composition = markdown_section(design_text, "Page Composition") or "Hero, proof, features, trust, conversion, FAQ, and final CTA."
    sources = selected_source_names(references)
    locale = brief_locale(brief)
    copy = localized_copy(locale)
    policy_text = POLICY_BY_LOCALE.get(locale, POLICY_FALLBACK)
    source_items = "\n".join(f"<li>{html.escape(source)}</li>" for source in sources[:5]) or "<li>Artic selected references</li>"
    if has_3d_runtime_reference(brief, references):
        runtime_block = f"""
    <section class=\"panel runtime-3d\" aria-label=\"model-viewer 3D runtime placeholder\">
      <span class=\"pill\">{html.escape(copy['model_label'])}</span>
      <div class=\"model-viewer-stub\" role=\"img\" aria-label=\"model-viewer placeholder\">model-viewer · GLB</div>
      <div class=\"interaction-zone\">
        <b>{html.escape(copy['interaction_title'])}</b>
        <p>{html.escape(copy['interaction_body'])}</p>
      </div>
      <p>{html.escape(copy['model_body'])}</p>
    </section>"""
    else:
        runtime_block = ""

    generated_at = datetime.now(timezone.utc).isoformat()
    return f"""<!doctype html>
<html lang="{html.escape(locale)}">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(name)} — Artic Preview</title>
  <style>
    :root {{ --primary: {primary}; --accent: {accent}; --surface: {surface}; --neutral: {neutral}; --text: {text}; --muted: {muted}; --border: {border}; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: var(--text); background: linear-gradient(180deg, var(--neutral), var(--surface)); }}
    .page {{ width: min(1120px, calc(100% - 32px)); margin: 0 auto; padding: 32px 0 64px; }}
    .nav {{ display: flex; justify-content: space-between; align-items: center; gap: 16px; margin-bottom: 72px; }}
    .brand {{ font-weight: 800; letter-spacing: -0.04em; }}
    .pill {{ display: inline-flex; align-items: center; border: 1px solid var(--border); border-radius: 999px; padding: 8px 12px; color: var(--muted); background: rgba(255,255,255,.72); }}
    .hero {{ display: grid; grid-template-columns: minmax(0, 1.1fr) minmax(280px, .9fr); gap: 40px; align-items: center; }}
    h1 {{ font-size: clamp(3rem, 8vw, 5.7rem); line-height: .92; letter-spacing: -0.07em; margin: 18px 0; }}
    h2 {{ font-size: clamp(2rem, 4vw, 3rem); letter-spacing: -0.045em; margin: 0 0 16px; }}
    p {{ color: var(--muted); line-height: 1.7; font-size: 1.04rem; }}
    .actions {{ display: flex; flex-wrap: wrap; gap: 12px; margin-top: 28px; }}
    .button {{ border: 0; border-radius: 14px; padding: 14px 18px; font-weight: 750; text-decoration: none; }}
    .primary {{ background: var(--primary); color: white; box-shadow: 0 18px 40px rgba(31,79,216,.22); }}
    .secondary {{ color: var(--text); border: 1px solid var(--border); background: white; }}
    .panel {{ border: 1px solid var(--border); background: rgba(255,255,255,.82); border-radius: 28px; padding: 28px; box-shadow: 0 24px 80px rgba(15,23,42,.08); }}
    .metric-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 12px; margin-top: 18px; }}
    .metric {{ padding: 18px; border-radius: 20px; background: var(--neutral); }}
    .metric strong {{ display: block; font-size: 1.35rem; color: var(--primary); }}
    .sections {{ display: grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap: 16px; margin-top: 56px; }}
    .card {{ border: 1px solid var(--border); border-radius: 24px; padding: 22px; background: white; }}
    .card b {{ display: block; margin-bottom: 8px; }}
    .source-list {{ padding-left: 20px; color: var(--muted); line-height: 1.8; }}
    .model-viewer-stub {{ display: grid; place-items: center; min-height: 300px; margin: 18px 0; border-radius: 28px; border: 1px dashed var(--border); color: var(--muted); background: radial-gradient(circle at 50% 36%, rgba(124,58,237,.18), transparent 34%), linear-gradient(145deg, var(--neutral), var(--surface)); font-weight: 800; letter-spacing: .08em; }}
    .interaction-zone {{ border: 1px solid var(--border); border-radius: 20px; padding: 16px; background: var(--neutral); }}
    .runtime-3d {{ margin-top: 24px; }}
    .policy {{ margin-top: 56px; padding: 18px; border-left: 4px solid var(--accent); background: white; border-radius: 16px; color: var(--muted); }}
    @media (max-width: 820px) {{ .hero, .sections {{ grid-template-columns: 1fr; }} .nav {{ align-items: flex-start; flex-direction: column; }} }}
  </style>
</head>
<body>
  <main class="page">
    <nav class="nav">
      <div class="brand">{html.escape(name)}</div>
      <div class="pill">{html.escape(copy['preview_badge'])}</div>
    </nav>
    <section class="hero">
      <div>
        <span class="pill">{html.escape(copy['for_label'])}: {html.escape(audience)}</span>
        <h1>{html.escape(name)} {html.escape(copy['headline_suffix'])}</h1>
        <p>{html.escape(overview)}</p>
        <div class="actions">
          <a class="button primary" href="#conversion">{html.escape(copy['drive'])}: {html.escape(goal)}</a>
          <a class="button secondary" href="#design-system">{html.escape(copy['view_logic'])}</a>
        </div>
      </div>
      <aside class="panel" aria-label="Design north star">
        <span class="pill">{html.escape(copy['north_star'])}</span>
        <h2>{html.escape(north_star[:110] or description)}</h2>
        <p>{html.escape(composition)}</p>
        <div class="metric-grid">
          <div class="metric"><strong>AA</strong><span>{html.escape(copy['accessibility'])}</span></div>
          <div class="metric"><strong>{len(sources) or 3}</strong><span>{html.escape(copy['reference_roles'])}</span></div>
        </div>
      </aside>
    </section>
    <section id="design-system" class="sections">
      <article class="card"><b>{html.escape(copy['promise_title'])}</b><p>{html.escape(copy['promise_body'])}</p></article>
      <article class="card"><b>{html.escape(copy['proof_title'])}</b><p>{html.escape(copy['proof_body'])}</p></article>
      <article class="card"><b>{html.escape(copy['system_title'])}</b><p>{html.escape(copy['system_body'])}</p></article>
    </section>
{runtime_block}
    <section class="panel" style="margin-top: 24px;" id="conversion">
      <h2>{html.escape(copy['reference_title'])}</h2>
      <p>{html.escape(copy['reference_body'])}</p>
      <ul class="source-list">{source_items}</ul>
    </section>
    <section class="policy">
      <strong>{html.escape(copy['policy_title'])}</strong><br />
      {html.escape(policy_text)}
      <br /><small>{html.escape(copy['generated'])}: {html.escape(generated_at)} · {html.escape(copy['root'])}: {html.escape(str(root))}</small>
    </section>
  </main>
</body>
</html>
"""


def create_show_preview(root: Path) -> dict[str, Any]:
    missing = required_missing(root)
    if missing:
        raise ValueError("missing required input(s) for @artic show: " + ", ".join(missing))
    design_text = (root / "DESIGN.md").read_text(encoding="utf-8")
    brief = read_json(root / ".artic" / "brief.json")
    references = read_json(root / ".artic" / "references.json")
    preview = root / ".artic" / "show" / "index.html"
    preview.parent.mkdir(parents=True, exist_ok=True)
    preview.write_text(render_html(root, brief, references, design_text), encoding="utf-8")
    return {
        "root": str(root.resolve()),
        "preview_file": str(preview),
        "modified_app_files": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a safe static Artic homepage preview from start-generated design docs.")
    parser.add_argument("--root", required=True, help="Project root containing DESIGN.md and .artic outputs from @artic start")
    args = parser.parse_args()
    try:
        payload = create_show_preview(Path(args.root))
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
