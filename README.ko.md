<div align="center">
<img width="110" alt="Artic logo" src="assets/artic-logo.png" />

  <h1>Artic</h1>

  <p>
    <strong>더 나은 홈페이지를 위한 레퍼런스 기반 AI-native 디자인 문서.</strong>
  </p>


  <p>
    <a href="README.md">English</a> | 한국어 | <a href="README.ja.md">日本語</a> | <a href="README.zh-CN.md">简体中文</a> | <a href="README.zh-TW.md">繁體中文（台灣）</a>
  </p>
</div>

---
Artic은 구현 전에 홈페이지 디자인 방향을 계약으로 고정하는 Claude/Codex 호환 agent design-direction protocol이자 contract-bound LLM design director입니다.

공개 사용자 흐름은 작고 단순합니다:

```text
@artic init      # 의도와 레퍼런스 수집
@artic start     # strategy artifacts를 작성한 뒤 DESIGN.md 문서 컴파일
@artic show      # 출처가 기록된 asset-first preview bundle 렌더링
@artic review    # 구현 결과를 문서 기준으로 검토
```

에이전트는 내부에서 사용자 인터뷰, brief 검색 facet 정규화, 전문/오픈소스 디자인 레퍼런스 검색, `.artic/strategy.json` 작성, `DESIGN.md`와 보조 문서 컴파일, 출력 검증을 처리합니다. 스크립트는 validator/compiler/renderer helper이며, 디자인 판단이나 strategy authorship을 대체하지 않습니다.

> Artic은 레퍼런스 사이트를 **복제하지 않습니다**. 전문/OSS 디자인 시스템에서 재사용 가능한 원칙을 추출하고, 프로젝트 맞춤 strategy와 AI-native 문서에 구현을 묶습니다.

## Quick Start

### Claude Code marketplace

marketplace 패키지 설치:

```text
/plugin marketplace add baskduf/artic
/plugin install claude-artic@artic
```

번들 skill 실행:

```text
/claude-artic:artic init
/claude-artic:artic start
/claude-artic:artic show
```

자연어로도 요청할 수 있습니다:

```text
홈페이지를 만들기 전에 Artic으로 AI-native 디자인 문서를 만들어줘.
```

### Codex marketplace

현재 기본 브랜치에서 marketplace 추가:

```bash
codex plugin marketplace add baskduf/artic
```

안정적인 설치가 필요하면 릴리즈 태그로 고정:

```bash
codex plugin marketplace add baskduf/artic@v0.4.0
```

플러그인 브라우저에서 `codex-artic` 설치:

```text
/plugins
```

또는 플러그인을 직접 설치:

```bash
codex plugin add codex-artic@artic
```

Codex에 요청:

```text
@artic init
@artic start
@artic show
```

### Local checkout fallback

```text
skills/artic                         # Claude/Hermes 스타일 skill 폴더
plugins/claude-artic                 # Claude Code 플러그인 패키지
plugins/codex-artic                  # Codex 플러그인 패키지
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

Helper scripts는 deterministic helper입니다. `validate_artic_outputs.py`는 contract를 검증하고, `artic_start.py`는 agent-authored strategy를 문서로 컴파일하며, `artic_show.py`는 preview를 렌더링합니다. 디자인 판단의 출처는 스크립트가 아니라 public `@artic start` agent workflow가 작성한 `.artic/strategy.json`입니다.

## What Changes In The Agent

Artic이 호출되면 에이전트는 다음을 수행합니다:

1. 모호한 홈페이지/디자인 요청을 바로 구현하지 않고 잠시 멈춥니다.
2. `@artic init`으로 제품, 타깃, 목표, 무드, 제약, 레퍼런스를 수집합니다.
3. 하나의 스타일에 의존하지 않고 여러 전문/OSS 디자인 리소스를 검색합니다.
4. 색상 역할, 타이포그래피, spacing, 컴포넌트, 모션, 접근성 규칙을 추출합니다.
5. 사용자 목표를 기준으로 레퍼런스 간 충돌을 해결합니다.
6. `@artic start`에서 public agent workflow가 `.artic/strategy.json`을 작성하고 `docs/artic-strategy.md`를 저장한 뒤 compiler를 실행해 `DESIGN.md`와 보조 문서를 생성합니다.
7. `@artic show`로 strategy artifacts 기반의 asset-first 시각 초안 bundle을 `.artic/show/` 아래 렌더링하며 앱 소스 파일은 바꾸지 않습니다.
8. `@artic review`로 구현을 `.artic/strategy.json`, `docs/artic-strategy.md`, `DESIGN.md`와 비교하고 생성 문서를 검증합니다.

## When To Use It

사용하세요:

- 홈페이지, 랜딩 페이지, 제품 페이지, 웹사이트 리디자인.
- 디자인 문서가 없거나 약한 프로젝트.
- 코딩 전 AI-native 디자인 문서가 필요할 때.
- 브랜드를 복제하지 않고 레퍼런스 기반 방향을 만들 때.

사용하지 마세요:

- 웹사이트나 브랜드의 정확한 복제.
- 로고, 상표, 일러스트, 저작권 자산 복사.
- 웹사이트/문서 산출물이 없는 일회성 그래픽 디자인.

## How Users Control It

| 목적 | 명령 |
| --- | --- |
| 디자인 인터뷰 시작 | `@artic init` |
| 빠른 인터뷰 실행 | `@artic init quick` |
| strategy 작성 및 문서 컴파일 | `@artic start` |
| strategy artifacts 기반 asset-first preview bundle 렌더링 | `@artic show` |
| strategy + `DESIGN.md` 기준 구현 결과 검토 | `@artic review the homepage against DESIGN.md` |
| 설치/최신 버전 확인 | `@artic version` |
| 안전한 업데이트 명령 출력 | `@artic update` |

`@artic init`은 사용자의 언어를 따릅니다. 예를 들어 `한국어로 Artic init 진행해줘. AI 회의록 서비스 랜딩을 만들고 싶어.`라고 말하면 한국어 인터뷰를 시작하고, `.artic/init-session.json.language`에 `ko-KR`을 저장하며, 부족한 항목을 질문합니다. 디자인 산출물은 사용자가 `@artic start`를 실행하기 전까지 생성하지 않습니다.

`@artic init`은 대화형 draft 상태만 저장합니다. 필수 정보가 모여도 자동으로 문서를 생성하지 않으며, 문서 생성은 사용자가 `@artic start`를 명시적으로 실행할 때만 시작됩니다.

`@artic start`에는 두 계층이 있습니다. public agent workflow는 design-director 계층으로, 완료된 intake와 references를 사용해 `.artic/strategy.json`과 `docs/artic-strategy.md`를 작성한 뒤 deterministic compiler를 실행합니다. raw `artic_start.py` fallback은 compiler-only입니다. strategy가 없으면 디자인 방향을 추측하지 않고 `.artic/strategy-prompt.md`를 작성한 뒤 non-zero로 종료합니다.

## Output Policy

Artic은 긴 디자인 설명을 채팅에 쏟아내지 않고 지속 가능한 파일을 작성합니다:

```text
.artic/init-session.json   # @artic init의 draft 인터뷰 상태
.artic/brief.json          # @artic start에서 finalization
.artic/references.json     # @artic start에서 finalization
.artic/strategy.json       # agent-authored design-direction contract for @artic start
.artic/strategy-prompt.md  # strategy가 없을 때 raw compiler fallback prompt
.artic/state.json
docs/artic-brief.md
docs/artic-strategy.md     # 사람이 읽는 strategy contract
DESIGN.md
docs/design-rules.md
docs/design-qa-checklist.md
docs/homepage-design-prompt.md
.artic/show/index.html
.artic/show/styles.css
.artic/show/tokens.json
.artic/show/assets/manifest.json  # asset 출처 기록; 미검증 asset은 preview-only이며 production-cleared가 아님
.artic/show/report.json
.artic/show/critique.md
.artic/show/selected.json
.artic/show/iterations/<NNN>/...  # @artic show가 생성; 앱 파일은 변경하지 않음
```

## Repository Layout

```text
.claude-plugin/marketplace.json       # Claude Code marketplace manifest
.agents/plugins/marketplace.json      # Codex marketplace manifest
skills/artic/                         # Claude/Hermes 스타일 skill 폴더
plugins/claude-artic/                 # Claude Code 플러그인 패키지
plugins/codex-artic/                  # Codex 플러그인 패키지
examples/prompts.md                   # 예시 프롬프트와 명령
tests/                                # manifest, sync, README, script 검증
```

## Development

```bash
python3 -m pip install pytest pyyaml
python3 -m pytest -q
```

CI는 Python scripts, JSON manifests, README 번역 구조, skill copy sync, smoke scaffolding, warning-free DESIGN.md lint, marketplace plugin layout을 검증합니다.

Distribution note: the wheel is metadata-only; marketplace packages, release tarballs, and sdists carry the skill/plugin payload.

## Community

- PR 전에 `CONTRIBUTING.md`를 읽어주세요.
- 민감한 이슈는 `SECURITY.md`를 따르고, secrets나 private design assets를 public issue에 올리지 마세요.
- issue와 PR에서는 `CODE_OF_CONDUCT.md`를 따릅니다.

## License

MIT
