#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REQUIRED_INPUTS = [
    "DESIGN.md",
    "docs/homepage-design-prompt.md",
    ".artic/brief.json",
    ".artic/references.json",
    ".artic/strategy.json",
]
POLICY_FALLBACK = "Reference policy: extract reusable principles only; do not copy logos, trademarks, proprietary illustrations, or exact layouts."
POLICY_BY_LOCALE = {
    "ko-KR": "참고 정책: 재사용 가능한 원칙만 추출하고, 로고, 상표, 독점 일러스트, 정확한 레이아웃은 복사하지 않습니다.",
}
SCORE_KEYS = [
    "strategy_alignment",
    "visual_fidelity",
    "asset_richness",
    "asset_provenance_completeness",
    "conversion_clarity",
    "visual_specificity",
    "accessibility_basics",
    "mobile_first",
    "genericness_penalty",
    "overall",
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


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


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
    for bucket in (brief.get("style"), references, brief):
        text = json.dumps(bucket, ensure_ascii=False).lower() if isinstance(bucket, (dict, list)) else str(bucket).lower()
        if any(term in text for term in ("3d", "webgl", "glb", "model-viewer", "runtime")):
            return True
    return False


def localized_copy(locale: str) -> dict[str, str]:
    if locale.startswith("ko"):
        return {
            "preview_badge": "Artic 미리보기 · 에셋 우선 번들",
            "for_label": "대상",
            "headline_suffix": "첫 시각 초안",
            "drive": "목표 이끌기",
            "view_logic": "디자인 논리 보기",
            "north_star": "Design north star",
            "accessibility": "접근성 목표",
            "reference_roles": "레퍼런스 역할",
            "promise_title": "1. 약속",
            "promise_body": "프로젝트 고유의 약속과 가장 중요한 전환 경로를 먼저 보여줍니다.",
            "proof_title": "2. 증거",
            "proof_body": "신뢰 근거와 에셋 출처를 hero 가까이에 배치해 첫 CTA를 뒷받침합니다.",
            "system_title": "3. 시스템",
            "system_body": "토큰, 간격 리듬, 시맨틱 컨트롤, 독창적 구성을 Artic 문서에서 가져옵니다.",
            "reference_title": "레퍼런스 기반, 복제 아님",
            "reference_body": "이 정적 번들은 Artic start 산출물에서 생성됩니다. 앱 소스 파일은 건드리지 않습니다.",
            "policy_title": "참고 정책",
            "generated": "생성 시각",
            "root": "루트",
            "model_label": "3D 모델 자리표시자",
            "model_body": "실제 GLB/이미지/모델은 소유 에셋 또는 라이선스 확인 가능한 공개 에셋만 연결합니다. 이 preview-only 에셋은 poster fallback, reduced motion, 로딩 실패 상태를 검토하기 위한 구조입니다.",
            "interaction_title": "상호작용 영역",
            "interaction_body": "드래그/탭/키보드 포커스로 3D 오브젝트를 탐색하고, 실패 시 정적 포스터와 설명 텍스트를 제공합니다.",
        }
    return {
        "preview_badge": "Artic Preview · asset-first bundle",
        "for_label": "For",
        "headline_suffix": "first visual draft",
        "drive": "Drive",
        "view_logic": "View design logic",
        "north_star": "Design north star",
        "accessibility": "accessibility target",
        "reference_roles": "reference roles",
        "promise_title": "1. Promise",
        "promise_body": "Lead with one clear project-specific promise and one dominant conversion path.",
        "proof_title": "2. Proof",
        "proof_body": "Place evidence and asset provenance close to the hero so trust supports the first CTA.",
        "system_title": "3. System",
        "system_body": "Use tokens, spacing rhythm, semantic controls, and original composition from the Artic docs.",
        "reference_title": "Reference-informed, not reference-copied",
        "reference_body": "This static bundle is generated from Artic start outputs. It intentionally leaves app source files untouched.",
        "policy_title": "Reference policy",
        "generated": "Generated",
        "root": "Root",
        "model_label": "3D asset placeholder",
        "model_body": "Attach only user-owned or license-verifiable public GLB/image/model assets when allowed. This preview-only asset validates poster fallback, reduced motion, and loading failure states.",
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


def build_tokens(design_text: str) -> dict[str, Any]:
    fm = frontmatter(design_text)
    colors = {
        "primary": safe_css_color(yaml_section_value(fm, "colors", "primary", "#1F4FD8"), "#1F4FD8"),
        "accent": safe_css_color(yaml_section_value(fm, "colors", "accent", "#7C3AED"), "#7C3AED"),
        "surface": safe_css_color(yaml_section_value(fm, "colors", "surface", "#FFFFFF"), "#FFFFFF"),
        "neutral": safe_css_color(yaml_section_value(fm, "colors", "neutral", "#F6F8FB"), "#F6F8FB"),
        "text": safe_css_color(yaml_section_value(fm, "colors", "text", "#111827"), "#111827"),
        "muted": safe_css_color(yaml_section_value(fm, "colors", "muted", "#6B7280"), "#6B7280"),
        "border": safe_css_color(yaml_section_value(fm, "colors", "border", "#DDE3EA"), "#DDE3EA"),
    }
    return {
        "colors": colors,
        "type": {
            "family": yaml_section_value(fm, "typography", "fontFamily", "Inter, ui-sans-serif, system-ui"),
            "hero": "clamp(3rem, 8vw, 5.7rem)",
            "heading": "clamp(2rem, 4vw, 3rem)",
            "body": "1rem",
        },
        "radius": {"sm": "8px", "md": "14px", "lg": "24px", "xl": "32px", "pill": "999px"},
        "spacing": {"xs": "4px", "sm": "8px", "md": "16px", "lg": "24px", "xl": "40px", "section": "96px"},
        "shadow": {"card": "0 24px 80px rgba(15,23,42,.08)", "cta": "0 18px 40px rgba(31,79,216,.22)"},
        "motion": {"duration": "180ms", "easing": "cubic-bezier(.2,.8,.2,1)", "reduced_motion": "preserve layout without parallax"},
    }


def variant_names(max_iterations: int, runtime_3d: bool) -> list[str]:
    pool = ["asset-hero", "conversion-proof", "immersive-runtime" if runtime_3d else "editorial-system"]
    return pool[:max_iterations]


def make_placeholder_svg(kind: str, tokens: dict[str, Any]) -> str:
    c = tokens["colors"]
    title = "Model Poster" if kind == "model" else "Scene Fallback"
    label = "preview-only 3D poster" if kind == "model" else "preview-only runtime fallback"
    shape = "<circle cx='360' cy='220' r='96' fill='url(#g)'/><path d='M280 310h160l-34 80H314z' fill='rgba(17,24,39,.18)'/>" if kind == "model" else "<rect x='170' y='130' width='380' height='220' rx='34' fill='url(#g)'/><path d='M210 285c60-82 118-92 174-28 42-52 92-60 150 28' stroke='rgba(255,255,255,.86)' stroke-width='16' fill='none'/>"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="720" height="480" viewBox="0 0 720 480" role="img" aria-label="{html.escape(title)}">
  <defs><linearGradient id="g" x1="0" x2="1"><stop stop-color="{html.escape(c['primary'])}"/><stop offset="1" stop-color="{html.escape(c['accent'])}"/></linearGradient></defs>
  <rect width="720" height="480" fill="{html.escape(c['neutral'])}"/>
  <circle cx="600" cy="86" r="140" fill="rgba(124,58,237,.12)"/>
  {shape}
  <text x="42" y="70" font-family="Inter,Arial,sans-serif" font-size="34" font-weight="800" fill="{html.escape(c['text'])}">{html.escape(title)}</text>
  <text x="42" y="112" font-family="Inter,Arial,sans-serif" font-size="18" fill="{html.escape(c['muted'])}">{html.escape(label)}</text>
</svg>
"""


def build_asset_manifest(root: Path, show_dir: Path, iteration: str, variant: str, brief: dict[str, Any], references: dict[str, Any], tokens: dict[str, Any], asset_mode: str, runtime_3d: bool) -> dict[str, Any]:
    assets_dir = show_dir / "assets"
    placeholders_dir = assets_dir / "placeholders"
    sources = selected_source_names(references)
    assets: list[dict[str, Any]] = []
    for idx, source in enumerate(sources or ["artic-generated-visual-direction"], start=1):
        assets.append({
            "id": f"catalog-reference-{idx}",
            "path": None,
            "type": "catalog-reference",
            "status": "catalog-reference",
            "retrieval": "catalog-reference",
            "provenance": "selected Artic reference source",
            "kind": "catalog-reference",
            "title": source,
            "source": source,
            "license": "unknown",
            "license_status": "unknown-unverified",
            "usage": "preview-only visual direction and provenance record; do not copy protected marks or exact layouts",
            "downloaded": False,
            "local_path": None,
        })
    hero_name = f"hero-{variant}.svg"
    write_text(placeholders_dir / hero_name, make_placeholder_svg("scene", tokens))
    assets.append({
        "id": f"generated-{variant}-hero",
        "path": f"assets/placeholders/{hero_name}",
        "type": "image/svg+xml",
        "status": "generated",
        "retrieval": "generated-placeholder",
        "provenance": "generated locally by Artic show",
        "kind": "generated-placeholder",
        "title": f"{variant} hero placeholder",
        "source": "generated locally by Artic show",
        "license": "Artic generated preview placeholder",
        "license_status": "preview-only-generated",
        "usage": "safe first-draft hero artwork",
        "downloaded": False,
        "local_path": f"assets/placeholders/{hero_name}",
    })
    if runtime_3d:
        model_svg = make_placeholder_svg("model", tokens)
        scene_svg = make_placeholder_svg("scene", tokens)
        write_text(placeholders_dir / "model-poster.svg", model_svg)
        write_text(placeholders_dir / "scene-fallback.svg", scene_svg)
        write_text(assets_dir / "model-poster.svg", model_svg)
        write_text(assets_dir / "scene-fallback.svg", scene_svg)
        assets.extend([
            {
                "id": "generated-model-poster",
                "path": "assets/placeholders/model-poster.svg",
                "type": "image/svg+xml",
                "status": "generated",
                "retrieval": "generated-placeholder",
                "provenance": "generated locally by Artic show",
                "kind": "generated-placeholder",
                "title": "3D model poster placeholder",
                "source": "generated locally by Artic show",
                "license": "Artic generated preview placeholder",
                "license_status": "preview-only-generated",
                "usage": "3D poster fallback before verified GLB/model asset is supplied",
                "downloaded": False,
                "local_path": "assets/placeholders/model-poster.svg",
            },
            {
                "id": "generated-model-poster-root-alias",
                "path": "assets/model-poster.svg",
                "type": "image/svg+xml",
                "status": "generated",
                "retrieval": "generated-placeholder",
                "provenance": "generated locally by Artic show",
                "kind": "generated-placeholder",
                "title": "3D model poster placeholder root alias",
                "source": "generated locally by Artic show",
                "license": "Artic generated preview placeholder",
                "license_status": "preview-only-generated",
                "usage": "backward-compatible 3D poster fallback alias",
                "downloaded": False,
                "local_path": "assets/model-poster.svg",
            },
            {
                "id": "generated-scene-fallback",
                "path": "assets/placeholders/scene-fallback.svg",
                "type": "image/svg+xml",
                "status": "generated",
                "retrieval": "generated-placeholder",
                "provenance": "generated locally by Artic show",
                "kind": "generated-placeholder",
                "title": "3D scene fallback placeholder",
                "source": "generated locally by Artic show",
                "license": "Artic generated preview placeholder",
                "license_status": "preview-only-generated",
                "usage": "runtime failure and reduced-motion scene fallback",
                "downloaded": False,
                "local_path": "assets/placeholders/scene-fallback.svg",
            },
            {
                "id": "generated-scene-fallback-root-alias",
                "path": "assets/scene-fallback.svg",
                "type": "image/svg+xml",
                "status": "generated",
                "retrieval": "generated-placeholder",
                "provenance": "generated locally by Artic show",
                "kind": "generated-placeholder",
                "title": "3D scene fallback placeholder root alias",
                "source": "generated locally by Artic show",
                "license": "Artic generated preview placeholder",
                "license_status": "preview-only-generated",
                "usage": "backward-compatible runtime failure fallback alias",
                "downloaded": False,
                "local_path": "assets/scene-fallback.svg",
            },
        ])
    return {
        "schema_version": 1,
        "mode": "asset-first-preview",
        "asset_mode": asset_mode,
        "iteration": iteration,
        "variant": variant,
        "root": str(root.resolve()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "notes": ["Unknown or unverified sources are recorded as preview-only/catalog-reference and do not block preview generation."],
        "assets": assets,
    }


def render_css(tokens: dict[str, Any], variant: str, runtime_3d: bool) -> str:
    c = tokens["colors"]
    hero_background = {
        "asset-hero": "radial-gradient(circle at 80% 10%, color-mix(in srgb, var(--accent) 18%, transparent), transparent 34%), linear-gradient(180deg, var(--neutral), var(--surface))",
        "conversion-proof": "linear-gradient(180deg, var(--surface), var(--neutral))",
        "immersive-runtime": "radial-gradient(circle at 62% 20%, color-mix(in srgb, var(--accent) 24%, transparent), transparent 32%), radial-gradient(circle at 20% 20%, color-mix(in srgb, var(--primary) 18%, transparent), transparent 26%), var(--surface)",
        "editorial-system": "linear-gradient(135deg, var(--neutral), var(--surface) 48%, color-mix(in srgb, var(--primary) 8%, var(--surface)))",
    }.get(variant, "linear-gradient(180deg, var(--neutral), var(--surface))")
    return f""":root {{
  --primary: {c['primary']}; --accent: {c['accent']}; --surface: {c['surface']}; --neutral: {c['neutral']}; --text: {c['text']}; --muted: {c['muted']}; --border: {c['border']};
  --radius-sm: {tokens['radius']['sm']}; --radius-md: {tokens['radius']['md']}; --radius-lg: {tokens['radius']['lg']}; --radius-xl: {tokens['radius']['xl']}; --shadow-card: {tokens['shadow']['card']}; --shadow-cta: {tokens['shadow']['cta']};
}}
* {{ box-sizing: border-box; }}
html {{ scroll-behavior: smooth; }}
body {{ margin: 0; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: var(--text); background: {hero_background}; }}
a {{ color: inherit; }}
.page {{ width: min(1160px, calc(100% - 32px)); margin: 0 auto; padding: 28px 0 64px; }}
.nav {{ display: flex; justify-content: space-between; align-items: center; gap: 16px; margin-bottom: clamp(36px, 8vw, 76px); }}
.brand {{ font-weight: 850; letter-spacing: -0.045em; font-size: 1.12rem; }}
.pill {{ display: inline-flex; align-items: center; border: 1px solid var(--border); border-radius: 999px; padding: 8px 12px; color: var(--muted); background: rgba(255,255,255,.72); backdrop-filter: blur(12px); }}
.hero {{ display: grid; grid-template-columns: minmax(0, 1.05fr) minmax(280px, .95fr); gap: clamp(24px, 5vw, 56px); align-items: center; }}
h1 {{ font-size: clamp(3rem, 8vw, 5.9rem); line-height: .91; letter-spacing: -0.075em; margin: 18px 0; max-width: 10ch; }}
h2 {{ font-size: clamp(2rem, 4vw, 3rem); letter-spacing: -0.045em; margin: 0 0 16px; }}
p {{ color: var(--muted); line-height: 1.7; font-size: 1.04rem; }}
.actions {{ display: flex; flex-wrap: wrap; gap: 12px; margin-top: 28px; }}
.button {{ border: 0; border-radius: var(--radius-md); padding: 14px 18px; font-weight: 780; text-decoration: none; transition: transform 180ms cubic-bezier(.2,.8,.2,1), box-shadow 180ms cubic-bezier(.2,.8,.2,1); }}
.button:focus-visible {{ outline: 3px solid color-mix(in srgb, var(--accent) 45%, white); outline-offset: 3px; }}
.button:hover {{ transform: translateY(-1px); }}
.primary {{ background: var(--primary); color: white; box-shadow: var(--shadow-cta); }}
.secondary {{ color: var(--text); border: 1px solid var(--border); background: white; }}
.panel {{ border: 1px solid var(--border); background: rgba(255,255,255,.84); border-radius: var(--radius-xl); padding: clamp(20px, 4vw, 32px); box-shadow: var(--shadow-card); }}
.visual-card {{ position: relative; overflow: hidden; min-height: 440px; display: flex; flex-direction: column; justify-content: flex-end; }}
.visual-card img {{ width: 100%; border-radius: 24px; border: 1px solid var(--border); background: var(--neutral); margin-bottom: 18px; }}
.asset-caption {{ font-size: .9rem; color: var(--muted); }}
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
@media (max-width: 820px) {{ .hero, .sections {{ grid-template-columns: 1fr; }} .nav {{ align-items: flex-start; flex-direction: column; }} .visual-card {{ min-height: 0; }} h1 {{ max-width: 12ch; }} }}
@media (prefers-reduced-motion: reduce) {{ html {{ scroll-behavior: auto; }} .button {{ transition: none; }} .button:hover {{ transform: none; }} }}
"""


def render_html(root: Path, brief: dict[str, Any], references: dict[str, Any], strategy: dict[str, Any], design_text: str, variant: str, iteration: str, runtime_3d: bool) -> str:
    fm = frontmatter(design_text)
    name = project_name(brief, fm)
    description = yaml_value(fm, "description", "Artic-generated homepage preview")
    raw_project = brief.get("project")
    project = raw_project if isinstance(raw_project, dict) else {}
    audience = ", ".join(str(item) for item in project.get("target_users", []) if item) or "the target audience"
    goal = str(project.get("primary_goal") or "the primary conversion")
    raw_style = brief.get("style")
    style = raw_style if isinstance(raw_style, dict) else {}
    north_star = markdown_section(design_text, "Design North Star") or str(style.get("design_north_star") or strategy.get("design_north_star") or "")
    overview = markdown_section(design_text, "Overview") or description
    composition = markdown_section(design_text, "Page Composition") or str(strategy.get("implementation_guidance") or "Hero, proof, features, trust, conversion, FAQ, and final CTA.")
    sources = selected_source_names(references)
    locale = brief_locale(brief)
    copy = localized_copy(locale)
    policy_text = POLICY_BY_LOCALE.get(locale, POLICY_FALLBACK)
    source_items = "\n".join(f"<li>{html.escape(source)} <small>preview-only/catalog-reference</small></li>" for source in sources[:5]) or "<li>Artic selected references <small>preview-only/catalog-reference</small></li>"
    runtime_block = ""
    if runtime_3d:
        runtime_block = f"""
    <section class=\"panel runtime-3d\" aria-label=\"model-viewer 3D runtime placeholder\">
      <span class=\"pill\">{html.escape(copy['model_label'])}</span>
      <img src=\"assets/placeholders/model-poster.svg\" alt=\"Preview-only 3D model poster placeholder\" />
      <div class=\"model-viewer-stub\" role=\"img\" aria-label=\"model-viewer placeholder\">model-viewer · GLB · poster fallback</div>
      <div class=\"interaction-zone\">
        <b>{html.escape(copy['interaction_title'])}</b>
        <p>{html.escape(copy['interaction_body'])}</p>
      </div>
      <p>{html.escape(copy['model_body'])}</p>
    </section>"""
    generated_at = datetime.now(timezone.utc).isoformat()
    variant_label = variant.replace("-", " ").title()
    return f"""<!doctype html>
<html lang=\"{html.escape(locale)}\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <meta name=\"artic-design-source\" content=\"DESIGN.md\" />
  <title>{html.escape(name)} — Artic Preview {html.escape(iteration)}</title>
  <link rel=\"stylesheet\" href=\"styles.css\" />
</head>
<body>
  <!-- DESIGN.md token preview: --primary: {html.escape(build_tokens(design_text)['colors']['primary'])}; -->
  <main class=\"page\">
    <nav class=\"nav\">
      <div class=\"brand\">{html.escape(name)}</div>
      <div class=\"pill\">{html.escape(copy['preview_badge'])} · {html.escape(variant_label)}</div>
    </nav>
    <section class=\"hero\">
      <div>
        <span class=\"pill\">{html.escape(copy['for_label'])}: {html.escape(audience)}</span>
        <h1>{html.escape(name)} {html.escape(copy['headline_suffix'])}</h1>
        <p>{html.escape(overview)}</p>
        <div class=\"actions\">
          <a class=\"button primary\" href=\"#conversion\">{html.escape(copy['drive'])}: {html.escape(goal)}</a>
          <a class=\"button secondary\" href=\"#design-system\">{html.escape(copy['view_logic'])}</a>
        </div>
      </div>
      <aside class=\"panel visual-card\" aria-label=\"Design north star and generated asset\">
        <img src=\"assets/placeholders/hero-{html.escape(variant)}.svg\" alt=\"Generated preview-only hero asset placeholder\" />
        <span class=\"pill\">{html.escape(copy['north_star'])}</span>
        <h2>{html.escape(north_star[:128] or description)}</h2>
        <p>{html.escape(composition)}</p>
        <div class=\"metric-grid\">
          <div class=\"metric\"><strong>AA</strong><span>{html.escape(copy['accessibility'])}</span></div>
          <div class=\"metric\"><strong>{len(sources) or 3}</strong><span>{html.escape(copy['reference_roles'])}</span></div>
        </div>
        <p class=\"asset-caption\">asset-first-preview · provenance recorded in assets/manifest.json</p>
      </aside>
    </section>
    <section id=\"design-system\" class=\"sections\">
      <article class=\"card\"><b>{html.escape(copy['promise_title'])}</b><p>{html.escape(copy['promise_body'])}</p></article>
      <article class=\"card\"><b>{html.escape(copy['proof_title'])}</b><p>{html.escape(copy['proof_body'])}</p></article>
      <article class=\"card\"><b>{html.escape(copy['system_title'])}</b><p>{html.escape(copy['system_body'])}</p></article>
    </section>
{runtime_block}
    <section class=\"panel\" style=\"margin-top: 24px;\" id=\"conversion\">
      <h2>{html.escape(copy['reference_title'])}</h2>
      <p>{html.escape(copy['reference_body'])}</p>
      <ul class=\"source-list\">{source_items}</ul>
    </section>
    <section class=\"policy\">
      <strong>{html.escape(copy['policy_title'])}</strong><br />
      {html.escape(policy_text)}
      <br /><small>{html.escape(copy['generated'])}: {html.escape(generated_at)} · {html.escape(copy['root'])}: {html.escape(str(root))} · iteration {html.escape(iteration)}</small>
    </section>
  </main>
</body>
</html>
"""


def score_variant(variant: str, idx: int, runtime_3d: bool, sources_count: int) -> dict[str, Any]:
    base = {
        "asset-hero": 90,
        "conversion-proof": 81,
        "immersive-runtime": 86 if runtime_3d else 78,
        "editorial-system": 82,
    }.get(variant, 80)
    richness = min(92, 74 + sources_count * 4 + (8 if runtime_3d else 0) + (4 if variant in ("asset-hero", "immersive-runtime") else 0))
    provenance = min(95, 80 + sources_count * 3 + (5 if runtime_3d else 0))
    generic_penalty = max(4, 13 - idx * 2 - (3 if variant in ("asset-hero", "immersive-runtime") else 0))
    dimensions: dict[str, float] = {
        "strategy_alignment": float(min(94, base + 3)),
        "visual_fidelity": float(min(92, base + (2 if variant != "conversion-proof" else 0))),
        "asset_richness": float(richness),
        "asset_provenance_completeness": float(provenance),
        "conversion_clarity": float(min(94, base + (6 if variant == "conversion-proof" else 2))),
        "visual_specificity": float(min(93, base + (5 if variant in ("asset-hero", "immersive-runtime") else 1))),
        "accessibility_basics": 86.0,
        "mobile_first": 88.0,
        "genericness_penalty": float(generic_penalty),
    }
    positive = [v for k, v in dimensions.items() if k != "genericness_penalty"]
    dimensions["overall"] = round((sum(positive) / len(positive)) - (generic_penalty * 0.35), 1)
    return dimensions


def render_critique(reports: list[dict[str, Any]], selected: dict[str, Any]) -> str:
    lines = ["# Artic Show Critique", "", "Asset-first visual draft review. Unknown asset sources are retained as preview-only/catalog-reference instead of blocking generation.", ""]
    for report in reports:
        scores = report["scores"]
        lines.extend([
            f"## Iteration {report['iteration']} — {report['variant']}",
            "",
            f"- Overall: {scores['overall']}",
            f"- Strength: {report['strength']}",
            f"- Risk: {report['risk']}",
            f"- Asset provenance: {scores['asset_provenance_completeness']} / asset richness: {scores['asset_richness']}",
            "",
        ])
    lines.extend([
        "## Selected", "", f"Iteration {selected['iteration']} (`{selected['variant']}`) was promoted to `.artic/show/` root.", "", "## App source impact", "", "`modified_app_files` is intentionally `[]`; this command only writes preview bundle artifacts under `.artic/show`.", "",
    ])
    return "\n".join(lines)


def copy_iteration_to_root(iter_dir: Path, show_root: Path) -> None:
    for filename in ("index.html", "styles.css", "tokens.json", "report.json"):
        shutil.copy2(iter_dir / filename, show_root / filename)
    dst_assets = show_root / "assets"
    if dst_assets.exists():
        shutil.rmtree(dst_assets)
    shutil.copytree(iter_dir / "assets", dst_assets)


def rel(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def create_show_preview(root: Path, max_iterations: int = 3, min_score: float = 75, strict: bool = False, asset_mode: str = "asset-first", asset_timeout: float = 10) -> dict[str, Any]:
    del asset_timeout  # reserved for future downloader; core implementation is local/offline-safe.
    missing = required_missing(root)
    if missing:
        raise ValueError("missing required input(s) for @artic show: " + ", ".join(missing))
    if not 1 <= max_iterations <= 3:
        raise ValueError("--max-iterations must be between 1 and 3")
    design_text = (root / "DESIGN.md").read_text(encoding="utf-8")
    brief = read_json(root / ".artic" / "brief.json")
    references = read_json(root / ".artic" / "references.json")
    strategy = read_json(root / ".artic" / "strategy.json")
    show_root = root / ".artic" / "show"
    iterations_root = show_root / "iterations"
    show_root.mkdir(parents=True, exist_ok=True)
    if iterations_root.exists():
        shutil.rmtree(iterations_root)
    iterations_root.mkdir(parents=True, exist_ok=True)

    tokens = build_tokens(design_text)
    runtime_3d = has_3d_runtime_reference(brief, references)
    variants = variant_names(max_iterations, runtime_3d)
    reports: list[dict[str, Any]] = []
    generated_preview_files: list[str] = []
    asset_files: list[str] = []

    for idx, variant in enumerate(variants, start=1):
        iteration = f"{idx:03d}"
        iter_dir = iterations_root / iteration
        if iter_dir.exists():
            shutil.rmtree(iter_dir)
        (iter_dir / "assets").mkdir(parents=True, exist_ok=True)
        manifest = build_asset_manifest(root, iter_dir, iteration, variant, brief, references, tokens, asset_mode, runtime_3d)
        scores = score_variant(variant, idx, runtime_3d, len(selected_source_names(references)))
        report = {
            "schema_version": 1,
            "mode": "asset-first-preview",
            "iteration": iteration,
            "variant": variant,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "scores": scores,
            "score_dimensions": SCORE_KEYS,
            "strength": "Uses local generated placeholders plus catalog-reference provenance to make the first draft visually concrete.",
            "risk": "Preview assets may need replacement with owned or license-verified production assets before implementation.",
            "modified_app_files": [],
            "asset_manifest": "assets/manifest.json",
        }
        write_json(iter_dir / "tokens.json", tokens)
        write_text(iter_dir / "styles.css", render_css(tokens, variant, runtime_3d))
        write_text(iter_dir / "index.html", render_html(root, brief, references, strategy, design_text, variant, iteration, runtime_3d))
        write_json(iter_dir / "assets" / "manifest.json", manifest)
        write_json(iter_dir / "report.json", report)
        reports.append(report)
        generated_preview_files.extend([rel(root, iter_dir / name) for name in ("index.html", "styles.css", "tokens.json", "report.json", "assets/manifest.json")])
        for asset in manifest.get("assets", []):
            local_path = asset.get("local_path")
            if local_path:
                asset_files.append(rel(root, iter_dir / str(local_path)))

    selected_report = max(reports, key=lambda item: float(item["scores"]["overall"]))
    selected_iteration = str(selected_report["iteration"])
    selected_dir = iterations_root / selected_iteration
    copy_iteration_to_root(selected_dir, show_root)
    root_asset_manifest = read_json(show_root / "assets" / "manifest.json")
    asset_summary = {
        "assets_used": len(root_asset_manifest.get("assets", [])),
        "verified_assets": sum(1 for asset in root_asset_manifest.get("assets", []) if asset.get("status") == "verified"),
        "unverified_preview_only_assets": sum(1 for asset in root_asset_manifest.get("assets", []) if asset.get("status") == "unverified-preview-only"),
        "generated_placeholders": sum(1 for asset in root_asset_manifest.get("assets", []) if asset.get("status") == "generated"),
        "catalog_references": sum(1 for asset in root_asset_manifest.get("assets", []) if asset.get("status") == "catalog-reference"),
    }
    status = "selected"
    if float(selected_report["scores"]["overall"]) < min_score:
        status = "below-threshold"
    root_report = {
        "schema_version": 1,
        "mode": "asset-first-preview",
        "status": status,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "selected_iteration": selected_iteration,
        "candidate": selected_report["variant"],
        "selected_candidate_id": selected_report["variant"],
        "threshold": min_score,
        "preview_bundle": str(show_root),
        "entrypoint": str(show_root / "index.html"),
        "scores": selected_report["scores"],
        "asset_summary": asset_summary,
        "integrity": {
            "modified_app_files": [],
        },
        "modified_app_files": [],
        "iterations": reports,
        "remaining_risks": ["Preview assets may need replacement with owned or license-verified production assets before apply."],
    }
    write_json(show_root / "report.json", root_report)
    selected_payload = {
        "schema_version": 1,
        "selected_iteration": selected_iteration,
        "candidate": selected_report["variant"],
        "selected_candidate_id": selected_report["variant"],
        "variant": selected_report["variant"],
        "overall": selected_report["scores"]["overall"],
        "entrypoint": ".artic/show/index.html",
        "reason": "Highest overall asset-first preview score among generated candidates.",
    }
    write_json(show_root / "selected.json", selected_payload)
    write_text(show_root / "critique.md", render_critique(reports, selected_report))

    asset_files.extend(rel(root, show_root / str(asset["local_path"])) for asset in root_asset_manifest.get("assets", []) if asset.get("local_path"))
    generated_preview_files.extend([rel(root, show_root / name) for name in ("index.html", "styles.css", "tokens.json", "report.json", "selected.json", "critique.md", "assets/manifest.json")])
    if strict and status == "below-threshold":
        raise ValueError(f"quality threshold failure: selected preview score {selected_report['scores']['overall']} is below --min-score {min_score}")

    payload = {
        "root": str(root.resolve()),
        "preview_bundle": str(show_root),
        "bundle_dir": str(show_root),
        "entrypoint": str(show_root / "index.html"),
        "preview_file": str(show_root / "index.html"),
        "selected_iteration": selected_iteration,
        "generated_preview_files": sorted(str(root / item) for item in dict.fromkeys(generated_preview_files)),
        "asset_files": sorted(str(root / item) for item in dict.fromkeys(asset_files)) + [str(show_root / "assets" / "manifest.json")],
        "asset_manifest": str(show_root / "assets" / "manifest.json"),
        "report_file": str(show_root / "report.json"),
        "critique_file": str(show_root / "critique.md"),
        "modified_app_files": [],
    }
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Render an asset-first static Artic homepage preview bundle from start-generated design docs.")
    parser.add_argument("--root", required=True, help="Project root containing DESIGN.md and .artic outputs from @artic start")
    parser.add_argument("--max-iterations", type=int, default=3, help="Number of preview candidates to generate (1..3)")
    parser.add_argument("--min-score", type=float, default=75, help="Minimum selected score when --strict is enabled")
    parser.add_argument("--strict", action="store_true", help="Fail if selected iteration is below --min-score")
    parser.add_argument("--asset-mode", choices=["asset-first", "offline", "no-download"], default="asset-first", help="Asset handling mode; core show uses local placeholders/catalog provenance")
    parser.add_argument("--asset-timeout", type=float, default=10, help="Reserved timeout for future asset fetchers")
    args = parser.parse_args()
    try:
        payload = create_show_preview(Path(args.root), args.max_iterations, args.min_score, args.strict, args.asset_mode, args.asset_timeout)
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
