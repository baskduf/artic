<div align="center">
<img width="300" height="300" alt=" -7" src="https://github.com/user-attachments/assets/d624d91c-6ae8-4c44-89d2-0a9058377e43" />

  <h1>Artic</h1>

  <p>
    <strong>面向更好首页的参考驱动 AI-native 设计文档。</strong>
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
    <a href="README.md">English</a> | <a href="README.ko.md">한국어</a> | <a href="README.ja.md">日本語</a> | 简体中文 | <a href="README.zh-TW.md">繁體中文（台灣）</a>
  </p>
</div>

---
Artic 是一个兼容 Claude/Codex 的 skill，用于把首页设计意图转成 AI-native 设计文档。

它围绕用户流程设计，而不是暴露内部流水线：

```text
@artic init
@artic init quick
@artic start
@artic review
```

Agent 会处理内部流程：访谈用户、把 brief 归一化为搜索 facets、检索专业/开源设计参考、合成兼容模式、生成 `DESIGN.md` 并验证输出。

> Artic **不会** 克隆参考网站。
> 它从专业/OSS 设计系统中提取可复用原则，并编译成项目专属的 AI-native 文档。

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

```bash
codex plugin marketplace add baskduf/artic
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

CI validates Python scripts, JSON manifests, README translation structure, skill-copy sync, and smoke scaffolding.

## Community

- Read `CONTRIBUTING.md` before opening a pull request.
- Report sensitive issues using `SECURITY.md`; do not post secrets or private design assets in public issues.
- Follow `CODE_OF_CONDUCT.md` in issues and pull requests.

## License

MIT
