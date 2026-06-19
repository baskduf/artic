---
name: artic
description: "Use when creating or improving a homepage/website and design rules are missing or weak. Artic runs @artic init to interview the user, searches professional/OSS design references, then @artic start synthesizes AI-native DESIGN.md docs without copying protected brand assets."
version: 0.1.1
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [design, design-system, homepage, design-md, ai-native-docs, references, oss]
    related_skills: [design-md, user-facing-skill-productization]
---

# Artic

Artic is a reference-driven design onboarding skill for AI-built websites.

Core flow:

```text
@artic init
→ collect project/design intent
→ normalize into search facets
→ search professional and open-source design references
→ select and combine the best patterns

@artic start
→ compile the brief + selected references into AI-native design docs
→ generate DESIGN.md and implementation guidance
→ validate outputs
```

Artic is not a generic design prompt. Its core value is searching multiple professional/OSS design resources, extracting compatible patterns, and synthesizing one project-specific AI-native design direction.

## When to Use

Use Artic when:
- The user asks to create a homepage, landing page, marketing site, product page, or redesign.
- The repo has no `DESIGN.md` or design rules.
- Existing docs describe product behavior but not visual design.
- The user provides reference sites/images and wants the design improved.
- The user wants AI-native docs before implementation.

Do not use Artic for exact cloning of a brand/site or copying logos, trademarks, proprietary illustrations, exact layouts, copywriting, or animations.

## Commands

### `@artic init`

Purpose: run the design intake interview and create a structured brief.

Required behavior:
1. Inspect existing docs if available: `DESIGN.md`, `docs/design-rules.md`, `docs/artic-brief.md`, `README.md`, and project docs under `docs/`.
2. Ask a compact interview unless the user already supplied enough context.
3. Capture answers into `.artic/brief.json` and `docs/artic-brief.md`.
4. Normalize answers into searchable facets.
5. Search the Artic source catalog and select 3-5 candidate references.
6. Save `.artic/references.json` and `.artic/state.json`.

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

Fast path: if user says `@artic init quick`, ask only product, audience, goal, vibe, and references.

### `@artic start`

Purpose: compile the Artic brief into AI-native design docs.

Executable path for agents/hosts that expose shell-backed commands:

```bash
python3 <artic-skill>/scripts/artic_start.py --root <project-root>
# use --no-validate only when you intentionally want generation without the Artic validator
```

Required behavior:
1. Read `.artic/brief.json`, `.artic/references.json`, and existing project docs.
2. Search/combine multiple professional/OSS design sources.
3. Extract reusable design principles only.
4. Resolve conflicts explicitly based on user goal.
5. Generate `DESIGN.md`, `docs/design-rules.md`, `docs/design-qa-checklist.md`, and `docs/homepage-design-prompt.md`.
6. Validate with `scripts/validate_artic_outputs.py` when available.
7. If Node is available, optionally run `npx -y @google/design.md lint DESIGN.md`.

### `@artic review` MVP-light

After implementation, compare the current homepage against Artic docs. Check token consistency, typography hierarchy, spacing rhythm, CTA hierarchy, mobile behavior, accessibility basics, and no-copy reference safety.

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

Use `application_guidance` for this product-facing catalog copy. Do not add `risk_notes` or other defensive/internal field names for new catalog work.

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

## Reference Safety

Allowed: token structure, color role relationships, typography hierarchy, spacing systems, component behavior, accessibility rules, motion principles.

Forbidden unless user owns rights: logos, trademarks, proprietary illustrations, exact page composition, exact brand palette as identity, copywriting, copyrighted imagery.

Required phrase in generated docs:

```text
Reference policy: extract reusable principles only; do not copy logos, trademarks, proprietary illustrations, or exact layouts.
```

## Output Contract

`@artic init` creates:

```text
.artic/brief.json
.artic/references.json
.artic/state.json
docs/artic-brief.md
```

`@artic start` creates:

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
python3 ~/.hermes/skills/creative/artic/scripts/validate_artic_outputs.py --root <project-root>
python3 ~/.hermes/skills/creative/artic/scripts/search_reference_catalog.py --query "ai product developer saas premium" --limit 3
```

## Common Pitfalls

1. Treating `@artic start` as another interview. `init` asks; `start` compiles.
2. Using only one reference source. Search at least 3 candidates unless the user owns a single brand system.
3. Copying a famous brand. Abstract: “premium developer SaaS” instead of “Stripe clone”.
4. Producing prose without tokens. Always generate tokenized `DESIGN.md`.
5. Skipping validation. Run the Artic validator and DESIGN.md lint when possible.
