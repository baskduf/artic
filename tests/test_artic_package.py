from __future__ import annotations
import json, re, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README_FILES = ["README.md", "README.ko.md", "README.ja.md", "README.zh-CN.md", "README.zh-TW.md"]

def test_json_manifests_parse():
    for rel in [".claude-plugin/marketplace.json", ".agents/plugins/marketplace.json", "plugins/claude-artic/.claude-plugin/plugin.json", "plugins/codex-artic/.codex-plugin/plugin.json", "skills/artic/references/source-catalog.json", "skills/artic/templates/brief.schema.json"]:
        json.loads((ROOT / rel).read_text())

def test_skill_copies_are_in_sync():
    canonical = ROOT / "skills" / "artic"
    for copy in [ROOT / "plugins" / "claude-artic" / "skills" / "artic", ROOT / "plugins" / "codex-artic" / "skills" / "artic"]:
        for path in canonical.rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts:
                rel = path.relative_to(canonical)
                assert (copy / rel).read_bytes() == path.read_bytes(), rel

def headings(path: Path):
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.startswith("## ")]

def test_readme_translations_have_synced_structure():
    expected = headings(ROOT / "README.md")
    assert expected
    for rel in README_FILES[1:]:
        assert headings(ROOT / rel) == expected, rel

def test_readmes_have_language_nav():
    for rel in README_FILES:
        text = (ROOT / rel).read_text(encoding="utf-8")
        for target in README_FILES:
            if target != rel:
                assert target in text or (target == "README.md" and "English" in text), rel

def test_scaffold_and_validate_smoke():
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/scaffold_artic_files.py"), "--root", tmp], check=True)
        subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/validate_artic_outputs.py"), "--root", tmp], check=True)

def test_catalog_search_smoke():
    result = subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/search_reference_catalog.py"), "--query", "ai product developer saas", "--limit", "3"], check=True, capture_output=True, text=True)
    rows = json.loads(result.stdout)
    assert len(rows) == 3
    assert rows[0]["score"] > 0
