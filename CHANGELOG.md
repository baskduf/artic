# Changelog

## 0.6.0 - 2026-06-20

### Added
- Added source-role metadata across the Artic catalog so references declare whether they are visual, system, implementation, behavior, QA, asset, legal, or copy guidance.
- Preserved source-role metadata in init reference outputs and source plans for downstream agent strategy authoring.

### Changed
- Gated role-grounded source selection with source-role eligibility and explicit-context metadata so implementation, asset, legal, and system references do not leak into unrelated visual guidance.
- Reduced default source over-selection so Polaris, shadcn/ui, Tailwind, and similar implementation sources are selected only when the project context supports their role.

## 0.5.0 - 2026-06-20

### Removed
- Removed the public `@artic show` and `@artic review` workflow surface to keep Artic focused on `@artic init` → `@artic start`.
- Removed show preview bundle generation, risk-readiness gating, production-readiness status fields, and related defensive output sections from the skill, scripts, schemas, validators, docs, and mirrored Claude/Codex packages.

### Changed
- Reframed reference safety as constructive design-principle extraction for original project-specific direction.

## 0.4.1 - 2026-06-20

### Fixed
- Updated the Codex marketplace manifest to use the current `plugins[].source` schema required by `codex plugin marketplace add`.

## 0.4.0 - 2026-06-19

### Added
- Added asset-first `@artic show` preview bundles with iterations, selected candidate metadata, critique output, token/style artifacts, and asset provenance manifests under `.artic/show/`.
- Added Artic risk-readiness analysis so high-risk homepage requests can proceed as explicit placeholder previews while blocking production implementation until required assets, interactions, trust, or integration details are supplied.
- Added mirrored Claude/Codex risk-readiness and asset-first show support, including schema/template updates and package coverage.

### Changed
- Updated English, Korean, Japanese, Simplified Chinese, and Traditional Chinese docs to describe the asset-first show bundle contract and stable marketplace install tag.
- Strengthened release/package tests for show bundle outputs, risk readiness, mirrored plugin payloads, version sync, and artifact hygiene.

## 0.3.0 - 2026-06-19

### Added
- Added `@artic show` to render Artic design outputs into `.artic/show/index.html` as a safe static preview without modifying app source files by default.
- Added 3D/resource catalog coverage for spatial, immersive, and asset-heavy homepage design direction.
- Added release artifact hygiene checks for marketplace archives, source distributions, wheels, and required skill/plugin payload files.

### Changed
- Documented `@artic show`, `@artic version`, and `@artic update` across English, Korean, Japanese, Simplified Chinese, and Traditional Chinese READMEs.
- Updated stable Codex marketplace install examples to pin `baskduf/artic@v0.3.0`.
- Expanded Artic reference synthesis so agents can route 3D-heavy prompts to relevant resource catalogs while preserving reference-safety boundaries.

## 0.2.0 - 2026-06-19

### Added
- Added LLM-first Artic init flow that turns user intent into searchable design facets before reference lookup.
- Added multilingual init sessions that preserve the user's language and store draft intake state in `.artic/init-session.json`.
- Added Korean market reference catalog coverage and broader professional/open-source design intelligence.
- Added lifecycle documentation for the `@artic init` / `@artic start` boundary.

### Changed
- `@artic init` is now a draft-only interview phase and does not generate durable design artifacts before explicit `@artic start`.
- `@artic start` now treats `.artic/init-session.json` as authoritative, finalizing ready sessions and blocking collecting sessions even when stale finalized files exist.
- Mirrored Claude and Codex plugin skill packages are synchronized with the canonical Artic skill.

### Fixed
- Prevented accidental generation when an init session becomes ready but the user has not explicitly started document generation.
- Prevented stale `.artic/brief.json` and `.artic/references.json` files from overriding the current init session state.
