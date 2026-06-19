# Artic Strategy Prompt

You are the public Artic agent. Produce `.artic/strategy.json`; scripts only validate and compile your design judgment.

Inputs available:
- `.artic/brief.json`
- `.artic/references.json`
- `.artic/intent.json` if present (internal normalized input, not authoritative design judgment)

Write valid JSON matching `skills/artic/templates/strategy.schema.json` with these required fields:

- `schema_version`
- `created_by`: `agent` or `agent-assisted`
- `project_summary`
- `design_north_star`
- `target_user_interpretation`
- `conversion_strategy`
- `reference_roles`: prefer 3-5 entries; each needs `source_id`, `role`, `why_selected`, `extract`, `avoid`
- `conflict_resolution`
- `visual_system`
- `component_rules`
- `accessibility`
- `implementation_guidance`
- `reference_policy`: exactly `artic-policy: reference-safety-v1`
- `forbidden_copy_elements`: include `logos`, `trademarks`, `proprietary illustrations`, `exact layouts`, `source copywriting`

Rules:
- Own the strategy. Do not ask the runtime to infer design judgment.
- Treat references as role-bound reusable principles, not clone targets.
- Preserve project language and policy requirements.
- Keep implementation guidance concrete enough to compile into DESIGN.md and supporting docs.
