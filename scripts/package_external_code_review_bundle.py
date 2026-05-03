#!/usr/bin/env python
"""Package a source-code bundle for external AI code review.

Author: SheafSignal contributors
Date: 2026-05-04
Purpose: create a small source-code review archive that excludes raw data,
processed omics objects, generated figures, release archives, credentials, and
large matrices.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import zipfile
from dataclasses import dataclass
from pathlib import Path


OUTPUT_DIR = Path("external_ai_review_packet/source_code_review_bundle")
ARCHIVE_NAME = "sheafsignal_source_code_review_bundle.zip"
MANIFEST_PATH = OUTPUT_DIR / "SOURCE_CODE_REVIEW_BUNDLE_MANIFEST.tsv"
REPORT_PATH = OUTPUT_DIR / "SOURCE_CODE_REVIEW_BUNDLE_REPORT.md"
ARCHIVE_PATH = OUTPUT_DIR / ARCHIVE_NAME

REQUIRED_TOP_LEVEL_FILES = [
    "README.md",
    "pyproject.toml",
    "Dockerfile",
    "Makefile",
    "LICENSE",
]

CODE_PATTERNS = [
    "src/**/*.py",
    "scripts/**/*.py",
    "tests/**/*.py",
    ".github/workflows/*.yml",
    ".github/workflows/*.yaml",
    "envs/*.yml",
    "envs/*.yaml",
    "envs/*lock*.txt",
    "docs/reviewer_reproducibility_quickstart.md",
    "docs/github_release_checklist.md",
    "docs/data_and_code_availability_template.md",
    "external_ai_review_packet/EXTERNAL_AI_CODE_REVIEW_PROMPT_2026-05-04.md",
]

EXCLUDED_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "data",
    "results",
    "figures",
    "release",
    "logs",
    "tmp",
}

EXCLUDED_SUFFIXES = {
    ".zip",
    ".h5ad",
    ".h5",
    ".loom",
    ".rds",
    ".rdata",
    ".fastq",
    ".fq",
    ".bam",
    ".bai",
    ".cram",
    ".vcf",
    ".mtx",
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".svg",
}


@dataclass(frozen=True)
class SourceBundleRow:
    rel_path: str
    included: str
    size_bytes: int
    sha256: str
    reason: str


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def _write_tsv_atomic(path: Path, rows: list[SourceBundleRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    fieldnames = list(SourceBundleRow.__dataclass_fields__.keys())
    with tmp_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow(row.__dict__)
    tmp_path.replace(path)


def _is_safe_source_file(path: Path, root: Path) -> bool:
    try:
        rel = path.relative_to(root)
    except ValueError:
        return False
    if any(part.lower() in EXCLUDED_PARTS for part in rel.parts):
        return False
    lower_name = path.name.lower()
    if lower_name in {"github_token.txt", "zenodo_token.txt"}:
        return False
    return not any(str(rel).lower().endswith(suffix) for suffix in EXCLUDED_SUFFIXES)


def collect_source_files(root: Path) -> list[Path]:
    root = root.resolve()
    files: set[Path] = set()
    for rel in REQUIRED_TOP_LEVEL_FILES:
        path = root / rel
        if path.exists() and path.is_file() and _is_safe_source_file(path, root):
            files.add(path)
    for pattern in CODE_PATTERNS:
        for path in root.glob(pattern):
            if path.exists() and path.is_file() and _is_safe_source_file(path, root):
                files.add(path)
    return sorted(files, key=lambda path: path.relative_to(root).as_posix())


def build_manifest(root: Path) -> list[SourceBundleRow]:
    rows = []
    for path in collect_source_files(root):
        rel = path.relative_to(root).as_posix()
        rows.append(
            SourceBundleRow(
                rel_path=rel,
                included="yes",
                size_bytes=path.stat().st_size,
                sha256=_sha256(path),
                reason="source/test/config file for external code review",
            )
        )
    return rows


def classify_decision(rows: list[SourceBundleRow]) -> str:
    included_paths = {row.rel_path for row in rows if row.included == "yes"}
    required_present = [
        rel for rel in REQUIRED_TOP_LEVEL_FILES if rel in included_paths
    ]
    has_package_source = any(row.rel_path.startswith("src/") for row in rows)
    has_tests = any(row.rel_path.startswith("tests/") for row in rows)
    if len(required_present) < 3 or not has_package_source or not has_tests:
        return "SOURCE_CODE_REVIEW_BUNDLE_BLOCKED_MISSING_SOURCE_OR_TESTS"
    return "SOURCE_CODE_REVIEW_BUNDLE_READY"


def write_archive(root: Path, rows: list[SourceBundleRow], archive_path: Path) -> str:
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = archive_path.with_suffix(archive_path.suffix + ".tmp")
    with zipfile.ZipFile(tmp_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for row in rows:
            if row.included == "yes":
                archive.write(root / row.rel_path, row.rel_path)
    tmp_path.replace(archive_path)
    return _sha256(archive_path)


def build_report(
    rows: list[SourceBundleRow],
    *,
    decision: str,
    archive_path: Path,
    archive_sha256: str,
) -> str:
    included_paths = [row.rel_path for row in rows if row.included == "yes"]
    source_count = sum(path.startswith("src/") for path in included_paths)
    script_count = sum(path.startswith("scripts/") for path in included_paths)
    test_count = sum(path.startswith("tests/") for path in included_paths)
    return "\n".join(
        [
            "# Source Code Review Bundle Report",
            "",
            f"- Decision: `{decision}`",
            f"- Archive: `{archive_path.as_posix()}`",
            f"- Archive SHA256: `{archive_sha256}`",
            f"- Included files: `{len(included_paths)}`",
            f"- Source files under `src/`: `{source_count}`",
            f"- Script files under `scripts/`: `{script_count}`",
            f"- Test files under `tests/`: `{test_count}`",
            "",
            "## What To Send",
            "",
            "Send this source-code archive together with:",
            "`external_ai_review_packet/EXTERNAL_AI_CODE_REVIEW_PROMPT_2026-05-04.md`",
            "",
            "## What To Ask Reviewers To Report",
            "",
            "- Model name and version used for the review.",
            "- Review timestamp and timezone.",
            "- Claimed training-data cutoff, if the model reports one.",
            "- External references consulted, if any.",
            "- Fatal / major / minor code-level concerns.",
            "",
            "## Exclusions",
            "",
            "The archive excludes raw data, processed omics objects, generated figures,",
            "release archives, credentials, virtual environments, caches, and large matrices.",
            "",
            "## Boundary",
            "",
            "This bundle supports code review only. It does not guarantee correctness,",
            "security, reproducibility, or journal acceptance.",
            "",
        ]
    )


def build_outputs(root: Path, *, create_archive: bool = True) -> dict[str, object]:
    root = root.resolve()
    rows = build_manifest(root)
    decision = classify_decision(rows)
    archive_sha256 = "not_created"
    archive_path = root / ARCHIVE_PATH
    if create_archive and decision == "SOURCE_CODE_REVIEW_BUNDLE_READY":
        archive_sha256 = write_archive(root, rows, archive_path)
    _write_tsv_atomic(root / MANIFEST_PATH, rows)
    _write_text_atomic(
        root / REPORT_PATH,
        build_report(
            rows,
            decision=decision,
            archive_path=ARCHIVE_PATH,
            archive_sha256=archive_sha256,
        ),
    )
    return {
        "decision": decision,
        "archive": ARCHIVE_PATH.as_posix() if create_archive else "not_created",
        "archive_sha256": archive_sha256,
        "included_files": sum(row.included == "yes" for row in rows),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--no-archive", action="store_true")
    args = parser.parse_args(argv)

    summary = build_outputs(Path(args.root), create_archive=not args.no_archive)
    print(summary["decision"])
    print(f"Archive: {summary['archive']}")
    print(f"Archive SHA256: {summary['archive_sha256']}")
    print(f"Included files: {summary['included_files']}")
    return 0 if summary["decision"] == "SOURCE_CODE_REVIEW_BUNDLE_READY" else 1


if __name__ == "__main__":
    raise SystemExit(main())

