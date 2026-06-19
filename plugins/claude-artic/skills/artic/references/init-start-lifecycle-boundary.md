# Init/Start Lifecycle Boundary

## Problem

Users may answer an `@artic init` question and an agent may accidentally treat that reply as permission to complete a full Artic cycle. That collapses the intended interview phase into generation and prevents the user from refining missing or weak design intent.

## Rule

Only explicit `@artic start` may finalize or generate files. In the public workflow, `@artic start` is an agent strategy step first and a compiler step second.

`@artic init` and normal follow-up replies are draft collection only. They may update `.artic/init-session.json`, ask missing questions, or summarize readiness, but they must not create finalized brief/reference/strategy/design outputs. When `.artic/init-session.json` exists, its status is authoritative for `@artic start` even if older `.artic/brief.json` or `.artic/references.json` files already exist.

The public `@artic start` agent workflow must author `.artic/strategy.json` and `docs/artic-strategy.md` before invoking the compiler. The raw `artic_start.py` fallback is compiler-only: if `.artic/strategy.json` is missing, it writes `.artic/strategy-prompt.md` and exits non-zero so the agent can supply design direction instead of letting a script invent it.

## Allowed Outputs By Command

### `@artic init` or follow-up answer

Allowed:

```text
.artic/init-session.json
```

Forbidden:

```text
.artic/intent.json
.artic/brief.json
.artic/references.json
.artic/strategy.json
.artic/strategy-prompt.md
.artic/state.json
docs/artic-brief.md
docs/artic-strategy.md
DESIGN.md
docs/design-rules.md
docs/design-qa-checklist.md
docs/homepage-design-prompt.md
```

### `@artic start`

If `.artic/init-session.json.status` is `collecting`, stop and ask the remaining questions.

If `.artic/init-session.json.status` is `ready`, finalize first:

```text
.artic/intent.json
.artic/brief.json
.artic/references.json
.artic/strategy.json
.artic/state.json
docs/artic-brief.md
docs/artic-strategy.md
```

Then generate:

```text
DESIGN.md
docs/design-rules.md
docs/design-qa-checklist.md
docs/homepage-design-prompt.md
```

Fallback-only output when an agent calls raw `artic_start.py` without strategy:

```text
.artic/strategy-prompt.md
```

## Agent Response Patterns

### Collecting

Ask only the missing questions, in the user's language. Do not mention generated docs as already started.

### Ready

Summarize the captured answers and wait:

```text
The required Artic intake is ready.

Captured answers:
- Project: ...
- Audience: ...
- Goal: ...
- Vibe: ...

To generate Artic design docs, run `@artic start`.
```

For Korean sessions:

```text
필수 정보는 충분히 모였습니다.

현재 수집된 핵심:
- 제품: ...
- 타깃: ...
- 목표: ...
- 무드: ...

문서 생성을 시작하려면 `@artic start`를 실행하세요.
```

### Start

Finalize a ready session, author `.artic/strategy.json` and `docs/artic-strategy.md`, generate docs through the compiler, and run validation. If the session is still collecting, return a clear error with the missing fields/questions. If the raw compiler reports missing strategy and writes `.artic/strategy-prompt.md`, the agent must answer that prompt and rerun `@artic start` rather than treating the prompt as completed design output.

## Regression Tests

The lifecycle boundary is covered by these pytest tests:

```text
test_artic_conversational_init_collecting_writes_only_session
test_artic_conversational_init_ready_does_not_finalize_without_start
test_artic_conversational_init_finalize_creates_start_inputs_only_when_explicit
test_artic_init_session_ready_payload_instructs_start_without_generating
test_artic_start_finalizes_ready_init_session_before_generating_docs
test_artic_start_refuses_collecting_init_session
test_artic_start_refuses_collecting_session_even_with_stale_finalized_outputs
test_artic_start_finalizes_ready_session_over_stale_finalized_outputs
test_readmes_document_init_start_lifecycle_boundary
```
