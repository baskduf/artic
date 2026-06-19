#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import tarfile
from pathlib import Path

DEFAULT_INCLUDE_PATHS = [
    "skills",
    "plugins",
    ".claude-plugin",
    ".agents",
    "README.md",
    "README.ko.md",
    "README.ja.md",
    "README.zh-CN.md",
    "README.zh-TW.md",
    "LICENSE",
]
FORBIDDEN_SUFFIXES = (".pyc", ".pyo", ".pyd")


def should_skip(path: Path) -> bool:
    return "__pycache__" in path.parts or path.name.endswith(FORBIDDEN_SUFFIXES)


def safe_relative_path(root: Path, rel: Path) -> Path:
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError(f"path outside archive root: {rel}")
    path = (root / rel).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"path outside archive root: {rel}") from exc
    return path


def clean_info(info: tarfile.TarInfo) -> tarfile.TarInfo:
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    info.mtime = 0
    return info


def add_path(tf: tarfile.TarFile, root: Path, rel: Path) -> None:
    path = safe_relative_path(root, rel)
    if not path.exists():
        raise FileNotFoundError(path)
    if should_skip(rel):
        return
    if path.is_dir():
        for child in sorted(path.rglob("*")):
            child_rel = child.relative_to(root)
            if should_skip(child_rel):
                continue
            tf.add(child, arcname=child_rel.as_posix(), recursive=False, filter=clean_info)
    else:
        tf.add(path, arcname=rel.as_posix(), recursive=False, filter=clean_info)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a clean Artic skill marketplace archive.")
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--output", required=True, help="Output .tar.gz path")
    parser.add_argument("paths", nargs="*", help="Optional repo-relative paths to include")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    include_paths = [Path(path) for path in (args.paths or DEFAULT_INCLUDE_PATHS)]
    for rel in include_paths:
        safe_relative_path(root, rel)

    temp_output = output.with_name(output.name + ".tmp")
    with temp_output.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as gz:
            with tarfile.open(fileobj=gz, mode="w") as tf:
                for rel in include_paths:
                    add_path(tf, root, rel)
    temp_output.replace(output)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
