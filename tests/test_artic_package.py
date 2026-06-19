from __future__ import annotations
import functools, importlib, importlib.util, json, re, subprocess, sys, tarfile, tempfile, threading, urllib.error, zipfile
from email.message import Message
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "skills" / "artic" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

artic_update = importlib.import_module("artic_update")
artic_version = importlib.import_module("artic_version")
artic_init_session = importlib.import_module("artic_init_session")

README_FILES = ["README.md", "README.ko.md", "README.ja.md", "README.zh-CN.md", "README.zh-TW.md"]

def project_version() -> str:
    match = re.search(r'^version = "([^"]+)"', (ROOT / "pyproject.toml").read_text(encoding="utf-8"), re.MULTILINE)
    assert match, "pyproject.toml missing project version"
    return match.group(1)


def project_tag() -> str:
    return f"v{project_version()}"


def assert_no_finalized_artic_outputs(root: Path):
    forbidden = [
        ".artic/intent.json",
        ".artic/brief.json",
        ".artic/references.json",
        ".artic/state.json",
        ".artic/strategy.json",
        "docs/artic-brief.md",
        "docs/artic-strategy.md",
        "DESIGN.md",
        "docs/design-rules.md",
        "docs/design-qa-checklist.md",
        "docs/homepage-design-prompt.md",
    ]
    for rel in forbidden:
        assert not (root / rel).exists(), rel

def write_fixture_strategy(root: Path, source_ids: list[str] | None = None, north_star: str | None = None) -> dict:
    """Write a minimal valid strategy-first contract fixture for @artic start."""
    source_ids = ["voltagent-awesome-design-md", "shadcn-ui", "material-design"] if source_ids is None else source_ids
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


def load_strategy_validator_module():
    path = ROOT / "skills" / "artic" / "scripts" / "validate_artic_strategy.py"
    if not path.exists():
        return None
    spec = importlib.util.spec_from_file_location("validate_artic_strategy", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_json_manifests_parse():
    for rel in [".claude-plugin/marketplace.json", ".agents/plugins/marketplace.json", "plugins/claude-artic/.claude-plugin/plugin.json", "plugins/codex-artic/.codex-plugin/plugin.json", "skills/artic/references/source-catalog.json", "skills/artic/templates/brief.schema.json", "skills/artic/templates/strategy.schema.json"]:
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
    image_re = re.compile(r'<img width="220" alt="Artic logo" src="assets/artic-logo\.png" />')
    expected = image_re.search((ROOT / "README.md").read_text(encoding="utf-8"))
    assert expected, "README.md missing synced hero image"
    for rel in README_FILES[1:]:
        found = image_re.search((ROOT / rel).read_text(encoding="utf-8"))
        assert found and found.group(0) == expected.group(0), rel


def test_readme_logo_asset_exists():
    logo = ROOT / "assets" / "artic-logo.png"
    assert logo.is_file(), "README logo asset is missing"
    assert logo.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"), "README logo asset must be a PNG"


def test_readmes_do_not_render_badges():
    badge_patterns = [
        "img.shields.io",
        "github/actions/workflow/status",
        "alt=\"Claude Skill\"",
        "alt=\"Codex Plugin\"",
        "alt=\"DESIGN.md\"",
        "alt=\"License MIT\"",
        "alt=\"CI\"",
    ]
    for rel in README_FILES:
        text = (ROOT / rel).read_text(encoding="utf-8")
        for pattern in badge_patterns:
            assert pattern not in text, (rel, pattern)


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


def test_readmes_document_version_and_update_commands():
    required_phrases = [
        "codex plugin add codex-artic@artic",
        f"codex plugin marketplace add baskduf/artic@{project_tag()}",
        "@artic version",
        "@artic update",
        "python3 skills/artic/scripts/artic_version.py --root .",
        "python3 skills/artic/scripts/artic_update.py --root .",
    ]
    for rel in README_FILES:
        text = (ROOT / rel).read_text(encoding="utf-8")
        for phrase in required_phrases:
            assert phrase in text, (rel, phrase)


def test_readmes_document_init_start_show_lifecycle_boundary():
    required_phrases = [
        ".artic/init-session.json",
        ".artic/show/index.html",
        ".artic/strategy.json",
        "docs/artic-strategy.md",
        "@artic init",
        "@artic start",
        "@artic show",
        "@artic review",
        "python3 skills/artic/scripts/artic_show.py --root .",
    ]
    for rel in README_FILES:
        text = (ROOT / rel).read_text(encoding="utf-8")
        for phrase in required_phrases:
            assert phrase in text, (rel, phrase)


def test_artic_version_no_network_marks_latest_unchecked():
    payload = artic_version.collect_version_info(ROOT, no_network=True)
    assert payload["latest_state"] == "unchecked"
    assert payload["latest_error"] is None
    assert payload["status"] == "latest-unchecked"
    assert "unchecked (--no-network)" in artic_version.render_text(payload)


def test_artic_version_404_marks_latest_not_found(monkeypatch):
    def raise_404(repo: str, timeout: float = 10.0) -> dict:
        raise urllib.error.HTTPError("https://api.github.com/repos/example/missing/releases/latest", 404, "Not Found", Message(), None)

    monkeypatch.setattr(artic_version, "fetch_latest_release", raise_404)
    payload = artic_version.collect_version_info(ROOT, repo="example/missing")
    assert payload["latest_state"] == "not_found"
    assert payload["latest_error"] is None
    assert payload["latest"] is None
    assert payload["status"] == "latest-not-found"
    assert "not found: no GitHub latest release" in artic_version.render_text(payload)


def test_artic_version_network_failure_marks_latest_unavailable(monkeypatch):
    def raise_network_failure(repo: str, timeout: float = 10.0) -> dict:
        raise urllib.error.URLError("offline")

    monkeypatch.setattr(artic_version, "fetch_latest_release", raise_network_failure)
    payload = artic_version.collect_version_info(ROOT, repo="example/repo")
    assert payload["latest_state"] == "unavailable"
    assert payload["latest_error"]
    assert payload["status"] == "latest-unavailable"
    assert "unavailable:" in artic_version.render_text(payload)


def test_artic_update_guidance_without_latest_omits_version_pin():
    payload = {
        "installed_version": project_version(),
        "latest": None,
        "latest_state": "not_found",
        "status": "latest-not-found",
        "version_mismatches": [],
    }
    text = artic_update.render_update_guidance(payload)
    assert "Latest: not found (no GitHub latest release)" in text
    assert "marketplace commands below intentionally omit a version pin" in text
    assert "baskduf/artic@<latest-tag>" not in text
    assert "codex plugin marketplace add baskduf/artic\n" in text

def test_scaffold_and_validate_smoke():
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/scaffold_artic_files.py"), "--root", tmp], check=True)
        subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/validate_artic_outputs.py"), "--root", tmp], check=True)

def test_strategy_validator_accepts_valid_strategy_when_available():
    validator = load_strategy_validator_module()
    if validator is None:
        return
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_fixture_strategy(root)
        if hasattr(validator, "validate"):
            assert validator.validate(root) == []
        else:
            result = subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/validate_artic_strategy.py"), "--root", tmp], capture_output=True, text=True)
            assert result.returncode == 0, result.stdout


def test_strategy_validator_rejects_invalid_strategy_when_available():
    validator = load_strategy_validator_module()
    if validator is None:
        return
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_fixture_strategy(root, source_ids=[])
        path = root / ".artic" / "strategy.json"
        strategy = json.loads(path.read_text(encoding="utf-8"))
        strategy.pop("design_north_star")
        path.write_text(json.dumps(strategy, indent=2) + "\n", encoding="utf-8")
        if hasattr(validator, "validate"):
            errors = validator.validate(root)
            assert errors
            assert any("north_star" in error or "source_ids" in error for error in errors)
        else:
            result = subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/validate_artic_strategy.py"), "--root", tmp], capture_output=True, text=True)
            assert result.returncode != 0
            assert "strategy" in result.stdout.lower()

def test_catalog_search_smoke():
    result = subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/search_reference_catalog.py"), "--query", "ai product developer saas", "--limit", "3"], check=True, capture_output=True, text=True)
    rows = json.loads(result.stdout)
    assert len(rows) == 3
    assert rows[0]["score"] > 0



def test_catalog_sources_have_quality_retrieval_metadata():
    catalog = json.loads((ROOT / "skills/artic/references/source-catalog.json").read_text(encoding="utf-8"))
    required = {"product_fit", "visual_traits", "page_patterns", "implementation_fit", "extraction_targets", "avoid_when", "application_guidance"}
    banned_guidance_terms = re.compile(r"\b(risk|risky|warning|caution|danger|be careful)\b", re.IGNORECASE)
    for source in catalog:
        missing = required - set(source)
        assert not missing, (source["id"], missing)
        assert "risk_notes" not in source, source["id"]
        for key in required - {"application_guidance"}:
            assert isinstance(source[key], list) and source[key], (source["id"], key)
        guidance = source["application_guidance"]
        assert isinstance(guidance, str) and guidance, source["id"]
        assert banned_guidance_terms.search(guidance) is None, (source["id"], guidance)
        assert any(verb in guidance for verb in ["Use ", "Apply ", "Translate ", "Pair ", "Ground ", "Keep ", "Connect ", "Adapt "]), (source["id"], guidance)


def test_weighted_catalog_search_routes_distinct_design_intents():
    cases = [
        ("developer tool ai saas react tailwind", {"voltagent-awesome-design-md", "shadcn-ui", "google-design-md"}),
        ("enterprise data dashboard forms accessibility", {"ibm-carbon", "ant-design", "microsoft-fluent"}),
        ("mobile app landing ios motion haptics", {"meliwat-awesome-ios-design-md", "material-design"}),
        ("commerce trust forms admin", {"shopify-polaris", "material-design"}),
    ]
    for query, expected_any in cases:
        result = subprocess.run([
            sys.executable,
            str(ROOT / "skills/artic/scripts/search_reference_catalog.py"),
            "--query",
            query,
            "--limit",
            "3",
        ], check=True, capture_output=True, text=True)
        ids = {row["id"] for row in json.loads(result.stdout)}
        assert ids & expected_any, (query, ids)


def test_weighted_catalog_search_routes_3d_resource_intents():
    cases = [
        ("3d webgl interactive product hero react", {"threejs-examples", "react-three-fiber-examples", "model-viewer"}),
        ("safe cc0 3d icon asset landing", {"poly-haven", "kenney-assets", "3dicons"}),
        ("webgl performance accessibility reduced motion 3d", {"mdn-webgl-best-practices", "web-dev-motion-accessibility", "model-viewer-loading"}),
    ]
    for query, expected_any in cases:
        result = subprocess.run([
            sys.executable,
            str(ROOT / "skills/artic/scripts/search_reference_catalog.py"),
            "--query",
            query,
            "--limit",
            "5",
        ], check=True, capture_output=True, text=True)
        ids = {row["id"] for row in json.loads(result.stdout)}
        assert ids & expected_any, (query, ids)


def test_artic_init_semantic_intent_selects_3d_runtime_and_safety_sources():
    with tempfile.TemporaryDirectory() as tmp:
        result = subprocess.run([
            sys.executable,
            str(ROOT / "skills/artic/scripts/artic_init.py"),
            "--root",
            tmp,
            "--project",
            "3D product configurator landing",
            "--audience",
            "shoppers comparing hardware options",
            "--goal",
            "purchase conversion",
            "--vibe",
            "interactive WebGL 3D hero with reduced motion fallback",
            "--stack",
            "React three.js model-viewer",
            "--limit",
            "4",
        ], check=True, capture_output=True, text=True)
        payload = json.loads(result.stdout)
        selected_ids = {row["id"] for row in payload["selected_sources"]}

    assert selected_ids & {"threejs-examples", "react-three-fiber-examples", "model-viewer"}, selected_ids
    assert selected_ids & {"mdn-webgl-best-practices", "web-dev-motion-accessibility", "model-viewer-loading"}, selected_ids


def test_artic_init_does_not_route_plain_2d_canvas_to_3d_sources():
    with tempfile.TemporaryDirectory() as tmp:
        result = subprocess.run([
            sys.executable,
            str(ROOT / "skills/artic/scripts/artic_init.py"),
            "--root",
            tmp,
            "--project",
            "Collaborative canvas whiteboard",
            "--audience",
            "remote teams",
            "--goal",
            "signup",
            "--vibe",
            "clean realtime drawing canvas",
            "--stack",
            "React",
            "--limit",
            "4",
        ], check=True, capture_output=True, text=True)
        payload = json.loads(result.stdout)
        selected_ids = {row["id"] for row in payload["selected_sources"]}
        style_facets = set(payload["intent"]["style_facets"])

    assert "3d-webgl" not in style_facets
    assert not selected_ids & {"model-viewer", "threejs-examples", "react-three-fiber-examples"}, selected_ids


def test_artic_init_generates_brief_and_reference_search_outputs():
    with tempfile.TemporaryDirectory() as tmp:
        result = subprocess.run([
            sys.executable,
            str(ROOT / "skills/artic/scripts/artic_init.py"),
            "--root",
            tmp,
            "--project",
            "Korean AI Meeting Assistant",
            "--audience",
            "startup operators and sales teams",
            "--goal",
            "demo requests",
            "--vibe",
            "clean trustworthy mobile-first saas",
            "--references",
            "Linear clarity, Shopify Polaris trust, Material token discipline",
            "--stack",
            "React Tailwind",
            "--limit",
            "4",
        ], check=True, capture_output=True, text=True)
        payload = json.loads(result.stdout)
        assert payload["selected_count"] >= 3
        assert payload["query"]
        assert payload["intent"]["mapper"].startswith("artic-llm-first")
        assert payload["intent"]["design_north_star"]
        brief = json.loads((Path(tmp) / ".artic" / "brief.json").read_text(encoding="utf-8"))
        intent = json.loads((Path(tmp) / ".artic" / "intent.json").read_text(encoding="utf-8"))
        references = json.loads((Path(tmp) / ".artic" / "references.json").read_text(encoding="utf-8"))
        state = json.loads((Path(tmp) / ".artic" / "state.json").read_text(encoding="utf-8"))
        assert intent["design_north_star"]
        assert {"role", "source_ids", "selection_reason"} <= set(intent["reference_roles"][0])
        assert brief["style"]["search_facets"]
        assert brief["style"]["design_north_star"] == intent["design_north_star"]
        assert len(references["selected_sources"]) >= 3
        assert len(references["role_assignments"]) >= 3
        assert all({"id", "name", "score", "reason", "extraction_targets"} <= set(row) for row in references["selected_sources"])
        assert all({"source_id", "role", "extract", "transform", "avoid"} <= set(row) for row in references["source_plan"])
        assert state["status"] == "initialized"
        assert state["intent_path"] == ".artic/intent.json"
        assert "Reference candidates" in (Path(tmp) / "docs" / "artic-brief.md").read_text(encoding="utf-8")


def test_artic_conversational_init_collecting_writes_only_session():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        session = artic_init_session.create_or_update_session(
            root,
            "한국어로 Artic init 진행해줘. AI 회의록 서비스 랜딩을 만들고 싶어.",
        )
        assert session["status"] == "collecting"
        assert (root / ".artic" / "init-session.json").exists()
        assert session["language"]["locale"] == "ko-KR"
        assert "project" in session["answers"]
        assert session["missing"]
        assert_no_finalized_artic_outputs(root)


def test_artic_conversational_init_ready_does_not_finalize_without_start():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        session = artic_init_session.create_or_update_session(
            root,
            "AI 회의록 서비스. 타깃은 스타트업 운영팀과 세일즈팀. 목표는 데모 요청. 쉽고 신뢰감 있는 모바일 우선 SaaS 느낌.",
            answers={
                "project": "AI 회의록 서비스",
                "audience": "스타트업 운영팀과 세일즈팀",
                "goal": "데모 요청",
                "vibe": "쉽고 신뢰감 있는 모바일 우선 SaaS",
                "stack": "React Tailwind",
            },
        )
        assert session["status"] == "ready"
        assert session["missing"] == []
        assert (root / ".artic" / "init-session.json").exists()
        assert_no_finalized_artic_outputs(root)


def test_artic_conversational_init_finalize_creates_start_inputs_only_when_explicit():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        artic_init_session.create_or_update_session(
            root,
            "AI 회의록 서비스",
            answers={
                "project": "AI 회의록 서비스",
                "audience": "스타트업 운영팀과 세일즈팀",
                "goal": "데모 요청",
                "vibe": "clean trustworthy mobile-first saas",
                "stack": "React Tailwind",
            },
        )
        assert_no_finalized_artic_outputs(root)

        payload = artic_init_session.finalize_session(root, limit=4)

        assert payload["selected_count"] >= 3
        assert (root / ".artic" / "intent.json").exists()
        assert (root / ".artic" / "brief.json").exists()
        assert (root / ".artic" / "references.json").exists()
        assert (root / ".artic" / "state.json").exists()
        assert (root / "docs" / "artic-brief.md").exists()
        assert not (root / "DESIGN.md").exists()
        session = json.loads((root / ".artic" / "init-session.json").read_text(encoding="utf-8"))
        assert session["status"] == "initialized"


def test_artic_init_session_ready_payload_instructs_start_without_generating():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        session = artic_init_session.create_or_update_session(
            root,
            "AI 회의록 서비스",
            answers={
                "project": "AI 회의록 서비스",
                "audience": "스타트업 운영팀과 세일즈팀",
                "goal": "데모 요청",
                "vibe": "쉽고 신뢰감 있는 모바일 우선 SaaS",
            },
        )
        assert session["status"] == "ready"

        summary = artic_init_session.render_ready_summary(session)

        assert "@artic start" in summary
        assert "AI 회의록 서비스" in summary
        assert_no_finalized_artic_outputs(root)


def test_artic_start_ready_init_without_strategy_writes_prompt_and_refuses_generation():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        artic_init_session.create_or_update_session(
            root,
            "AI 회의록 서비스",
            answers={
                "project": "AI 회의록 서비스",
                "audience": "스타트업 운영팀과 세일즈팀",
                "goal": "데모 요청",
                "vibe": "clean trustworthy mobile-first saas",
                "stack": "React Tailwind",
            },
        )

        result = subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/artic_start.py"), "--root", tmp], capture_output=True, text=True)

        assert result.returncode != 0
        assert "strategy" in result.stdout.lower()
        assert (root / ".artic" / "strategy-prompt.md").exists()
        assert not (root / "DESIGN.md").exists()


def test_artic_start_existing_brief_without_strategy_writes_prompt_and_refuses_generation():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        subprocess.run([
            sys.executable,
            str(ROOT / "skills/artic/scripts/artic_init.py"),
            "--root",
            tmp,
            "--project",
            "Korean AI Meeting Assistant",
            "--audience",
            "startup operators and sales teams",
            "--goal",
            "demo requests",
            "--vibe",
            "clean trustworthy mobile-first saas",
            "--stack",
            "React Tailwind",
            "--limit",
            "4",
        ], check=True, capture_output=True, text=True)

        result = subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/artic_start.py"), "--root", tmp], capture_output=True, text=True)

        assert result.returncode != 0
        assert "strategy" in result.stdout.lower()
        assert (root / ".artic" / "strategy-prompt.md").exists()
        assert not (root / "DESIGN.md").exists()


def test_artic_start_invalid_strategy_reports_validation_errors():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/scaffold_artic_files.py"), "--root", tmp], check=True)
        write_fixture_strategy(root, source_ids=[])
        path = root / ".artic" / "strategy.json"
        strategy = json.loads(path.read_text(encoding="utf-8"))
        strategy.pop("design_north_star")
        path.write_text(json.dumps(strategy, indent=2) + "\n", encoding="utf-8")

        result = subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/artic_start.py"), "--root", tmp], capture_output=True, text=True)

        assert result.returncode != 0
        assert "strategy" in result.stdout.lower()
        assert "design_north_star" in result.stdout or "reference_roles" in result.stdout


def test_artic_start_valid_strategy_generates_strategy_doc_and_design_north_star():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/scaffold_artic_files.py"), "--root", tmp], check=True)
        north_star = "Signal Lantern north-star phrase for strategy-first Artic generation."
        strategy = write_fixture_strategy(root, north_star=north_star)

        result = subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/artic_start.py"), "--root", tmp], check=True, capture_output=True, text=True)

        payload = json.loads(result.stdout)
        assert payload["validated"] is True
        assert "docs/artic-strategy.md" in payload["generated_files"]
        assert payload.get("strategy", {}).get("design_north_star") == strategy["design_north_star"]
        assert (root / "docs" / "artic-strategy.md").exists()
        design = (root / "DESIGN.md").read_text(encoding="utf-8")
        assert north_star in design

def test_artic_start_generates_and_validates_docs_from_init_outputs():
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([
            sys.executable,
            str(ROOT / "skills/artic/scripts/artic_init.py"),
            "--root",
            tmp,
            "--project",
            "Korean AI Meeting Assistant",
            "--audience",
            "startup operators and sales teams",
            "--goal",
            "demo requests",
            "--vibe",
            "clean trustworthy mobile-first saas",
            "--references",
            "Linear clarity, Shopify Polaris trust, Material token discipline",
            "--stack",
            "React Tailwind",
            "--limit",
            "4",
        ], check=True)
        write_fixture_strategy(Path(tmp))
        result = subprocess.run([
            sys.executable,
            str(ROOT / "skills/artic/scripts/artic_start.py"),
            "--root",
            tmp,
        ], check=True, capture_output=True, text=True)
        payload = json.loads(result.stdout)
        assert payload["validated"] is True
        assert payload["generated_files"] == [
            "docs/artic-strategy.md",
            "DESIGN.md",
            "docs/design-rules.md",
            "docs/design-qa-checklist.md",
            "docs/homepage-design-prompt.md",
        ]
        root = Path(tmp)
        for rel in payload["generated_files"]:
            assert (root / rel).exists(), rel
        design = (root / "DESIGN.md").read_text(encoding="utf-8")
        rules = (root / "docs" / "design-rules.md").read_text(encoding="utf-8")
        assert "Korean AI Meeting Assistant" in design
        assert "## Design North Star" in design
        assert design.count("<!-- artic-policy: reference-safety-v1 -->") == 1
        assert "Reference Synthesis" in rules
        assert "## Source Application Plan" in rules
        assert "Transform:" in rules
        assert "Avoid:" in rules
        state = json.loads((root / ".artic" / "state.json").read_text(encoding="utf-8"))
        assert state["status"] == "generated"


def test_artic_start_finalizes_ready_init_session_before_generating_docs():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        artic_init_session.create_or_update_session(
            root,
            "AI 회의록 서비스",
            answers={
                "project": "AI 회의록 서비스",
                "audience": "스타트업 운영팀과 세일즈팀",
                "goal": "데모 요청",
                "vibe": "clean trustworthy mobile-first saas",
                "stack": "React Tailwind",
            },
        )
        assert_no_finalized_artic_outputs(root)

        write_fixture_strategy(root)
        result = subprocess.run([
            sys.executable,
            str(ROOT / "skills/artic/scripts/artic_start.py"),
            "--root",
            tmp,
        ], check=True, capture_output=True, text=True)

        payload = json.loads(result.stdout)
        assert payload["validated"] is True
        assert (root / ".artic" / "brief.json").exists()
        assert (root / ".artic" / "references.json").exists()
        assert (root / "DESIGN.md").exists()
        state = json.loads((root / ".artic" / "state.json").read_text(encoding="utf-8"))
        assert state["status"] == "generated"


def test_artic_start_refuses_collecting_init_session():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        artic_init_session.create_or_update_session(
            root,
            "한국어로 Artic init 진행해줘. AI 회의록 서비스 랜딩을 만들고 싶어.",
        )

        result = subprocess.run([
            sys.executable,
            str(ROOT / "skills/artic/scripts/artic_start.py"),
            "--root",
            tmp,
        ], check=False, capture_output=True, text=True)

        assert result.returncode != 0
        assert "cannot run @artic start before init is ready" in result.stdout
        assert not (root / "DESIGN.md").exists()
        assert not (root / ".artic" / "brief.json").exists()


def test_artic_start_refuses_collecting_session_even_with_stale_finalized_outputs():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        subprocess.run([
            sys.executable,
            str(ROOT / "skills/artic/scripts/artic_init.py"),
            "--root",
            tmp,
            "--project",
            "Old Project",
            "--audience",
            "old audience",
            "--goal",
            "old goal",
            "--vibe",
            "clean trustworthy mobile-first saas",
            "--stack",
            "React Tailwind",
            "--limit",
            "4",
        ], check=True, capture_output=True, text=True)
        artic_init_session.create_or_update_session(
            root,
            "한국어로 Artic init 진행해줘. AI 회의록 서비스 랜딩을 만들고 싶어.",
        )

        result = subprocess.run([
            sys.executable,
            str(ROOT / "skills/artic/scripts/artic_start.py"),
            "--root",
            tmp,
            "--no-validate",
        ], check=False, capture_output=True, text=True)

        assert result.returncode != 0
        assert "cannot run @artic start before init is ready" in result.stdout
        session = artic_init_session.read_session(root)
        assert session["status"] == "collecting"


def test_artic_start_finalizes_ready_session_over_stale_finalized_outputs():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        subprocess.run([
            sys.executable,
            str(ROOT / "skills/artic/scripts/artic_init.py"),
            "--root",
            tmp,
            "--project",
            "Old Project",
            "--audience",
            "old audience",
            "--goal",
            "old goal",
            "--vibe",
            "clean trustworthy mobile-first saas",
            "--stack",
            "React Tailwind",
            "--limit",
            "4",
        ], check=True, capture_output=True, text=True)
        artic_init_session.create_or_update_session(
            root,
            "AI 회의록 서비스",
            answers={
                "project": "AI 회의록 서비스",
                "audience": "스타트업 운영팀과 세일즈팀",
                "goal": "데모 요청",
                "vibe": "clean trustworthy mobile-first saas",
                "stack": "React Tailwind",
            },
        )

        write_fixture_strategy(root)
        subprocess.run([
            sys.executable,
            str(ROOT / "skills/artic/scripts/artic_start.py"),
            "--root",
            tmp,
        ], check=True, capture_output=True, text=True)

        brief = json.loads((root / ".artic" / "brief.json").read_text(encoding="utf-8"))
        session = artic_init_session.read_session(root)
        design = (root / "DESIGN.md").read_text(encoding="utf-8")
        assert session["status"] == "initialized"
        assert brief["project"]["name"] == "AI 회의록 서비스"
        assert "AI 회의록 서비스" in design
        assert "Old Project" not in design


def test_artic_start_synthesis_preserves_initialized_reference_selection():
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([
            sys.executable,
            str(ROOT / "skills/artic/scripts/artic_init.py"),
            "--root",
            tmp,
            "--project",
            "Korean AI Meeting Assistant",
            "--audience",
            "startup operators and sales teams",
            "--goal",
            "demo requests",
            "--vibe",
            "clean trustworthy mobile-first saas",
            "--references",
            "Linear clarity, Shopify Polaris trust, Material token discipline",
            "--stack",
            "React Tailwind",
            "--limit",
            "4",
        ], check=True)
        root = Path(tmp)
        initialized = json.loads((root / ".artic" / "references.json").read_text(encoding="utf-8"))["selected_sources"]
        initialized_ids = {row["id"] for row in initialized}
        write_fixture_strategy(root, source_ids=list(initialized_ids))
        subprocess.run([
            sys.executable,
            str(ROOT / "skills/artic/scripts/artic_start.py"),
            "--root",
            tmp,
        ], check=True, capture_output=True, text=True)

        rules = (root / "docs" / "design-rules.md").read_text(encoding="utf-8")
        synthesized_ids = set(re.findall(r"`([^`]+)`\)", rules))
        assert initialized_ids <= synthesized_ids
        assert "voltagent-awesome-design-md" not in synthesized_ids - initialized_ids


def test_artic_start_rejects_invalid_runtime_inputs_before_writing_outputs():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        subprocess.run([
            sys.executable,
            str(ROOT / "skills/artic/scripts/artic_init.py"),
            "--root",
            tmp,
            "--project",
            "Invalid Intent Fixture",
            "--audience",
            "operators",
            "--goal",
            "signup",
            "--vibe",
            "clean trustworthy saas",
            "--stack",
            "React",
            "--limit",
            "3",
        ], check=True)
        write_fixture_strategy(root)
        (root / ".artic" / "intent.json").write_text(json.dumps({"schema_version": 1}) + "\n", encoding="utf-8")

        result = subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/artic_start.py"), "--root", tmp], capture_output=True, text=True)

        assert result.returncode != 0
        assert "invalid_runtime_inputs" in result.stdout
        assert not (root / "DESIGN.md").exists()
        state = json.loads((root / ".artic" / "state.json").read_text(encoding="utf-8"))
        assert state.get("status") != "generated"


def test_validator_rejects_missing_strategy_contract():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/scaffold_artic_files.py"), "--root", tmp], check=True)
        (root / ".artic" / "strategy.json").unlink()
        result = subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/validate_artic_outputs.py"), "--root", tmp], capture_output=True, text=True)
        assert result.returncode != 0
        assert ".artic/strategy.json" in result.stdout


def test_validator_rejects_invalid_strategy_contract():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/scaffold_artic_files.py"), "--root", tmp], check=True)
        write_fixture_strategy(root, source_ids=[])
        strategy_path = root / ".artic" / "strategy.json"
        strategy = json.loads(strategy_path.read_text(encoding="utf-8"))
        strategy.pop("design_north_star")
        strategy_path.write_text(json.dumps(strategy, indent=2) + "\n", encoding="utf-8")
        result = subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/validate_artic_outputs.py"), "--root", tmp], capture_output=True, text=True)
        assert result.returncode != 0
        assert "strategy" in result.stdout.lower()
        assert "design_north_star" in result.stdout or "reference_roles" in result.stdout


def test_validator_accepts_scaffold_generated_strategy_artifacts():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/scaffold_artic_files.py"), "--root", tmp], check=True)
        assert (root / ".artic" / "strategy.json").exists()
        assert (root / "docs" / "artic-strategy.md").exists()
        result = subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/validate_artic_outputs.py"), "--root", tmp], capture_output=True, text=True)
        assert result.returncode == 0, result.stdout

def test_artic_init_role_assignments_only_reference_selected_sources():
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([
            sys.executable,
            str(ROOT / "skills/artic/scripts/artic_init.py"),
            "--root",
            tmp,
            "--project",
            "AI dev mobile app",
            "--audience",
            "startup operators",
            "--goal",
            "demo requests",
            "--vibe",
            "developer mobile ai trust",
            "--stack",
            "React Tailwind",
            "--limit",
            "3",
        ], check=True)
        references = json.loads((Path(tmp) / ".artic" / "references.json").read_text(encoding="utf-8"))
        selected_ids = {row["id"] for row in references["selected_sources"]}
        planned_ids = {row["source_id"] for row in references["source_plan"]}
        assigned_ids = {
            source_id
            for role in references["role_assignments"]
            for source_id in role.get("selected_source_ids", [])
        }
        assert assigned_ids <= selected_ids
        assert assigned_ids <= planned_ids
        write_fixture_strategy(Path(tmp))
        subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/artic_start.py"), "--root", tmp], check=True, capture_output=True, text=True)
        result = subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/validate_artic_outputs.py"), "--root", tmp], capture_output=True, text=True)
        assert result.returncode == 0, result.stdout


def test_validator_rejects_role_assignments_for_unselected_sources():
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/scaffold_artic_files.py"), "--root", tmp], check=True)
        references_path = Path(tmp) / ".artic" / "references.json"
        references = json.loads(references_path.read_text(encoding="utf-8"))
        references["role_assignments"].append({
            "role": "unselected_role",
            "source_ids": ["apple-hig"],
            "selected_source_ids": ["apple-hig"],
            "selection_reason": "Regression fixture for inconsistent role assignments.",
        })
        references_path.write_text(json.dumps(references, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        result = subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/validate_artic_outputs.py"), "--root", tmp], capture_output=True, text=True)
        assert result.returncode == 1
        assert "role assignment references unselected source: apple-hig" in result.stdout


def test_artic_start_no_validate_skips_validator_but_writes_outputs():
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/scaffold_artic_files.py"), "--root", tmp], check=True)
        write_fixture_strategy(Path(tmp))
        result = subprocess.run([
            sys.executable,
            str(ROOT / "skills/artic/scripts/artic_start.py"),
            "--root",
            tmp,
            "--no-validate",
        ], check=True, capture_output=True, text=True)
        payload = json.loads(result.stdout)
        assert payload["validated"] is False
        assert (Path(tmp) / "DESIGN.md").exists()


def test_artic_show_blocks_missing_design_inputs_without_creating_preview():
    with tempfile.TemporaryDirectory() as tmp:
        result = subprocess.run([
            sys.executable,
            str(ROOT / "skills/artic/scripts/artic_show.py"),
            "--root",
            tmp,
        ], capture_output=True, text=True)
        assert result.returncode == 1
        payload = json.loads(result.stdout)
        assert "missing required input" in payload["error"]
        assert "DESIGN.md" in payload["error"]
        assert not (Path(tmp) / ".artic" / "show").exists()


def test_artic_show_generates_static_preview_without_modifying_app_files():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/scaffold_artic_files.py"), "--root", tmp], check=True)
        app_file = root / "src" / "App.tsx"
        app_file.parent.mkdir(parents=True)
        original_app = "export default function App() { return <main>Existing app</main>; }\n"
        app_file.write_text(original_app, encoding="utf-8")

        result = subprocess.run([
            sys.executable,
            str(ROOT / "skills/artic/scripts/artic_show.py"),
            "--root",
            tmp,
        ], check=True, capture_output=True, text=True)

        payload = json.loads(result.stdout)
        preview = root / ".artic" / "show" / "index.html"
        assert payload["preview_file"] == str(preview)
        assert payload["modified_app_files"] == []
        assert preview.exists()
        assert app_file.read_text(encoding="utf-8") == original_app
        html = preview.read_text(encoding="utf-8")
        assert "<!doctype html>" in html
        assert "Artic Preview" in html
        assert "Reference policy" in html
        assert "DESIGN.md" in html


def test_artic_show_sanitizes_design_token_values_before_css_output():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/scaffold_artic_files.py"), "--root", tmp], check=True)
        design = root / "DESIGN.md"
        design.write_text(
            design.read_text(encoding="utf-8").replace(
                '  primary: "#1F4FD8"',
                '  primary: "red;} </style><script>alert(1)</script><style>"',
            ),
            encoding="utf-8",
        )

        subprocess.run([
            sys.executable,
            str(ROOT / "skills/artic/scripts/artic_show.py"),
            "--root",
            tmp,
        ], check=True, capture_output=True, text=True)

        html = (root / ".artic" / "show" / "index.html").read_text(encoding="utf-8")
        assert "<script>alert(1)</script>" not in html
        assert "--primary: #1F4FD8;" in html


def test_artic_start_migrates_legacy_init_outputs_without_intent_file():
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/scaffold_artic_files.py"), "--root", tmp], check=True)
        (Path(tmp) / ".artic" / "intent.json").unlink()
        write_fixture_strategy(Path(tmp))
        result = subprocess.run([
            sys.executable,
            str(ROOT / "skills/artic/scripts/artic_start.py"),
            "--root",
            tmp,
        ], check=True, capture_output=True, text=True)
        payload = json.loads(result.stdout)
        assert payload["validated"] is True
        intent = json.loads((Path(tmp) / ".artic" / "intent.json").read_text(encoding="utf-8"))
        assert intent["mapper"] == "artic-internal-normalized-input-legacy-migration"
        assert intent["design_north_star"]


def test_validator_rejects_non_list_role_assignments():
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/scaffold_artic_files.py"), "--root", tmp], check=True)
        references_path = Path(tmp) / ".artic" / "references.json"
        references = json.loads(references_path.read_text(encoding="utf-8"))
        references["role_assignments"] = None
        references_path.write_text(json.dumps(references, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        result = subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/validate_artic_outputs.py"), "--root", tmp], capture_output=True, text=True)
        assert result.returncode == 1
        assert "references role_assignments must be a list" in result.stdout


def test_validator_rejects_non_list_selected_source_ids():
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/scaffold_artic_files.py"), "--root", tmp], check=True)
        references_path = Path(tmp) / ".artic" / "references.json"
        references = json.loads(references_path.read_text(encoding="utf-8"))
        references["role_assignments"][0]["selected_source_ids"] = None
        references_path.write_text(json.dumps(references, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        result = subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/validate_artic_outputs.py"), "--root", tmp], capture_output=True, text=True)
        assert result.returncode == 1
        assert "role assignment selected_source_ids must be a list" in result.stdout


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
        assert "언어: ko-KR / Korean" in brief_doc
        assert "보존 용어: DESIGN.md, AI-native" in brief_doc
        assert "<!-- artic-policy: reference-safety-v1 -->" in brief_doc
        assert "참고 정책:" in brief_doc
        assert "Reference policy:" not in brief_doc


def test_locale_detection_prefers_explicit_locale_and_user_text():
    locale_contract = importlib.import_module("locale_contract")
    assert locale_contract.detect_locale_from_text("한국어 문장", explicit_locale="en-US") == "en-US"
    assert locale_contract.detect_locale_from_text("anything", explicit_locale="ko") == "ko-KR"
    assert locale_contract.detect_locale_from_text("한국 스타트업 느낌으로") == "ko-KR"
    assert locale_contract.detect_locale_from_text("日本語でお願いします") == "ja-JP"
    assert locale_contract.detect_locale_from_text("简体中文设计") == "zh-CN"


def test_artic_init_session_detects_korean_and_renders_missing_questions():
    session_mod = importlib.import_module("artic_init_session")
    with tempfile.TemporaryDirectory() as tmp:
        session = session_mod.create_or_update_session(
            Path(tmp),
            "한국 스타트업 느낌의 AI 회의록 랜딩. 토스처럼 쉽고 신뢰감 있게. 데모 요청이 목표.",
        )
        assert session["language"]["locale"] == "ko-KR"
        assert session["status"] == "collecting"
        assert session["answers"]["project"] == "AI 회의록 서비스"
        assert session["answers"]["goal"] == "데모 요청"
        assert "audience" in session["missing"]
        assert (Path(tmp) / ".artic" / "init-session.json").exists()
        questions = session_mod.render_questions(session)
        assert questions
        assert any("타깃" in question for question in questions)


def test_artic_init_session_ready_does_not_generate_outputs_before_start():
    session_mod = importlib.import_module("artic_init_session")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        session = session_mod.create_or_update_session(
            root,
            "한국어로 진행해줘",
            answers={
                "project": "AI 회의록 서비스",
                "audience": "한국 스타트업 운영팀",
                "goal": "데모 요청",
                "vibe": "쉽고 신뢰감 있는 모바일 우선 SaaS",
            },
        )
        assert session["status"] == "ready"
        assert (root / ".artic" / "init-session.json").exists()
        for rel in [
            ".artic/brief.json",
            ".artic/references.json",
            ".artic/state.json",
            "docs/artic-brief.md",
            "DESIGN.md",
            "docs/design-rules.md",
        ]:
            assert not (root / rel).exists(), rel


def test_artic_start_finalizes_ready_init_session():
    session_mod = importlib.import_module("artic_init_session")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        session_mod.write_session(root, {
            "schema_version": 1,
            "status": "ready",
            "language": {
                "locale": "ko-KR",
                "output_language": "Korean",
                "tone": "친근하지만 전문적인 제품/디자인 대화체",
                "preserve_terms": ["DESIGN.md", "AI-native", "Artic", "WCAG AA"],
                "bilingual_terms": True,
            },
            "answers": {
                "project": "AI 회의록 서비스",
                "audience": "한국 스타트업 운영팀과 세일즈팀",
                "goal": "데모 요청",
                "vibe": "토스처럼 쉽고 신뢰감 있는 모바일 우선 SaaS",
                "references": "Toss clarity, Shopify Polaris trust",
                "stack": "React Tailwind",
            },
            "missing": [],
            "last_question_ids": [],
        })
        write_fixture_strategy(root)
        subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/artic_start.py"), "--root", tmp], check=True, capture_output=True, text=True)
        assert (root / ".artic" / "brief.json").exists()
        assert (root / ".artic" / "references.json").exists()
        assert (root / "DESIGN.md").exists()
        session = session_mod.read_session(root)
        assert session["status"] == "initialized"


def test_artic_start_blocks_collecting_init_session():
    session_mod = importlib.import_module("artic_init_session")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        session_mod.create_or_update_session(root, "한국어로 AI 회의록 서비스 랜딩 만들고 싶어")
        result = subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/artic_start.py"), "--root", tmp], capture_output=True, text=True)
        assert result.returncode == 1
        assert "cannot run @artic start before init is ready" in result.stdout
        assert "missing audience, goal, vibe" in result.stdout
        assert not (root / ".artic" / "brief.json").exists()


def test_artic_init_session_finalizes_korean_outputs():
    session_mod = importlib.import_module("artic_init_session")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        session_mod.write_session(root, {
            "schema_version": 1,
            "status": "collecting",
            "language": {
                "locale": "ko-KR",
                "output_language": "Korean",
                "tone": "친근하지만 전문적인 제품/디자인 대화체",
                "preserve_terms": ["DESIGN.md", "AI-native", "Artic", "WCAG AA"],
                "bilingual_terms": True,
            },
            "answers": {
                "project": "AI 회의록 서비스",
                "audience": "한국 스타트업 운영팀과 세일즈팀",
                "goal": "데모 요청",
                "vibe": "토스처럼 쉽고 신뢰감 있는 모바일 우선 SaaS",
                "references": "Toss clarity, Shopify Polaris trust",
                "stack": "React Tailwind",
            },
            "missing": [],
            "last_question_ids": [],
        })
        payload = session_mod.finalize_session(root, limit=4)
        assert payload["language"]["locale"] == "ko-KR"
        session = session_mod.read_session(root)
        assert session["status"] == "initialized"
        brief = json.loads((root / ".artic" / "brief.json").read_text(encoding="utf-8"))
        assert brief["language"]["locale"] == "ko-KR"
        assert "참고 정책" in (root / "docs" / "artic-brief.md").read_text(encoding="utf-8")


def test_artic_start_preserves_korean_language_contract():
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([
            sys.executable,
            str(ROOT / "skills/artic/scripts/artic_init.py"),
            "--root",
            tmp,
            "--project",
            "AI 회의록 서비스",
            "--audience",
            "한국 스타트업 운영팀과 세일즈팀",
            "--goal",
            "데모 요청",
            "--vibe",
            "토스처럼 쉽고 신뢰감 있는 모바일 우선 SaaS",
            "--references",
            "Toss clarity, Shopify Polaris trust",
            "--stack",
            "React Tailwind",
            "--locale",
            "ko-KR",
            "--tone",
            "친근하지만 전문적인 제품/디자인 대화체",
            "--bilingual-terms",
            "--limit",
            "4",
        ], check=True)
        write_fixture_strategy(Path(tmp))
        subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/artic_start.py"), "--root", tmp], check=True, capture_output=True, text=True)
        root = Path(tmp)
        for rel in ["DESIGN.md", "docs/design-rules.md", "docs/design-qa-checklist.md", "docs/homepage-design-prompt.md"]:
            text = (root / rel).read_text(encoding="utf-8")
            assert "<!-- artic-language: ko-KR -->" in text, rel
            assert "Locale: ko-KR" in text, rel
            assert "<!-- artic-policy: reference-safety-v1 -->" in text, rel
            assert "참고 정책:" in text, rel


def test_artic_init_asks_asset_permission_and_start_preserves_custom_answers():
    session_mod = importlib.import_module("artic_init_session")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        session = session_mod.create_or_update_session(
            root,
            "한국어로 인터랙티브 3D 석고상 홈페이지를 만들고 싶어.",
            answers={
                "project": "중앙에 만질 수 있는 3D 석고상이 있고 회전/줌 상호작용을 제공하는 예술가 포트폴리오 홈페이지",
                "audience": "전시 기획자와 컬렉터",
                "goal": "작품 문의",
                "vibe": "고급스럽고 조용한 3D 런타임 중심",
                "stack": "React model-viewer",
                "must_have_feature": "중앙의 만질 수 있는 3D 석고상",
                "brand_constraints": "무채색, 갤러리 같은 여백",
            },
        )
        assert any("에셋" in question for question in session_mod.render_optional_questions(session))
        session = session_mod.create_or_update_session(
            root,
            "에셋 정책 답변 추가",
            answers={"asset_policy": "허용 시 CC0/CC-BY 공개 3D 에셋만 사용하고 출처를 남긴다"},
        )

        session_mod.finalize_session(root, limit=4)

        brief = json.loads((root / ".artic" / "brief.json").read_text(encoding="utf-8"))
        assert brief["project"]["name"] == "3D 석고상"
        assert "중앙에 만질 수 있는 3D 석고상" in brief["project"]["description"]
        assert brief["requirements"]["must_have_feature"] == "중앙의 만질 수 있는 3D 석고상"
        assert brief["constraints"]["brand_constraints"] == "무채색, 갤러리 같은 여백"
        assert brief["asset_policy"]["mode"] == "licensed-public-assets-allowed"
        brief_doc = (root / "docs" / "artic-brief.md").read_text(encoding="utf-8")
        assert "에셋 사용 정책" in brief_doc
        assert "외부 레퍼런스는 원칙/패턴 참고용" in brief_doc


def test_artic_asset_policy_negative_answers_keep_reference_only_boundary():
    artic_init = importlib.import_module("artic_init")
    negative_answers = [
        "do not allow external assets; references only",
        "not allowed, reference principles only",
        "외부 에셋은 허용하지 말고 원칙 참고로만 사용",
    ]
    for answer in negative_answers:
        payload = artic_init.asset_policy_payload(answer)
        assert payload["mode"] == "reference-principles-only", answer


def test_artic_start_and_show_localize_korean_3d_runtime_preview():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        subprocess.run([
            sys.executable,
            str(ROOT / "skills/artic/scripts/artic_init.py"),
            "--root",
            tmp,
            "--project",
            "중앙에 만질 수 있는 3D 석고상이 있고 회전/줌 상호작용을 제공하는 예술가 포트폴리오 홈페이지",
            "--audience",
            "전시 기획자와 컬렉터",
            "--goal",
            "작품 문의",
            "--vibe",
            "고급스럽고 조용한 3D WebGL 런타임",
            "--stack",
            "React model-viewer",
            "--locale",
            "ko-KR",
            "--requirement",
            "must_have_feature=중앙의 만질 수 있는 3D 석고상",
            "--constraint",
            "brand_constraints=무채색, 갤러리 같은 여백",
            "--asset-policy",
            "허용 시 CC0/CC-BY 공개 3D 에셋만 사용하고 출처를 남긴다",
            "--limit",
            "4",
        ], check=True)
        refs = json.loads((root / ".artic" / "references.json").read_text(encoding="utf-8"))
        write_fixture_strategy(root, source_ids=[row["id"] for row in refs["selected_sources"]])
        subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/artic_start.py"), "--root", tmp], check=True, capture_output=True, text=True)
        subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/artic_show.py"), "--root", tmp], check=True, capture_output=True, text=True)

        brief = json.loads((root / ".artic" / "brief.json").read_text(encoding="utf-8"))
        assert brief["project"]["name"] == "3D 석고상"
        design = (root / "DESIGN.md").read_text(encoding="utf-8")
        assert "is a homepage direction for" not in design
        assert "홈페이지 방향입니다" in design
        html = (root / ".artic" / "show" / "index.html").read_text(encoding="utf-8")
        assert '<html lang="ko-KR">' in html
        assert "3D 모델 자리표시자" in html
        assert "model-viewer" in html
        assert "interaction-zone" in html
        assert "homepage direction" not in html
        assert "This static preview" not in html


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


def test_validator_requires_language_marker_for_localized_outputs():
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([
            sys.executable,
            str(ROOT / "skills/artic/scripts/scaffold_artic_files.py"),
            "--root",
            tmp,
            "--locale",
            "ko-KR",
        ], check=True)
        design_path = Path(tmp) / "DESIGN.md"
        design_path.write_text(design_path.read_text(encoding="utf-8").replace("<!-- artic-language: ko-KR -->\n", ""), encoding="utf-8")
        result = subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/validate_artic_outputs.py"), "--root", tmp], capture_output=True, text=True)
        assert result.returncode == 1
        assert "localized outputs missing language marker: ko-KR" in result.stdout


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

def test_design_intent_mapper_normalizes_user_language_to_facets():
    result = subprocess.run([
        sys.executable,
        str(ROOT / "skills/artic/scripts/design_intent_mapper.py"),
        "--project",
        "B2B SaaS developer tool",
        "--audience",
        "engineering leaders",
        "--goal",
        "signup conversion",
        "--vibe",
        "Linear/Stripe 느낌으로 신뢰감 있게, 너무 기업스럽진 않게",
        "--avoid",
        "too corporate",
    ], check=True, capture_output=True, text=True)
    intent = json.loads(result.stdout)
    assert intent["selected_preset"] == "developer-tool"
    assert "developer-tool" in intent["style_facets"]
    assert "premium-saas" in intent["style_facets"]
    assert "trust" in intent["style_facets"]
    assert "heavy-corporate" in intent["avoid_facets"]
    assert "clear-cta" in intent["design_principles"]
    assert "catalog_query" in intent and "developer-tool" in intent["catalog_query"]
    assert intent["llm_contract"]["role"].startswith("Map user language")


def test_catalog_search_can_use_semantic_intent_mapping():
    result = subprocess.run([
        sys.executable,
        str(ROOT / "skills/artic/scripts/search_reference_catalog.py"),
        "--semantic-intent",
        "--project",
        "B2B SaaS developer tool",
        "--goal",
        "signup conversion",
        "--vibe",
        "Linear/Stripe 느낌으로 신뢰감 있게",
        "--avoid",
        "too corporate",
        "--limit",
        "3",
        "--include-intent",
    ], check=True, capture_output=True, text=True)
    payload = json.loads(result.stdout)
    assert "developer-tool" in payload["intent"]["style_facets"]
    assert len(payload["results"]) == 3
    assert payload["results"][0]["score"] > 0


def test_design_intent_mapper_brand_safes_korean_brand_phrases():
    result = subprocess.run([
        sys.executable,
        str(ROOT / "skills/artic/scripts/design_intent_mapper.py"),
        "--project",
        "한국 핀테크 모바일 앱",
        "--audience",
        "20-40대 한국 사용자",
        "--goal",
        "본인인증 전환",
        "--vibe",
        "토스처럼 쉽고 신뢰감 있게, 한국 앱스럽게",
    ], check=True, capture_output=True, text=True)
    intent = json.loads(result.stdout)
    assert "korean-fintech" in intent["style_facets"]
    assert "korean-mobile-native" in intent["style_facets"]
    assert "trust" in intent["style_facets"]
    assert "brand-clone" in intent["avoid_facets"]
    for principle in ["low-friction-fintech", "plain-korean-copy", "trustworthy-feedback", "pretendard-typography"]:
        assert principle in intent["design_principles"]
    assert any(role["role"] == "korean_market_fit" for role in intent["reference_roles"])
    serialized = json.dumps(intent, ensure_ascii=False).lower()
    for forbidden in ["toss_blue", "toss-logo", "kakao_yellow", "naver_green"]:
        assert forbidden not in serialized


def test_catalog_search_routes_korean_market_queries_to_korean_sources():
    result = subprocess.run([
        sys.executable,
        str(ROOT / "skills/artic/scripts/search_reference_catalog.py"),
        "--query",
        "korean mobile fintech trust onboarding privacy consent social login pretendard",
        "--limit",
        "10",
    ], check=True, capture_output=True, text=True)
    ids = {row["id"] for row in json.loads(result.stdout)}
    assert ids & {
        "daangn-seed-design",
        "pretendard-typeface",
        "kakao-login-design-guide",
        "naver-login-button-guide",
        "kwcag-22-korean-web-accessibility",
        "korean-privacy-consent-guide",
    }



def markdown_section(text: str, heading: str) -> str:
    marker = f"### {heading}"
    start = text.index(marker)
    next_heading = text.find("\n### ", start + len(marker))
    next_major = text.find("\n## ", start + len(marker))
    candidates = [idx for idx in (next_heading, next_major) if idx != -1]
    end = min(candidates) if candidates else len(text)
    return text[start:end]


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
        for heading in ["### Color Roles", "### Typography", "### Layout Rhythm", "### CTA Behavior", "### Accessibility", "## Pattern Attribution", "## Forbidden Copy Elements"]:
            assert heading in synthesis
        assert set(payload["pattern_categories"]) >= {"color_roles", "typography", "layout_rhythm", "cta_behavior", "accessibility"}


def test_reference_synthesis_keeps_safety_warnings_out_of_visual_categories():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        fixtures = root / "fixtures"
        fixtures.mkdir()
        (fixtures / "pollution-source.design.md").write_text("""---
source_id: pollution-source
source_name: Pollution Source
license: MIT
tags: [saas, ai-product, developer-tool]
---

# Pollution Regression Fixture

## Reusable Patterns
- Treat brand-inspired examples as pattern references only; never copy exact layouts, names, copy, or palettes.
- Use calm surface colors, clear borders, and contrast-safe accents.
- Preserve readable body copy with a distinct heading hierarchy.

## Components
- Feature cards should expose one primary action and one quiet secondary action.

## Accessibility
- Ensure keyboard focus states and semantic button/link distinctions.
""", encoding="utf-8")
        catalog = root / "catalog.json"
        catalog.write_text(json.dumps([{
            "id": "pollution-source",
            "name": "Pollution Source",
            "type": "design-fixture",
            "license": "MIT",
            "tags": ["saas", "ai-product", "developer-tool"],
            "strengths": ["saas developer visual patterns"],
            "use_for": ["reference synthesis"],
        }]), encoding="utf-8")
        output = root / "reference-synthesis.md"

        subprocess.run([
            sys.executable,
            str(ROOT / "skills/artic/scripts/synthesize_reference_notes.py"),
            "--query",
            "ai product developer saas",
            "--catalog",
            str(catalog),
            "--fixtures-dir",
            str(fixtures),
            "--limit",
            "1",
            "--output",
            str(output),
        ], check=True, capture_output=True, text=True)

        synthesis = output.read_text(encoding="utf-8")
        warning = "Treat brand-inspired examples as pattern references only; never copy exact layouts, names, copy, or palettes."
        assert warning not in markdown_section(synthesis, "Color Roles")
        assert warning not in markdown_section(synthesis, "Typography")
        assert warning not in markdown_section(synthesis, "Layout Rhythm")
        assert "## Reference Safety Notes" in synthesis
        assert warning in synthesis
        assert "Use calm surface colors" in markdown_section(synthesis, "Color Roles")
        assert "Preserve readable body copy" in markdown_section(synthesis, "Typography")



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


def test_validator_rejects_low_quality_design_docs():
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/scaffold_artic_files.py"), "--root", tmp], check=True)
        design = Path(tmp) / "DESIGN.md"
        text = design.read_text(encoding="utf-8")
        text = text.replace("  h2:\n    fontFamily: Inter\n    fontSize: 2.5rem\n    fontWeight: 720\n    lineHeight: 1.12\n", "")
        text = text.replace("## Responsive Behavior\n\nMobile-first: stack sections, keep one primary CTA visible, and preserve readable line lengths.\n\n", "")
        design.write_text(text, encoding="utf-8")
        result = subprocess.run([sys.executable, str(ROOT / "skills/artic/scripts/validate_artic_outputs.py"), "--root", tmp], capture_output=True, text=True)
        assert result.returncode != 0
        assert "typography missing quality token: h2" in result.stdout
        assert "DESIGN.md missing section: ## Responsive Behavior" in result.stdout


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


def test_design_templates_include_quality_guardrails_and_review_scoring():
    for rel in [
        "skills/artic/templates/DESIGN.template.md",
        "plugins/claude-artic/skills/artic/templates/DESIGN.template.md",
        "plugins/codex-artic/skills/artic/templates/DESIGN.template.md",
    ]:
        text = (ROOT / rel).read_text(encoding="utf-8")
        for snippet in ["## Page Composition", "## Visual Hierarchy", "## Responsive Behavior", "## Motion", "## Anti-Patterns"]:
            assert snippet in text, (rel, snippet)
        for token in ["  h3:", "  caption:", "  section:", "  form-field:", "  proof-strip:"]:
            assert token in text, (rel, token)
    checklist = (ROOT / "skills/artic/templates/design-qa-checklist.template.md").read_text(encoding="utf-8")
    for snippet in ["Visual hierarchy", "Brand coherence", "Conversion clarity", "Mobile quality", "Reference safety"]:
        assert snippet in checklist


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
        "scripts/artic_init.py",
        "scripts/artic_start.py",
        "scripts/artic_version.py",
        "scripts/artic_update.py",
        "scripts/synthesize_reference_notes.py",
        "scripts/scaffold_artic_files.py",
        "scripts/validate_artic_outputs.py",
        "scripts/validate_artic_strategy.py",
        "templates/strategy.schema.json",
        "templates/strategy-prompt.template.md",
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
    skill_paths = [
        ROOT / "skills" / "artic" / "SKILL.md",
        ROOT / "plugins" / "claude-artic" / "skills" / "artic" / "SKILL.md",
        ROOT / "plugins" / "codex-artic" / "skills" / "artic" / "SKILL.md",
    ]
    for path in skill_paths:
        skill_text = path.read_text(encoding="utf-8")
        skill_version = re.search(r"^version: ([^\n]+)", skill_text, re.MULTILINE)
        assert skill_version and skill_version.group(1).strip() == version, path
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"## {version}" in changelog


def test_version_command_reports_installed_versions_without_network():
    script = ROOT / "skills" / "artic" / "scripts" / "artic_version.py"
    result = subprocess.run([
        sys.executable,
        str(script),
        "--root",
        str(ROOT),
        "--no-network",
        "--json",
    ], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["installed"]["pyproject"] == project_version()
    assert payload["installed"]["skill"] == project_version()
    assert payload["status"] == "latest-unchecked"
    assert payload["version_mismatches"] == []


def test_update_command_is_dry_run_by_default_without_network():
    script = ROOT / "skills" / "artic" / "scripts" / "artic_update.py"
    result = subprocess.run([
        sys.executable,
        str(script),
        "--root",
        str(ROOT),
        "--no-network",
    ], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr or result.stdout
    assert "No files were modified" in result.stdout
    assert "codex plugin marketplace add baskduf/artic" in result.stdout
    assert "/plugin marketplace add baskduf/artic" in result.stdout


def test_version_command_supports_installed_plugin_roots_without_network():
    for plugin_root, expected_key in [
        (ROOT / "plugins" / "claude-artic", "claude_plugin"),
        (ROOT / "plugins" / "codex-artic", "codex_plugin"),
    ]:
        script = plugin_root / "skills" / "artic" / "scripts" / "artic_version.py"
        result = subprocess.run([
            sys.executable,
            str(script),
            "--root",
            str(plugin_root),
            "--no-network",
            "--json",
        ], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr or result.stdout
        payload = json.loads(result.stdout)
        assert payload["installed"]["skill"] == project_version()
        assert payload["installed"][expected_key] == project_version()
        assert payload["status"] == "latest-unchecked"
        assert payload["version_mismatches"] == []


def test_update_command_supports_installed_plugin_roots_without_network():
    script = ROOT / "plugins" / "claude-artic" / "skills" / "artic" / "scripts" / "artic_update.py"
    result = subprocess.run([
        sys.executable,
        str(script),
        "--root",
        str(ROOT / "plugins" / "claude-artic"),
        "--no-network",
    ], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr or result.stdout
    assert f"Current: {project_version()}" in result.stdout
    assert "Blocked:" not in result.stdout
    assert "No files were modified" in result.stdout


def test_skill_docs_expose_version_update_start_and_show_commands():
    for rel in [
        "skills/artic/SKILL.md",
        "plugins/claude-artic/skills/artic/SKILL.md",
        "plugins/codex-artic/skills/artic/SKILL.md",
    ]:
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert "@artic start" in text, rel
        assert "artic_start.py --root <project-root>" in text, rel
        assert "@artic show" in text, rel
        assert "artic_show.py --root <project-root>" in text, rel
        assert ".artic/show/index.html" in text, rel
        assert "@artic version" in text, rel
        assert "@artic update" in text, rel


def test_skill_docs_expose_shared_catalog_curation_instruction():
    required_phrases = [
        "Shared Catalog Curation Instruction",
        "user-facing design intelligence",
        "not an internal audit log",
        "application guidance",
        "project-specific homepage/design docs",
    ]
    for rel in [
        "skills/artic/SKILL.md",
        "plugins/claude-artic/skills/artic/SKILL.md",
        "plugins/codex-artic/skills/artic/SKILL.md",
    ]:
        text = (ROOT / rel).read_text(encoding="utf-8")
        for phrase in required_phrases:
            assert phrase in text, (rel, phrase)


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
    for workflow in [ci, release]:
        assert "check_release_artifacts.py" in workflow
        assert "build_skill_archive.py" in workflow


def test_release_artifact_checker_rejects_bytecode_and_requires_payload():
    checker = ROOT / "scripts" / "check_release_artifacts.py"
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        bad_tar = root / "bad.tar.gz"
        payload = root / "payload"
        (payload / "skills/artic/scripts/__pycache__").mkdir(parents=True)
        (payload / "skills/artic/SKILL.md").write_text("skill", encoding="utf-8")
        (payload / "skills/artic/references").mkdir(parents=True)
        (payload / "skills/artic/references/source-catalog.json").write_text("[]", encoding="utf-8")
        (payload / "skills/artic/scripts/artic_init.py").write_text("", encoding="utf-8")
        (payload / "skills/artic/scripts/artic_start.py").write_text("", encoding="utf-8")
        (payload / "skills/artic/scripts/artic_version.py").write_text("", encoding="utf-8")
        (payload / "skills/artic/scripts/artic_update.py").write_text("", encoding="utf-8")
        (payload / "skills/artic/scripts/search_reference_catalog.py").write_text("", encoding="utf-8")
        (payload / "skills/artic/scripts/synthesize_reference_notes.py").write_text("", encoding="utf-8")
        (payload / "skills/artic/scripts/validate_artic_outputs.py").write_text("", encoding="utf-8")
        (payload  / "skills/artic/scripts/validate_artic_strategy.py").write_text("", encoding="utf-8")
        (payload  / "skills/artic/templates").mkdir(parents=True, exist_ok=True)
        (payload  / "skills/artic/templates/strategy.schema.json").write_text("{}", encoding="utf-8")
        (payload  / "skills/artic/templates/strategy-prompt.template.md").write_text("prompt", encoding="utf-8")
        (payload / "plugins/claude-artic/.claude-plugin").mkdir(parents=True)
        (payload / "plugins/claude-artic/.claude-plugin/plugin.json").write_text("{}", encoding="utf-8")
        (payload / "plugins/codex-artic/.codex-plugin").mkdir(parents=True)
        (payload / "plugins/codex-artic/.codex-plugin/plugin.json").write_text("{}", encoding="utf-8")
        (payload / "skills/artic/scripts/__pycache__/artic_init.cpython-39.pyc").write_bytes(b"bad")
        with tarfile.open(bad_tar, "w:gz") as tf:
            tf.add(payload, arcname=f"artic-{project_version()}")
        result = subprocess.run([sys.executable, str(checker), "--require-payload", str(bad_tar)], capture_output=True, text=True)
        assert result.returncode != 0
        assert "forbidden bytecode/cache entry" in result.stdout

        missing_command_tar = root / "missing-command.tar.gz"
        clean_payload = root / "clean-payload"
        (clean_payload / "skills/artic/scripts").mkdir(parents=True)
        (clean_payload / "skills/artic/SKILL.md").write_text("skill", encoding="utf-8")
        (clean_payload / "skills/artic/references").mkdir(parents=True)
        (clean_payload / "skills/artic/references/source-catalog.json").write_text("[]", encoding="utf-8")
        (clean_payload / "skills/artic/scripts/artic_init.py").write_text("", encoding="utf-8")
        (clean_payload / "skills/artic/scripts/artic_start.py").write_text("", encoding="utf-8")
        (clean_payload / "skills/artic/scripts/artic_version.py").write_text("", encoding="utf-8")
        (clean_payload / "skills/artic/scripts/artic_update.py").write_text("", encoding="utf-8")
        (clean_payload / "skills/artic/scripts/search_reference_catalog.py").write_text("", encoding="utf-8")
        (clean_payload / "skills/artic/scripts/synthesize_reference_notes.py").write_text("", encoding="utf-8")
        (clean_payload / "skills/artic/scripts/validate_artic_outputs.py").write_text("", encoding="utf-8")
        (clean_payload  / "skills/artic/templates").mkdir(parents=True, exist_ok=True)
        (clean_payload  / "skills/artic/templates/strategy.schema.json").write_text("{}", encoding="utf-8")
        (clean_payload  / "skills/artic/templates/strategy-prompt.template.md").write_text("prompt", encoding="utf-8")
        (clean_payload / "plugins/claude-artic/.claude-plugin").mkdir(parents=True)
        (clean_payload / "plugins/claude-artic/.claude-plugin/plugin.json").write_text("{}", encoding="utf-8")
        (clean_payload / "plugins/codex-artic/.codex-plugin").mkdir(parents=True)
        (clean_payload / "plugins/codex-artic/.codex-plugin/plugin.json").write_text("{}", encoding="utf-8")
        with tarfile.open(missing_command_tar, "w:gz") as tf:
            tf.add(clean_payload, arcname=f"artic-{project_version()}")
        result = subprocess.run([sys.executable, str(checker), "--require-payload", str(missing_command_tar)], capture_output=True, text=True)
        assert result.returncode != 0
        assert "missing required payload skills/artic/scripts/validate_artic_strategy.py" in result.stdout

        good_zip = root / "metadata.whl"
        with zipfile.ZipFile(good_zip, "w") as zf:
            zf.writestr(f"artic-{project_version()}.dist-info/METADATA", f"Name: artic\nVersion: {project_version()}\n")
        result = subprocess.run([sys.executable, str(checker), str(good_zip)], capture_output=True, text=True)
        assert result.returncode == 0, result.stdout


def test_skill_archive_builder_excludes_bytecode_from_marketplace_archive():
    builder = ROOT / "scripts" / "build_skill_archive.py"
    checker = ROOT / "scripts" / "check_release_artifacts.py"
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / f"artic-skill-{project_tag()}.tar.gz"
        subprocess.run([sys.executable, str(builder), "--root", str(ROOT), "--output", str(output)], check=True)
        result = subprocess.run([sys.executable, str(checker), "--require-payload", str(output)], capture_output=True, text=True)
        assert result.returncode == 0, result.stdout


def test_manifest_excludes_bytecode_from_source_distribution():
    manifest = (ROOT / "MANIFEST.in").read_text(encoding="utf-8")
    assert "global-exclude *.py[cod]" in manifest
    assert "global-exclude __pycache__/*" in manifest


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
