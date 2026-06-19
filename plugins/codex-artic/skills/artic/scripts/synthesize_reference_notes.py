#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from search_reference_catalog import search

POLICY = "Reference policy: extract reusable principles only; do not copy logos, trademarks, proprietary illustrations, or exact layouts."


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


def extract_bullets(markdown: str, limit: int = 6) -> list[str]:
    bullets = []
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            bullets.append(stripped)
        if len(bullets) >= limit:
            break
    return bullets


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
    lines = [
        "# Reference Synthesis",
        "",
        "## Selected Sources",
        "",
    ]
    for row in selected:
        source_kind = row["fixture"].get("source", "fixture")
        lines.append(f"- {row['name']} (`{row['id']}`), score {row['score']}: {source_kind} {row['fixture']['path']}")
    lines += ["", "## Extracted Common Patterns", ""]
    seen = set()
    for row in selected:
        for bullet in extract_bullets(row["fixture"]["body"]):
            key = re.sub(r"\W+", " ", bullet.lower()).strip()
            if key and key not in seen:
                lines.append(bullet)
                seen.add(key)
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
        f"Use {', '.join(row['name'] for row in selected)} as compatible source patterns for `{query}`. Generate project-specific tokens, components, and QA guidance from these reusable principles only.",
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
