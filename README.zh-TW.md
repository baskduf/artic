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
Artic 是一個相容 Claude/Codex 的 skill，用來在實作前建立參考驅動的 AI-native 首页设计文件。

它把公開使用者流程保持得很小：

```text
@artic init      # 收集意圖和參考
@artic start     # 生成 DESIGN.md 和輔助文件
@artic show      # 渲染安全的靜態 preview
@artic review    # 依文件檢查實作
```

Agent 會在內部處理使用者訪談、把 brief 正規化为搜索 facets、檢索專業/開源设计参考、合成可重用模式、生成 `DESIGN.md` 並驗證輸出。

> Artic **不會** 克隆参考网站。它从專業/OSS 设计系统中提取可重用原则，并编译成專案專屬的 AI-native 文件。

## Quick Start

### Claude Code marketplace

安裝 marketplace 包：

```text
/plugin marketplace add baskduf/artic
/plugin install claude-artic@artic
```

執行內建 skill：

```text
/claude-artic:artic init
/claude-artic:artic start
/claude-artic:artic show
```

也可以用自然語言請求：

```text
在建置这个首页之前，用 Artic 创建 AI-native 设计文件。
```

### Codex marketplace

从目前預設分支新增 marketplace：

```bash
codex plugin marketplace add baskduf/artic
```

需要稳定安裝时固定到发布标签：

```bash
codex plugin marketplace add baskduf/artic@v0.3.0
```

在外掛瀏覽器中安裝 `codex-artic`：

```text
/plugins
```

也可以直接安裝外掛：

```bash
codex plugin add codex-artic@artic
```

然後向 Codex 請求：

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

Artic 被呼叫後，Agent 會：

1. 當首頁/設計請求很模糊時，先暫停而不是直接實作。
2. 執行 `@artic init` 收集 product、audience、goal、vibe、constraints 和 references。
3. Search multiple professional/OSS design resources instead of relying on one style.
4. Extract reusable rules: color roles, type hierarchy, spacing rhythm, components, motion, accessibility.
5. Resolve conflicts between references based on the user's project goal.
6. 執行 `@artic start` 生成 `DESIGN.md` 和輔助文件。
7. 執行 `@artic show` 渲染 `.artic/show/index.html`，作為不會修改應用程式原始碼的安全靜態 preview。
8. 在實作前驗證生成的設計文件。

## When To Use It

適合用於：

- Homepages, landing pages, product pages, and website redesigns.
- Projects with weak or missing design docs.
- AI-native design documentation before coding.
- Reference-driven design direction without exact brand copying.

不適合用於：

- Exact cloning of a website or brand.
- Logo, trademark, illustration, or copyrighted asset copying.
- One-off graphic design with no website/doc output.

## How Users Control It

| 目標 | 命令 |
| --- | --- |
| 開始設計訪談 | `@artic init` |
| 執行快速访谈 | `@artic init quick` |
| 編譯文件 | `@artic start` |
| 渲染安全靜態 preview | `@artic show` |
| 審查實作 | `@artic review the homepage against DESIGN.md` |
| 检查已安裝/最新版本 | `@artic version` |
| 輸出安全更新命令 | `@artic update` |

`@artic init` 只會把對話式 draft 狀態儲存到 `.artic/init-session.json`。即使必填資訊已完整，也不會自動產生文件；只有使用者明確執行 `@artic start` 後才會開始產生。

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
.artic/show/index.html     # 由 @artic show 生成的 preview 檔案；預設不修改應用程式檔案
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
