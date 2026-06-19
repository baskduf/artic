<div align="center">
<img width="110" alt="Artic logo" src="assets/artic-logo.png" />

  <h1>Artic</h1>

  <p>
    <strong>為更好的首頁而生的參考驅動 AI-native 設計文件。</strong>
  </p>


  <p>
    <a href="README.md">English</a> | <a href="README.ko.md">한국어</a> | <a href="README.ja.md">日本語</a> | <a href="README.zh-CN.md">简体中文</a> | 繁體中文（台灣）
  </p>
</div>

---
Artic 是一個相容 Claude/Codex 的 agent design-direction protocol，也是在實作前把首頁設計方向固定為契約的 contract-bound LLM design director。

它把公開使用者流程保持得很小：

```text
@artic init      # 收集意圖和參考
@artic start     # 編寫 strategy artifacts，再編譯 DESIGN.md 文件
@artic show      # 渲染記錄來源的 asset-first preview bundle
@artic review    # 依文件檢查實作
```

Agent 會在內部處理使用者訪談、把 brief 正規化為搜索 facets、檢索專業/開源設計參考、編寫 `.artic/strategy.json`、把它編譯成 `DESIGN.md` 和輔助文件，並驗證輸出。腳本只是 validator/compiler/renderer helper，不是設計判斷或 strategy authorship 的來源。

> Artic **不會** 克隆參考網站。它從專業/OSS 設計系統中提取可重用原則，並把實作綁定到專案專屬 strategy 和 AI-native 文件。

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
在建置這個首頁之前，用 Artic 建立 AI-native 設計文件。
```

### Codex marketplace

從目前預設分支新增 marketplace：

```bash
codex plugin marketplace add baskduf/artic
```

需要穩定安裝時固定到發布標籤：

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

Helper scripts 是 deterministic helper：`validate_artic_outputs.py` 驗證 contract，`artic_start.py` 把 agent-authored strategy 編譯成文件，`artic_show.py` 渲染 preview。設計判斷的來源不是腳本，而是 public `@artic start` agent workflow 寫入的 `.artic/strategy.json`。

## What Changes In The Agent

Artic 被呼叫後，Agent 會：

1. 當首頁/設計請求很模糊時，先暫停而不是直接實作。
2. 執行 `@artic init` 收集 product、audience、goal、vibe、constraints 和 references。
3. 搜尋多個專業/OSS 設計資源，而不是依賴單一風格。
4. 萃取可重用規則：色彩角色、字體層級、間距節奏、元件、動效與可存取性。
5. 依據使用者的專案目標解決不同參考之間的衝突。
6. 執行 `@artic start`，讓 public agent workflow 編寫 `.artic/strategy.json`、儲存 `docs/artic-strategy.md`，再執行 compiler 生成 `DESIGN.md` 和輔助文件。
7. 執行 `@artic show`，基於 strategy artifacts 在 `.artic/show/` 下渲染 asset-first visual draft bundle，且不會修改應用程式原始碼。
8. 執行 `@artic review`，把實作與 `.artic/strategy.json`、`docs/artic-strategy.md`、`DESIGN.md` 對比，並驗證生成的設計文件。

## When To Use It

適合用於：

- 首頁、登陸頁、產品頁和網站改版。
- 設計文件薄弱或缺失的專案。
- 編碼前的 AI-native 設計文件。
- 不精確複製品牌的參考驅動設計方向。

不適合用於：

- Exact cloning of a website or brand.
- Logo, trademark, illustration, or copyrighted asset copying.
- One-off graphic design with no website/doc output.

## How Users Control It

| 目標 | 命令 |
| --- | --- |
| 開始設計訪談 | `@artic init` |
| 執行快速访谈 | `@artic init quick` |
| 編寫 strategy 並編譯文件 | `@artic start` |
| 基於 strategy artifacts 渲染 asset-first preview bundle | `@artic show` |
| 依 strategy + `DESIGN.md` 審查實作 | `@artic review the homepage against DESIGN.md` |
| 检查已安裝/最新版本 | `@artic version` |
| 輸出安全更新命令 | `@artic update` |

`@artic init` 只會把對話式 draft 狀態儲存到 `.artic/init-session.json`。即使必填資訊已完整，也不會自動產生文件；只有使用者明確執行 `@artic start` 後才會開始產生。

`@artic start` 有兩層。public agent workflow 是 design-director 層：它使用完成的 intake 和 references 編寫 `.artic/strategy.json` 與 `docs/artic-strategy.md`，然後呼叫 deterministic compiler。raw `artic_start.py` fallback 只是 compiler-only：如果缺少 strategy，它會寫出 `.artic/strategy-prompt.md`，提示 agent 必須回答的問題，並以 non-zero 退出，而不是臆造設計方向。

## Output Policy

Artic 會寫入持久文件，而不是把大段設計說明直接倒進聊天裡：

```text
.artic/init-session.json   # draft interview state from @artic init
.artic/brief.json          # finalized by @artic start
.artic/references.json     # finalized by @artic start
.artic/strategy.json       # agent-authored design-direction contract for @artic start
.artic/strategy-prompt.md  # 缺少 strategy 時的 raw compiler fallback prompt
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
.artic/show/assets/manifest.json  # asset provenance；未驗證 asset 僅限 preview-only，不代表 production-cleared
.artic/show/report.json
.artic/show/critique.md
.artic/show/selected.json
.artic/show/iterations/<NNN>/...  # 由 @artic show 生成；不修改應用程式檔案
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

CI 會驗證 Python 腳本、JSON 清單、README 翻譯結構、skill copy 同步、smoke scaffold、無警告 DESIGN.md lint，以及 marketplace plugin layout。

Distribution note: the wheel is metadata-only; marketplace packages, release tarballs, and sdists carry the skill/plugin payload.

## Community

- Read `CONTRIBUTING.md` before opening a pull request.
- Report sensitive issues using `SECURITY.md`; do not post secrets or private design assets in public issues.
- Follow `CODE_OF_CONDUCT.md` in issues and pull requests.

## License

MIT
