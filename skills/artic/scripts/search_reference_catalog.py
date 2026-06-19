#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

WEIGHTS = {
    "product_fit": 5,
    "visual_traits": 4,
    "page_patterns": 3,
    "implementation_fit": 2,
    "extraction_targets": 2,
    "tags": 3,
    "strengths": 2,
    "use_for": 2,
    "id": 1,
    "name": 1,
    "type": 1,
}
AVOID_PENALTY = 5


def load_catalog(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def terms(text: str) -> set[str]:
    return {p.strip().lower() for p in text.replace(",", " ").replace("/", " ").replace("-", " ").replace("_", " ").split() if p.strip()}


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


def score_source(source: dict, query_terms: set[str]) -> int:
    score = 0
    for key, weight in WEIGHTS.items():
        if key in ("id", "name", "type"):
            values = [str(source.get(key, ""))]
        else:
            values = values_for(source, key)
        score += field_score(values, query_terms, weight)
    avoid_values = values_for(source, "avoid_when")
    score -= field_score(avoid_values, query_terms, AVOID_PENALTY)
    return score


def search(query: str, catalog_path: Path, limit: int) -> list[dict]:
    if limit < 1:
        raise ValueError("limit must be >= 1")
    query_terms = terms(query)
    rows = [{"score": score_source(src, query_terms), **src} for src in load_catalog(catalog_path)]
    rows.sort(key=lambda row: (row["score"], row["id"]), reverse=True)
    return rows[:limit]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    parser.add_argument("--catalog", default=str(Path(__file__).resolve().parents[1] / "references" / "source-catalog.json"))
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()
    try:
        rows = search(args.query, Path(args.catalog), args.limit)
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(rows, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
