#!/usr/bin/env python
"""Build GitHub/Zenodo reproducibility release manifests.

Author: SheafSignal contributors
Date: 2026-04-30
Purpose: freeze public-release file inventories, checksums, and claim
boundaries for a 20-50 IF methods-manuscript submission package.
"""

from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

import pandas as pd


EXCLUDE_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "env",
}

ZENODO_PREFIXES = (
    "data/processed/",
    "benchmarks/results/tenx_breast_visium/spatial/",
)

GITHUB_PREFIXES = (
    "src/",
    "scripts/",
    "tests/",
    "metadata/",
    "envs/",
    "docs/",
    "manuscript/",
    "examples/",
    "benchmarks/results/",
)

ROOT_GITHUB_FILES = {
    "README.md",
    "PROJECT_STATUS.md",
    "pyproject.toml",
    ".gitignore",
    "LICENSE",
}

BLOCKED_GITHUB_SUFFIXES = {
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
    ".gz",
    ".zip",
    ".tar",
    ".tgz",
}


def normalize_rel(path: Path) -> str:
    return path.as_posix()


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_release_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel_parts = path.relative_to(root).parts
        if any(part in EXCLUDE_DIRS for part in rel_parts):
            continue
        if rel_parts[0] in {"data"} and len(rel_parts) > 1 and rel_parts[1] in {
            "raw",
            "external",
        }:
            continue
        if rel_parts[0] == "release":
            continue
        files.append(path)
    return sorted(files)


def classify_release_target(rel: str, size_mb: float, suffix: str) -> tuple[str, str]:
    lower_suffix = suffix.lower()
    if rel == "data/raw/.gitkeep":
        return "github", "empty raw-data sentinel"
    if rel.startswith(ZENODO_PREFIXES):
        return "zenodo", "processed/frozen benchmark object"
    if lower_suffix in BLOCKED_GITHUB_SUFFIXES:
        return "zenodo", "large or binary omics-like file"
    if size_mb > 20:
        return "zenodo", "file exceeds GitHub release audit threshold"
    if rel in ROOT_GITHUB_FILES or rel.startswith(GITHUB_PREFIXES):
        return "github", "code, metadata, manifest, or small benchmark result"
    if rel.startswith("figures/"):
        return "generated_not_tracked", "regenerable manuscript figure"
    return "github", "small auxiliary repository file"


def build_release_inventory(root: Path) -> pd.DataFrame:
    rows = []
    for path in iter_release_files(root):
        rel = normalize_rel(path.relative_to(root))
        size_bytes = path.stat().st_size
        size_mb = size_bytes / 1024 / 1024
        target, reason = classify_release_target(rel, size_mb, path.suffix)
        rows.append(
            {
                "relative_path": rel,
                "release_target": target,
                "size_bytes": int(size_bytes),
                "size_mb": round(size_mb, 6),
                "sha256": sha256_file(path),
                "reason": reason,
            }
        )
    return pd.DataFrame(rows).sort_values(["release_target", "relative_path"])


def write_sha256sums(inventory: pd.DataFrame, output: Path, target: str) -> None:
    subset = inventory.loc[inventory["release_target"] == target].copy()
    lines = [f"{row.sha256}  {row.relative_path}" for row in subset.itertuples(index=False)]
    output.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def write_summary(
    *,
    output: Path,
    inventory: pd.DataFrame,
    github_manifest: Path,
    zenodo_manifest: Path,
) -> None:
    counts = inventory.groupby("release_target").agg(
        n_files=("relative_path", "size"),
        total_mb=("size_mb", "sum"),
    )
    github = counts.loc["github"] if "github" in counts.index else None
    zenodo = counts.loc["zenodo"] if "zenodo" in counts.index else None
    text = f"""# SheafSignal Reproducibility Release Summary

## Release Boundary

This repository is prepared for a public GitHub + Zenodo release. GitHub should
contain source code, manifests, environment files, tests, documentation, and
small benchmark result tables. Zenodo should contain frozen processed benchmark
objects and large generated spatial benchmark tables.

## Current Inventory

- GitHub-target files: {0 if github is None else int(github['n_files'])}
- GitHub-target size MB: {0.0 if github is None else float(github['total_mb']):.3f}
- Zenodo-target files: {0 if zenodo is None else int(zenodo['n_files'])}
- Zenodo-target size MB: {0.0 if zenodo is None else float(zenodo['total_mb']):.3f}

## Generated Files

- GitHub manifest: `{github_manifest.as_posix()}`
- Zenodo manifest: `{zenodo_manifest.as_posix()}`
- GitHub SHA256 sums: `release/github_sha256sums.txt`
- Zenodo SHA256 sums: `release/zenodo_sha256sums.txt`
- Zenodo deposition metadata: `release/zenodo_deposition_metadata.json`
- Zenodo deposition instructions: `release/ZENODO_DEPOSITION_INSTRUCTIONS.md`

## Claim Boundary

This script does not mint a DOI. If a real DOI has already been inserted into
`metadata/datasets.tsv` or the manuscript data availability statement, it is
preserved when release manifests are regenerated.
"""
    output.write_text(text, encoding="utf-8")


def _current_zenodo_doi(root: Path) -> str:
    candidates = [
        root / "release/ZENODO_API_UPLOAD_SUMMARY.json",
        root / "metadata/datasets.tsv",
        root / "release/DATA_AVAILABILITY_STATEMENT_DRAFT.md",
    ]
    pattern = re.compile(r"10\.5281/zenodo\.\d+")
    for path in candidates:
        if not path.exists():
            continue
        match = pattern.search(path.read_text(encoding="utf-8", errors="replace"))
        if match:
            return match.group(0)
    return "PENDING_ZENODO_RELEASE"


def write_data_availability(output: Path, root: Path) -> None:
    doi = _current_zenodo_doi(root)
    doi_line = (
        f"Current DOI status: `https://doi.org/{doi}`.\n\n"
        f"Frozen processed benchmark objects are available at https://doi.org/{doi}."
        if doi != "PENDING_ZENODO_RELEASE"
        else "Current DOI status: `PENDING_ZENODO_RELEASE`."
    )
    text = f"""# Data And Code Availability Statement Draft

All source code, tests, benchmark scripts, dataset manifests, and small summary
tables are intended for public release on GitHub. Raw public datasets remain
available from their original GEO/10x Genomics accessions as listed in
`metadata/datasets.tsv`.

Frozen processed benchmark objects and large generated spatial result tables
should be deposited on Zenodo before submission. The Zenodo record must include
the files listed in `release/zenodo_upload_manifest.tsv` and checksums from
`release/zenodo_sha256sums.txt`.

{doi_line}
"""
    output.write_text(text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--output-dir", default="release")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = root / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    inventory = build_release_inventory(root)
    inventory_path = output_dir / "release_file_inventory.tsv"
    github_manifest = output_dir / "github_release_manifest.tsv"
    zenodo_manifest = output_dir / "zenodo_upload_manifest.tsv"
    summary_path = output_dir / "REPRODUCIBILITY_RELEASE_SUMMARY.md"
    data_statement = output_dir / "DATA_AVAILABILITY_STATEMENT_DRAFT.md"

    inventory.to_csv(inventory_path, sep="\t", index=False)
    inventory.loc[inventory["release_target"] == "github"].to_csv(
        github_manifest,
        sep="\t",
        index=False,
    )
    inventory.loc[inventory["release_target"] == "zenodo"].to_csv(
        zenodo_manifest,
        sep="\t",
        index=False,
    )
    write_sha256sums(inventory, output_dir / "github_sha256sums.txt", "github")
    write_sha256sums(inventory, output_dir / "zenodo_sha256sums.txt", "zenodo")
    write_summary(
        output=summary_path,
        inventory=inventory,
        github_manifest=github_manifest.relative_to(root),
        zenodo_manifest=zenodo_manifest.relative_to(root),
    )
    write_data_availability(data_statement, root)

    print(f"wrote {inventory_path}")
    print(f"wrote {github_manifest}")
    print(f"wrote {zenodo_manifest}")
    print(f"wrote {summary_path}")
    print(f"wrote {data_statement}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
