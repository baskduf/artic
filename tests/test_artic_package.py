from __future__ import annotations
import functools, json, re, subprocess, sys, tempfile, threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
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


def test_artic_init_persists_llm_native_language_contract():
    with tempfile.TemporaryDirectory() as tmp:
        result = subprocess.run([
            sys.executable,
            str(ROOT / "skills/artic/scripts/artic_init.py"),
            "--root",
            tmp,
            "--project",
            "한국어 AI 회의 도우미",
            "--audience",
            "한국 스타트업 운영팀",
            "--goal",
            "데모 요청",
            "--vibe",
            "신뢰감 있고 명확한 모바일 우선 SaaS",
            "--references",
            "Linear clarity, Shopify Polaris trust, Material token discipline",
            "--stack",
            "React Tailwind",
            "--locale",
            "ko-KR",
            "--tone",
            "명확하고 전문적인 한국 스타트업 톤",
            "--preserve-term",
            "DESIGN.md",
            "--preserve-term",
            "AI-native",
            "--limit",
            "4",
        ], check=True, capture_output=True, text=True)
        payload = json.loads(result.stdout)
        assert payload["language"]["locale"] == "ko-KR"
        brief = json.loads((Path(tmp) / ".artic" / "brief.json").read_text(encoding="utf-8"))
        assert brief["language"] == {
            "locale": "ko-KR",
            "output_language": "Korean",
            "tone": "명확하고 전문적인 한국 스타트업 톤",
            "preserve_terms": ["DESIGN.md", "AI-native"],
            "bilingual_terms": False,
        }
        brief_doc = (Path(tmp) / "docs" / "artic-brief.md").read_text(encoding="utf-8")
        assert "Language: ko-KR / Korean" in brief_doc
        assert "Preserve terms: DESIGN.md, AI-native" in brief_doc
        assert "<!-- artic-policy: reference-safety-v1 -->" in brief_doc
        assert "참고 정책:" in brief_doc
        assert "Reference policy:" not in brief_doc


def test_validator_accepts_localized_policy_copy_when_invariant_marker_exists():
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([
            sys.executable,
            str(ROOT / "skills/artic/scripts/scaffold_artic_files.py"),
            "--root",
            tmp,
            "--locale",
            "ko-KR",
        ], check=True)
        for rel in ["DESIGN.md", "docs/design-rules.md", "docs/design-qa-checklist.md", "docs/homepage-design-prompt.md"]:
            text = (Path(tmp) / rel).read_text(encoding="utf-8")
            assert "<!-- artic-policy: reference-safety-v1 -->" in text, rel
            assert "참고 정책:" in text, rel
            assert "extract reusable principles only" not in text, rel
        result = subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/validate_artic_outputs.py"), "--root", tmp], capture_output=True, text=True)
        assert result.returncode == 0, result.stdout


def test_artic_init_rejects_reference_limits_below_validator_minimum():
    with tempfile.TemporaryDirectory() as tmp:
        result = subprocess.run([
            sys.executable,
            str(ROOT / "skills/artic/scripts/artic_init.py"),
            "--root",
            tmp,
            "--project",
            "AI Meeting Assistant",
            "--audience",
            "startup operators",
            "--goal",
            "demo requests",
            "--vibe",
            "clean trustworthy saas",
            "--limit",
            "1",
        ], capture_output=True, text=True)
        assert result.returncode != 0
        assert "limit must be >= 3" in result.stdout


def test_validator_requires_language_contract_in_brief():
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/scaffold_artic_files.py"), "--root", tmp], check=True)
        brief_path = Path(tmp) / ".artic" / "brief.json"
        brief = json.loads(brief_path.read_text(encoding="utf-8"))
        brief.pop("language")
        brief_path.write_text(json.dumps(brief, indent=2), encoding="utf-8")
        result = subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/validate_artic_outputs.py"), "--root", tmp], capture_output=True, text=True)
        assert result.returncode != 0
        assert "brief missing key: language" in result.stdout


def test_validator_checks_quality_tokens_inside_their_own_sections():
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/scaffold_artic_files.py"), "--root", tmp], check=True)
        design = Path(tmp) / "DESIGN.md"
        text = design.read_text(encoding="utf-8")
        text = text.replace("  sm: 8px\n", "")
        text = text.replace("  md: 16px\n", "")
        text = text.replace("  lg: 24px\n", "")
        design.write_text(text, encoding="utf-8")
        result = subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/validate_artic_outputs.py"), "--root", tmp], capture_output=True, text=True)
        assert result.returncode != 0
        assert "spacing missing quality token: sm" in result.stdout
        assert "spacing missing quality token: md" in result.stdout
        assert "spacing missing quality token: lg" in result.stdout


def test_reference_synthesis_smoke_uses_local_fixture_corpus():
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / "reference-synthesis.md"
        result = subprocess.run([
            sys.executable,
            str(ROOT / "skills/artic/scripts/synthesize_reference_notes.py"),
            "--query",
            "ai product developer saas",
            "--limit",
            "3",
            "--output",
            str(output),
        ], check=True, capture_output=True, text=True)
        payload = json.loads(result.stdout)
        assert payload["output"].endswith("reference-synthesis.md")
        assert payload["selected_count"] == 3
        assert payload["fixture_count"] >= 3
        synthesis = output.read_text(encoding="utf-8")
        assert "## Selected Sources" in synthesis
        assert "## Extracted Common Patterns" in synthesis
        assert "Reference policy: extract reusable principles only" in synthesis
        assert "VoltAgent awesome-design-md" in synthesis



def test_validator_rejects_missing_design_frontmatter_closing_delimiter():
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/scaffold_artic_files.py"), "--root", tmp], check=True)
        design = Path(tmp) / "DESIGN.md"
        design.write_text(design.read_text(encoding="utf-8").replace("\n---\n\n## Overview", "\n\n## Overview"), encoding="utf-8")
        result = subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/validate_artic_outputs.py"), "--root", tmp], capture_output=True, text=True)
        assert result.returncode != 0
        assert "closing delimiter" in result.stdout


def test_validator_requires_policy_in_each_generated_doc():
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/scaffold_artic_files.py"), "--root", tmp], check=True)
        checklist = Path(tmp) / "docs" / "design-qa-checklist.md"
        checklist.write_text("# Artic Design QA Checklist\n\n- [ ] Tokens are used consistently.\n", encoding="utf-8")
        result = subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/validate_artic_outputs.py"), "--root", tmp], capture_output=True, text=True)
        assert result.returncode != 0
        assert "docs/design-qa-checklist.md missing reference safety phrase" in result.stdout


def test_reference_synthesis_rejects_invalid_limit():
    with tempfile.TemporaryDirectory() as tmp:
        result = subprocess.run([
            sys.executable,
            str(ROOT / "skills/artic/scripts/synthesize_reference_notes.py"),
            "--query",
            "ai product developer saas",
            "--limit",
            "0",
            "--output",
            str(Path(tmp) / "reference-synthesis.md"),
        ], capture_output=True, text=True)
        assert result.returncode != 0
        assert "limit must be >= 1" in result.stdout


def test_reference_synthesis_can_live_fetch_and_cache_remote_sources():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        remote = root / "remote"
        remote.mkdir()
        (remote / "voltagent.md").write_text("# Remote VoltAgent\n\n- Live fetched SaaS hero pattern.\n", encoding="utf-8")
        (remote / "shadcn.md").write_text("# Remote shadcn\n\n- Live fetched component primitive pattern.\n", encoding="utf-8")
        catalog = root / "catalog.json"
        cache = root / "cache"
        output = root / "reference-synthesis.md"

        handler = functools.partial(SimpleHTTPRequestHandler, directory=str(remote))
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base = f"http://127.0.0.1:{server.server_port}"
            catalog.write_text(json.dumps([
                {
                    "id": "voltagent-awesome-design-md",
                    "name": "VoltAgent awesome-design-md",
                    "type": "design-md-corpus",
                    "license": "MIT",
                    "tags": ["homepage", "saas", "ai-product", "developer-tool"],
                    "strengths": ["homepage style patterns"],
                    "use_for": ["style candidates"],
                    "live_sources": [{"url": f"{base}/voltagent.md", "kind": "markdown", "license": "MIT"}],
                },
                {
                    "id": "shadcn-ui",
                    "name": "shadcn/ui ecosystem",
                    "type": "ui-implementation-ecosystem",
                    "license": "MIT",
                    "tags": ["react", "components", "developer-tool", "saas"],
                    "strengths": ["component primitives"],
                    "use_for": ["component defaults"],
                    "live_sources": [{"url": f"{base}/shadcn.md", "kind": "markdown", "license": "MIT"}],
                },
            ]), encoding="utf-8")

            result = subprocess.run([
                sys.executable,
                str(ROOT / "skills/artic/scripts/synthesize_reference_notes.py"),
                "--query",
                "ai product developer saas",
                "--catalog",
                str(catalog),
                "--fixtures-dir",
                str(root / "missing-fixtures"),
                "--cache-dir",
                str(cache),
                "--live-fetch",
                "--limit",
                "2",
                "--output",
                str(output),
            ], check=True, capture_output=True, text=True)
        finally:
            server.shutdown()
            server.server_close()

        payload = json.loads(result.stdout)
        assert payload["live_fetch_count"] == 2
        assert payload["cache_dir"] == str(cache)
        assert len(list(cache.glob("*.md"))) == 2
        synthesis = output.read_text(encoding="utf-8")
        assert "live-fetched" in synthesis
        assert "Live fetched SaaS hero pattern" in synthesis
        assert "Live fetched component primitive pattern" in synthesis


def test_design_templates_reference_all_declared_color_tokens():
    for rel in [
        "skills/artic/templates/DESIGN.template.md",
        "plugins/claude-artic/skills/artic/templates/DESIGN.template.md",
        "plugins/codex-artic/skills/artic/templates/DESIGN.template.md",
    ]:
        text = (ROOT / rel).read_text(encoding="utf-8")
        for token in ("primary", "secondary", "accent", "surface", "neutral", "text", "muted", "border"):
            assert f"colors.{token}" in text, (rel, token)


def test_rendered_design_template_passes_artic_validator():
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/scaffold_artic_files.py"), "--root", tmp], check=True)
        template = (ROOT / "skills/artic/templates/DESIGN.template.md").read_text(encoding="utf-8")
        rendered = template.replace("{{PROJECT_NAME}}", "Template Smoke Project")
        rendered = rendered.replace("{{DESIGN_DESCRIPTION}}", "Template-rendered Artic design system.")
        rendered = rendered.replace("{{OVERVIEW}}", "Template-rendered clean SaaS homepage direction.")
        (Path(tmp) / "DESIGN.md").write_text(rendered, encoding="utf-8")
        result = subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/validate_artic_outputs.py"), "--root", tmp], capture_output=True, text=True)
        assert result.returncode == 0, result.stdout


def test_marketplace_plugin_layout_smoke():
    required_skill_files = [
        "SKILL.md",
        "references/source-catalog.json",
        "references/fixtures/voltagent-saas.design.md",
        "scripts/search_reference_catalog.py",
        "scripts/synthesize_reference_notes.py",
        "scripts/scaffold_artic_files.py",
        "scripts/validate_artic_outputs.py",
        "templates/DESIGN.template.md",
        "templates/reference-synthesis.template.md",
    ]
    for plugin_root, manifest_rel in [
        (ROOT / "plugins/claude-artic", ".claude-plugin/plugin.json"),
        (ROOT / "plugins/codex-artic", ".codex-plugin/plugin.json"),
    ]:
        manifest = json.loads((plugin_root / manifest_rel).read_text(encoding="utf-8"))
        skill_path = plugin_root / manifest["skills"][0]["path"]
        for rel in required_skill_files:
            assert (skill_path / rel).exists(), (plugin_root, rel)


def test_readmes_document_distribution_intent():
    for rel in README_FILES:
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert "wheel is metadata-only" in text
        assert "marketplace packages, release tarballs, and sdists carry the skill/plugin payload" in text


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
    assert "actionlint_1.7.12_linux_amd64.tar.gz" in ci
    assert "permissions:" in release
    assert "contents: write" in release
    assert "Resolve and validate release ref" in release
    assert "DISPATCH_TAG: ${{ inputs.tag }}" in release
    assert "re.fullmatch(r'v\\d+\\.\\d+\\.\\d+', tag)" in release
    assert "persist-credentials: false" in release
    assert "--verify-tag" in release
    assert "Verify tag points at HEAD" in release
    assert "Verify version matches tag" in release
    assert "publish GitHub release" in release
    assert "actions/download-artifact@v4" in release


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
