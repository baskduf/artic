# Artic Work Handoff / Scope Lock

Date: 2026-06-19
Owner: Hermes / current agent
Repo: `/Users/wb/Desktop/artic`
Branch observed: `release/v0.2.0`

## Active ownership

This agent owns the proposed `artic show` work. Other agents should not edit the files listed in the reserved scope below unless WB explicitly reassigns or clears this handoff.

## Proposed feature

Add a safe `show` command that renders an Artic-generated design into a preview page using the existing outputs from `artic start`.

Intended default behavior:
- Read `DESIGN.md`, `docs/homepage-design-prompt.md`, `.artic/brief.json`, and `.artic/references.json` from a target project root.
- Generate a non-invasive static preview, likely `.artic/show/index.html`.
- Do not modify the user's actual app/source files by default.
- If project code application is added later, it must require explicit opt-in such as `--apply` or a separate `artic apply` command.

## Reserved edit scope

Canonical Artic skill:
- `skills/artic/SKILL.md`
- `skills/artic/scripts/artic_show.py` if created
- `skills/artic/templates/` only for show/preview-specific templates if needed
- `skills/artic/scripts/artic_start.py` only if minimal integration/shared helpers are truly needed
- `skills/artic/scripts/validate_artic_outputs.py` only if show output validation is added

Plugin sync copies:
- `plugins/claude-artic/skills/artic/SKILL.md`
- `plugins/claude-artic/skills/artic/scripts/artic_show.py` if created
- `plugins/claude-artic/skills/artic/templates/` only matching canonical show/preview changes
- `plugins/codex-artic/skills/artic/SKILL.md`
- `plugins/codex-artic/skills/artic/scripts/artic_show.py` if created
- `plugins/codex-artic/skills/artic/templates/` only matching canonical show/preview changes

Tests/docs:
- `tests/test_artic_package.py` or a new targeted test file for `artic_show`
- `README.md`, `README.ko.md`, `README.ja.md`, `README.zh-CN.md`, `README.zh-TW.md` only if command docs are added

## Out of scope / do not touch

Other agents should avoid these while this handoff is active:
- Catalog expansion work in `skills/artic/references/source-catalog.json`
- Existing init/start lifecycle behavior unless required by show tests
- Locale/multilingual workflow changes unrelated to show
- Release artifacts under `dist/`
- Unrelated package/version/release changes
- Any user's downstream website source files such as `app/page.tsx`, `src/App.tsx`, `pages/index.tsx`, etc.

## Expected verification when implemented

Run at minimum:
- `python3 -m pytest -q`

Feature-specific tests should verify:
- `show` fails cleanly when required design inputs are missing.
- `show` creates a preview under `.artic/show/` when design inputs exist.
- default `show` does not modify app/source files.
- canonical skill changes are synced into Claude and Codex plugin copies.

## Release condition

This handoff can be cleared when either:
1. WB explicitly cancels/reassigns the `artic show` work, or
2. the implementation is complete, verified, and summarized back to WB.
