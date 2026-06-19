#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

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
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "validate_artic_outputs.py"), "--root", tmp],
                check=True, text=True, capture_output=True,
            )
            self.assertIn("Artic validation passed", result.stdout)

    def test_skill_frontmatter(self):
        content = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(content.startswith("---\n"))
        self.assertIn("name: artic", content)
        self.assertIn("description:", content)

if __name__ == "__main__":
    unittest.main(verbosity=2)
