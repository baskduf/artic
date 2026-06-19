<div align="center">
<img width="300" height="300" alt=" -7" src="https://github.com/user-attachments/assets/d624d91c-6ae8-4c44-89d2-0a9058377e43" />

  <h1>Artic</h1>

  <p>
    <strong>為更好的首頁而生的參考驅動 AI-native 設計文件。</strong>
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
    <a href="README.md">English</a> | <a href="README.ko.md">한국어</a> | <a href="README.ja.md">日本語</a> | <a href="README.zh-CN.md">简体中文</a> | 繁體中文（台灣）
  </p>
</div>

---
Artic 是一個相容 Claude/Codex 的 skill，用來把首頁設計意圖轉成 AI-native 設計文件。

它以使用者流程為中心，而不是暴露內部管線：

```text
@artic init
@artic init quick
@artic start
@artic review
```

Agent 會處理內部流程：訪談使用者、把 brief 正規化為搜尋 facets、檢索專業/開源設計參考、合成相容模式、生成 `DESIGN.md` 並驗證輸出。

> Artic **不會** 複製參考網站。
> 它會從專業/OSS 設計系統中萃取可重用原則，並編譯成專案專屬的 AI-native 文件。

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

從儲存庫目前的預設分支新增 marketplace：

```bash
codex plugin marketplace add baskduf/artic
```

如果已有 GitHub Release，可以改為固定明確標籤：

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
python3 skills/artic/scripts/artic_version.py --root .
python3 skills/artic/scripts/artic_update.py --root .
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

檢查已安裝的 Artic 版本與最新 GitHub Release：

```text
@artic version
```

輸出適用於 Claude Code、Codex 或 local checkout 的安全更新命令：

```text
@artic update
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
