#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    from design_intent_mapper import map_design_intent
except ImportError:  # pragma: no cover - supports direct embedding by plugin runners.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from design_intent_mapper import map_design_intent

WEIGHTS = {
    "product_fit": 5,
    "visual_traits": 4,
    "page_patterns": 3,
    "implementation_fit": 2,
    "extraction_targets": 2,
    "tags": 3,
    "strengths": 2,
    "use_for": 2,
    "application_guidance": 2,
    "id": 1,
    "name": 1,
    "type": 1,
}
AVOID_PENALTY = 5


def load_catalog(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def terms(text: str) -> set[str]:
    return {
        p.strip().lower()
        for p in text.replace(",", " ").replace("/", " ").replace("-", " ").replace("_", " ").split()
        if p.strip()
    }


def values_for(source: dict, key: str) -> list[str]:
    value = source.get(key, [])
    if isinstance(value, list):
        return [str(item) for item in value]
    if value:
        return [str(value)]
    return []


def field_score(values: list[str], query_terms: set[str], weight: int) -> int:
    score = 0
    hay_terms: set[str] = set()
    hay_phrases: set[str] = set()
    for value in values:
        lower = value.lower()
        hay_phrases.add(lower)
        hay_terms |= terms(lower)
    for term in query_terms:
        if term in hay_terms:
            score += weight
        elif any(term in phrase for phrase in hay_phrases):
            score += max(1, weight // 2)
    return score


def score_source(source: dict, query_terms: set[str], avoid_terms: set[str] | None = None) -> int:
    score = 0
    for key, weight in WEIGHTS.items():
        if key in ("id", "name", "type"):
            values = [str(source.get(key, ""))]
        else:
            values = values_for(source, key)
        score += field_score(values, query_terms, weight)
    score -= field_score(values_for(source, "avoid_when"), avoid_terms or query_terms, AVOID_PENALTY)
    return score


def query_from_intent(intent: dict[str, Any]) -> tuple[str, set[str]]:
    query_parts: list[str] = []
    for key in ("catalog_query", "search_facets", "style_facets", "design_principles"):
        value = intent.get(key)
        if isinstance(value, str):
            query_parts.append(value)
        elif isinstance(value, list):
            query_parts.extend(str(item) for item in value)
    avoid_terms = terms(" ".join(str(item) for item in intent.get("avoid_facets", []) if item))
    return " ".join(query_parts).strip(), avoid_terms


def search(query: str, catalog_path: Path, limit: int, *, avoid_terms: set[str] | None = None) -> list[dict]:
    if limit < 1:
        raise ValueError("limit must be >= 1")
    query_terms = terms(query)
    rows = [{"score": score_source(src, query_terms, avoid_terms), **src} for src in load_catalog(catalog_path)]
    rows.sort(key=lambda row: (row["score"], row["id"]), reverse=True)
    return rows[:limit]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", default="")
    parser.add_argument(
        "--semantic-intent",
        action="store_true",
        help="Normalize project/audience/goal/vibe into design facets before catalog search.",
    )
    parser.add_argument("--intent-json", help="Path to a design intent JSON file produced by design_intent_mapper.py.")
    parser.add_argument("--project", default="")
    parser.add_argument("--audience", default="")
    parser.add_argument("--goal", default="")
    parser.add_argument("--vibe", default="")
    parser.add_argument("--references", default="")
    parser.add_argument("--avoid", default="")
    parser.add_argument("--stack", default="")
    parser.add_argument("--catalog", default=str(Path(__file__).resolve().parents[1] / "references" / "source-catalog.json"))
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--include-intent", action="store_true")
    args = parser.parse_args()

    intent = None
    avoid_terms: set[str] = set()
    query = args.query
    if args.intent_json:
        intent = json.loads(Path(args.intent_json).read_text(encoding="utf-8"))
        query, avoid_terms = query_from_intent(intent)
    elif args.semantic_intent:
        intent = map_design_intent(
            project=args.project,
            audience=args.audience,
            goal=args.goal,
            vibe=args.vibe or args.query,
            references=args.references,
            avoid=args.avoid,
            stack=args.stack,
        )
        query, avoid_terms = query_from_intent(intent)
    if not query.strip():
        parser.error("--query, --semantic-intent fields, or --intent-json must provide search input")

    try:
        rows = search(query, Path(args.catalog), args.limit, avoid_terms=avoid_terms)
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 1
    if args.include_intent:
        print(json.dumps({"intent": intent, "results": rows}, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
