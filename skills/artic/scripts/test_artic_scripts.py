#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def write_fixture_strategy(root: Path, source_ids=None, north_star=None):
    source_ids = ["voltagent-awesome-design-md", "shadcn-ui", "material-design"] if source_ids is None else source_ids
    north_star = north_star or "Make the product feel like a calm command center for proof-rich decisions."
    strategy = {
        "schema_version": 1,
        "project": {
            "name": "Strategy Fixture Product",
            "audience": "startup operators comparing AI workflow tools",
            "goal": "qualified demo requests",
            "vibe": "calm proof-rich command center",
            "stack": "React Tailwind",
        },
        "strategy": {
            "north_star": north_star,
            "positioning": "Trustworthy AI operations workspace with visible proof and fast evaluation paths.",
            "primary_user_journey": ["understand value", "inspect proof", "request demo"],
            "success_metrics": ["demo-request conversion", "trust signal engagement"],
        },
        "references": {
            "source_ids": source_ids,
            "selection_rationale": "Use compatible source patterns as reusable principles only.",
        },
        "language": {
            "locale": "en-US",
            "output_language": "English",
            "tone": "clear, professional, product-focused",
            "preserve_terms": ["DESIGN.md", "AI-native", "Artic"],
            "bilingual_terms": False,
        },
    }
    path = root / ".artic" / "strategy.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(strategy, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return strategy

class ArticScriptTests(unittest.TestCase):
    def test_source_catalog_parses(self):
        catalog = json.loads((ROOT / "references" / "source-catalog.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(catalog), 8)
        self.assertTrue(any(item["id"] == "voltagent-awesome-design-md" for item in catalog))

    def test_search_catalog_returns_results(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "search_reference_catalog.py"), "--query", "ai product developer saas", "--limit", "3"],
            check=True, text=True, capture_output=True,
        )
        rows = json.loads(result.stdout)
        self.assertEqual(len(rows), 3)
        self.assertGreater(rows[0]["score"], 0)

    def test_scaffold_then_validate(self):
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "scaffold_artic_files.py"), "--root", tmp],
                check=True, text=True, capture_output=True,
            )
            self.assertTrue((Path(tmp) / ".artic" / "strategy.json").exists())
            self.assertTrue((Path(tmp) / "docs" / "artic-strategy.md").exists())
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "validate_artic_outputs.py"), "--root", tmp],
                check=True, text=True, capture_output=True,
            )
            self.assertIn("Artic validation passed", result.stdout)

    def test_start_valid_strategy_writes_strategy_doc_and_design(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            north_star = "Signal Lantern north-star phrase for strategy-first Artic generation."
            write_fixture_strategy(root, north_star=north_star)
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "artic_start.py"), "--root", tmp],
                check=True, text=True, capture_output=True,
            )
            payload = json.loads(result.stdout)
            self.assertIn("docs/artic-strategy.md", payload["generated_files"])
            self.assertTrue((root / "docs" / "artic-strategy.md").exists())
            self.assertIn(north_star, (root / "DESIGN.md").read_text(encoding="utf-8"))

    def test_skill_frontmatter(self):
        content = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(content.startswith("---\n"))
        self.assertIn("name: artic", content)
        self.assertIn("description:", content)

if __name__ == "__main__":
    unittest.main(verbosity=2)
