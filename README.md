<div align="center">
<img width="110" alt="Artic logo" src="assets/artic-logo.png" />

  <h1>Artic</h1>

  <p>
    <strong>Reference-driven AI-native design docs for better homepages.</strong>
  </p>


  <p>
    English | <a href="README.ko.md">한국어</a> | <a href="README.ja.md">日本語</a> | <a href="README.zh-CN.md">简体中文</a> | <a href="README.zh-TW.md">繁體中文（台灣）</a>
  </p>
</div>

---
Artic is a Claude/Codex-compatible agent design-direction protocol: a contract-bound LLM design director for homepage work before implementation.

It keeps the public workflow small:

```text
@artic init      # collect intent and references
@artic start     # author strategy artifacts, then compile DESIGN.md docs
@artic show      # render a provenance-recorded asset-first preview bundle
@artic review    # check implementation against the docs
```

The agent handles the design-direction work: interview the user, normalize the brief into search facets, search professional/open-source design references, author `.artic/strategy.json`, compile it into `DESIGN.md` and supporting docs, then validate the output. Scripts are validator/compiler/renderer helpers; they do not replace the agent's design judgment or strategy authorship.

> Artic does **not** clone reference sites. It extracts reusable principles from professional and OSS design systems, then binds implementation to project-specific strategy and AI-native docs.

## Quick Start

### Claude Code marketplace

Install the marketplace package:

```text
/plugin marketplace add baskduf/artic
/plugin install claude-artic@artic
```

Run the bundled skill:

```text
/claude-artic:artic init
/claude-artic:artic start
/claude-artic:artic show
```

Or ask naturally:

```text
Use Artic to create AI-native design docs before building this homepage.
```

### Codex marketplace

Add the marketplace from the current default branch:

```bash
codex plugin marketplace add baskduf/artic
```

Pin a released version when you want a stable install:

```bash
codex plugin marketplace add baskduf/artic@v0.3.0
```

Install `codex-artic` from the plugin browser:

```text
/plugins
```

Or install the plugin directly:

```bash
codex plugin add codex-artic@artic
```

Then ask Codex:

```text
@artic init
@artic start
@artic show
```

### Local checkout fallback

```text
skills/artic                         # Claude/Hermes-style skill folder
plugins/claude-artic                 # Claude Code plugin package
plugins/codex-artic                  # Codex plugin package
```

### Helper scripts

```bash
python3 skills/artic/scripts/search_reference_catalog.py --query "ai product developer saas" --limit 3
python3 skills/artic/scripts/synthesize_reference_notes.py --query "ai product developer saas" --limit 3 --output /tmp/artic-smoke/docs/reference-synthesis.md
python3 skills/artic/scripts/synthesize_reference_notes.py --query "ai product developer saas" --limit 3 --live-fetch --cache-dir /tmp/artic-cache --fixtures-dir /tmp/no-fixtures --output /tmp/artic-smoke/docs/live-reference-synthesis.md
python3 skills/artic/scripts/scaffold_artic_files.py --root /tmp/artic-smoke
python3 skills/artic/scripts/validate_artic_outputs.py --root /tmp/artic-smoke
python3 skills/artic/scripts/artic_show.py --root .
python3 skills/artic/scripts/artic_version.py --root .
python3 skills/artic/scripts/artic_update.py --root .
```

Helper scripts are deterministic helpers: `validate_artic_outputs.py` validates contracts, `artic_start.py` compiles agent-authored strategy into docs, and `artic_show.py` renders previews. They are not the source of design judgment; the public `@artic start` agent workflow supplies that judgment in `.artic/strategy.json`.

## What Changes In The Agent

When invoked, Artic asks the agent to:

1. Pause before implementation when a homepage/design request is vague.
2. Run `@artic init` to collect product, audience, goal, vibe, constraints, and references.
3. Search multiple professional/OSS design resources instead of relying on one style.
4. Extract reusable rules: color roles, type hierarchy, spacing rhythm, components, motion, accessibility.
5. Resolve conflicts between references based on the user's project goal.
6. Run `@artic start` so the public agent workflow authors `.artic/strategy.json`, writes `docs/artic-strategy.md`, then runs the compiler for `DESIGN.md` and supporting docs.
7. Run `@artic show` to render a provenance-recorded asset-first visual draft bundle under `.artic/show/` without changing app source files.
8. Run `@artic review` to compare implementation against `.artic/strategy.json`, `docs/artic-strategy.md`, and `DESIGN.md`, then validate the generated design docs before implementation.

## When To Use It

Use it for:

- Homepages, landing pages, product pages, and website redesigns.
- Projects with weak or missing design docs.
- AI-native design documentation before coding.
- Reference-driven design direction without exact brand copying.

Skip it for:

- Exact cloning of a website or brand.
- Logo, trademark, illustration, or copyrighted asset copying.
- One-off graphic design with no website/doc output.

## How Users Control It

| Goal | Command |
| --- | --- |
| Start the design interview | `@artic init` |
| Run the fast interview | `@artic init quick` |
| Author strategy and compile docs | `@artic start` |
| Render an asset-first preview bundle from strategy artifacts | `@artic show` |
| Review implementation against strategy + `DESIGN.md` | `@artic review the homepage against DESIGN.md` |
| Check installed/latest version | `@artic version` |
| Print safe update commands | `@artic update` |

`@artic init` follows the user's language. For example, `한국어로 Artic init 진행해줘. AI 회의록 서비스 랜딩을 만들고 싶어.` starts a Korean interview, stores `ko-KR` in `.artic/init-session.json.language`, asks for missing fields, and does not generate design artifacts until `@artic start`.

`@artic init` only saves draft interview state. Even when the required fields are complete, document generation starts only after the user explicitly runs `@artic start`.

`@artic start` has two layers. The public agent workflow is the design-director layer: it uses the completed intake and references to author `.artic/strategy.json` and `docs/artic-strategy.md`, then invokes the deterministic compiler. The raw `artic_start.py` fallback is compiler-only: if strategy is missing, it writes `.artic/strategy-prompt.md` with the questions the agent must answer and exits non-zero instead of inventing design direction.

## Output Policy

Artic writes durable files instead of dumping long design prose into chat:

```text
.artic/init-session.json   # draft interview state from @artic init
.artic/brief.json          # finalized by @artic start
.artic/references.json     # finalized by @artic start
.artic/strategy.json       # agent-authored design-direction contract for @artic start
.artic/strategy-prompt.md  # raw compiler fallback prompt when strategy is missing
.artic/state.json
docs/artic-brief.md
docs/artic-strategy.md     # human-readable strategy contract
DESIGN.md
docs/design-rules.md
docs/design-qa-checklist.md
docs/homepage-design-prompt.md
.artic/show/index.html
.artic/show/styles.css
.artic/show/tokens.json
.artic/show/assets/manifest.json  # asset provenance; unverified assets are preview-only, not production-cleared
.artic/show/report.json
.artic/show/critique.md
.artic/show/selected.json
.artic/show/iterations/<NNN>/...  # generated by @artic show; app files unchanged
```

## Repository Layout

```text
.claude-plugin/marketplace.json       # Claude Code marketplace manifest
.agents/plugins/marketplace.json      # Codex marketplace manifest
skills/artic/                         # Claude/Hermes-style skill folder
plugins/claude-artic/                 # Claude Code plugin package
plugins/codex-artic/                  # Codex plugin package
examples/prompts.md                   # Example prompts and commands
tests/                                # Manifest, sync, README, and script checks
```

## Development

```bash
python3 -m pip install pytest pyyaml
python3 -m pytest -q
```

CI validates Python scripts, JSON manifests, README translation structure, skill-copy sync, smoke scaffolding, warning-free DESIGN.md lint, and marketplace plugin layout.

Distribution note: the wheel is metadata-only; marketplace packages, release tarballs, and sdists carry the skill/plugin payload.

## Community

- Read `CONTRIBUTING.md` before opening a pull request.
- Report sensitive issues using `SECURITY.md`; do not post secrets or private design assets in public issues.
- Follow `CODE_OF_CONDUCT.md` in issues and pull requests.

## License

MIT
