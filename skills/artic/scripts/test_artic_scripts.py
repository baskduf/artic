#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def write_fixture_strategy(root: Path, source_ids: list[str] | None = None, north_star: str | None = None) -> dict:
    """Write a minimal valid strategy-first contract fixture for @artic start."""
    if source_ids is None:
        references_path = root / ".artic" / "references.json"
        if references_path.exists():
            references = json.loads(references_path.read_text(encoding="utf-8"))
            selected = references.get("selected_sources", []) if isinstance(references, dict) else []
            source_ids = [str(row["id"]) for row in selected if isinstance(row, dict) and row.get("id")][:3]
        else:
            source_ids = ["voltagent-awesome-design-md", "shadcn-ui", "material-design"]
    north_star = north_star or "Make the product feel like a calm command center for proof-rich decisions."
    reference_roles = [
        {
            "source_id": source_id,
            "role": f"strategy_fixture_reference_{index + 1}",
            "why_selected": "Fixture source used to verify strategy-driven compilation.",
            "extract": ["tokens", "hierarchy", "component discipline"],
            "avoid": ["exact layouts", "brand identity", "source copywriting"],
        }
        for index, source_id in enumerate(source_ids)
    ]
    strategy = {
        "schema_version": 1,
        "created_by": "agent",
        "project_summary": {
            "name": "Strategy Fixture Product",
            "audience": "startup operators comparing AI workflow tools",
            "primary_goal": "qualified demo requests",
            "stack": "React Tailwind",
        },
        "design_north_star": north_star,
        "target_user_interpretation": ["Users need clarity and trust before conversion."],
        "conversion_strategy": {
            "primary_cta": "Request demo",
            "secondary_cta": "View example",
            "proof_sequence": ["understand value", "inspect proof", "request demo"],
        },
        "reference_roles": reference_roles,
        "conflict_resolution": [
            {
                "conflict": "clarity versus visual richness",
                "decision": "prioritize clarity in the hero and move richness into supporting sections",
                "rationale": "conversion depends on fast comprehension",
            }
        ],
        "visual_system": {
            "tone": ["clear", "trustworthy", "proof-rich"],
            "color_roles": {"primary": "CTA", "surface": "content", "accent": "proof"},
            "typography": "clear hierarchy",
            "spacing": "mobile-first rhythm",
        },
        "component_rules": ["Use one dominant primary CTA."],
        "motion_interaction": ["Respect reduced motion."],
        "accessibility": ["WCAG AA contrast", "keyboard reachable controls"],
        "implementation_guidance": ["Use semantic HTML and tokenized styles."],
        "language": {
            "locale": "en-US",
            "output_language": "English",
            "tone": "clear, professional, product-focused",
            "preserve_terms": ["DESIGN.md", "AI-native", "Artic"],
            "bilingual_terms": False,
        },
        "reference_policy": "artic-policy: reference-safety-v1",
        "forbidden_copy_elements": ["logos", "trademarks", "proprietary illustrations", "exact layouts", "source copywriting"],
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
            subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "scaffold_artic_files.py"), "--root", tmp],
                check=True, text=True, capture_output=True,
            )
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
