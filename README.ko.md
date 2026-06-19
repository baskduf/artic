<div align="center">
<img width="300" height="300" alt=" -7" src="https://github.com/user-attachments/assets/d624d91c-6ae8-4c44-89d2-0a9058377e43" />

  <h1>Artic</h1>

  <p>
    <strong>더 나은 홈페이지를 위한 레퍼런스 기반 AI-native 디자인 문서.</strong>
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
    <a href="README.md">English</a> | 한국어 | <a href="README.ja.md">日本語</a> | <a href="README.zh-CN.md">简体中文</a> | <a href="README.zh-TW.md">繁體中文（台灣）</a>
  </p>
</div>

---
Artic은 홈페이지 디자인 의도를 AI-native 디자인 문서로 바꾸는 Claude/Codex 호환 skill입니다.

사용자 플로우 중심으로 설계되어 있습니다:

```text
@artic init
@artic init quick
@artic start
@artic review
```

에이전트는 내부에서 사용자 인터뷰, brief 정규화, 전문/오픈소스 디자인 레퍼런스 검색, 패턴 합성, `DESIGN.md` 생성, 출력 검증을 처리합니다.

> Artic은 레퍼런스 사이트를 **복제하지 않습니다**.
> 전문/OSS 디자인 시스템에서 재사용 가능한 원칙을 추출하고, 프로젝트 맞춤 AI-native 문서로 컴파일합니다.

## Quick Start

### Claude Code marketplace

```text
/plugin marketplace add baskduf/artic
/plugin install claude-artic@artic
```

번들 skill 실행:

```text
/claude-artic:artic init
/claude-artic:artic start
```

자연어로도 요청할 수 있습니다:

```text
홈페이지를 만들기 전에 Artic으로 AI-native 디자인 문서를 만들어줘.
```

### Codex marketplace

```bash
codex plugin marketplace add baskduf/artic
```

플러그인 브라우저에서 `codex-artic` 설치:

```text
/plugins
```

Codex에 요청:

```text
@artic init
@artic start
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
python3 skills/artic/scripts/scaffold_artic_files.py --root /tmp/artic-smoke
python3 skills/artic/scripts/validate_artic_outputs.py --root /tmp/artic-smoke
```

## What Changes In The Agent

Artic이 호출되면 에이전트는 다음을 수행합니다:

1. 모호한 홈페이지 요청을 바로 구현하지 않습니다.
2. `@artic init`으로 제품, 타깃, 목표, 무드, 제약, 레퍼런스를 수집합니다.
3. 하나의 스타일에 의존하지 않고 여러 전문/OSS 디자인 리소스를 검색합니다.
4. 색상 역할, 타이포그래피, spacing, 컴포넌트, 모션, 접근성 규칙을 추출합니다.
5. 사용자 목표를 기준으로 레퍼런스 간 충돌을 해결합니다.
6. `@artic start`로 `DESIGN.md`와 보조 문서를 생성합니다.
7. 구현 전에 생성 문서를 검증합니다.

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

디자인 인터뷰:

```text
@artic init
```

빠른 인터뷰:

```text
@artic init quick
```

문서 컴파일:

```text
@artic start
```

구현 결과 검토:

```text
@artic review the homepage against DESIGN.md
```

## Output Policy

Artic은 긴 디자인 설명을 채팅에 쏟아내지 않고 지속 가능한 파일을 작성합니다:

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

CI는 Python scripts, JSON manifests, README 번역 구조, skill copy sync, smoke scaffolding을 검증합니다.

## Community

- PR 전에 `CONTRIBUTING.md`를 읽어주세요.
- 민감한 이슈는 `SECURITY.md`를 따르고, secrets나 private design assets를 public issue에 올리지 마세요.
- issue와 PR에서는 `CODE_OF_CONDUCT.md`를 따릅니다.

## License

MIT
