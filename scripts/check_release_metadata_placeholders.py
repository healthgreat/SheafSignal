#!/usr/bin/env python
"""Audit unresolved release metadata placeholders.

Author: SheafSignal contributors
Date: 2026-05-02
Purpose: separate author-owned metadata, public GitHub URL, and Zenodo DOI
placeholders before a 20-50 IF submission package is frozen.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path


DEFAULT_AUDIT_PATH = Path("release/RELEASE_METADATA_PLACEHOLDER_AUDIT.tsv")
DEFAULT_REPORT_PATH = Path("release/RELEASE_METADATA_PLACEHOLDER_REPORT.md")

TARGET_FILES = [
    "CITATION.cff",
    ".zenodo.json",
    "pyproject.toml",
    "metadata/datasets.tsv",
    "release/DATA_AVAILABILITY_STATEMENT_DRAFT.md",
    "release/zenodo_deposition_metadata.json",
    "release/ZENODO_DEPOSITION_INSTRUCTIONS.md",
    "release/GITHUB_RELEASE_INSTRUCTIONS.md",
    "manuscript/NATURE_METHODS_GO_NO_GO_REPORT.md",
    "manuscript/submission_metadata/AUTHOR_METADATA_TEMPLATE.tsv",
    "manuscript/submission_metadata/AFFILIATIONS_TEMPLATE.tsv",
    "manuscript/submission_metadata/AUTHOR_CONTRIBUTIONS_CREDIT_TEMPLATE.tsv",
    "manuscript/submission_metadata/COMPETING_INTERESTS_TEMPLATE.md",
    "manuscript/submission_metadata/ETHICS_AND_DATA_USE_STATEMENT.md",
    "manuscript/submission_metadata/SUBMISSION_SYSTEM_METADATA_CHECKLIST.tsv",
]

PLACEHOLDER_TOKENS = [
    "TBD",
    "PENDING_ZENODO_RELEASE",
    "PENDING",
    "github.com/TBD",
    "doi:10.",
]


@dataclass(frozen=True)
class PlaceholderHit:
    file: str
    line: int
    token: str
    category: str
    severity: str
    evidence: str
    required_action: str


def _write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def _write_tsv_atomic(path: Path, rows: list[PlaceholderHit]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    fieldnames = [
        "file",
        "line",
        "token",
        "category",
        "severity",
        "evidence",
        "required_action",
    ]
    with tmp_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow(row.__dict__)
    tmp_path.replace(path)


def classify_placeholder(rel_path: str, line_text: str, token: str) -> tuple[str, str, str]:
    rel = rel_path.replace("\\", "/")
    lower = line_text.lower()

    if "PENDING_ZENODO_RELEASE" in line_text or "zenodo" in rel and "doi" in lower:
        return (
            "zenodo_doi_pending",
            "blocking",
            "Mint the final Zenodo DOI only after release freeze, then replace this placeholder.",
        )

    if "github.com/TBD" in line_text or "repository-code" in lower or rel == "pyproject.toml":
        if "github" in lower or "repository" in lower or "homepage" in lower:
            return (
                "github_url_pending",
                "blocking",
                "Add the public GitHub repository URL after the remote is created.",
            )

    if rel.startswith("manuscript/submission_metadata/") or "tbd_by_authors" in lower:
        return (
            "author_owned_submission_metadata",
            "pending_author",
            "Authors must fill this journal submission field before upload.",
        )

    if rel in {"CITATION.cff", ".zenodo.json", "release/zenodo_deposition_metadata.json"} and "TBD" in line_text:
        return (
            "software_author_metadata_pending",
            "pending_author",
            "Replace software citation/deposition creators with final author names.",
        )

    if "pending" in lower:
        return (
            "status_or_instruction_pending",
            "informational",
            "Keep as status wording unless this file is part of final upload metadata.",
        )

    return (
        "generic_placeholder",
        "review",
        "Review whether this placeholder is intentional or must be replaced.",
    )


def scan_placeholders(root: Path, target_files: list[str] | None = None) -> list[PlaceholderHit]:
    root = root.resolve()
    hits: list[PlaceholderHit] = []
    for rel_path in target_files or TARGET_FILES:
        path = root / rel_path
        if not path.exists() or not path.is_file():
            continue
        for line_number, line_text in enumerate(
            path.read_text(encoding="utf-8", errors="replace").splitlines(),
            start=1,
        ):
            for token in PLACEHOLDER_TOKENS:
                if token in line_text:
                    category, severity, action = classify_placeholder(
                        rel_path, line_text, token
                    )
                    hits.append(
                        PlaceholderHit(
                            file=rel_path,
                            line=line_number,
                            token=token,
                            category=category,
                            severity=severity,
                            evidence=line_text.strip(),
                            required_action=action,
                        )
                    )
                    break
    return hits


def classify_decision(hits: list[PlaceholderHit]) -> str:
    if any(hit.severity == "blocking" for hit in hits):
        return "RELEASE_METADATA_BLOCKED_EXTERNAL_IDENTIFIERS"
    if any(hit.severity == "pending_author" for hit in hits):
        return "RELEASE_METADATA_AUTHOR_FIELDS_PENDING"
    if hits:
        return "RELEASE_METADATA_REVIEW_PLACEHOLDERS_PRESENT"
    return "RELEASE_METADATA_PLACEHOLDERS_CLEAR"


def build_report(hits: list[PlaceholderHit]) -> str:
    decision = classify_decision(hits)
    counts: dict[str, int] = {}
    for hit in hits:
        counts[hit.severity] = counts.get(hit.severity, 0) + 1

    count_lines = [f"- `{key}`: {value}" for key, value in sorted(counts.items())]
    if not count_lines:
        count_lines = ["- no placeholders detected"]

    blocking_lines = [
        f"- `{hit.file}:{hit.line}` [{hit.category}] {hit.evidence}"
        for hit in hits
        if hit.severity == "blocking"
    ]
    if not blocking_lines:
        blocking_lines = ["- none"]

    author_lines = [
        f"- `{hit.file}:{hit.line}` [{hit.category}] {hit.evidence}"
        for hit in hits
        if hit.severity == "pending_author"
    ][:20]
    if not author_lines:
        author_lines = ["- none"]

    return "\n".join(
        [
            "# Release Metadata Placeholder Report",
            "",
            f"- Decision: `{decision}`",
            f"- Placeholder hits: `{len(hits)}`",
            "",
            "## Severity Counts",
            "",
            *count_lines,
            "",
            "## Blocking External Identifiers",
            "",
            *blocking_lines,
            "",
            "## Author-Owned Fields",
            "",
            *author_lines,
            "",
            "## Interpretation Boundary",
            "",
            "This audit does not fill author names, affiliations, competing interests, "
            "public repository URLs, or Zenodo DOI values. It separates these pending "
            "items from code/scientific blockers so the release can be frozen only "
            "after the required external identifiers and author metadata are real.",
            "",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--audit-path", default=str(DEFAULT_AUDIT_PATH))
    parser.add_argument("--report-path", default=str(DEFAULT_REPORT_PATH))
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    hits = scan_placeholders(root)
    audit_path = root / args.audit_path
    report_path = root / args.report_path
    _write_tsv_atomic(audit_path, hits)
    _write_text_atomic(report_path, build_report(hits))

    decision = classify_decision(hits)
    print(decision)
    print(f"Audit: {audit_path.relative_to(root).as_posix()}")
    print(f"Report: {report_path.relative_to(root).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
