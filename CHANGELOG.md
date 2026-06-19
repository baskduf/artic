# Changelog

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
