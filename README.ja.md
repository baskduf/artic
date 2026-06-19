<div align="center">
<img width="300" height="300" alt=" -7" src="https://github.com/user-attachments/assets/d624d91c-6ae8-4c44-89d2-0a9058377e43" />

  <h1>Artic</h1>

  <p>
    <strong>より良いホームページのための参照駆動 AI-native デザイン文書。</strong>
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
    <a href="README.md">English</a> | <a href="README.ko.md">한국어</a> | 日本語 | <a href="README.zh-CN.md">简体中文</a> | <a href="README.zh-TW.md">繁體中文（台灣）</a>
  </p>
</div>

---
Artic は、ホームページのデザイン意図を AI-native なデザイン文書へ変換する Claude/Codex 互換 skill です。

内部パイプラインではなく、ユーザーフローを中心に設計されています:

```text
@artic init
@artic init quick
@artic start
@artic review
```

エージェントは、ユーザーへのヒアリング、brief の検索 facet 化、専門/OSS デザイン参照の検索、パターン合成、`DESIGN.md` 生成、出力検証を処理します。

> Artic は参照サイトを **クローンしません**。
> 専門/OSS デザインシステムから再利用可能な原則を抽出し、プロジェクト固有の AI-native 文書へコンパイルします。

## Quick Start

### Claude Code marketplace

```text
/plugin marketplace add baskduf/artic
/plugin install claude-artic@artic
```

Then invoke the bundled skill:

```text
/claude-artic:artic init
/claude-artic:artic start
```

Or ask naturally:

```text
Use Artic to create AI-native design docs before building this homepage.
```

### Codex marketplace

リポジトリの現在のデフォルトブランチから marketplace を追加します:

```bash
codex plugin marketplace add baskduf/artic
```

GitHub Release が存在する場合は、明示的なタグに固定できます:

```bash
codex plugin marketplace add baskduf/artic@<tag>
```

Then open the plugin browser and install `codex-artic`:

```text
/plugins
```

Then ask Codex:

```text
@artic init
@artic start
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
```

## What Changes In The Agent

When invoked, Artic asks the agent to:

1. Accept vague homepage/design requests without jumping straight to implementation.
2. Run `@artic init` to collect product, audience, goal, vibe, constraints, and references.
3. Search multiple professional/OSS design resources instead of relying on one style.
4. Extract reusable rules: color roles, type hierarchy, spacing rhythm, components, motion, accessibility.
5. Resolve conflicts between references based on the user's project goal.
6. Run `@artic start` to generate `DESIGN.md` and supporting docs.
7. Validate the generated design docs before implementation.

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

Design interview:

```text
@artic init
```

Fast interview:

```text
@artic init quick
```

Compile docs:

```text
@artic start
```

Review implementation:

```text
@artic review the homepage against DESIGN.md
```

## Output Policy

Artic writes durable files instead of dumping long design prose into chat:

```text
.artic/brief.json
.artic/references.json
.artic/state.json
docs/artic-brief.md
DESIGN.md
docs/design-rules.md
docs/design-qa-checklist.md
docs/homepage-design-prompt.md
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
