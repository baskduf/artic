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


def test_readme_hero_image_is_synced():
    image_re = re.compile(r'<img width="300" height="300" alt=" -7" src="https://github.com/user-attachments/assets/[^"]+" />')
    expected = image_re.search((ROOT / "README.md").read_text(encoding="utf-8"))
    assert expected, "README.md missing synced hero image"
    for rel in README_FILES[1:]:
        found = image_re.search((ROOT / rel).read_text(encoding="utf-8"))
        assert found and found.group(0) == expected.group(0), rel

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


def test_versions_are_synced_across_manifests():
    version_match = re.search(r'^version = "([^"]+)"', (ROOT / "pyproject.toml").read_text(encoding="utf-8"), re.MULTILINE)
    assert version_match, "pyproject.toml missing project version"
    version = version_match.group(1)
    manifest_paths = [
        ROOT / ".claude-plugin" / "marketplace.json",
        ROOT / ".agents" / "plugins" / "marketplace.json",
        ROOT / "plugins" / "claude-artic" / ".claude-plugin" / "plugin.json",
        ROOT / "plugins" / "codex-artic" / ".codex-plugin" / "plugin.json",
    ]
    for path in manifest_paths:
        assert json.loads(path.read_text(encoding="utf-8"))["version"] == version, path


def test_ci_and_release_workflows_are_hardened():
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    release = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    assert "permissions:" in ci
    assert "contents: read" in ci
    assert "concurrency:" in ci
    assert "timeout-minutes:" in ci
    assert "fail-fast: false" in ci
    assert "repository-integrity:" in ci
    assert "release-dry-run:" in ci
    assert "@google/design.md lint" in ci
    assert "Check for common committed secrets" in ci
    assert "actions/checkout@v5" in ci
    assert "actions/setup-python@v6" in ci
    assert "actions/upload-artifact@v4" in ci
    assert "permissions:" in release
    assert "contents: write" in release
    assert "Resolve and validate release ref" in release
    assert "DISPATCH_TAG: ${{ inputs.tag }}" in release
    assert "grep -Eq '^v[0-9]+\\.[0-9]+\\.[0-9]+$'" in release
    assert "--verify-tag" in release
    assert "Verify tag points at HEAD" in release
    assert "Verify version matches tag" in release


def test_readmes_document_release_and_ci_expectations():
    required = [
        "python3 -m pip install pytest pyyaml",
        "python3 -m pytest -q",
        "CI",
    ]
    for rel in README_FILES:
        text = (ROOT / rel).read_text(encoding="utf-8")
        for snippet in required:
            assert snippet in text, (rel, snippet)
