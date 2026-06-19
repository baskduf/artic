<div align="center">
<img width="110" alt="Artic logo" src="assets/artic-logo.png" />

  <h1>Artic</h1>

  <p>
    <strong>より良いホームページのための参照駆動 AI-native デザイン文書。</strong>
  </p>


  <p>
    <a href="README.md">English</a> | <a href="README.ko.md">한국어</a> | 日本語 | <a href="README.zh-CN.md">简体中文</a> | <a href="README.zh-TW.md">繁體中文（台灣）</a>
  </p>
</div>

---
Artic は、実装前にホームページのデザイン方向を契約として固定する Claude/Codex 互換の agent design-direction protocol であり、contract-bound LLM design director です。

公開されるユーザーフローは小さくシンプルです:

```text
@artic init      # 意図と参照を収集
@artic start     # strategy artifacts を作成し DESIGN.md 文書をコンパイル
@artic show      # provenance を記録した asset-first preview bundle をレンダリング
@artic review    # 実装を文書に照らして確認
```

エージェントは内部で、ユーザーへのヒアリング、brief の検索 facet 化、専門/OSS デザイン参照の検索、`.artic/strategy.json` 作成、`DESIGN.md` と補助文書のコンパイル、出力検証を処理します。スクリプトは validator/compiler/renderer helper であり、design judgment や strategy authorship を置き換えません。

> Artic は参照サイトを **クローンしません**。専門/OSS デザインシステムから再利用可能な原則を抽出し、project-specific な strategy と AI-native docs に実装を結び付けます。

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

Helper scripts は deterministic helper です。`validate_artic_outputs.py` は contract を検証し、`artic_start.py` は agent-authored strategy を文書へコンパイルし、`artic_show.py` は preview をレンダリングします。design judgment の出所はスクリプトではなく、public `@artic start` agent workflow が作成する `.artic/strategy.json` です。

## What Changes In The Agent

Artic が呼び出されると、エージェントは次を行います:

1. ホームページ/デザイン依頼が曖昧な場合、実装前に立ち止まります。
2. `@artic init` で product、audience、goal、vibe、constraints、references を収集します。
3. 1つのスタイルに頼らず、複数のプロフェッショナル/OSSデザインリソースを検索します。
4. 色の役割、タイプ階層、余白リズム、コンポーネント、モーション、アクセシビリティなど、再利用可能なルールを抽出します。
5. ユーザーのプロジェクト目標に基づいて、レファレンス間の衝突を解決します。
6. `@artic start` で public agent workflow が `.artic/strategy.json` を作成し、`docs/artic-strategy.md` を保存してから compiler を実行し、`DESIGN.md` と補助文書を生成します。
7. `@artic show` で strategy artifacts に基づく asset-first visual draft bundle を `.artic/show/` にレンダリングし、アプリのソースファイルは変更しません。
8. `@artic review` で実装を `.artic/strategy.json`、`docs/artic-strategy.md`、`DESIGN.md` と比較し、生成されたデザイン文書を検証します。

## When To Use It

使う場面:

- ホームページ、ランディングページ、プロダクトページ、Webサイトリデザイン。
- デザインドキュメントが弱い、または存在しないプロジェクト。
- 実装前に作るAI-nativeなデザインドキュメント。
- ブランドを正確にコピーしない、レファレンス駆動のデザインディレクション。

使わない場面:

- Exact cloning of a website or brand.
- Logo, trademark, illustration, or copyrighted asset copying.
- One-off graphic design with no website/doc output.

## How Users Control It

| 目的 | コマンド |
| --- | --- |
| デザインヒアリング開始 | `@artic init` |
| 高速ヒアリング実行 | `@artic init quick` |
| strategy 作成と文書コンパイル | `@artic start` |
| strategy artifacts から asset-first preview bundle をレンダリング | `@artic show` |
| strategy + `DESIGN.md` に対して実装をレビュー | `@artic review the homepage against DESIGN.md` |
| インストール済み/最新バージョン確認 | `@artic version` |
| 安全な更新コマンド表示 | `@artic update` |

`@artic init` は会話型の draft 状態だけを `.artic/init-session.json` に保存します。必須情報がそろっても自動では文書を生成せず、ユーザーが明示的に `@artic start` を実行したときだけ生成を開始します。

`@artic start` には 2 つの層があります。public agent workflow は design-director 層で、完了した intake と references を使って `.artic/strategy.json` と `docs/artic-strategy.md` を作成し、その後 deterministic compiler を実行します。raw `artic_start.py` fallback は compiler-only です。strategy が無い場合は design direction を作り上げず、`.artic/strategy-prompt.md` を書いて non-zero で終了します。

## Output Policy

Artic は長いデザイン説明をチャットに流すのではなく、永続的なファイルを書き出します:

```text
.artic/init-session.json   # draft interview state from @artic init
.artic/brief.json          # finalized by @artic start
.artic/references.json     # finalized by @artic start
.artic/strategy.json       # agent-authored design-direction contract for @artic start
.artic/strategy-prompt.md  # strategy が無い時の raw compiler fallback prompt
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
.artic/show/assets/manifest.json  # asset provenance; 未検証 asset は preview-only で production-cleared ではありません
.artic/show/report.json
.artic/show/critique.md
.artic/show/selected.json
.artic/show/iterations/<NNN>/...  # @artic show が生成。アプリファイルは変更しません
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

CI は Python スクリプト、JSON マニフェスト、README 翻訳構造、skill copy 同期、smoke scaffold、警告なしの DESIGN.md lint、marketplace plugin layout を検証します。

Distribution note: the wheel is metadata-only; marketplace packages, release tarballs, and sdists carry the skill/plugin payload.

## Community

- Read `CONTRIBUTING.md` before opening a pull request.
- Report sensitive issues using `SECURITY.md`; do not post secrets or private design assets in public issues.
- Follow `CODE_OF_CONDUCT.md` in issues and pull requests.

## License

MIT
