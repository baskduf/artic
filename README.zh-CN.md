<div align="center">
<img width="300" height="300" alt=" -7" src="https://github.com/user-attachments/assets/d624d91c-6ae8-4c44-89d2-0a9058377e43" />

  <h1>Artic</h1>

  <p>
    <strong>面向更好首页的参考驱动 AI-native 设计文档。</strong>
  </p>


  <p>
    <a href="README.md">English</a> | <a href="README.ko.md">한국어</a> | <a href="README.ja.md">日本語</a> | 简体中文 | <a href="README.zh-TW.md">繁體中文（台灣）</a>
  </p>
</div>

---
Artic 是一个兼容 Claude/Codex 的 agent design-direction protocol，也是在实现前把首页设计方向固定为契约的 contract-bound LLM design director。

它把公开用户流程保持得很小：

```text
@artic init      # 收集意图和参考
@artic start     # 编写 strategy artifacts，再编译 DESIGN.md 文档
@artic show      # 渲染安全的静态 preview
@artic review    # 按文档检查实现
```

Agent 会在内部处理用户访谈、把 brief 归一化为搜索 facets、检索专业/开源设计参考、编写 `.artic/strategy.json`、把它编译成 `DESIGN.md` 和辅助文档，并验证输出。脚本只是 validator/compiler/renderer helper，不是设计判断或 strategy authorship 的来源。

> Artic **不会** 克隆参考网站。它从专业/OSS 设计系统中提取可复用原则，并把实现绑定到项目专属 strategy 和 AI-native 文档。

## Quick Start

### Claude Code marketplace

安装 marketplace 包：

```text
/plugin marketplace add baskduf/artic
/plugin install claude-artic@artic
```

运行内置 skill：

```text
/claude-artic:artic init
/claude-artic:artic start
/claude-artic:artic show
```

也可以用自然语言请求：

```text
在构建这个首页之前，用 Artic 创建 AI-native 设计文档。
```

### Codex marketplace

从当前默认分支添加 marketplace：

```bash
codex plugin marketplace add baskduf/artic
```

需要稳定安装时固定到发布标签：

```bash
codex plugin marketplace add baskduf/artic@v0.3.0
```

在插件浏览器中安装 `codex-artic`：

```text
/plugins
```

也可以直接安装插件：

```bash
codex plugin add codex-artic@artic
```

然后向 Codex 请求：

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

Helper scripts 是 deterministic helper：`validate_artic_outputs.py` 验证 contract，`artic_start.py` 把 agent-authored strategy 编译成文档，`artic_show.py` 渲染 preview。设计判断的来源不是脚本，而是 public `@artic start` agent workflow 写入的 `.artic/strategy.json`。

## What Changes In The Agent

Artic 被调用后，Agent 会：

1. 当首页/设计请求很模糊时，先暂停而不是直接实现。
2. 运行 `@artic init` 收集 product、audience、goal、vibe、constraints 和 references。
3. Search multiple professional/OSS design resources instead of relying on one style.
4. Extract reusable rules: color roles, type hierarchy, spacing rhythm, components, motion, accessibility.
5. Resolve conflicts between references based on the user's project goal.
6. 运行 `@artic start`，让 public agent workflow 编写 `.artic/strategy.json`、保存 `docs/artic-strategy.md`，再运行 compiler 生成 `DESIGN.md` 和辅助文档。
7. 运行 `@artic show`，基于 strategy artifacts 渲染 `.artic/show/index.html`，作为不会修改应用源码的安全静态 preview。
8. 运行 `@artic review`，把实现与 `.artic/strategy.json`、`docs/artic-strategy.md`、`DESIGN.md` 对比，并验证生成的设计文档。

## When To Use It

适合用于：

- Homepages, landing pages, product pages, and website redesigns.
- Projects with weak or missing design docs.
- AI-native design documentation before coding.
- Reference-driven design direction without exact brand copying.

不适合用于：

- Exact cloning of a website or brand.
- Logo, trademark, illustration, or copyrighted asset copying.
- One-off graphic design with no website/doc output.

## How Users Control It

| 目标 | 命令 |
| --- | --- |
| 开始设计访谈 | `@artic init` |
| 运行快速访谈 | `@artic init quick` |
| 编写 strategy 并编译文档 | `@artic start` |
| 基于 strategy artifacts 渲染安全静态 preview | `@artic show` |
| 按 strategy + `DESIGN.md` 审查实现 | `@artic review the homepage against DESIGN.md` |
| 检查已安装/最新版本 | `@artic version` |
| 输出安全更新命令 | `@artic update` |

`@artic init` 只把会话式 draft 状态保存到 `.artic/init-session.json`。即使必填信息已经完整，也不会自动生成文档；只有用户明确运行 `@artic start` 后才会开始生成。

`@artic start` 有两层。public agent workflow 是 design-director 层：它使用完成的 intake 和 references 编写 `.artic/strategy.json` 与 `docs/artic-strategy.md`，然后调用 deterministic compiler。raw `artic_start.py` fallback 只是 compiler-only：如果缺少 strategy，它会写出 `.artic/strategy-prompt.md`，提示 agent 必须回答的问题，并以 non-zero 退出，而不是臆造设计方向。

## Output Policy

Artic writes durable files instead of dumping long design prose into chat:

```text
.artic/init-session.json   # draft interview state from @artic init
.artic/brief.json          # finalized by @artic start
.artic/references.json     # finalized by @artic start
.artic/strategy.json       # agent-authored design-direction contract for @artic start
.artic/strategy-prompt.md  # 缺少 strategy 时的 raw compiler fallback prompt
.artic/state.json
docs/artic-brief.md
docs/artic-strategy.md     # human-readable strategy contract
DESIGN.md
docs/design-rules.md
docs/design-qa-checklist.md
docs/homepage-design-prompt.md
.artic/show/index.html     # 由 @artic show 基于 strategy artifacts 生成的 preview 文件；默认不修改应用文件
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
