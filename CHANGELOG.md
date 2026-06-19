# Changelog

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
