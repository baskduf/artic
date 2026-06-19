#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from search_reference_catalog import search, terms

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
    query = make_query(args.project, args.audience, args.goal, args.vibe, args.references, args.stack)
    catalog_path = Path(args.catalog)
    rows = search(query, catalog_path, args.limit)
    selected_sources = [selected_source_payload(row) for row in rows]
    facets = normalize_facets(args.project, args.audience, args.goal, args.vibe, args.references, args.stack)

    brief = {
        "artic_version": "0.1.1",
        "project": {
            "name": args.project,
            "type": "homepage",
            "description": args.project,
            "target_users": [args.audience],
            "primary_goal": args.goal,
        },
        "style": {
            "desired_impression": [item.strip() for item in args.vibe.replace(",", " ").split() if item.strip()],
            "selected_preset": infer_preset(args.vibe),
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
        "synthesis": "Use selected sources as compatible patterns; localize prose according to the brief language contract while preserving source names and protected terms.",
    }
    state = {"artic_version": "0.1.1", "last_generated_at": now, "status": "initialized", "language": lang}

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
