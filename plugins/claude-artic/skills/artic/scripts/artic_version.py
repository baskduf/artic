#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

VERSION_FILES = {
    "pyproject": ["pyproject.toml"],
    "skill": ["skills/artic/SKILL.md", "SKILL.md"],
    "claude_marketplace": [".claude-plugin/marketplace.json"],
    "codex_marketplace": [".agents/plugins/marketplace.json"],
    "claude_plugin": ["plugins/claude-artic/.claude-plugin/plugin.json", ".claude-plugin/plugin.json"],
    "codex_plugin": ["plugins/codex-artic/.codex-plugin/plugin.json", ".codex-plugin/plugin.json"],
}
VERSION_PRIORITY = ["pyproject", "skill", "claude_plugin", "codex_plugin", "claude_marketplace", "codex_marketplace"]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_pyproject_version(path: Path) -> str | None:
    match = re.search(r'^version = "([^"]+)"', read_text(path), re.MULTILINE)
    return match.group(1) if match else None


def read_skill_version(path: Path) -> str | None:
    match = re.search(r"^version:\s*([^\n]+)", read_text(path), re.MULTILINE)
    return match.group(1).strip() if match else None


def read_json_version(path: Path) -> str | None:
    return json.loads(read_text(path)).get("version")


def collect_installed_versions(root: Path) -> dict[str, str | None]:
    versions: dict[str, str | None] = {}
    for key, rels in VERSION_FILES.items():
        path = next((root / rel for rel in rels if (root / rel).exists()), None)
        if path is None:
            versions[key] = None
        elif key == "pyproject":
            versions[key] = read_pyproject_version(path)
        elif key == "skill":
            versions[key] = read_skill_version(path)
        else:
            versions[key] = read_json_version(path)
    return versions


def installed_version(versions: dict[str, str | None]) -> str | None:
    for key in VERSION_PRIORITY:
        version = versions.get(key)
        if version is not None:
            return version
    return None


def version_mismatches(versions: dict[str, str | None]) -> list[dict[str, str | None]]:
    expected = installed_version(versions)
    if expected is None:
        return [{"name": "installed", "version": None, "expected": None}]
    return [
        {"name": name, "version": version, "expected": expected}
        for name, version in versions.items()
        if version is not None and version != expected
    ]


def semver_tuple(value: str | None) -> tuple[int, int, int] | None:
    if not value:
        return None
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", value)
    if not match:
        return None
    return tuple(int(part) for part in match.groups())  # type: ignore[return-value]


def fetch_latest_release(repo: str, timeout: float = 10.0) -> dict[str, Any]:
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "artic-version"})
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed GitHub API URL from repo arg.
        payload = json.loads(response.read().decode("utf-8"))
    return {
        "tag_name": payload.get("tag_name"),
        "name": payload.get("name"),
        "html_url": payload.get("html_url"),
        "prerelease": bool(payload.get("prerelease")),
    }


def status_for(installed: str | None, latest: str | None, mismatches: list[dict[str, str | None]], no_network: bool, latest_error: str | None) -> str:
    if mismatches:
        return "version-mismatch"
    if no_network:
        return "latest-unchecked"
    if latest_error or latest is None:
        return "latest-unavailable"
    current_tuple = semver_tuple(installed)
    latest_tuple = semver_tuple(latest)
    if current_tuple is None or latest_tuple is None:
        return "version-unknown"
    if current_tuple == latest_tuple:
        return "up-to-date"
    if current_tuple < latest_tuple:
        return "update-available"
    return "local-newer"


def collect_version_info(root: Path, repo: str = "baskduf/artic", no_network: bool = False) -> dict[str, Any]:
    installed = collect_installed_versions(root)
    current_version = installed_version(installed)
    mismatches = version_mismatches(installed)
    latest: dict[str, Any] | None = None
    latest_error: str | None = None
    if not no_network:
        try:
            latest = fetch_latest_release(repo)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            latest_error = str(exc)
    latest_version = latest.get("tag_name") if latest else None
    return {
        "repo": repo,
        "installed_version": current_version,
        "installed": installed,
        "latest": latest,
        "latest_error": latest_error,
        "status": status_for(current_version, latest_version, mismatches, no_network, latest_error),
        "version_mismatches": mismatches,
    }


def render_text(payload: dict[str, Any]) -> str:
    lines = ["Artic version", "", "Installed:"]
    for name, version in payload["installed"].items():
        lines.append(f"- {name}: {version or 'missing'}")
    lines.append("")
    latest = payload.get("latest")
    if latest:
        lines.extend(["Latest:", f"- GitHub release: {latest.get('tag_name') or 'unknown'}", f"- URL: {latest.get('html_url') or 'unknown'}"])
    elif payload.get("latest_error"):
        lines.extend(["Latest:", f"- unavailable: {payload['latest_error']}"])
    else:
        lines.extend(["Latest:", "- unchecked (--no-network)"])
    lines.extend(["", "Status:", f"- {payload['status']}"])
    if payload["version_mismatches"]:
        lines.extend(["", "Version mismatches:"])
        for item in payload["version_mismatches"]:
            lines.append(f"- {item['name']}: {item['version']} (expected {item['expected']})")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Report installed and latest Artic versions.")
    parser.add_argument("--root", default=".", help="Repository or plugin root containing Artic files")
    parser.add_argument("--repo", default="baskduf/artic", help="GitHub owner/repo for release checks")
    parser.add_argument("--no-network", action="store_true", help="Do not query GitHub releases")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = parser.parse_args()

    payload = collect_version_info(Path(args.root).resolve(), repo=args.repo, no_network=args.no_network)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(render_text(payload))
    return 1 if payload["status"] == "version-mismatch" else 0


if __name__ == "__main__":
    raise SystemExit(main())
