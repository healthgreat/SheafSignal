#!/usr/bin/env python
"""Audit provenance for SheafSignal submission-facing artifacts.

Author: SheafSignal contributors
Date: 2026-05-01
Purpose: verify that key manuscript, figure, benchmark, quality-gate, upload,
and release artifacts are traceable to generator scripts or explicitly marked
as author-owned/external-pending before submission.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import json

import pandas as pd


STATIC_PROVENANCE_ROWS = [
    {
        "artifact_id": "publication_figures_manifest",
        "artifact_path": "manuscript/figure_manifest.tsv",
        "generator_path": "scripts/make_publication_figures.py",
        "source_paths": "benchmarks/results",
        "provenance_type": "generated",
    },
    {
        "artifact_id": "main_figure_quality_audit",
        "artifact_path": "manuscript/figure_quality/MAIN_FIGURE_QUALITY_AUDIT.tsv",
        "generator_path": "scripts/check_main_figure_quality.py",
        "source_paths": "manuscript/figure_manifest.tsv;manuscript/figure_legends/03_figure_source_map.tsv",
        "provenance_type": "generated",
    },
    {
        "artifact_id": "supplementary_artifact_audit",
        "artifact_path": "manuscript/supplementary_quality/SUPPLEMENTARY_ARTIFACT_AUDIT.tsv",
        "generator_path": "scripts/check_supplementary_artifacts.py",
        "source_paths": "manuscript/figure_manifest.tsv;manuscript/figure_legends/03_figure_source_map.tsv",
        "provenance_type": "generated",
    },
    {
        "artifact_id": "benchmark_result_contract_audit",
        "artifact_path": "benchmarks/results/BENCHMARK_RESULT_CONTRACT_AUDIT.tsv",
        "generator_path": "scripts/check_benchmark_result_contracts.py",
        "source_paths": "benchmarks/results/component_recovery.csv;benchmarks/results/public_tme_sheafsignal_summary.csv;benchmarks/results/tool_comparison.csv",
        "provenance_type": "generated",
    },
    {
        "artifact_id": "method_reporting_audit",
        "artifact_path": "manuscript/method_reporting/METHOD_REPORTING_AUDIT.tsv",
        "generator_path": "scripts/check_method_reporting_readiness.py",
        "source_paths": "manuscript/SCI_MANUSCRIPT_V2_POLISHED.md;benchmarks/results/BENCHMARK_RESULT_CONTRACT_AUDIT.tsv",
        "provenance_type": "generated",
    },
    {
        "artifact_id": "claim_safety_audit",
        "artifact_path": "manuscript/CLAIM_SAFETY_AUDIT.tsv",
        "generator_path": "scripts/check_claim_safety.py",
        "source_paths": "manuscript/SCI_MANUSCRIPT_V2_POLISHED.md;manuscript/nature_methods_package",
        "provenance_type": "generated",
    },
    {
        "artifact_id": "reference_package",
        "artifact_path": "manuscript/references/SCI_REFERENCE_GAP_REPORT.md",
        "generator_path": "scripts/build_reference_package.py",
        "source_paths": "manuscript/SCI_MANUSCRIPT_V1.md",
        "provenance_type": "generated",
    },
    {
        "artifact_id": "polished_manuscript_v2",
        "artifact_path": "manuscript/SCI_MANUSCRIPT_V2_POLISHED.md",
        "generator_path": "scripts/build_polished_sci_manuscript_v2.py",
        "source_paths": "manuscript/SCI_MANUSCRIPT_V1.md;manuscript/references/SCI_REFERENCE_GAP_REPORT.md",
        "provenance_type": "generated",
    },
    {
        "artifact_id": "submission_upload_package",
        "artifact_path": "manuscript/submission_upload_package/submission_upload_manifest.tsv",
        "generator_path": "scripts/build_submission_upload_package.py",
        "source_paths": "manuscript/SCI_MANUSCRIPT_V2_POLISHED.md;manuscript/SCI_COVER_LETTER_NatureMethods.md;manuscript/nature_methods_package/10_supplementary_information_draft.md",
        "provenance_type": "generated",
    },
    {
        "artifact_id": "nature_methods_format_audit",
        "artifact_path": "manuscript/NATURE_METHODS_FORMAT_AUDIT.tsv",
        "generator_path": "scripts/check_nature_methods_format.py",
        "source_paths": "manuscript/nature_methods_package",
        "provenance_type": "generated",
    },
    {
        "artifact_id": "final_submission_blockers",
        "artifact_path": "manuscript/FINAL_SUBMISSION_BLOCKERS.tsv",
        "generator_path": "scripts/check_final_submission_blockers.py",
        "source_paths": "metadata/datasets.tsv;manuscript/submission_metadata;release/DATA_AVAILABILITY_STATEMENT_DRAFT.md",
        "provenance_type": "generated",
    },
    {
        "artifact_id": "submission_readiness_report",
        "artifact_path": "manuscript/SUBMISSION_READINESS_REPORT.md",
        "generator_path": "scripts/build_submission_readiness_report.py",
        "source_paths": "manuscript/SCI20_50_SUBMISSION_GATES.tsv;benchmarks/results/tool_comparison.csv;release/archive_manifest.tsv",
        "provenance_type": "generated",
    },
    {
        "artifact_id": "reproducibility_release_manifest",
        "artifact_path": "release/github_release_manifest.tsv",
        "generator_path": "scripts/build_reproducibility_release.py",
        "source_paths": "src;scripts;tests;metadata;manuscript;benchmarks/results",
        "provenance_type": "generated",
    },
    {
        "artifact_id": "release_archives",
        "artifact_path": "release/archive_manifest.tsv",
        "generator_path": "scripts/package_release_archives.py",
        "source_paths": "release/github_release_manifest.tsv;release/zenodo_upload_manifest.tsv",
        "provenance_type": "generated",
    },
    {
        "artifact_id": "zenodo_deposition_metadata",
        "artifact_path": "release/zenodo_deposition_metadata.json",
        "generator_path": "scripts/build_zenodo_deposition_package.py",
        "source_paths": "release/archive_manifest.tsv;release/zenodo_upload_manifest.tsv",
        "provenance_type": "generated",
    },
    {
        "artifact_id": "submission_metadata_templates",
        "artifact_path": "manuscript/submission_metadata/AUTHOR_METADATA_TEMPLATE.tsv",
        "generator_path": "scripts/build_submission_metadata_templates.py",
        "source_paths": "manuscript/submission_metadata",
        "provenance_type": "author_owned_template",
    },
    {
        "artifact_id": "zenodo_doi",
        "artifact_path": "metadata/datasets.tsv",
        "generator_path": "NA",
        "source_paths": "release/archives/sheafsignal_zenodo_upload.zip",
        "provenance_type": "external_pending",
    },
    {
        "artifact_id": "github_public_release",
        "artifact_path": "release/archives/sheafsignal_github_release.zip",
        "generator_path": "NA",
        "source_paths": "release/github_release_manifest.tsv",
        "provenance_type": "external_pending",
    },
]


def _write_text_atomic(path: Path, text: str) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def _write_table_atomic(path: Path, table: pd.DataFrame) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    table.to_csv(tmp_path, sep="\t", index=False)
    tmp_path.replace(path)


def _resolve(root: Path, rel_or_abs: str) -> Path:
    path = Path(rel_or_abs.replace("\\", "/"))
    if not path.is_absolute():
        path = root / path
    return path


def _exists(root: Path, rel_or_abs: str) -> bool:
    if not rel_or_abs or rel_or_abs == "NA":
        return False
    return _resolve(root, rel_or_abs).exists()


def _missing_sources(root: Path, source_paths: str) -> list[str]:
    if not source_paths or source_paths == "NA":
        return []
    missing: list[str] = []
    for item in source_paths.split(";"):
        source = item.strip()
        if source and not _exists(root, source):
            missing.append(source)
    return missing


def _read_tsv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, sep="\t")


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def _zenodo_doi_completed(root: Path) -> bool:
    datasets = _read_text(root / "metadata/datasets.tsv")
    summary_path = root / "release/ZENODO_API_UPLOAD_SUMMARY.json"
    if "10.5281/zenodo." not in datasets or "PENDING_ZENODO_RELEASE" in datasets:
        return False
    if not summary_path.exists():
        return False
    try:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    published = str(summary.get("published_doi", ""))
    return published.startswith("10.5281/zenodo.")


def _github_release_completed(root: Path) -> bool:
    report = _read_text(root / "release/GITHUB_RELEASE_PUBLICATION_REPORT.md")
    return (
        "GITHUB_RELEASE_PUBLISHED" in report
        and "https://github.com/healthgreat/SheafSignal/releases/tag/v0.1.0" in report
    )


def _author_template_completed(root: Path, artifact_path: str) -> bool:
    text = _read_text(_resolve(root, artifact_path))
    pending_tokens = [
        "draft_pending_author_confirmation",
        "needs_author_confirmation",
        "tbd_by_authors",
        "TBD",
    ]
    return bool(text) and not any(token in text for token in pending_tokens)


def _status_for_row(
    *,
    artifact_exists: bool,
    generator_exists: bool,
    missing_sources: list[str],
    provenance_type: str,
) -> tuple[str, str]:
    if provenance_type == "external_pending":
        if artifact_exists and not missing_sources:
            return "pending_external", "external publication/deposition still required"
        return "fail", "external-pending artifact or upload source is missing"
    if provenance_type == "author_owned_template":
        if artifact_exists and generator_exists:
            return "pending_author_action", "template exists but author metadata must be completed"
        return "fail", "author-owned template or generator is missing"
    if not artifact_exists:
        return "fail", "artifact is missing"
    if not generator_exists:
        return "fail", "generator script is missing"
    if missing_sources:
        return "fail", "source path is missing"
    return "pass", "artifact has generator and source provenance"


def _static_rows(root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for item in STATIC_PROVENANCE_ROWS:
        artifact_exists = _exists(root, item["artifact_path"])
        generator_exists = (
            item["generator_path"] == "NA" or _exists(root, item["generator_path"])
        )
        missing_sources = _missing_sources(root, item["source_paths"])
        status, notes = _status_for_row(
            artifact_exists=artifact_exists,
            generator_exists=generator_exists,
            missing_sources=missing_sources,
            provenance_type=item["provenance_type"],
        )
        if item["artifact_id"] == "zenodo_doi" and _zenodo_doi_completed(root):
            status = "pass"
            notes = "Zenodo DOI minted and local metadata updated"
        elif item["artifact_id"] == "github_public_release" and _github_release_completed(root):
            status = "pass"
            notes = "GitHub release published and release URL recorded"
        elif item["provenance_type"] == "author_owned_template" and _author_template_completed(
            root, item["artifact_path"]
        ):
            status = "pass"
            notes = "author-owned metadata template is confirmed"
        rows.append(
            {
                **item,
                "artifact_exists": artifact_exists,
                "generator_exists": generator_exists,
                "missing_sources": ";".join(missing_sources) or "none",
                "status": status,
                "notes": notes,
            }
        )
    return rows


def _upload_manifest_rows(root: Path) -> list[dict[str, object]]:
    path = root / "manuscript/submission_upload_package/submission_upload_manifest.tsv"
    table = _read_tsv(path)
    rows: list[dict[str, object]] = []
    if table.empty or {"upload_item", "file_path", "source_path"}.difference(table.columns):
        rows.append(
            {
                "artifact_id": "upload_manifest_rows",
                "artifact_path": path.relative_to(root).as_posix(),
                "generator_path": "scripts/build_submission_upload_package.py",
                "source_paths": "manuscript/submission_upload_package/submission_upload_manifest.tsv",
                "provenance_type": "generated",
                "artifact_exists": path.exists(),
                "generator_exists": _exists(root, "scripts/build_submission_upload_package.py"),
                "missing_sources": "upload manifest missing or invalid",
                "status": "fail",
                "notes": "upload manifest schema is invalid",
            }
        )
        return rows
    for record in table.to_dict(orient="records"):
        upload_item = str(record.get("upload_item", "unknown"))
        file_path = str(record.get("file_path", ""))
        source_path = str(record.get("source_path", ""))
        artifact_exists = _exists(root, file_path)
        source_exists = source_path == "NA" or _exists(root, source_path)
        status = "pass" if artifact_exists and source_exists else "fail"
        rows.append(
            {
                "artifact_id": f"upload::{upload_item}",
                "artifact_path": file_path,
                "generator_path": "scripts/build_submission_upload_package.py",
                "source_paths": source_path,
                "provenance_type": "upload_manifest_item",
                "artifact_exists": artifact_exists,
                "generator_exists": _exists(root, "scripts/build_submission_upload_package.py"),
                "missing_sources": "none" if source_exists else source_path,
                "status": status,
                "notes": (
                    "upload item has source provenance"
                    if status == "pass"
                    else "upload item file or source is missing"
                ),
            }
        )
    return rows


def build_submission_provenance_audit(root: Path) -> pd.DataFrame:
    rows = [*_static_rows(root), *_upload_manifest_rows(root)]
    return pd.DataFrame(rows).sort_values(["status", "artifact_id"]).reset_index(drop=True)


def build_submission_provenance_report(audit: pd.DataFrame) -> str:
    failures = audit.loc[audit["status"].astype(str) == "fail"]
    pending = audit.loc[
        audit["status"].astype(str).isin(["pending_external", "pending_author_action"])
    ]
    decision = (
        "SUBMISSION_PROVENANCE_FAIL"
        if not failures.empty
        else "SUBMISSION_PROVENANCE_PASS_WITH_EXTERNAL_AND_AUTHOR_PENDING"
        if not pending.empty
        else "SUBMISSION_PROVENANCE_PASS"
    )
    lines = [
        "# Submission Provenance Audit",
        "",
        f"Decision: `{decision}`",
        "",
        f"- Provenance rows: {len(audit)}",
        f"- Failures: {len(failures)}",
        f"- External or author-pending rows: {len(pending)}",
        "",
        "## Rows Requiring Attention",
        "",
    ]
    if failures.empty and pending.empty:
        lines.append("None.")
    else:
        for row in pd.concat([failures, pending]).to_dict(orient="records"):
            lines.append(
                f"- `{row['artifact_id']}` `{row['status']}`: {row['notes']} "
                f"Artifact: `{row['artifact_path']}`"
            )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This audit checks local provenance and explicit external/author pending",
            "status. It does not mint a DOI, publish GitHub, or complete author",
            "metadata on behalf of the authors.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument(
        "--audit-out",
        default="manuscript/provenance/SUBMISSION_PROVENANCE_AUDIT.tsv",
    )
    parser.add_argument(
        "--report-out",
        default="manuscript/provenance/SUBMISSION_PROVENANCE_REPORT.md",
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Write outputs and return success even when provenance checks fail.",
    )
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    audit_out = root / args.audit_out
    report_out = root / args.report_out
    audit_out.parent.mkdir(parents=True, exist_ok=True)
    audit = build_submission_provenance_audit(root)
    _write_table_atomic(audit_out, audit)
    _write_text_atomic(report_out, build_submission_provenance_report(audit))
    print(f"wrote {audit_out}")
    print(f"wrote {report_out}")
    has_failures = bool((audit["status"].astype(str) == "fail").any())
    if has_failures and not args.report_only:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
