#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from artic_version import collect_version_info


def command_suffix(latest_tag: str | None) -> str:
    return f"@{latest_tag}" if latest_tag else ""


def render_update_guidance(payload: dict, apply: bool = False) -> str:
    installed = payload.get("installed_version") or "unknown"
    latest = payload.get("latest") or {}
    latest_tag = latest.get("tag_name")
    suffix = command_suffix(latest_tag)
    lines = [
        "Artic update",
        "",
        f"Current: {installed}",
        f"Latest: {latest_tag or 'unchecked/unavailable'}",
        f"Status: {payload['status']}",
        "",
    ]
    if payload.get("version_mismatches"):
        lines.extend([
            "Blocked:",
            "- Installed Artic files have mismatched versions. Fix the package first, then update.",
            "",
        ])
    lines.extend([
        "Recommended update commands:",
        "",
        "Claude Code marketplace:",
        f"/plugin marketplace add baskduf/artic{suffix}",
        "/plugin install claude-artic@artic",
        "",
        "Codex marketplace:",
        f"codex plugin marketplace add baskduf/artic{suffix}",
        "# then open /plugins and install or refresh codex-artic",
        "",
        "Local checkout:",
        "git fetch --tags origin",
        f"git switch {latest_tag or '<latest-tag>'}",
        "",
    ])
    if apply:
        lines.extend([
            "Apply mode:",
            "- Automatic host-specific mutation is intentionally not implemented yet.",
            "- Run the command for your active host above so Claude/Codex owns its plugin state.",
            "",
        ])
    lines.append("No files were modified.")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Artic update availability and print safe update commands.")
    parser.add_argument("--root", default=".", help="Repository or plugin root containing Artic files")
    parser.add_argument("--repo", default="baskduf/artic", help="GitHub owner/repo for release checks")
    parser.add_argument("--no-network", action="store_true", help="Do not query GitHub releases")
    parser.add_argument("--apply", action="store_true", help="Reserved for future host-specific update execution")
    args = parser.parse_args()

    payload = collect_version_info(Path(args.root).resolve(), repo=args.repo, no_network=args.no_network)
    print(render_update_guidance(payload, apply=args.apply))
    return 1 if payload["status"] == "version-mismatch" else 0


if __name__ == "__main__":
    raise SystemExit(main())
