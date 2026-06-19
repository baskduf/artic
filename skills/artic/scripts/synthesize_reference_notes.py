#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from search_reference_catalog import search

POLICY = "Reference policy: extract reusable principles only; do not copy logos, trademarks, proprietary illustrations, or exact layouts."
PATTERN_CATEGORIES = [
    ("color_roles", "Color Roles"),
    ("typography", "Typography"),
    ("layout_rhythm", "Layout Rhythm"),
    ("component_treatment", "Component Treatment"),
    ("cta_behavior", "CTA Behavior"),
    ("trust_patterns", "Trust Patterns"),
    ("motion", "Motion"),
    ("accessibility", "Accessibility"),
]
CATEGORY_RULES: dict[str, tuple[tuple[str, int], ...]] = {
    "color_roles": (
        ("color", 3), ("colors", 3), ("palette", 3), ("palettes", 3), ("surface", 2),
        ("surfaces", 2), ("border", 1), ("borders", 1), ("contrast", 1), ("neutral", 1),
    ),
    "typography": (
        ("typography", 4), ("type", 2), ("h1", 3), ("h2", 3), ("heading", 2),
        ("headings", 2), ("body copy", 3), ("readable", 2), ("line length", 2),
    ),
    "layout_rhythm": (
        ("layout", 4), ("layouts", 4), ("section", 2), ("sections", 2), ("spacing", 2),
        ("hero", 2), ("row", 2), ("strip", 2), ("grid", 2), ("stack", 1), ("density", 1),
    ),
    "component_treatment": (
        ("component", 4), ("components", 4), ("primitive", 3), ("primitives", 3),
        ("card", 2), ("cards", 2), ("form", 2), ("badge", 2), ("badges", 2),
        ("panel", 2), ("panels", 2), ("controls", 2), ("variants", 2),
    ),
    "cta_behavior": (
        ("cta", 4), ("conversion", 3), ("action", 2), ("submit", 3), ("primary", 1),
        ("secondary", 1), ("demo", 2), ("waitlist", 2),
    ),
    "trust_patterns": (
        ("trust", 4), ("trustworthy", 4), ("proof", 3), ("metrics", 3),
        ("validation", 2), ("uncertainty", 3), ("confidence", 2),
    ),
    "motion": (
        ("motion", 4), ("animation", 3), ("animations", 3), ("haptic", 3),
        ("haptics", 3), ("transition", 2), ("transitions", 2),
    ),
    "accessibility": (
        ("accessibility", 4), ("focus", 3), ("keyboard", 3), ("semantic", 3),
        ("semantics", 3), ("labels", 2), ("labeled", 2), ("error", 2), ("contrast", 1),
    ),
}
SECTION_HINTS: dict[str, str] = {
    "accessibility": "accessibility",
    "components": "component_treatment",
    "component": "component_treatment",
    "reusable patterns": "layout_rhythm",
    "patterns": "layout_rhythm",
    "motion": "motion",
}
SAFETY_PHRASES = (
    "do not copy", "never copy", "without copying", "not clone", "clone targets",
    "brand assets", "brand identity", "brand-inspired", "exact layouts", "exact layout",
    "exact visuals", "exact palettes", "source copywriting", "proprietary", "trademark",
    "logos", "logo", "identity", "policy", "forbidden",
)
FALLBACKS = {
    "color_roles": "- Define semantic color roles for primary action, secondary action, accent, surface, neutral, text, muted text, and borders.",
    "typography": "- Preserve clear type hierarchy with distinct hero, section heading, body, and support text roles.",
    "layout_rhythm": "- Use consistent section rhythm and mobile-first stacking before adding desktop density.",
    "component_treatment": "- Build components from reusable tokens instead of one-off visual styles.",
    "cta_behavior": "- Keep one dominant primary CTA and make secondary actions visibly quieter.",
    "trust_patterns": "- Place proof, labels, validation, or metrics near conversion moments to reduce uncertainty.",
    "motion": "- Use restrained motion only to clarify state, hierarchy, or progression.",
    "accessibility": "- Preserve WCAG AA contrast, keyboard focus states, semantic buttons/links, and labeled form controls.",
}


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}, text
    meta: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip().strip('"')
    return meta, text[end + 5:].strip()


def load_fixtures(fixtures_dir: Path) -> dict[str, dict[str, str]]:
    fixtures: dict[str, dict[str, str]] = {}
    for path in sorted(fixtures_dir.glob("*.design.md")):
        meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        source_id = meta.get("source_id")
        if source_id:
            fixtures[source_id] = {"path": str(path), "body": body, "source": "fixture", **meta}
    return fixtures


def cache_name(source_id: str, url: str) -> str:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
    safe_id = re.sub(r"[^a-zA-Z0-9_.-]+", "-", source_id).strip("-")
    return f"{safe_id}-{digest}.md"


def fetch_live_sources(rows: list[dict], cache_dir: Path, timeout: int = 10) -> dict[str, dict[str, str]]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    fetched: dict[str, dict[str, str]] = {}
    for row in rows:
        for source in row.get("live_sources", []):
            url = source.get("url")
            if not url:
                continue
            cache_path = cache_dir / cache_name(row["id"], url)
            if cache_path.exists():
                body = cache_path.read_text(encoding="utf-8")
            else:
                try:
                    with urlopen(url, timeout=timeout) as response:
                        content_type = response.headers.get("Content-Type", "")
                        if "text" not in content_type and "markdown" not in content_type and "octet-stream" not in content_type:
                            continue
                        body = response.read(1_000_000).decode("utf-8")
                except (OSError, URLError, UnicodeDecodeError):
                    continue
                cache_path.write_text(body, encoding="utf-8")
            fetched[row["id"]] = {
                "path": str(cache_path),
                "body": body,
                "source": "live-fetched",
                "source_id": row["id"],
                "url": url,
                "license": source.get("license", row.get("license", "unknown")),
            }
            break
    return fetched


def extract_bullets(markdown: str, limit: int = 18) -> list[tuple[str, str]]:
    bullets: list[tuple[str, str]] = []
    current_heading = ""
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("##"):
            current_heading = stripped.lstrip("#").strip().lower()
            continue
        if stripped.startswith("- "):
            bullets.append((stripped, current_heading))
        if len(bullets) >= limit:
            break
    return bullets


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", text.lower())).strip()


def has_term(normalized: str, term: str) -> bool:
    return bool(re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", normalized))


def is_safety_bullet(normalized: str) -> bool:
    return any(phrase in normalized for phrase in SAFETY_PHRASES)


def category_scores(normalized: str, heading: str) -> dict[str, int]:
    scores: dict[str, int] = {}
    for key, rules in CATEGORY_RULES.items():
        score = sum(weight for term, weight in rules if has_term(normalized, term))
        if score:
            scores[key] = score
    hinted = SECTION_HINTS.get(heading)
    if hinted and hinted in scores:
        scores[hinted] += 2
    return scores


def choose_category(bullet: str, heading: str) -> str | None:
    normalized = normalize_text(bullet)
    if is_safety_bullet(normalized):
        return None
    scores = category_scores(normalized, heading)
    if not scores:
        return SECTION_HINTS.get(heading, "component_treatment")
    return max(scores.items(), key=lambda item: (item[1], -next(i for i, (key, _) in enumerate(PATTERN_CATEGORIES) if key == item[0])))[0]


def categorize_bullets(rows: list[dict]) -> tuple[dict[str, list[str]], dict[str, list[str]], dict[str, list[str]]]:
    categories = {key: [] for key, _ in PATTERN_CATEGORIES}
    attribution: dict[str, list[str]] = {}
    safety_notes: dict[str, list[str]] = {}
    seen: set[tuple[str, str]] = set()
    for row in rows:
        source_id = row["id"]
        attribution[source_id] = []
        safety_notes[source_id] = []
        bullets = extract_bullets(row["fixture"]["body"])
        for bullet, heading in bullets:
            normalized = normalize_text(bullet)
            attribution[source_id].append(bullet)
            if is_safety_bullet(normalized):
                marker = ("reference_safety", normalized)
                if marker not in seen:
                    safety_notes[source_id].append(bullet)
                    seen.add(marker)
                continue
            key = choose_category(bullet, heading)
            if not key:
                continue
            marker = (key, normalized)
            if marker not in seen:
                categories[key].append(bullet)
                seen.add(marker)
    for key in categories:
        if not categories[key]:
            categories[key].append(FALLBACKS[key])
    return categories, attribution, safety_notes


def make_synthesis(query: str, catalog_path: Path, fixtures_dir: Path, limit: int, *, live_fetch: bool = False, cache_dir: Path | None = None) -> tuple[str, dict]:
    if limit < 1:
        raise ValueError("limit must be >= 1")
    fixtures = load_fixtures(fixtures_dir)
    candidate_rows = search(query, catalog_path, max(limit, len(fixtures), 25))
    live_fixtures = fetch_live_sources(candidate_rows, cache_dir or fixtures_dir / ".cache") if live_fetch else {}
    available = {**fixtures, **live_fixtures}
    selected = []
    for row in candidate_rows:
        fixture = available.get(row["id"])
        if fixture:
            selected.append({**row, "fixture": fixture})
        if len(selected) >= limit:
            break
    if not selected:
        mode = "local or live" if live_fetch else "local"
        raise ValueError(f"no {mode} reference fixtures matched query: {query}")

    categories, attribution, safety_notes = categorize_bullets(selected)
    lines = ["# Reference Synthesis", "", "## Selected Sources", ""]
    for row in selected:
        source_kind = row["fixture"].get("source", "fixture")
        lines.append(f"- {row['name']} (`{row['id']}`), score {row['score']}: {source_kind} {row['fixture']['path']}")
    lines += ["", "## Extracted Common Patterns", ""]
    for key, title in PATTERN_CATEGORIES:
        lines += [f"### {title}", ""]
        for bullet in categories[key][:6]:
            lines.append(bullet)
        lines.append("")
    lines += ["## Pattern Attribution", ""]
    for row in selected:
        source_id = row["id"]
        lines.append(f"- `{source_id}`: " + "; ".join(attribution.get(source_id, [])[:3]))
    lines += [
        "",
        "## Conflicts Resolved",
        "",
        "- Prefer project-specific token roles over any single reference brand identity.",
        "- Keep the primary conversion path visually dominant while secondary actions remain quieter.",
        "- Use component/accessibility discipline from the selected systems without copying exact page compositions.",
        "",
        "## Final Direction",
        "",
        f"Use {', '.join(row['name'] for row in selected)} as compatible source patterns for `{query}`. Generate project-specific tokens, components, page composition, QA scoring, and implementation guidance from these reusable principles only.",
        "",
        "## Forbidden Copy Elements",
        "",
        "- Do not copy logos, trademarks, proprietary illustrations, exact page compositions, exact palettes as identity, or source copywriting.",
        "- Treat brand-inspired examples as pattern references, not clone targets.",
    ]
    selected_safety_notes = [note for notes in safety_notes.values() for note in notes][:6]
    if selected_safety_notes:
        lines += ["", "## Reference Safety Notes", ""]
        lines.extend(selected_safety_notes)
    lines += [
        "",
        POLICY,
        "",
    ]
    payload = {
        "query": query,
        "selected_count": len(selected),
        "fixture_count": len(fixtures),
        "live_fetch_count": len(live_fixtures),
        "cache_dir": str(cache_dir) if cache_dir else None,
        "pattern_categories": [key for key, _ in PATTERN_CATEGORIES],
        "selected_sources": [{"id": row["id"], "name": row["name"], "score": row["score"], "source": row["fixture"].get("source", "fixture")} for row in selected],
    }
    return "\n".join(lines), payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    parser.add_argument("--catalog", default=str(Path(__file__).resolve().parents[1] / "references" / "source-catalog.json"))
    parser.add_argument("--fixtures-dir", default=str(Path(__file__).resolve().parents[1] / "references" / "fixtures"))
    parser.add_argument("--cache-dir", default=None)
    parser.add_argument("--live-fetch", action="store_true")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    try:
        markdown, payload = make_synthesis(
            args.query,
            Path(args.catalog),
            Path(args.fixtures_dir),
            args.limit,
            live_fetch=args.live_fetch,
            cache_dir=Path(args.cache_dir) if args.cache_dir else None,
        )
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 1
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(markdown, encoding="utf-8")
    payload["output"] = str(output)
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
