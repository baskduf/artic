#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from design_intent_mapper import map_design_intent
from risk_readiness import analyze_risk_readiness
from search_reference_catalog import load_catalog, search, terms

POLICY_MARKER = "<!-- artic-policy: reference-safety-v1 -->"
POLICY_COPY = "Reference policy: extract reusable principles only; do not copy logos, trademarks, proprietary illustrations, or exact layouts."
POLICY_COPY_BY_LOCALE = {
    "en-US": POLICY_COPY,
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
DEFAULT_PRESERVE_TERMS = ["DESIGN.md", "AI-native", "Artic"]


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def infer_preset(vibe: str) -> str:
    lowered = vibe.lower()
    if "developer" in lowered or "docs" in lowered or "tailwind" in lowered:
        return "developer-tool"
    if "enterprise" in lowered or "dashboard" in lowered:
        return "enterprise-saas"
    if "mobile" in lowered or "ios" in lowered or "app" in lowered:
        return "korean-startup" if "korean" in lowered or "한국" in vibe else "clean-saas"
    if "premium" in lowered or "luxury" in lowered:
        return "luxury-minimal"
    if "playful" in lowered:
        return "playful-brand"
    return "clean-saas"


def normalize_facets(*parts: str) -> list[str]:
    facets: list[str] = []
    seen: set[str] = set()
    for part in parts:
        for token in sorted(terms(part)):
            if token not in seen:
                facets.append(token)
                seen.add(token)
    return facets


def language_contract(locale: str, tone: str, preserve_terms: list[str], bilingual_terms: bool) -> dict:
    output_language = SUPPORTED_LANGUAGES.get(locale, locale)
    terms_to_preserve = preserve_terms or DEFAULT_PRESERVE_TERMS
    return {
        "locale": locale,
        "output_language": output_language,
        "tone": tone,
        "preserve_terms": terms_to_preserve,
        "bilingual_terms": bilingual_terms,
    }


def make_query(project: str, audience: str, goal: str, vibe: str, references: str, stack: str) -> str:
    return " ".join(part for part in [project, audience, goal, vibe, references, stack] if part).strip()


def parse_key_values(values: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for item in values or []:
        text = str(item).strip()
        if not text:
            continue
        if "=" in text:
            key, value = text.split("=", 1)
        else:
            key, value = f"item_{len(parsed) + 1}", text
        key = key.strip()
        value = value.strip()
        if key and value:
            parsed[key] = value
    return parsed


def normalize_project(project: str) -> dict:
    description = project.strip()
    name = description
    lowered = description.lower()
    if ("3d" in lowered or "3D" in description) and "석고상" in description:
        name = "3D 석고상"
    elif len(description) > 48 or len(description.split()) > 6:
        name = " ".join(description.split()[:6]).strip()
        if len(name) > 36:
            name = name[:36].rstrip()
    return {"name": name or "Artic Project", "description": description or "Project-specific Artic homepage design system."}


def asset_policy_payload(asset_policy: str) -> dict:
    text = asset_policy.strip()
    lowered = text.lower()
    denial_phrases = (
        "do not allow",
        "don't allow",
        "not allow",
        "not allowed",
        "disallow",
        "forbid",
        "forbidden",
        "references only",
        "reference principles only",
        "principles only",
        "허용하지",
        "허용 안",
        "사용하지",
        "쓰지",
        "원칙 참고로만",
        "참고로만",
    )
    affirmative_tokens = ("허용", "allow", "allowed", "cc0", "cc-by", "public", "공개", "소유")
    denied = bool(text) and any(phrase in lowered or phrase in text for phrase in denial_phrases)
    allowed = bool(text) and not denied and any(token in lowered or token in text for token in affirmative_tokens)
    mode = "licensed-public-assets-allowed" if allowed else "reference-principles-only"
    if not text:
        text = "External references are principles/patterns only unless the user explicitly allows owned or clearly licensed public assets."
    return {
        "mode": mode,
        "user_answer": text,
        "reference_boundary": "External references inform reusable principles, interaction patterns, runtime constraints, and accessibility guidance; they are not copied as assets.",
        "asset_boundary": "External GLB/images/models may be used only when user-owned or license-verifiable public assets are allowed; record source URL, license, and attribution in docs.",
        "allowed_licenses": ["CC0", "CC-BY", "MIT", "Apache-2.0", "public-domain"],
    }


def query_from_intent(intent: dict) -> str:
    catalog_query = str(intent.get("catalog_query") or "").strip()
    if catalog_query:
        return catalog_query
    parts: list[str] = []
    for key in ("search_facets", "style_facets", "design_principles"):
        value = intent.get(key)
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, list):
            parts.extend(str(item) for item in value)
    return " ".join(part for part in parts if part).strip()


def select_role_grounded_sources(intent: dict, catalog_path: Path, limit: int) -> tuple[list[dict], list[dict]]:
    query = query_from_intent(intent)
    scored = search(query, catalog_path, max(limit, len(load_catalog(catalog_path))))
    by_id = {row["id"]: row for row in scored}
    selected: list[dict] = []
    seen: set[str] = set()
    role_assignments: list[dict] = []

    for role in intent.get("reference_roles", []):
        if not isinstance(role, dict):
            continue
        picked: list[str] = []
        for source_id in role.get("source_ids", []):
            row = by_id.get(source_id)
            if row and row["id"] not in seen:
                selected.append(row)
                seen.add(row["id"])
                picked.append(row["id"])
                break
        if picked:
            role_assignments.append({**role, "selected_source_ids": picked})

    for row in scored:
        if len(selected) >= limit:
            break
        if row["id"] not in seen:
            selected.append(row)
            seen.add(row["id"])

    selected = selected[:limit]
    selected_ids = {row["id"] for row in selected}
    role_assignments = [
        {**role, "selected_source_ids": [source_id for source_id in role.get("selected_source_ids", []) if source_id in selected_ids]}
        for role in role_assignments
        if any(source_id in selected_ids for source_id in role.get("selected_source_ids", []))
    ]
    return selected, role_assignments


def role_for_source(source_id: str, role_assignments: list[dict]) -> str:
    for role in role_assignments:
        if source_id in role.get("selected_source_ids", []):
            return str(role.get("role") or "supporting_reference")
    return "supporting_reference"


def selected_source_payload(row: dict) -> dict:
    reason_parts = []
    for key in ("product_fit", "strengths", "use_for"):
        values = row.get(key, [])
        if values:
            reason_parts.append(str(values[0]))
    return {
        "id": row["id"],
        "name": row["name"],
        "score": row["score"],
        "reason": "; ".join(reason_parts) or row.get("type", "reference source"),
        "extraction_targets": row.get("extraction_targets", row.get("use_for", [])),
        "url": row.get("url"),
        "license": row.get("license", "unknown"),
    }


def create_init_outputs(root: Path, args: argparse.Namespace) -> dict:
    if args.limit < 3:
        raise ValueError("limit must be >= 3 for Artic reference selection")
    now = datetime.now(timezone.utc).isoformat()
    lang = language_contract(args.locale, args.tone, args.preserve_term, args.bilingual_terms)
    catalog_path = Path(args.catalog)
    intent = map_design_intent(
        project=args.project,
        audience=args.audience,
        goal=args.goal,
        vibe=args.vibe,
        references=args.references,
        stack=args.stack,
    )
    query = query_from_intent(intent) or make_query(args.project, args.audience, args.goal, args.vibe, args.references, args.stack)
    rows, role_assignments = select_role_grounded_sources(intent, catalog_path, args.limit)
    selected_sources = [selected_source_payload(row) for row in rows]
    facets = list(intent.get("search_facets") or normalize_facets(args.project, args.audience, args.goal, args.vibe, args.references, args.stack))
    normalized_project = normalize_project(args.project)
    requirements = parse_key_values(getattr(args, "requirement", []))
    constraints = parse_key_values(getattr(args, "constraint", []))
    policy = asset_policy_payload(str(getattr(args, "asset_policy", "")))
    risk_answers = {
        "project": args.project,
        "audience": args.audience,
        "goal": args.goal,
        "vibe": args.vibe,
        "references": args.references,
        "stack": args.stack,
        "accessibility": args.accessibility,
        "asset_policy": str(getattr(args, "asset_policy", "")),
        **requirements,
        **constraints,
    }
    risk_answers["locale"] = args.locale
    if risk_answers.get("stack") and not risk_answers.get("technical_runtime"):
        risk_answers["technical_runtime"] = risk_answers["stack"]
    elif not risk_answers.get("technical_runtime"):
        vibe_text = str(risk_answers.get("vibe") or "")
        if re.search(r"runtime|런타임|webgl|model-viewer|3d", vibe_text, re.IGNORECASE):
            risk_answers["technical_runtime"] = vibe_text
    if risk_answers.get("asset_policy") and not risk_answers.get("license_clearance"):
        risk_answers["license_clearance"] = risk_answers["asset_policy"]
    interaction_answer = str(risk_answers.get("interaction_model") or "")
    if interaction_answer and not risk_answers.get("performance_accessibility_plan"):
        if re.search(r"reduced motion|reduced-motion|keyboard|키보드|대체|fallback|alt|접근성|성능|load|loading", interaction_answer, re.IGNORECASE):
            risk_answers["performance_accessibility_plan"] = interaction_answer
    risk_readiness = analyze_risk_readiness(risk_answers, intent)
    source_plan = [
        {
            "source_id": src["id"],
            "role": role_for_source(src["id"], role_assignments),
            "extract": src.get("extraction_targets", []),
            "transform": f"Translate {src['name']} into project-specific rules for {args.project}; keep the final layout, copy, and visual identity original.",
            "avoid": src.get("avoid_when", []) or ["exact layouts", "brand identity", "source copywriting"],
        }
        for src in selected_sources
    ]

    brief = {
        "artic_version": "0.4.0",
        "project": {
            "name": normalized_project["name"],
            "type": "homepage",
            "description": normalized_project["description"],
            "target_users": [args.audience],
            "primary_goal": args.goal,
        },
        "style": {
            "desired_impression": [item.strip() for item in args.vibe.replace(",", " ").split() if item.strip()],
            "selected_preset": intent.get("selected_preset") or infer_preset(args.vibe),
            "design_north_star": intent.get("design_north_star", ""),
            "design_rules": intent.get("design_rules", {}),
            "likes": [],
            "dislikes": [],
            "fixed_assets": {"colors": [], "fonts": [], "logo": None},
            "search_facets": facets,
        },
        "references": [ref.strip() for ref in args.references.split(",") if ref.strip()],
        "requirements": requirements,
        "constraints": constraints,
        "asset_policy": policy,
        "implementation": {"stack": args.stack or "unspecified", "mobile_first": "mobile" in args.vibe.lower(), "accessibility": args.accessibility},
        "risk_readiness": risk_readiness,
        "language": lang,
        "copy_policy": "artic-policy: reference-safety-v1",
    }
    references = {
        "query": query,
        "selected_sources": selected_sources,
        "role_assignments": role_assignments,
        "source_plan": source_plan,
        "synthesis": "Use selected sources as compatible patterns; localize prose according to the brief language contract while preserving source names and protected terms.",
    }
    state = {"artic_version": "0.4.0", "last_generated_at": now, "status": "initialized", "language": lang, "intent_path": ".artic/intent.json"}

    write(root / ".artic" / "intent.json", json.dumps(intent, indent=2, ensure_ascii=False) + "\n")
    write(root / ".artic" / "brief.json", json.dumps(brief, indent=2, ensure_ascii=False) + "\n")
    write(root / ".artic" / "references.json", json.dumps(references, indent=2, ensure_ascii=False) + "\n")
    write(root / ".artic" / "state.json", json.dumps(state, indent=2, ensure_ascii=False) + "\n")

    candidate_lines = "\n".join(
        f"- {src['name']} (`{src['id']}`), score {src['score']}: {src['reason']}" for src in selected_sources
    )
    preserved = ", ".join(lang["preserve_terms"])
    policy_copy = POLICY_COPY_BY_LOCALE.get(lang["locale"], POLICY_COPY)
    if lang["locale"].startswith("ko"):
        custom_lines = ["## 보존된 요구사항/제약", ""]
        for key, value in requirements.items():
            custom_lines.append(f"- 요구사항 `{key}`: {value}")
        for key, value in constraints.items():
            custom_lines.append(f"- 제약 `{key}`: {value}")
        if len(custom_lines) == 2:
            custom_lines.append("- 없음")
        asset_lines = [
            "## 에셋 사용 정책",
            "",
            f"- 모드: {policy['mode']}",
            f"- 사용자 답변: {policy['user_answer']}",
            "- 외부 레퍼런스는 원칙/패턴 참고용입니다. 레이아웃, 상호작용 원칙, 접근성/성능 제약만 추출합니다.",
            "- 외부 에셋은 사용자가 허용한 경우에만 소유 에셋 또는 CC0/CC-BY 등 라이선스 확인 가능한 공개 에셋을 사용하고 출처/라이선스를 문서에 남깁니다.",
        ]
        brief_doc = f"""# Artic Brief

프로젝트명: {normalized_project['name']}
설명: {normalized_project['description']}
타깃: {args.audience}
주요 목표: {args.goal}
무드: {args.vibe}
스택: {args.stack or 'unspecified'}
언어: {lang['locale']} / {lang['output_language']}
톤: {lang['tone']}
보존 용어: {preserved}

## Design north star

{intent.get('design_north_star', '')}

## Reference candidates

{candidate_lines}

{chr(10).join(custom_lines)}

{chr(10).join(asset_lines)}

{POLICY_MARKER}
{policy_copy}
"""
    else:
        custom_lines = ["## Preserved Requirements / Constraints", ""]
        for key, value in requirements.items():
            custom_lines.append(f"- Requirement `{key}`: {value}")
        for key, value in constraints.items():
            custom_lines.append(f"- Constraint `{key}`: {value}")
        if len(custom_lines) == 2:
            custom_lines.append("- None")
        brief_doc = f"""# Artic Brief

Project: {normalized_project['name']}
Description: {normalized_project['description']}
Audience: {args.audience}
Primary goal: {args.goal}
Vibe: {args.vibe}
Stack: {args.stack or 'unspecified'}
Language: {lang['locale']} / {lang['output_language']}
Tone: {lang['tone']}
Preserve terms: {preserved}

## Design north star

{intent.get('design_north_star', '')}

## Reference candidates

{candidate_lines}

{chr(10).join(custom_lines)}

## Asset usage policy

- Mode: {policy['mode']}
- User answer: {policy['user_answer']}
- External references are principle/pattern inputs only; extract interaction, layout, accessibility, and performance guidance, not assets.
- External assets may be used only when user-owned or license-verifiable public assets are allowed; record source URL, license, and attribution in docs.

{POLICY_MARKER}
{policy_copy}
"""
    write(root / "docs" / "artic-brief.md", brief_doc)

    payload = {
        "query": query,
        "selected_count": len(selected_sources),
        "selected_sources": selected_sources,
        "intent": intent,
        "language": lang,
        "root": str(root.resolve()),
    }
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--audience", required=True)
    parser.add_argument("--goal", required=True)
    parser.add_argument("--vibe", required=True)
    parser.add_argument("--references", default="")
    parser.add_argument("--stack", default="unspecified")
    parser.add_argument("--accessibility", default="WCAG AA")
    parser.add_argument("--requirement", action="append", default=[], help="Preserve a custom requirement as key=value or plain text")
    parser.add_argument("--constraint", action="append", default=[], help="Preserve a custom constraint as key=value or plain text")
    parser.add_argument("--asset-policy", default="", help="User answer for owned/licensed external asset usage")
    parser.add_argument("--locale", default="en-US")
    parser.add_argument("--tone", default="clear, professional, product-focused")
    parser.add_argument("--preserve-term", action="append", default=[])
    parser.add_argument("--bilingual-terms", action="store_true")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--catalog", default=str(Path(__file__).resolve().parents[1] / "references" / "source-catalog.json"))
    args = parser.parse_args()
    try:
        payload = create_init_outputs(Path(args.root), args)
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
