---
name: artic
description: "Use when creating or improving a homepage/website and design rules are missing or weak. Artic is an agent design-direction protocol: @artic init interviews the user, @artic start authors strategy artifacts, then the compiler produces AI-native DESIGN.md docs from reusable reference principles."
version: 0.6.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [design, design-system, homepage, design-md, ai-native-docs, references, oss]
    related_skills: [design-md, user-facing-skill-productization]
---

# Artic

Artic is a reference-informed design-documentation protocol for AI-built websites: a contract-bound LLM design director that turns project intent and reusable reference principles into implementation-ready design artifacts before coding.

Core flow:

```text
@artic init
→ collect project/design intent
→ normalize into search facets
→ search professional and open-source design references
→ preserve a draft intake session

@artic start
→ author `.artic/strategy.json` and `docs/artic-strategy.md` as the design-direction contract
→ run the compiler against that strategy
→ generate DESIGN.md and implementation guidance
→ validate outputs
```

Artic is not a generic design prompt or passive generator. Its core value is searching multiple professional/OSS design resources, extracting compatible patterns, and binding one project-specific AI-native design direction into a strategy contract. Scripts are validator/compiler helpers; they do not make the design judgment for the agent.

## When to Use

Use Artic when:
- The user asks to create a homepage, landing page, marketing site, product page, or redesign.
- The repo has no `DESIGN.md` or design rules.
- Existing docs describe product behavior but not visual design.
- The user provides reference sites/images and wants the design improved.
- The user wants AI-native docs before implementation.

Do not use Artic for exact cloning of a brand/site or copying logos, trademarks, proprietary illustrations, exact layouts, copywriting, or animations. Use references to extract reusable design principles, then create original project-specific direction.

## Commands

### `@artic init`

Purpose: run a conversational design intake and persist a draft session. Do not generate Artic design artifacts until the user explicitly asks for `@artic start`.

Required behavior:
1. Inspect existing docs if available: `DESIGN.md`, `docs/design-rules.md`, `docs/artic-brief.md`, `README.md`, and project docs under `docs/`.
2. Detect the user's language from explicit locale or the first message, then continue the interview in that language unless the user asks otherwise.
3. Ask only for missing information; do not repeat fields already supplied.
4. Persist every partial answer in `.artic/init-session.json`.
5. If required fields are still missing, ask the next compact set of questions in the user's language.
6. If the draft is ready, summarize the captured answers and tell the user to run `@artic start` to generate files.
7. Do not call the deterministic compiler, search the catalog, or write `.artic/brief.json`, `.artic/references.json`, `.artic/state.json`, `docs/artic-brief.md`, `DESIGN.md`, or design docs during `@artic init`.

Language behavior:
- Store draft language intent under `.artic/init-session.json.language` during `@artic init`.
- When `@artic start` compiles the ready session, carry the language contract into `.artic/brief.json.language`, `.artic/state.json.language`, and generated docs using `<!-- artic-language: <locale> -->`.
- Preserve machine-readable terms such as `DESIGN.md`, `AI-native`, `Artic`, source names, and design token keys.
- Localize user-facing interview questions and prose according to the language contract.
- Validate localized reference principle policy with the invariant `<!-- artic-policy: reference-safety-v1 -->` marker, not exact English copy.

Default interview questions:
1. What product/service is this homepage for?
2. What is the primary conversion goal?
3. Who is the target user?
4. What emotional impression should the page create?
5. Do you have reference URLs/images/brands?
6. What styles should be avoided?
7. Any fixed brand assets: logo, colors, fonts?
8. Desired content tone?
9. Mobile-first or desktop-first?
10. Tech stack?
11. Accessibility target? Default: WCAG AA.
12. Existing docs that must be reflected?

Reference boundary:
- External references are design/runtime sources used for reusable principles, interaction patterns, accessibility/performance constraints, token relationships, and implementation guidance.
- Artic treats external sources as reference-principles for strategy and documentation, not as concrete assets to copy into the user's site.
- Use reference guidance as constructive creative direction: translate patterns into original tokens, hierarchy, components, motion, and information architecture.

Fast path: if user says `@artic init quick`, ask only product, audience, goal, vibe, and references.

Hard lifecycle boundary:
- `@artic init` and normal user replies are draft collection only.
- They may only create or update `.artic/init-session.json`.
- They must not run `artic_init.py`, `artic_start.py`, or `scaffold_artic_files.py`.
- `ready` means “summarize and wait for explicit `@artic start`,” not “compile now.”
- Missing questions should be asked in the user's language.

For implementation details and regression-test shape for the init/start boundary, see `references/init-start-lifecycle-boundary.md`.

### `@artic start`

Purpose: author an Artic strategy contract, then compile it into AI-native design docs.

Public agent workflow:
1. Read the completed intake, existing docs, and selected references.
2. Make the LLM design-director judgment: audience promise, page thesis, reference synthesis, visual system, component priorities, accessibility stance, and implementation constraints.
3. Write `.artic/strategy.json` and `docs/artic-strategy.md`.
4. Run the deterministic compiler/validator scripts.

Executable path for agents/hosts that expose shell-backed commands after strategy exists:

```bash
python3 <artic-skill>/scripts/artic_start.py --root <project-root>
# use --no-validate only when you intentionally want generation without the Artic validator
```

Raw fallback behavior: `artic_start.py` is compiler-only. If `.artic/strategy.json` is missing, it writes `.artic/strategy-prompt.md` describing the strategy contract the agent must author and exits non-zero instead of inventing design direction.

Required behavior:
1. If `.artic/init-session.json` exists, read it first; its status is authoritative even when older `.artic/brief.json`/`.artic/references.json` files already exist.
2. If the session is still collecting, stop and ask the remaining init questions instead of generating files.
3. If the session is ready, compile it into `.artic/brief.json`, `.artic/references.json`, `.artic/state.json`, and `docs/artic-brief.md` before generating design docs.
4. Read `.artic/brief.json`, `.artic/references.json`, and existing project docs.
5. Search/combine multiple professional/OSS design sources.
6. Extract reusable design principles only.
7. Resolve conflicts explicitly based on user goal.
8. Preserve arbitrary custom answer fields from init in `.artic/brief.json` under `requirements` or `constraints`; examples: `must_have_feature`, `brand_constraints`.
9. Normalize long `project` answers into `project.name` and `project.description` instead of using the full requirement sentence as the title.
10. Author `.artic/strategy.json` and `docs/artic-strategy.md` as the design-direction contract.
11. Generate `DESIGN.md`, `docs/design-rules.md`, `docs/design-qa-checklist.md`, and `docs/homepage-design-prompt.md` from the strategy.
12. Validate with `scripts/validate_artic_outputs.py` when available.
13. If Node is available, optionally run `npx -y @google/design.md lint DESIGN.md`.

Lifecycle transition rule: `@artic start` is the only transition that may finalize a ready init session. If `.artic/init-session.json` is `collecting`, stop and ask the remaining questions; if it is `ready`, finalize it and then generate docs.

### `@artic version`

Purpose: report the installed Artic package versions and compare them with the latest GitHub release.

Required behavior:
1. Run `python3 <artic-skill>/scripts/artic_version.py --root <artic-root>` when the script is available.
2. Show installed versions from `pyproject.toml`, skill frontmatter, Claude marketplace manifest, Codex marketplace manifest, and plugin manifests.
3. Warn if any packaged copies have mismatched versions.
4. If network access is unavailable, report installed versions and say latest release was not checked.

### `@artic update`

Purpose: check for the latest Artic release and print safe host-specific update instructions.

Required behavior:
1. Run `python3 <artic-skill>/scripts/artic_update.py --root <artic-root>` when the script is available.
2. Default to dry-run guidance; do not overwrite installed plugin files directly.
3. Prefer marketplace-owned update flows for Claude Code and Codex.
4. If the latest release cannot be checked, still print the stable marketplace commands and mark the release as unchecked.
5. If installed versions are mismatched, stop and ask the user to fix the package before updating.

## Shared Catalog Curation Instruction

Use this as the common instruction for Hermes/Claude/Codex agents that collect or edit Artic catalog sources.

Artic catalog entries are user-facing design intelligence, not an internal audit log. When adding or revising a source, write the final guidance as polished application guidance for designers and AI agents:
- Explain what design quality the source contributes.
- Explain what the agent should extract conceptually: tokens, hierarchy, interaction behavior, accessibility patterns, motion principles, information architecture, or component discipline.
- Explain how to transform those patterns into original, project-specific homepage/design docs.
- Preserve reference-safety boundaries as constructive creative direction, not fear-based caveats.
- Avoid legalistic or unresolved language, fear-based caveats, or generic “do not copy” endings when a positive application sentence can say the same thing.
- Prefer wording such as “Use this for…”, “Apply its…”, “Translate… into project-specific…”, “Pair with…”, and “Keep identity, copy, and layout decisions original by…”.
- Keep each entry source-specific; do not flatten the catalog into repeated boilerplate.

Use `application_guidance` for this product-facing catalog copy. Keep catalog guidance positive, specific, and application-oriented.

Good pattern:
```text
Use this for developer-product clarity, dense navigation, and component discipline; translate workflow patterns into project-specific information architecture, tokens, and original interface composition.
```

Bad pattern:
```text
Internal caveat: possible brand copy issue. Do not copy exact layouts.
```

## Reference Search and Synthesis

Default source types:
- DESIGN.md collections: `VoltAgent/awesome-design-md`, `VoltAgent/awesome-claude-design`, `ndroussi/design-md-for-ai`, `meliwat/awesome-ios-design-md`
- Design skill registries: `bergside/awesome-design-skills`
- Professional design systems: Material, Shopify Polaris, IBM Carbon, Microsoft Fluent, Ant Design
- UI implementation ecosystems: shadcn/ui, Chakra UI, Tailwind-friendly component conventions
- Token standards: Google DESIGN.md, Material Design Tokens, W3C/DTCG

Synthesis rule:
- Select 3-5 candidates.
- Extract patterns, not assets.
- Merge compatible rules.
- Resolve conflicts based on project goal.
- Preserve rationale in `docs/artic-brief.md`.

## Reference Principle Policy

Allowed: token structure, color role relationships, typography hierarchy, spacing systems, component behavior, accessibility rules, motion principles.

Not part of Artic's output: logos, trademarks, proprietary illustrations, exact page composition, exact brand palette as identity, copywriting, copyrighted imagery.

Required phrase in generated docs:

```text
Reference policy: extract reusable principles only; create original project-specific direction.
```

## Output Contract

`@artic init` creates or updates only the draft session:

```text
.artic/init-session.json
```

`@artic start` finalizes a ready session into:

```text
.artic/brief.json
.artic/references.json
.artic/state.json
docs/artic-brief.md
```

`@artic start` then authors the strategy contract:

```text
.artic/strategy.json
docs/artic-strategy.md
```

Raw compiler fallback when strategy is missing:

```text
.artic/strategy-prompt.md
```

After strategy exists, the compiler creates:

```text
DESIGN.md
docs/design-rules.md
docs/design-qa-checklist.md
docs/homepage-design-prompt.md
```

Optional exports: `tailwind.theme.json`, `tokens.json`.

## Presets

Use presets only as search/synthesis starting points:
`clean-saas`, `developer-tool`, `ai-product`, `premium-consumer`, `editorial-landing`, `korean-startup`, `playful-brand`, `luxury-minimal`.

## Validation

```bash
python3 <artic-skill>/scripts/validate_artic_outputs.py --root <project-root>
python3 <artic-skill>/scripts/search_reference_catalog.py --query "ai product developer saas premium" --limit 3
```

Validation and compilation scripts enforce and materialize the contract. They are not a design judgment source; `@artic start` must provide that judgment through `.artic/strategy.json`.

## Common Pitfalls

1. Treating `@artic start` as another interview. `init` asks; `start` compiles.
2. Using only one reference source. Search at least 3 candidates unless the user owns a single brand system.
3. Copying a famous brand. Abstract: “premium developer SaaS” instead of “Stripe clone”.
4. Producing prose without tokens. Always generate tokenized `DESIGN.md`.
5. Skipping validation. Run the Artic validator and DESIGN.md lint when possible.
