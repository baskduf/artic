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
    source_items = "\n".join(f"<li>{html.escape(source)}</li>" for source in sources[:5]) or "<li>Artic selected references</li>"

    generated_at = datetime.now(timezone.utc).isoformat()
    return f"""<!doctype html>
<html lang="en">
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
    .policy {{ margin-top: 56px; padding: 18px; border-left: 4px solid var(--accent); background: white; border-radius: 16px; color: var(--muted); }}
    @media (max-width: 820px) {{ .hero, .sections {{ grid-template-columns: 1fr; }} .nav {{ align-items: flex-start; flex-direction: column; }} }}
  </style>
</head>
<body>
  <main class="page">
    <nav class="nav">
      <div class="brand">{html.escape(name)}</div>
      <div class="pill">Artic Preview · generated from DESIGN.md</div>
    </nav>
    <section class="hero">
      <div>
        <span class="pill">For {html.escape(audience)}</span>
        <h1>{html.escape(name)} homepage direction</h1>
        <p>{html.escape(overview)}</p>
        <div class="actions">
          <a class="button primary" href="#conversion">Drive {html.escape(goal)}</a>
          <a class="button secondary" href="#design-system">View design logic</a>
        </div>
      </div>
      <aside class="panel" aria-label="Design north star">
        <span class="pill">Design north star</span>
        <h2>{html.escape(north_star[:110] or description)}</h2>
        <p>{html.escape(composition)}</p>
        <div class="metric-grid">
          <div class="metric"><strong>AA</strong><span>accessibility target</span></div>
          <div class="metric"><strong>{len(sources) or 3}</strong><span>reference roles</span></div>
        </div>
      </aside>
    </section>
    <section id="design-system" class="sections">
      <article class="card"><b>1. Promise</b><p>Lead with one clear project-specific promise and one dominant conversion path.</p></article>
      <article class="card"><b>2. Proof</b><p>Place evidence close to the hero so trust supports the first CTA.</p></article>
      <article class="card"><b>3. System</b><p>Use tokens, spacing rhythm, semantic controls, and original composition from the Artic docs.</p></article>
    </section>
    <section class="panel" style="margin-top: 24px;" id="conversion">
      <h2>Reference-informed, not reference-copied</h2>
      <p>This static preview is generated from Artic start outputs. It intentionally writes only .artic/show/index.html and leaves app source files untouched.</p>
      <ul class="source-list">{source_items}</ul>
    </section>
    <section class="policy">
      <strong>Reference policy</strong><br />
      {html.escape(POLICY_FALLBACK)}
      <br /><small>Generated: {html.escape(generated_at)} · Root: {html.escape(str(root))}</small>
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
