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
Artic は、実装前に参照駆動の AI-native ホームページデザイン文書を作る Claude/Codex 互換 skill です。

公開されるユーザーフローは小さくシンプルです:

```text
@artic init      # 意図と参照を収集
@artic start     # DESIGN.md と補助文書を生成
@artic show      # 安全な静的 preview をレンダリング
@artic review    # 実装を文書に照らして確認
```

エージェントは内部で、ユーザーへのヒアリング、brief の検索 facet 化、専門/OSS デザイン参照の検索、再利用可能なパターン合成、`DESIGN.md` 生成、出力検証を処理します。

> Artic は参照サイトを **クローンしません**。専門/OSS デザインシステムから再利用可能な原則を抽出し、プロジェクト固有の AI-native 文書へコンパイルします。

## Quick Start

### Claude Code marketplace

marketplace パッケージをインストールします:

```text
/plugin marketplace add baskduf/artic
/plugin install claude-artic@artic
```

同梱 skill を実行します:

```text
/claude-artic:artic init
/claude-artic:artic start
/claude-artic:artic show
```

自然文でも依頼できます:

```text
このホームページを作る前に Artic で AI-native デザイン文書を作って。
```

### Codex marketplace

現在のデフォルトブランチから marketplace を追加します:

```bash
codex plugin marketplace add baskduf/artic
```

安定したインストールが必要な場合はリリースタグに固定します:

```bash
codex plugin marketplace add baskduf/artic@v0.3.0
```

プラグインブラウザから `codex-artic` をインストールします:

```text
/plugins
```

またはプラグインを直接インストールします:

```bash
codex plugin add codex-artic@artic
```

Codex に依頼します:

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

Artic が呼び出されると、エージェントは次を行います:

1. ホームページ/デザイン依頼が曖昧な場合、実装前に立ち止まります。
2. `@artic init` で product、audience、goal、vibe、constraints、references を収集します。
3. Search multiple professional/OSS design resources instead of relying on one style.
4. Extract reusable rules: color roles, type hierarchy, spacing rhythm, components, motion, accessibility.
5. Resolve conflicts between references based on the user's project goal.
6. `@artic start` で `DESIGN.md` と補助文書を生成します。
7. `@artic show` で、アプリのソースファイルを変更しない安全な静的 preview `.artic/show/index.html` をレンダリングします。
8. 実装前に生成されたデザイン文書を検証します。

## When To Use It

使う場面:

- Homepages, landing pages, product pages, and website redesigns.
- Projects with weak or missing design docs.
- AI-native design documentation before coding.
- Reference-driven design direction without exact brand copying.

使わない場面:

- Exact cloning of a website or brand.
- Logo, trademark, illustration, or copyrighted asset copying.
- One-off graphic design with no website/doc output.

## How Users Control It

| 目的 | コマンド |
| --- | --- |
| デザインヒアリング開始 | `@artic init` |
| 高速ヒアリング実行 | `@artic init quick` |
| 文書をコンパイル | `@artic start` |
| 安全な静的 preview をレンダリング | `@artic show` |
| 実装をレビュー | `@artic review the homepage against DESIGN.md` |
| インストール済み/最新バージョン確認 | `@artic version` |
| 安全な更新コマンド表示 | `@artic update` |

`@artic init` は会話型の draft 状態だけを `.artic/init-session.json` に保存します。必須情報がそろっても自動では文書を生成せず、ユーザーが明示的に `@artic start` を実行したときだけ生成を開始します。

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
.artic/show/index.html     # @artic show が生成する preview 専用ファイル。デフォルトではアプリファイルを変更しません
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
