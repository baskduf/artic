#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from design_intent_mapper import map_design_intent
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
        "artic_version": "0.3.0",
        "project": {
            "name": args.project,
            "type": "homepage",
            "description": args.project,
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
        "implementation": {"stack": args.stack or "unspecified", "mobile_first": "mobile" in args.vibe.lower(), "accessibility": args.accessibility},
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
    state = {"artic_version": "0.3.0", "last_generated_at": now, "status": "initialized", "language": lang, "intent_path": ".artic/intent.json"}

    write(root / ".artic" / "intent.json", json.dumps(intent, indent=2, ensure_ascii=False) + "\n")
    write(root / ".artic" / "brief.json", json.dumps(brief, indent=2, ensure_ascii=False) + "\n")
    write(root / ".artic" / "references.json", json.dumps(references, indent=2, ensure_ascii=False) + "\n")
    write(root / ".artic" / "state.json", json.dumps(state, indent=2, ensure_ascii=False) + "\n")

    candidate_lines = "\n".join(
        f"- {src['name']} (`{src['id']}`), score {src['score']}: {src['reason']}" for src in selected_sources
    )
    preserved = ", ".join(lang["preserve_terms"])
    policy_copy = POLICY_COPY_BY_LOCALE.get(lang["locale"], POLICY_COPY)
    brief_doc = f"""# Artic Brief

Project: {args.project}
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
