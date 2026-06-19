<div align="center">
<img width="300" height="300" alt=" -7" src="https://github.com/user-attachments/assets/d624d91c-6ae8-4c44-89d2-0a9058377e43" />

  <h1>Artic</h1>

  <p>
    <strong>Reference-driven AI-native design docs for better homepages.</strong>
  </p>

  <p>
    <img alt="Claude Skill" src="https://img.shields.io/badge/Claude-Skill-D97745?style=for-the-badge" />
    <img alt="Codex Plugin" src="https://img.shields.io/badge/Codex-Plugin-black?style=for-the-badge" />
    <img alt="DESIGN.md" src="https://img.shields.io/badge/DESIGN.md-AI_Native-39C5BB?style=for-the-badge" />
    <img alt="License MIT" src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" />
    <a href="https://github.com/baskduf/artic/actions/workflows/ci.yml">
      <img alt="CI" src="https://img.shields.io/github/actions/workflow/status/baskduf/artic/ci.yml?branch=main&label=CI&style=for-the-badge" />
    </a>
  </p>

  <p>
    English | <a href="README.ko.md">한국어</a> | <a href="README.ja.md">日本語</a> | <a href="README.zh-CN.md">简体中文</a> | <a href="README.zh-TW.md">繁體中文（台灣）</a>
  </p>
</div>

---
Artic is a Claude/Codex-compatible skill for creating reference-driven, AI-native homepage design docs before implementation.

It keeps the public workflow small:

```text
@artic init      # collect intent and references
@artic start     # generate DESIGN.md and supporting docs
@artic show      # render a safe static preview
@artic review    # check implementation against the docs
```

The agent handles the internal work: interview the user, normalize the brief into search facets, search professional/open-source design references, synthesize reusable patterns, generate `DESIGN.md`, and validate the output.

> Artic does **not** clone reference sites. It extracts reusable principles from professional and OSS design systems, then compiles project-specific AI-native docs.

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

## What Changes In The Agent

When invoked, Artic asks the agent to:

1. Pause before implementation when a homepage/design request is vague.
2. Run `@artic init` to collect product, audience, goal, vibe, constraints, and references.
3. Search multiple professional/OSS design resources instead of relying on one style.
4. Extract reusable rules: color roles, type hierarchy, spacing rhythm, components, motion, accessibility.
5. Resolve conflicts between references based on the user's project goal.
6. Run `@artic start` to generate `DESIGN.md` and supporting docs.
7. Run `@artic show` to render `.artic/show/index.html` as a safe static preview without changing app source files.
8. Validate the generated design docs before implementation.

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
| Compile docs | `@artic start` |
| Render a safe static preview | `@artic show` |
| Review implementation | `@artic review the homepage against DESIGN.md` |
| Check installed/latest version | `@artic version` |
| Print safe update commands | `@artic update` |

`@artic init` follows the user's language. For example, `한국어로 Artic init 진행해줘. AI 회의록 서비스 랜딩을 만들고 싶어.` starts a Korean interview, stores `ko-KR` in `.artic/init-session.json.language`, asks for missing fields, and does not generate design artifacts until `@artic start`.

`@artic init` only saves draft interview state. Even when the required fields are complete, document generation starts only after the user explicitly runs `@artic start`.

## Output Policy

Artic writes durable files instead of dumping long design prose into chat:

```text
.artic/init-session.json   # draft interview state from @artic init
.artic/brief.json          # finalized by @artic start
.artic/references.json     # finalized by @artic start
.artic/state.json
docs/artic-brief.md
DESIGN.md
docs/design-rules.md
docs/design-qa-checklist.md
docs/homepage-design-prompt.md
.artic/show/index.html     # generated by @artic show; preview only, app files unchanged by default
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
