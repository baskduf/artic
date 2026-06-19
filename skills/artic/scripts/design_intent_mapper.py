#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from typing import Any

# LLM-first contract with a deterministic fallback implementation.
# Runtime hosts can replace the fallback with an LLM call as long as they emit
# this schema. CI keeps the deterministic path so tests stay reproducible.

FACET_RULES: tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...] = (
    ("premium-saas", ("premium", "luxury", "고급", "고급스럽", "세련", "polished", "stripe"), ("generous-whitespace", "restrained-motion", "subtle-depth")),
    ("developer-tool", ("developer", "devtool", "api", "sdk", "github", "linear", "개발자", "툴", "tool"), ("code-friendly", "sharp-hierarchy", "documentation-ready")),
    ("b2b-saas", ("b2b", "enterprise", "업무", "관리자", "기업", "saas"), ("trust", "clear-cta", "modular-sections")),
    ("trust", ("trust", "trusted", "신뢰", "믿음", "안정", "secure", "security"), ("calm-palette", "explicit-proof", "accessible-contrast")),
    ("playful-brand", ("playful", "fun", "cute", "귀엽", "장난", "친근", "friendly"), ("warm-accent", "rounded-shapes", "light-motion")),
    ("editorial-landing", ("editorial", "magazine", "story", "스토리", "콘텐츠", "글", "읽"), ("strong-type-scale", "longform-rhythm", "image-led-sections")),
    ("korean-startup", ("korean", "한국", "토스", "toss", "당근", "리멤버", "라인"), ("mobile-first", "friendly-trust", "clear-benefit-copy")),
    ("korean-fintech", ("토스", "toss", "금융", "핀테크", "본인인증", "인증", "결제", "송금"), ("low-friction-fintech", "plain-korean-copy", "trustworthy-feedback", "single-primary-action")),
    ("korean-social-onboarding", ("카카오", "kakao", "네이버", "naver", "간편로그인", "간편가입", "소셜로그인", "로그인"), ("friendly-social-onboarding", "provider-identity-clarity", "low-barrier-entry")),
    ("korean-mobile-native", ("한국 앱", "한국앱", "한국 서비스", "한국어", "국내", "모바일앱"), ("pretendard-typography", "thumb-friendly-cta", "local-auth-payment-expectations", "polite-plain-korean")),
    ("ai-product", ("ai", "llm", "agent", "에이아이", "인공지능", "자동화"), ("abstract-visuals", "capability-led-sections", "responsible-ai-copy")),
    ("mobile-first", ("mobile", "모바일", "앱", "app", "ios", "android"), ("thumb-friendly", "single-column-first", "compact-navigation")),
    ("minimal", ("minimal", "simple", "clean", "미니멀", "깔끔", "단순"), ("limited-palette", "low-ornament", "clear-spacing")),
)

AVOID_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("heavy-corporate", ("too corporate", "corporate", "딱딱", "기업스럽", "boring", "지루")),
    ("playful-toy", ("too playful", "too cute", "장난스럽", "유치", "toy")),
    ("flashy-neon", ("neon", "flashy", "과한", "번쩍", "cyberpunk")),
    ("busy-layout", ("busy", "복잡", "clutter", "정보 과다")),
    ("cold-minimal", ("cold", "차갑", "무미건조")),
    ("brand-clone", ("토스", "toss", "카카오", "kakao", "네이버", "naver", "카카오뱅크", "kakaobank", "배민", "baemin")),
)

PRESET_PRIORITY = (
    ("developer-tool", "developer-tool"),
    ("premium-saas", "clean-saas"),
    ("b2b-saas", "clean-saas"),
    ("korean-startup", "korean-startup"),
    ("playful-brand", "playful-brand"),
    ("editorial-landing", "editorial-landing"),
    ("ai-product", "ai-product"),
    ("minimal", "luxury-minimal"),
)

RULE_LIBRARY: dict[str, dict[str, str]] = {
    "premium-saas": {
        "color": "Neutral base, one confident accent, avoid noisy gradients.",
        "spacing": "Generous whitespace with fewer competing sections.",
        "motion": "Slow, subtle, functional transitions only.",
    },
    "developer-tool": {
        "typography": "High information clarity, code-friendly labels, strong hierarchy.",
        "components": "Documentation-ready cards, command snippets, precise states.",
    },
    "b2b-saas": {
        "layout": "Modular problem-solution-proof flow with obvious CTA hierarchy.",
        "content": "Outcome-led copy with concrete trust markers.",
    },
    "trust": {
        "color": "Calm palette with accessible contrast and stable neutrals.",
        "components": "Use proof blocks, metrics, badges, and transparent states.",
    },
    "playful-brand": {
        "shape": "Softer radius, warm accents, friendly illustration rhythm.",
        "motion": "Light delight, never blocking comprehension.",
    },
    "editorial-landing": {
        "typography": "Editorial scale contrast with readable longform rhythm.",
        "layout": "Narrative sections and image-led pacing.",
    },
    "korean-startup": {
        "content": "Plain benefit-first copy, fast comprehension, mobile-first trust cues.",
        "components": "Compact cards, friendly empty states, clear app-like actions.",
    },
    "ai-product": {
        "visuals": "Abstract capability visuals; avoid fake dashboards that overpromise.",
        "content": "Explain automation boundaries and user control clearly.",
    },
    "mobile-first": {
        "layout": "Single-column first, thumb-friendly CTA placement, short sections.",
        "components": "Large tap targets and compact navigation.",
    },
    "korean-fintech": {
        "content": "Use plain Korean copy, explicit next actions, and reassuring feedback around sensitive financial or identity steps.",
        "layout": "Keep one dominant action per step, with clear confirmation, retry, and recovery states.",
    },
    "korean-social-onboarding": {
        "components": "Treat Kakao, Naver, and other provider buttons as official provider actions with equal sizing and clear labels, not as decorative brand styles.",
        "content": "Separate login, signup, consent, and account-linking intent in the surrounding copy.",
    },
    "korean-mobile-native": {
        "typography": "Prefer Hangul-readable UI typography such as Pretendard/system Korean sans with relaxed line-height and label spacing.",
        "components": "Use familiar Korean mobile patterns such as thumb-friendly CTAs, bottom sheets, compact lists, and local auth/payment expectations.",
    },
    "minimal": {
        "color": "Limited palette and restrained surfaces.",
        "layout": "Clear spacing rhythm; remove ornamental sections.",
    },
}

TOKEN_RE = re.compile(r"[\w가-힣]+", re.UNICODE)


def normalize_text(value: str) -> str:
    return value.strip().lower()


def contains_any(text: str, needles: tuple[str, ...]) -> bool:
    lowered = normalize_text(text)
    return any(needle.lower() in lowered for needle in needles)


def add_unique(target: list[str], values: list[str] | tuple[str, ...]) -> None:
    for value in values:
        if value and value not in target:
            target.append(value)


def infer_preset(facets: list[str]) -> str:
    for facet, preset in PRESET_PRIORITY:
        if facet in facets:
            return preset
    return "clean-saas"


def infer_design_rules(facets: list[str], avoid_facets: list[str]) -> dict[str, str]:
    rules: dict[str, str] = {}
    for facet in facets:
        for key, value in RULE_LIBRARY.get(facet, {}).items():
            rules.setdefault(key, value)
    if "heavy-corporate" in avoid_facets:
        rules.setdefault("tone", "Credible but human; avoid institutional stock-photo stiffness.")
    if "playful-toy" in avoid_facets:
        rules.setdefault("tone", "Friendly but not toy-like; keep trust and conversion clarity first.")
    if "flashy-neon" in avoid_facets:
        rules.setdefault("color", "Avoid neon/cyberpunk effects; use controlled accent contrast.")
    return rules


def design_north_star(project: str, audience: str, goal: str, facets: list[str]) -> str:
    product = project or "this homepage"
    users = audience or "the target users"
    outcome = goal or "the primary conversion goal"
    if "ai-product" in facets and "trust" in facets:
        return f"{product} should feel like a calm, trustworthy assistant that helps {users} reach {outcome} without AI hype or visual noise."
    if "developer-tool" in facets:
        return f"{product} should feel precise, documentation-ready, and useful before it feels decorative, helping {users} reach {outcome} quickly."
    if "premium-saas" in facets:
        return f"{product} should feel polished and restrained, using confidence and clarity to move {users} toward {outcome}."
    return f"{product} should turn the user's intent into a clear, trustworthy homepage direction for {users}, with every visual choice supporting {outcome}."


def reference_roles(facets: list[str], stack: str) -> list[dict[str, Any]]:
    roles: list[dict[str, Any]] = [
        {
            "role": "trust_and_conversion",
            "source_ids": ["shopify-polaris", "wcag-quickref", "w3c-wai-designing-accessibility"],
            "selection_reason": "Use trust cues, validation behavior, and accessibility guardrails around conversion moments.",
        },
        {
            "role": "component_restraint",
            "source_ids": ["shadcn-ui", "radix-ui-primitives", "base-ui", "react-aria"],
            "selection_reason": "Use quiet, composable primitives instead of decorative one-off UI.",
        },
        {
            "role": "token_discipline",
            "source_ids": ["tailwind-css", "open-props", "dtcg-design-tokens", "style-dictionary"],
            "selection_reason": "Translate design intent into reusable color, spacing, radius, and typography tokens.",
        },
    ]
    if "mobile-first" in facets:
        roles.append({
            "role": "mobile_confidence",
            "source_ids": ["apple-hig", "meliwat-awesome-ios-design-md", "material-design"],
            "selection_reason": "Preserve mobile-first hierarchy, thumb-friendly actions, and restrained motion.",
        })
    if any(facet in facets for facet in ("korean-startup", "korean-fintech", "korean-social-onboarding", "korean-mobile-native")):
        roles.append({
            "role": "korean_market_fit",
            "source_ids": ["krds-korea-design-system", "line-design-system", "daangn-seed-design", "pretendard-typeface", "kwcag-22-korean-web-accessibility"],
            "selection_reason": "Map Korean market language into mobile-native typography, local trust cues, social-login clarity, and accessibility without copying protected brand assets.",
        })
    if "developer-tool" in facets or "react" in stack.lower() or "tailwind" in stack.lower():
        roles.append({
            "role": "implementation_clarity",
            "source_ids": ["github-primer", "atlassian-design-system", "shadcn-ui", "tailwind-css"],
            "selection_reason": "Keep the generated rules practical for implementation in the project's UI stack.",
        })
    return roles


def map_design_intent(
    *,
    project: str = "",
    audience: str = "",
    goal: str = "",
    vibe: str = "",
    references: str = "",
    avoid: str = "",
    stack: str = "",
) -> dict[str, Any]:
    combined = " ".join(part for part in [project, audience, goal, vibe, references, stack] if part)
    avoid_text = " ".join(part for part in [avoid, vibe] if part)
    style_facets: list[str] = []
    search_facets: list[str] = ["homepage"]
    design_principles: list[str] = []
    avoid_facets: list[str] = []

    for facet, triggers, principles in FACET_RULES:
        if contains_any(combined, triggers):
            add_unique(style_facets, (facet,))
            add_unique(search_facets, (facet,))
            add_unique(design_principles, principles)

    for facet, triggers in AVOID_RULES:
        if contains_any(avoid_text, triggers):
            add_unique(avoid_facets, (facet,))

    if contains_any(combined, ("토스", "toss", "카카오", "kakao", "네이버", "naver", "카카오뱅크", "kakaobank", "배민", "baemin")):
        add_unique(avoid_facets, ("brand-clone",))

    if "trust" not in style_facets and contains_any(goal + " " + audience, ("signup", "sales", "구매", "전환", "conversion")):
        add_unique(style_facets, ("trust",))
        add_unique(search_facets, ("trust",))
        add_unique(design_principles, ("clear-cta", "explicit-proof"))

    if "mobile-first" not in style_facets and contains_any(vibe + " " + stack, ("mobile", "모바일", "app")):
        add_unique(style_facets, ("mobile-first",))
        add_unique(search_facets, ("mobile-first",))

    if len(search_facets) < 3:
        add_unique(search_facets, ("clean-saas", "trust"))

    selected_preset = infer_preset(style_facets)
    query = " ".join(search_facets + design_principles)
    north_star = design_north_star(project, audience, goal, style_facets)
    return {
        "schema_version": 1,
        "mapper": "artic-llm-first-contract-deterministic-fallback",
        "selected_preset": selected_preset,
        "project_archetype": "-".join(style_facets[:3]) or "homepage",
        "audience_context": audience,
        "conversion_goal": goal,
        "emotional_target": design_principles[:6],
        "style_facets": style_facets,
        "search_facets": search_facets,
        "avoid_facets": avoid_facets,
        "design_principles": design_principles,
        "design_rules": infer_design_rules(style_facets, avoid_facets),
        "design_north_star": north_star,
        "reference_roles": reference_roles(style_facets, stack),
        "reference_hints": [ref.strip() for ref in re.split(r"[,\n]", references) if ref.strip()],
        "catalog_query": query,
        "llm_contract": {
            "role": "Map user language to this schema, not to final pass/fail scoring.",
            "must_preserve": ["style_facets", "avoid_facets", "design_rules", "catalog_query"],
            "must_not": ["copy protected brand assets", "choose exact layouts as clone targets", "turn Korean brand names into required colors, logos, copy, or product flows"],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize user design language into Artic search facets and design rules.")
    parser.add_argument("--project", default="")
    parser.add_argument("--audience", default="")
    parser.add_argument("--goal", default="")
    parser.add_argument("--vibe", default="")
    parser.add_argument("--references", default="")
    parser.add_argument("--avoid", default="")
    parser.add_argument("--stack", default="")
    args = parser.parse_args()
    payload = map_design_intent(
        project=args.project,
        audience=args.audience,
        goal=args.goal,
        vibe=args.vibe,
        references=args.references,
        avoid=args.avoid,
        stack=args.stack,
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
