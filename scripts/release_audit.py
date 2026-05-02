#!/usr/bin/env python
"""Check common blockers before making the GitHub repository public."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


BLOCKED_SUFFIXES = {
    ".h5ad",
    ".h5",
    ".loom",
    ".rds",
    ".rdata",
    ".fastq",
    ".fq",
    ".bam",
    ".cram",
    ".vcf",
}

SENSITIVE_NAMES = {
    "patient",
    "patients",
    "clinical",
    "hospital",
    "barcode",
    "sample_info",
    "metadata_private",
}


def is_git_ignored(root: Path, rel: Path) -> bool:
    """Return True when rel is ignored by Git."""
    try:
        result = subprocess.run(
            [
                "git",
                "-c",
                f"safe.directory={root.as_posix()}",
                "check-ignore",
                "-q",
                "--",
                str(rel).replace("\\", "/"),
            ],
            cwd=root,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        return False
    return result.returncode == 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--max-mb", type=float, default=20.0)
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    max_bytes = args.max_mb * 1024 * 1024
    problems: list[str] = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        rel_text = str(rel).replace("\\", "/")

        if ".git/" in rel_text or ".venv/" in rel_text or "__pycache__/" in rel_text:
            continue
        if is_git_ignored(root, rel):
            continue

        suffixes = {suffix.lower() for suffix in path.suffixes}
        if suffixes.intersection(BLOCKED_SUFFIXES):
            problems.append(f"large/omics file should not be committed: {rel}")

        if path.stat().st_size > max_bytes:
            problems.append(f"file exceeds {args.max_mb:g} MB: {rel}")

        lower_name = path.name.lower()
        if any(token in lower_name for token in SENSITIVE_NAMES):
            problems.append(f"review for possible sensitive metadata: {rel}")

    if problems:
        print("Release audit found possible blockers:")
        for item in problems:
            print(f"- {item}")
        return 1

    print("Release audit passed: no obvious large or sensitive files detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
