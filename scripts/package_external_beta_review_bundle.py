#!/usr/bin/env python
"""Package a small shareable external beta-review bundle.

Author: SheafSignal contributors
Date: 2026-05-03
Purpose: create a reviewer handoff archive containing only small manuscript,
status, checklist, and review-form files. Large matrices, raw data, processed
objects, and release archives are intentionally excluded.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import zipfile
from dataclasses import dataclass
from pathlib import Path


OUTPUT_DIR = Path("external_ai_review_packet/shareable_review_bundle")
ARCHIVE_NAME = "sheafsignal_external_beta_review_bundle.zip"
MANIFEST_PATH = OUTPUT_DIR / "SHAREABLE_REVIEW_BUNDLE_MANIFEST.tsv"
REPORT_PATH = OUTPUT_DIR / "SHAREABLE_REVIEW_BUNDLE_REPORT.md"
ARCHIVE_PATH = OUTPUT_DIR / ARCHIVE_NAME

REQUIRED_FILES = [
    "README.md",
    "manuscript/IF20_50_DISTANCE_REPORT.md",
    "manuscript/SHEAFSIGNAL_STATUS_DASHBOARD_2026-05-03.md",
    "manuscript/SCI_MANUSCRIPT_V2_POLISHED.md",
    "manuscript/CLAIM_SAFETY_AUDIT_REPORT.md",
    "manuscript/novelty_overlap/SHEAFSIGNAL_NOVELTY_OVERLAP_REPORT.md",
    "manuscript/comparator_scope/COMPARATOR_SCOPE_REPORT.md",
    "manuscript/visium_scope/VISIUM_SCOPE_REPORT.md",
    "manuscript/method_reporting/METHOD_REPORTING_REPORT.md",
    "manuscript/journal_metric_audit/JOURNAL_METRIC_AUDIT_REPORT.md",
    "manuscript/submission_metadata/AUTHOR_CONFIRMATION_PREFLIGHT_REPORT.md",
    "release/SUBMISSION_UNBLOCKER_HANDOFF_ZH.md",
    "release/POST_UNBLOCK_RELEASE_PIPELINE_REPORT.md",
    "release/ZENODO_UPLOAD_PREFLIGHT_REPORT.md",
    "release/EXTERNAL_RELEASE_AUTHORIZATION_REPORT.md",
    "external_ai_review_packet/beta_review_packet_2026-05-02/00_README_FOR_REVIEWERS.md",
    "external_ai_review_packet/beta_review_packet_2026-05-02/01_BETA_REVIEW_PACKET_STATUS.md",
    "external_ai_review_packet/beta_review_packet_2026-05-02/02_EVIDENCE_FILE_INDEX.tsv",
    "external_ai_review_packet/beta_review_packet_2026-05-02/03_REVIEWER_CHECKLIST.tsv",
    "external_ai_review_packet/beta_review_packet_2026-05-02/04_AI_REVIEW_PROMPT.md",
    "external_ai_review_packet/beta_review_packet_2026-05-02/05_REVIEW_FORM_TEMPLATE.md",
    "external_ai_review_packet/EXTERNAL_BETA_REVIEW_TRIAGE_REPORT.md",
    "external_ai_review_packet/external_beta_review_action_matrix.tsv",
]

OPTIONAL_FILES = [
    "external_ai_review_packet/ROUND1_MULTI_AGENT_REVIEW_SUMMARY_2026-05-02.md",
    "external_ai_review_packet/round1_review_response_matrix.tsv",
    "external_ai_review_packet/ROUND2_HARDENING_STATUS_2026-05-02.md",
    "external_ai_review_packet/ROUND3_RETURNED_REVIEW_TRIAGE_2026-05-02.md",
    "external_ai_review_packet/round3_returned_review_triage.tsv",
    "benchmarks/results/BENCHMARK_RESULT_CONTRACT_REPORT.md",
    "benchmarks/results/confirmatory_10000/CONFIRMATORY_PERMUTATION_STATUS.md",
]


@dataclass(frozen=True)
class BundleRow:
    rel_path: str
    required: str
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


def _write_tsv_atomic(path: Path, rows: list[BundleRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    fieldnames = list(BundleRow.__dataclass_fields__.keys())
    with tmp_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow(row.__dict__)
    tmp_path.replace(path)


def _write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def _safe_files(root: Path, rel_paths: list[str], required: str) -> list[BundleRow]:
    rows = []
    for rel in rel_paths:
        path = root / rel
        if path.exists() and path.is_file():
            rows.append(
                BundleRow(
                    rel_path=rel,
                    required=required,
                    included="yes",
                    size_bytes=path.stat().st_size,
                    sha256=_sha256(path),
                    reason="small reviewer-facing evidence file",
                )
            )
        else:
            rows.append(
                BundleRow(
                    rel_path=rel,
                    required=required,
                    included="no",
                    size_bytes=0,
                    sha256="NA",
                    reason="missing",
                )
            )
    return rows


def build_bundle_manifest(root: Path) -> list[BundleRow]:
    rows = []
    rows.extend(_safe_files(root, REQUIRED_FILES, "yes"))
    rows.extend(_safe_files(root, OPTIONAL_FILES, "no"))
    return rows


def classify_decision(rows: list[BundleRow]) -> str:
    missing_required = [
        row for row in rows if row.required == "yes" and row.included != "yes"
    ]
    if missing_required:
        return "SHAREABLE_REVIEW_BUNDLE_BLOCKED_MISSING_REQUIRED_FILES"
    return "SHAREABLE_REVIEW_BUNDLE_READY"


def write_archive(root: Path, rows: list[BundleRow], archive_path: Path) -> str:
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = archive_path.with_suffix(archive_path.suffix + ".tmp")
    with zipfile.ZipFile(tmp_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for row in rows:
            if row.included == "yes":
                archive.write(root / row.rel_path, row.rel_path)
    tmp_path.replace(archive_path)
    return _sha256(archive_path)


def build_report(
    rows: list[BundleRow],
    *,
    decision: str,
    archive_path: Path,
    archive_sha256: str,
) -> str:
    included = [row for row in rows if row.included == "yes"]
    missing_required = [
        row.rel_path for row in rows if row.required == "yes" and row.included != "yes"
    ]
    missing_lines = [f"- `{path}`" for path in missing_required] or ["- none"]
    return "\n".join(
        [
            "# Shareable External Beta Review Bundle Report",
            "",
            f"- Decision: `{decision}`",
            f"- Archive: `{archive_path.as_posix()}`",
            f"- Archive SHA256: `{archive_sha256}`",
            f"- Included files: `{len(included)}`",
            f"- Missing required files: `{len(missing_required)}`",
            "",
            "## Missing Required Files",
            "",
            *missing_lines,
            "",
            "## Reviewer Instructions",
            "",
            "Send the archive to an external AI or human reviewer together with the request:",
            "`Please judge novelty, reproducibility, statistics, claim boundaries, and journal fit.`",
            "Returned `.md`, `.txt`, or `.tsv` reviews should be placed under",
            "`external_ai_review_packet/returned_reviews/` and triaged with:",
            "",
            "```bash",
            "python scripts/triage_external_beta_reviews.py",
            "```",
            "",
            "## Boundary",
            "",
            "This bundle is a review handoff. It does not contain raw data, processed omics objects,",
            "release archives, access tokens, or any guarantee of journal acceptance.",
            "",
        ]
    )


def build_outputs(root: Path, *, create_archive: bool = True) -> dict[str, object]:
    root = root.resolve()
    rows = build_bundle_manifest(root)
    decision = classify_decision(rows)
    archive_sha256 = "not_created"
    archive_path = root / ARCHIVE_PATH
    if create_archive and decision == "SHAREABLE_REVIEW_BUNDLE_READY":
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
        "missing_required": sum(row.required == "yes" and row.included != "yes" for row in rows),
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
    print(f"Missing required: {summary['missing_required']}")
    return 0 if summary["decision"] == "SHAREABLE_REVIEW_BUNDLE_READY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
