#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

def load_catalog(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))

def terms(text: str) -> set[str]:
    return {p.strip().lower() for p in text.replace(",", " ").replace("/", " ").replace("-", " ").split() if p.strip()}

def score_source(source: dict, query_terms: set[str]) -> int:
    hay = set()
    for key in ("id", "name", "type"):
        hay |= terms(str(source.get(key, "")))
    for key in ("tags", "strengths", "use_for"):
        for value in source.get(key, []):
            hay |= terms(str(value))
            hay.add(str(value).lower())
    score = 0
    for term in query_terms:
        if term in hay:
            score += 3
        if any(term in item for item in hay):
            score += 1
    return score

def search(query: str, catalog_path: Path, limit: int) -> list[dict]:
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
    print(json.dumps(search(args.query, Path(args.catalog), args.limit), indent=2, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
