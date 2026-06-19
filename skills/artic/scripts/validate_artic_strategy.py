#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

POLICY_ID = "artic-policy: reference-safety-v1"
FORBIDDEN_COPY_ELEMENTS = {
    "logos",
    "trademarks",
    "proprietary illustrations",
    "exact layouts",
    "source copywriting",
}
REQUIRED_TOP_LEVEL = (
    "schema_version",
    "project_summary",
    "design_north_star",
    "target_user_interpretation",
    "conversion_strategy",
    "reference_roles",
    "conflict_resolution",
    "visual_system",
    "component_rules",
    "accessibility",
    "implementation_guidance",
    "reference_policy",
    "forbidden_copy_elements",
)
REQUIRED_ROLE_KEYS = ("source_id", "role", "why_selected", "extract", "avoid")


def read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"missing required strategy file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object in {path}")
    return payload


def _has_text(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return any(_has_text(item) for item in value)
    if isinstance(value, dict):
        return any(_has_text(item) for item in value.values())
    return value is not None


def validate_strategy_payload(strategy: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    for key in REQUIRED_TOP_LEVEL:
        if key not in strategy:
            errors.append(f"ERROR: strategy missing key: {key}")
        elif key not in {"reference_roles", "forbidden_copy_elements"} and not _has_text(strategy.get(key)):
            errors.append(f"ERROR: strategy key must not be empty: {key}")

    created_by = strategy.get("created_by")
    authorship = strategy.get("authorship")
    if created_by is None and authorship is None:
        errors.append("ERROR: strategy must include created_by or authorship")
    if created_by is not None and created_by not in {"agent", "agent-assisted"}:
        errors.append("ERROR: strategy created_by must be 'agent' or 'agent-assisted'")
    if isinstance(authorship, dict):
        author_type = authorship.get("created_by") or authorship.get("type")
        if author_type is not None and author_type not in {"agent", "agent-assisted"}:
            errors.append("ERROR: strategy authorship.created_by/type must be 'agent' or 'agent-assisted'")
    elif isinstance(authorship, str) and authorship not in {"agent", "agent-assisted"}:
        errors.append("ERROR: strategy authorship must be 'agent' or 'agent-assisted' when it is a string")

    if strategy.get("reference_policy") != POLICY_ID:
        errors.append(f"ERROR: strategy reference_policy must be {POLICY_ID}")

    forbidden = strategy.get("forbidden_copy_elements")
    if not isinstance(forbidden, list):
        errors.append("ERROR: strategy forbidden_copy_elements must be a list")
    else:
        normalized = {str(item).strip().lower() for item in forbidden}
        missing = sorted(FORBIDDEN_COPY_ELEMENTS - normalized)
        for item in missing:
            errors.append(f"ERROR: strategy forbidden_copy_elements missing: {item}")

    roles = strategy.get("reference_roles")
    if not isinstance(roles, list) or not roles:
        errors.append("ERROR: strategy reference_roles must include at least 1 role assignment")
    else:
        for index, role in enumerate(roles, start=1):
            if not isinstance(role, dict):
                errors.append(f"ERROR: strategy reference_roles[{index}] must be an object")
                continue
            for key in REQUIRED_ROLE_KEYS:
                if key not in role:
                    errors.append(f"ERROR: strategy reference_roles[{index}] missing key: {key}")
                elif not _has_text(role.get(key)):
                    errors.append(f"ERROR: strategy reference_roles[{index}].{key} must not be empty")

    return errors


def validate_strategy_file(path: Path) -> list[str]:
    try:
        strategy = read_json(path)
    except ValueError as exc:
        return [f"ERROR: {exc}"]
    return validate_strategy_payload(strategy)


def validate_root(root: Path) -> list[str]:
    return validate_strategy_file(root / ".artic" / "strategy.json")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate .artic/strategy.json for Artic strategy-first runtime.")
    parser.add_argument("--root", required=True, help="Project root containing .artic/strategy.json")
    args = parser.parse_args()
    errors = validate_root(Path(args.root))
    if errors:
        print("Artic strategy validation failed:")
        print("\n".join(errors))
        return 1
    print("Artic strategy validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
