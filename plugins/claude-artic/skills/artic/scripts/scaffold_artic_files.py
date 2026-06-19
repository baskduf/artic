#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from datetime import datetime, timezone
from pathlib import Path

POLICY = "Reference policy: extract reusable principles only; do not copy logos, trademarks, proprietary illustrations, or exact layouts."
POLICY_MARKER = "<!-- artic-policy: reference-safety-v1 -->"
POLICY_COPY_BY_LOCALE = {
    "en-US": POLICY,
    "ko-KR": "참고 정책: 재사용 가능한 원칙만 추출하고, 로고, 상표, 독점 일러스트, 정확한 레이아웃은 복사하지 않습니다.",
    "ja-JP": "参照ポリシー: 再利用可能な原則のみを抽出し、ロゴ、商標、独自イラスト、正確なレイアウトはコピーしません。",
    "zh-CN": "参考政策：仅提取可复用原则，不复制标志、商标、专有插画或精确布局。",
    "zh-TW": "參考政策：僅萃取可重用原則，不複製標誌、商標、專有插圖或精確版面。",
}
SUPPORTED_LANGUAGES = {
    "en-US": "English",
    "ko-KR": "Korean",
    "ja-JP": "Japanese",
    "zh-CN": "Simplified Chinese",
    "zh-TW": "Traditional Chinese (Taiwan)",
}


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def policy_block(locale: str) -> str:
    return f"{POLICY_MARKER}\n{POLICY_COPY_BY_LOCALE.get(locale, POLICY)}"


def language_contract(locale: str) -> dict:
    return {
        "locale": locale,
        "output_language": SUPPORTED_LANGUAGES.get(locale, locale),
        "tone": "clear, professional, product-focused",
        "preserve_terms": ["DESIGN.md", "AI-native", "Artic"],
        "bilingual_terms": False,
    }


def language_block(language: dict) -> str:
    locale = language.get("locale", "en-US")
    preserve = ", ".join(str(item) for item in language.get("preserve_terms", []))
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


def scaffold(root: Path, project_name: str, locale: str = "en-US") -> None:
    now = datetime.now(timezone.utc).isoformat()
    language = language_contract(locale)
    policy = policy_block(locale)
    language_info = language_block(language)
    north_star = f"{project_name} should feel clear, trustworthy, and ready for implementation before it feels decorative."
    intent = {
        "schema_version": 1,
        "mapper": "artic-internal-normalized-input-scaffold",
        "selected_preset": "clean-saas",
        "design_north_star": north_star,
        "catalog_query": "homepage clean-saas trust mobile-first wcag",
        "style_facets": ["b2b-saas", "trust", "mobile-first"],
        "search_facets": ["homepage", "clean-saas", "trust", "mobile-first", "wcag"],
        "avoid_facets": ["generic-saas"],
        "design_principles": ["clear-cta", "explicit-proof", "accessible-contrast"],
        "design_rules": {"layout": "Use a modular problem-proof-conversion flow.", "content": "Use concrete trust markers near CTAs."},
        "reference_roles": [
            {"role": "output_contract", "source_ids": ["google-design-md"], "selection_reason": "Keep generated DESIGN.md structured and machine-readable."},
            {"role": "homepage_patterns", "source_ids": ["voltagent-awesome-design-md"], "selection_reason": "Use compatible homepage and SaaS reference patterns."},
            {"role": "token_accessibility", "source_ids": ["material-design"], "selection_reason": "Preserve token and accessibility discipline."},
        ],
    }
    strategy = {
        "schema_version": 1,
        "created_by": "agent-assisted",
        "project_summary": f"{project_name} is a scaffolded homepage for early adopters and buyers, optimized for waitlist signup.",
        "design_north_star": north_star,
        "target_user_interpretation": "Visitors need a fast explanation, immediate proof, and a low-friction path to join the waitlist.",
        "conversion_strategy": "Use one primary waitlist CTA in the hero and final section, with proof and feature clarity reducing hesitation between them.",
        "reference_roles": [
            {"source_id": "google-design-md", "role": "output_contract", "why_selected": "Keep generated DESIGN.md structured and machine-readable.", "extract": ["tokens", "validation"], "avoid": ["generic prose only"]},
            {"source_id": "voltagent-awesome-design-md", "role": "homepage_patterns", "why_selected": "Use compatible homepage and SaaS reference patterns.", "extract": ["layout", "cta", "proof"], "avoid": ["exact layouts"]},
            {"source_id": "material-design", "role": "token_accessibility", "why_selected": "Preserve token and accessibility discipline.", "extract": ["tokens", "accessibility", "components"], "avoid": ["brand identity"]},
        ],
        "conflict_resolution": "When references disagree, prefer the project conversion goal, WCAG AA accessibility, and original visual identity over any single reference source.",
        "visual_system": "Clean SaaS hierarchy with role-based blue primary, restrained accent use, generous whitespace, clear typographic scale, and subtle surfaces.",
        "component_rules": "Buttons, cards, forms, proof strips, feature blocks, FAQ, and final CTA must use documented tokens and have one clear job per component.",
        "accessibility": "Target WCAG AA contrast, visible focus states, semantic controls, labeled forms, readable line lengths, and reduced decorative density on mobile.",
        "implementation_guidance": "Build a mobile-first hero, proof strip, feature sections, trust/comparison block, waitlist form, FAQ, and final CTA using DESIGN.md tokens.",
        "reference_policy": "artic-policy: reference-safety-v1",
        "forbidden_copy_elements": ["logos", "trademarks", "proprietary illustrations", "exact layouts", "source copywriting"],
    }
    brief = {
        "artic_version": "0.4.1",
        "project": {
            "name": project_name,
            "type": "homepage",
            "description": "Smoke-test project generated by Artic.",
            "target_users": ["early adopters", "buyers"],
            "primary_goal": "waitlist signup",
        },
        "style": {
            "desired_impression": ["trustworthy", "modern", "clear"],
            "selected_preset": "clean-saas",
            "design_north_star": north_star,
            "design_rules": intent["design_rules"],
            "likes": ["clear hierarchy", "premium whitespace"],
            "dislikes": ["generic gradients", "clutter"],
            "fixed_assets": {"colors": [], "fonts": [], "logo": None},
            "search_facets": ["homepage", "clean-saas", "trust", "mobile-first", "wcag"],
        },
        "references": [],
        "implementation": {"stack": "unspecified", "mobile_first": True, "accessibility": "WCAG AA"},
        "language": language,
        "copy_policy": "artic-policy: reference-safety-v1",
    }
    references = {
        "selected_sources": [
            {"id": "google-design-md", "reason": "output contract and validation", "extraction_targets": ["tokens", "validation"]},
            {"id": "voltagent-awesome-design-md", "reason": "homepage and SaaS style candidates", "extraction_targets": ["layout", "cta", "proof"]},
            {"id": "material-design", "reason": "token and accessibility discipline", "extraction_targets": ["tokens", "accessibility", "components"]},
        ],
        "role_assignments": [
            {**role, "selected_source_ids": [role["source_ids"][0]]} for role in intent["reference_roles"]
        ],
        "source_plan": [
            {"source_id": "google-design-md", "role": "output_contract", "extract": ["tokens", "validation"], "transform": "Use the structure as a machine-readable contract, not as visual style.", "avoid": ["generic prose only"]},
            {"source_id": "voltagent-awesome-design-md", "role": "homepage_patterns", "extract": ["layout", "cta", "proof"], "transform": "Translate reference patterns into original project-specific page rhythm.", "avoid": ["exact layouts"]},
            {"source_id": "material-design", "role": "token_accessibility", "extract": ["tokens", "accessibility", "components"], "transform": "Use token and accessibility discipline without copying Material identity.", "avoid": ["brand identity"]},
        ],
        "synthesis": "Clean SaaS hierarchy with token discipline and mobile-first accessibility.",
    }
    state = {"artic_version": "0.4.1", "last_generated_at": now, "status": "scaffolded", "language": language, "intent_path": ".artic/intent.json", "strategy_path": ".artic/strategy.json"}
    write(root / ".artic" / "intent.json", json.dumps(intent, indent=2, ensure_ascii=False) + "\n")
    write(root / ".artic" / "strategy.json", json.dumps(strategy, indent=2, ensure_ascii=False) + "\n")
    write(root / ".artic" / "brief.json", json.dumps(brief, indent=2, ensure_ascii=False) + "\n")
    write(root / ".artic" / "references.json", json.dumps(references, indent=2, ensure_ascii=False) + "\n")
    write(root / ".artic" / "state.json", json.dumps(state, indent=2, ensure_ascii=False) + "\n")
    write(root / "docs" / "artic-brief.md", f"# Artic Brief\n\nProject: {project_name}\nLanguage: {language['locale']} / {language['output_language']}\n\n{policy}\n")
    roles_md = "\n".join(
        f"- `{role['source_id']}` as **{role['role']}** — {role['why_selected']} Extract: {', '.join(role['extract'])}. Avoid: {', '.join(role['avoid'])}."
        for role in strategy["reference_roles"]
    )
    write(root / "docs" / "artic-strategy.md", f"# Artic Strategy: {project_name}\n\n{language_info}\n\n{policy}\n\n## Project Summary\n\n{strategy['project_summary']}\n\n## Design North Star\n\n{strategy['design_north_star']}\n\n## Target User Interpretation\n\n{strategy['target_user_interpretation']}\n\n## Conversion Strategy\n\n{strategy['conversion_strategy']}\n\n## Reference Roles\n\n{roles_md}\n\n## Conflict Resolution\n\n{strategy['conflict_resolution']}\n\n## Visual System\n\n{strategy['visual_system']}\n\n## Component Rules\n\n{strategy['component_rules']}\n\n## Accessibility\n\n{strategy['accessibility']}\n\n## Implementation Guidance\n\n{strategy['implementation_guidance']}\n\n## Forbidden Copy Elements\n\n- logos\n- trademarks\n- proprietary illustrations\n- exact layouts\n- source copywriting\n")
    design = f'''---
version: alpha
name: "{project_name}"
description: "Clean SaaS homepage design system generated by Artic."
colors:
  primary: "#1F4FD8"
  secondary: "#465064"
  accent: "#7C3AED"
  surface: "#FFFFFF"
  neutral: "#F6F8FB"
  text: "#111827"
  muted: "#6B7280"
  border: "#DDE3EA"
typography:
  h1:
    fontFamily: Inter
    fontSize: 4rem
    fontWeight: 760
    lineHeight: 1.05
    letterSpacing: "-0.04em"
  h2:
    fontFamily: Inter
    fontSize: 2.5rem
    fontWeight: 720
    lineHeight: 1.12
  h3:
    fontFamily: Inter
    fontSize: 1.5rem
    fontWeight: 680
    lineHeight: 1.25
  body-md:
    fontFamily: Inter
    fontSize: 1rem
    fontWeight: 400
    lineHeight: 1.65
  caption:
    fontFamily: Inter
    fontSize: 0.875rem
    fontWeight: 500
    lineHeight: 1.45
rounded:
  sm: 6px
  md: 12px
  lg: 20px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 40px
  section: 96px
components:
  button-primary:
    backgroundColor: "{{colors.primary}}"
    textColor: "#FFFFFF"
    rounded: "{{rounded.md}}"
    padding: 12px
  button-secondary:
    backgroundColor: "{{colors.secondary}}"
    textColor: "#FFFFFF"
    rounded: "{{rounded.md}}"
    padding: 12px
  accent-badge:
    backgroundColor: "{{colors.accent}}"
    textColor: "#FFFFFF"
    rounded: "{{rounded.sm}}"
    padding: "{{spacing.sm}}"
  card:
    backgroundColor: "{{colors.surface}}"
    textColor: "{{colors.text}}"
    rounded: "{{rounded.lg}}"
    padding: "{{spacing.lg}}"
  form-field:
    backgroundColor: "{{colors.surface}}"
    textColor: "{{colors.text}}"
    rounded: "{{rounded.md}}"
    padding: "{{spacing.sm}}"
  proof-strip:
    backgroundColor: "{{colors.neutral}}"
    textColor: "{{colors.muted}}"
    rounded: "{{rounded.lg}}"
    padding: "{{spacing.md}}"
  divider:
    backgroundColor: "{{colors.border}}"
    height: 1px
    width: 100%
  muted-panel:
    backgroundColor: "{{colors.neutral}}"
    textColor: "{{colors.muted}}"
    rounded: "{{rounded.md}}"
    padding: "{{spacing.md}}"
---

## Overview

Clean, trustworthy, mobile-first SaaS homepage direction.

{language_info}

## Design North Star

{north_star}

{policy}

## Colors

Use role-based colors and preserve contrast.

## Typography

Use clear hierarchy and readable body text.

## Layout

Use mobile-first sections and consistent spacing.

## Page Composition

Hero, proof, feature, trust, conversion, FAQ, and final CTA sections should answer one user question at a time.

## Visual Hierarchy

Primary CTA and promise must dominate; secondary actions remain quieter.

## Responsive Behavior

Mobile-first: stack sections, keep one primary CTA visible, and preserve readable line lengths.

## Elevation & Depth

Use subtle surfaces and restrained shadows.

## Shapes

Use the documented radius scale.

## Components

Buttons, cards, forms, proof sections, and final CTA blocks must use documented tokens.

## Motion

Use restrained motion only where it clarifies hierarchy or state.

## Accessibility

Target WCAG AA contrast, visible focus states, semantic controls, and labeled forms.

## Anti-Patterns

Avoid generic gradients, off-token colors, competing primary CTAs, centered long copy, and exact reference layouts.

## Do's and Don'ts

Do follow tokens and synthesis. Don't clone references.
'''
    write(root / "DESIGN.md", design)
    write(root / "docs" / "design-rules.md", f"# Design Rules\n\n{language_info}\n\n{policy}\n\n## Selected Reference Synthesis\n\nClean SaaS + Material token discipline.\n\n## Anti-Patterns\n\nAvoid generic gradients, off-token colors, and exact reference layouts.\n")
    write(root / "docs" / "design-qa-checklist.md", f"# Artic Design QA Checklist\n\n{language_info}\n\n{policy}\n\n## Scored Review\n\n- [ ] Visual hierarchy: 0-5\n- [ ] Brand coherence: 0-5\n- [ ] Conversion clarity: 0-5\n- [ ] Mobile quality: 0-5\n- [ ] Accessibility: 0-5\n- [ ] Reference safety: pass/fail\n\n## Binary Gates\n\n- [ ] Tokens are used consistently.\n- [ ] CTA hierarchy is clear.\n- [ ] Mobile layout works.\n")
    write(root / "docs" / "homepage-design-prompt.md", f"# Homepage Implementation Prompt\n\n{language_info}\n\nUse DESIGN.md and docs/design-rules.md.\n\n{policy}\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--project-name", default="Artic Smoke Project")
    parser.add_argument("--locale", default="en-US")
    args = parser.parse_args()
    scaffold(Path(args.root), args.project_name, args.locale)
    print(f"Scaffolded Artic files at {Path(args.root).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
