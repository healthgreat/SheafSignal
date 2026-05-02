#!/usr/bin/env python
"""Check final submission blockers for the SheafSignal Nature Methods route.

Author: SheafSignal contributors
Date: 2026-04-30
Purpose: make the final go/no-go state machine-readable before any 20-50 IF
submission attempt.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd

REQUIRED_NATURE_METHODS_FILES = [
    "manuscript/nature_methods_package/00_title_page.md",
    "manuscript/nature_methods_package/01_abstract.md",
    "manuscript/nature_methods_package/02_cover_letter_draft.md",
    "manuscript/nature_methods_package/03_main_text_skeleton.md",
    "manuscript/nature_methods_package/04_methods_skeleton.md",
    "manuscript/nature_methods_package/05_claim_evidence_map.tsv",
    "manuscript/nature_methods_package/06_figure_plan.tsv",
    "manuscript/nature_methods_package/07_submission_checklist.tsv",
    "manuscript/nature_methods_package/08_claim_boundaries_and_limitations.md",
    "manuscript/nature_methods_package/09_full_manuscript_draft.md",
    "manuscript/nature_methods_package/10_supplementary_information_draft.md",
]

REQUIRED_RELEASE_FILES = [
    "release/github_release_manifest.tsv",
    "release/zenodo_upload_manifest.tsv",
    "release/github_sha256sums.txt",
    "release/zenodo_sha256sums.txt",
    "release/archive_manifest.tsv",
    "release/REPRODUCIBILITY_RELEASE_SUMMARY.md",
    "release/DATA_AVAILABILITY_STATEMENT_DRAFT.md",
    "release/zenodo_deposition_metadata.json",
    "release/ZENODO_DEPOSITION_INSTRUCTIONS.md",
    "release/GITHUB_RELEASE_INSTRUCTIONS.md",
]

REQUIRED_SUBMISSION_METADATA_FILES = [
    "manuscript/submission_metadata/AUTHOR_METADATA_TEMPLATE.tsv",
    "manuscript/submission_metadata/AFFILIATIONS_TEMPLATE.tsv",
    "manuscript/submission_metadata/AUTHOR_CONTRIBUTIONS_CREDIT_TEMPLATE.tsv",
    "manuscript/submission_metadata/SUBMISSION_SYSTEM_METADATA_CHECKLIST.tsv",
    "manuscript/submission_metadata/COMPETING_INTERESTS_TEMPLATE.md",
    "manuscript/submission_metadata/ETHICS_AND_DATA_USE_STATEMENT.md",
    "manuscript/NATURE_METHODS_FORMAT_AUDIT.tsv",
    "manuscript/NATURE_METHODS_FORMAT_AUDIT_REPORT.md",
    "manuscript/presubmission_inquiry/00_one_page_editor_summary.md",
    "manuscript/presubmission_inquiry/01_presubmission_inquiry_letter.md",
    "manuscript/presubmission_inquiry/02_editorial_triage_risk_audit.tsv",
    "manuscript/presubmission_inquiry/03_novelty_evidence_matrix.tsv",
    "manuscript/presubmission_inquiry/04_editor_claim_boundary_note.md",
]

REQUIRED_RESPONSE_TRANSFER_FILES = [
    "manuscript/response_transfer/00_decision_tree.md",
    "manuscript/response_transfer/01_editorial_rejection_response_template.md",
    "manuscript/response_transfer/02_reviewer_response_skeleton.md",
    "manuscript/response_transfer/03_transfer_package_by_journal.tsv",
    "manuscript/response_transfer/04_target_specific_rewrite_actions.tsv",
    "manuscript/response_transfer/05_do_not_claim_checklist.md",
]

REQUIRED_FIGURE_LEGEND_FILES = [
    "manuscript/figure_legends/00_figure_legend_inventory.tsv",
    "manuscript/figure_legends/01_main_figure_legends.md",
    "manuscript/figure_legends/02_supplementary_figure_legends.md",
    "manuscript/figure_legends/03_figure_source_map.tsv",
    "manuscript/figure_legends/04_figure_claim_boundary_checklist.tsv",
]

REQUIRED_FIGURE_QUALITY_FILES = [
    "manuscript/figure_quality/MAIN_FIGURE_QUALITY_AUDIT.tsv",
    "manuscript/figure_quality/MAIN_FIGURE_QUALITY_REPORT.md",
]

REQUIRED_SUPPLEMENTARY_QUALITY_FILES = [
    "manuscript/supplementary_quality/SUPPLEMENTARY_ARTIFACT_AUDIT.tsv",
    "manuscript/supplementary_quality/SUPPLEMENTARY_ARTIFACT_REPORT.md",
]

REQUIRED_BENCHMARK_CONTRACT_FILES = [
    "benchmarks/results/BENCHMARK_RESULT_CONTRACT_AUDIT.tsv",
    "benchmarks/results/BENCHMARK_RESULT_CONTRACT_REPORT.md",
]

REQUIRED_SUBMISSION_PROVENANCE_FILES = [
    "manuscript/provenance/SUBMISSION_PROVENANCE_AUDIT.tsv",
    "manuscript/provenance/SUBMISSION_PROVENANCE_REPORT.md",
]

REQUIRED_METHOD_REPORTING_FILES = [
    "manuscript/method_reporting/METHOD_REPORTING_AUDIT.tsv",
    "manuscript/method_reporting/METHOD_REPORTING_REPORT.md",
    "manuscript/method_reporting/REVIEWER_RISK_REGISTER.tsv",
    "manuscript/method_reporting/REVIEWER_RISK_REPORT.md",
]

REQUIRED_CLAIM_SAFETY_FILES = [
    "manuscript/CLAIM_SAFETY_AUDIT.tsv",
    "manuscript/CLAIM_SAFETY_AUDIT_REPORT.md",
]

REQUIRED_SUPERGROK_HARDENING_FILES = [
    "manuscript/novelty_overlap/SHEAFSIGNAL_NOVELTY_OVERLAP_TABLE.tsv",
    "manuscript/novelty_overlap/SHEAFSIGNAL_NOVELTY_OVERLAP_REPORT.md",
    "manuscript/claim_hardening/CLAIM_HARDENING_AUDIT.tsv",
    "manuscript/claim_hardening/CLAIM_HARDENING_REPORT.md",
    "benchmarks/results/sensitivity/sensitivity_panel.csv",
    "benchmarks/results/sensitivity/SENSITIVITY_PANEL_REPORT.md",
    "benchmarks/results/gse154778_pdac_scrna/reannotation/reannotation_readiness.csv",
    "benchmarks/results/gse154778_pdac_scrna/reannotation/GSE154778_REANNOTATION_READINESS_REPORT.md",
]

REQUIRED_FORMAL_MANUSCRIPT_FILES = [
    "manuscript/SCI_TITLE_ABSTRACT_KEYWORDS.md",
    "manuscript/SCI_MANUSCRIPT_V1.md",
    "manuscript/SCI_MANUSCRIPT_V1_claim_tracked.md",
    "manuscript/SCI_COVER_LETTER_NatureMethods.md",
    "manuscript/SCI_AUTHOR_TODO.md",
]

REQUIRED_REFERENCE_FILES = [
    "manuscript/references/SCI_REFERENCES_VERIFIED.tsv",
    "manuscript/references/SCI_REFERENCES.bib",
    "manuscript/references/SCI_REFERENCE_PLACEHOLDER_MAP.tsv",
    "manuscript/references/SCI_REFERENCES.md",
    "manuscript/references/SCI_REFERENCE_GAP_REPORT.md",
    "manuscript/references/SCI_MANUSCRIPT_V1_referenced.md",
]

REQUIRED_POLISHED_MANUSCRIPT_FILES = [
    "manuscript/SCI_MANUSCRIPT_V2_POLISHED.md",
    "manuscript/SCI_MANUSCRIPT_V2_POLISHED_claim_tracked.md",
    "manuscript/SCI_MANUSCRIPT_V2_EDITORIAL_AUDIT.tsv",
    "manuscript/SCI_MANUSCRIPT_V2_CHANGELOG.tsv",
]

REQUIRED_SUBMISSION_UPLOAD_FILES = [
    "manuscript/submission_upload_package/SheafSignal_main_manuscript_v2.docx",
    "manuscript/submission_upload_package/SheafSignal_cover_letter_NatureMethods.docx",
    "manuscript/submission_upload_package/SheafSignal_supplementary_information.docx",
    "manuscript/submission_upload_package/submission_upload_manifest.tsv",
    "manuscript/submission_upload_package/submission_upload_preflight_checklist.tsv",
    "manuscript/submission_upload_package/main_figure_upload_manifest.tsv",
    "manuscript/submission_upload_package/DOCX_TEXT_EXTRACTION_CHECK.md",
    "manuscript/submission_upload_package/DOCX_LAYOUT_CHECK.tsv",
    "manuscript/submission_upload_package/README.md",
    "manuscript/submission_upload_package/main_figures/publication_figure1_sheafsignal_concept.pdf",
    "manuscript/submission_upload_package/main_figures/publication_figure2_component_recovery.pdf",
    "manuscript/submission_upload_package/main_figures/publication_figure3_tme_summary.pdf",
    "manuscript/submission_upload_package/main_figures/publication_figure4_gse154778_claim_gating.pdf",
    "manuscript/submission_upload_package/main_figures/publication_figure5_comparator_alignment.pdf",
]

BLOCKING_CHECKLIST_STATUSES = {
    "blocking_pending",
}

PENDING_CHECKLIST_STATUSES = {
    "pending",
    "pending_submission_day_check",
    "tbd_by_authors",
}

FORBIDDEN_POSITIVE_CLAIM_PATTERNS = {
    "guaranteed_acceptance": re.compile(
        r"\b(guarantee|guaranteed|guarantees)\b.{0,40}\b(acceptance|publication)\b",
        re.IGNORECASE,
    ),
    "clinical_utility_positive": re.compile(
        r"\b(demonstrate|demonstrates|establish|establishes|prove|proves)\b"
        r".{0,50}\bclinical utility\b",
        re.IGNORECASE,
    ),
    "therapeutic_recommendation_positive": re.compile(
        r"\b(recommend|recommends|guide|guides)\b.{0,60}\b(treatment|therapy|therapeutic)\b",
        re.IGNORECASE,
    ),
    "broad_superiority_positive": re.compile(
        r"\b(superior|outperform|outperforms|better than)\b.{0,80}"
        r"\b(CellChat|CellPhoneDB|LIANA|NicheNet|niche-DE|CCC tools)\b",
        re.IGNORECASE,
    ),
}

CLAIM_SCAN_FILES = [
    "manuscript/nature_methods_package/00_title_page.md",
    "manuscript/nature_methods_package/01_abstract.md",
    "manuscript/nature_methods_package/02_cover_letter_draft.md",
    "manuscript/nature_methods_package/03_main_text_skeleton.md",
    "manuscript/nature_methods_package/04_methods_skeleton.md",
    "manuscript/SCI_MANUSCRIPT_V2_POLISHED.md",
]


def _read_tsv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, sep="\t")


def _write_text_atomic(path: Path, text: str) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def _add_row(
    rows: list[dict[str, str]],
    *,
    blocker_id: str,
    severity: str,
    status: str,
    evidence: str,
    required_action: str,
) -> None:
    rows.append(
        {
            "blocker_id": blocker_id,
            "severity": severity,
            "status": status,
            "evidence": evidence,
            "required_action": required_action,
        }
    )


def check_required_files(root: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for rel in [
        *REQUIRED_NATURE_METHODS_FILES,
        *REQUIRED_RELEASE_FILES,
        *REQUIRED_SUBMISSION_METADATA_FILES,
        *REQUIRED_RESPONSE_TRANSFER_FILES,
        *REQUIRED_FIGURE_LEGEND_FILES,
        *REQUIRED_FIGURE_QUALITY_FILES,
        *REQUIRED_SUPPLEMENTARY_QUALITY_FILES,
        *REQUIRED_BENCHMARK_CONTRACT_FILES,
        *REQUIRED_SUBMISSION_PROVENANCE_FILES,
        *REQUIRED_METHOD_REPORTING_FILES,
        *REQUIRED_CLAIM_SAFETY_FILES,
        *REQUIRED_SUPERGROK_HARDENING_FILES,
        *REQUIRED_FORMAL_MANUSCRIPT_FILES,
        *REQUIRED_REFERENCE_FILES,
        *REQUIRED_POLISHED_MANUSCRIPT_FILES,
        *REQUIRED_SUBMISSION_UPLOAD_FILES,
    ]:
        exists = (root / rel).exists()
        _add_row(
            rows,
            blocker_id=f"required_file::{rel}",
            severity="blocking" if not exists else "pass",
            status="pass" if exists else "missing",
            evidence=rel,
            required_action="Create or regenerate this required submission file.",
        )
    return rows


def check_submission_metadata(root: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    checks = [
        (
            "author_metadata::authors",
            root / "manuscript/submission_metadata/AUTHOR_METADATA_TEMPLATE.tsv",
            "Fill all author names, emails, ORCIDs when available, corresponding author status, and conflict statements.",
        ),
        (
            "author_metadata::affiliations",
            root / "manuscript/submission_metadata/AFFILIATIONS_TEMPLATE.tsv",
            "Fill all affiliations.",
        ),
        (
            "author_metadata::credit_roles",
            root
            / "manuscript/submission_metadata/AUTHOR_CONTRIBUTIONS_CREDIT_TEMPLATE.tsv",
            "Assign authors to CRediT roles.",
        ),
        (
            "author_metadata::submission_system_checklist",
            root
            / "manuscript/submission_metadata/SUBMISSION_SYSTEM_METADATA_CHECKLIST.tsv",
            "Complete submission-system metadata checklist.",
        ),
    ]
    for blocker_id, path, action in checks:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        has_tbd = (
            "TBD" in text or "tbd_by_authors" in text or "pending_zenodo_doi" in text
        )
        _add_row(
            rows,
            blocker_id=blocker_id,
            severity="pending" if has_tbd else "pass",
            status="tbd_by_authors" if has_tbd else "pass",
            evidence=str(path.relative_to(root)),
            required_action=action,
        )

    for blocker_id, path, action in [
        (
            "author_metadata::competing_interests",
            root / "manuscript/submission_metadata/COMPETING_INTERESTS_TEMPLATE.md",
            "Replace TBD with final competing interests statement.",
        ),
        (
            "author_metadata::ethics_data_use",
            root / "manuscript/submission_metadata/ETHICS_AND_DATA_USE_STATEMENT.md",
            "Confirm final ethics/data-use wording with authors or institution.",
        ),
    ]:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        has_tbd = "TBD" in text
        _add_row(
            rows,
            blocker_id=blocker_id,
            severity="pending" if has_tbd else "pass",
            status="tbd_by_authors" if has_tbd else "pass",
            evidence=str(path.relative_to(root)),
            required_action=action,
        )
    return rows


def check_format_audit(root: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    path = root / "manuscript/NATURE_METHODS_FORMAT_AUDIT.tsv"
    if not path.exists():
        return rows
    audit = pd.read_csv(path, sep="\t")
    if audit.empty or "status" not in audit.columns:
        _add_row(
            rows,
            blocker_id="format_audit::invalid",
            severity="pending",
            status="invalid",
            evidence=str(path.relative_to(root)),
            required_action="Regenerate Nature Methods format audit.",
        )
        return rows
    issues = audit.loc[audit["status"].astype(str) != "pass"]
    _add_row(
        rows,
        blocker_id="format_audit::nature_methods",
        severity="pending" if not issues.empty else "pass",
        status="format_pending" if not issues.empty else "pass",
        evidence=(
            ";".join(issues["check_id"].astype(str).tolist())
            if not issues.empty
            else "all local format checks pass"
        ),
        required_action="Resolve Nature Methods format audit issues.",
    )
    return rows


def check_zenodo_doi(root: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    datasets = _read_tsv(root / "metadata/datasets.tsv")
    if datasets.empty or "zenodo_doi" not in datasets.columns:
        _add_row(
            rows,
            blocker_id="zenodo_doi::dataset_manifest",
            severity="blocking",
            status="missing_column_or_manifest",
            evidence="metadata/datasets.tsv",
            required_action="Add zenodo_doi values for public benchmark processed objects.",
        )
        return rows

    public_rows = datasets.loc[
        datasets["benchmark_role"].astype(str).str.contains("public_", na=False)
    ].copy()
    pending = public_rows.loc[
        public_rows["zenodo_doi"]
        .astype(str)
        .str.contains("PENDING|NA|TBD", case=False, na=True)
    ]
    _add_row(
        rows,
        blocker_id="zenodo_doi::dataset_manifest",
        severity="blocking" if not pending.empty else "pass",
        status="pending" if not pending.empty else "pass",
        evidence=(
            ";".join(pending["dataset_id"].astype(str).tolist())
            if not pending.empty
            else "all public benchmark rows have DOI values"
        ),
        required_action="Mint Zenodo DOI and replace PENDING_ZENODO_RELEASE in metadata/datasets.tsv.",
    )

    data_statement = root / "release/DATA_AVAILABILITY_STATEMENT_DRAFT.md"
    text = data_statement.read_text(encoding="utf-8") if data_statement.exists() else ""
    pending_statement = "PENDING_ZENODO_RELEASE" in text
    _add_row(
        rows,
        blocker_id="zenodo_doi::data_availability_statement",
        severity="blocking" if pending_statement else "pass",
        status="pending" if pending_statement else "pass",
        evidence="release/DATA_AVAILABILITY_STATEMENT_DRAFT.md",
        required_action="Insert the minted DOI into the data availability statement.",
    )
    return rows


def check_submission_checklist(root: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    checklist = _read_tsv(
        root / "manuscript/nature_methods_package/07_submission_checklist.tsv"
    )
    if checklist.empty:
        _add_row(
            rows,
            blocker_id="checklist::missing",
            severity="blocking",
            status="missing",
            evidence="manuscript/nature_methods_package/07_submission_checklist.tsv",
            required_action="Regenerate the Nature Methods submission package.",
        )
        return rows

    for row in checklist.to_dict(orient="records"):
        status = str(row.get("status", "missing"))
        if status in BLOCKING_CHECKLIST_STATUSES:
            severity = "blocking"
        elif status in PENDING_CHECKLIST_STATUSES:
            severity = "pending"
        else:
            severity = "pass"
        _add_row(
            rows,
            blocker_id=f"checklist::{row.get('item', 'unknown')}",
            severity=severity,
            status=status,
            evidence=str(row.get("evidence_or_action", "")),
            required_action=str(row.get("evidence_or_action", "")),
        )
    return rows


def check_forbidden_positive_claims(root: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    found = []
    for rel in CLAIM_SCAN_FILES:
        path = root / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for pattern_name, pattern in FORBIDDEN_POSITIVE_CLAIM_PATTERNS.items():
            match = pattern.search(text)
            if match:
                found.append(f"{rel}:{pattern_name}:{match.group(0)}")
    _add_row(
        rows,
        blocker_id="forbidden_positive_claims::manuscript_draft",
        severity="blocking" if found else "pass",
        status="found" if found else "pass",
        evidence=(
            " | ".join(found)
            if found
            else "No forbidden positive claim patterns detected."
        ),
        required_action="Remove or rewrite any positive clinical, guaranteed-publication, or broad-superiority claims.",
    )
    return rows


def check_claim_safety_audit(root: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    path = root / "manuscript/CLAIM_SAFETY_AUDIT.tsv"
    if not path.exists():
        _add_row(
            rows,
            blocker_id="claim_safety_audit::missing",
            severity="blocking",
            status="missing",
            evidence="manuscript/CLAIM_SAFETY_AUDIT.tsv",
            required_action="Run python scripts/check_claim_safety.py --report-only.",
        )
        return rows
    audit = pd.read_csv(path, sep="\t")
    if audit.empty or "classification" not in audit.columns:
        _add_row(
            rows,
            blocker_id="claim_safety_audit::invalid",
            severity="pending",
            status="invalid_or_empty",
            evidence="manuscript/CLAIM_SAFETY_AUDIT.tsv",
            required_action="Regenerate claim safety audit.",
        )
        return rows
    blocking = audit.loc[
        audit["classification"].astype(str) == "blocking_positive_claim"
    ]
    review = audit.loc[audit["classification"].astype(str) == "needs_author_review"]
    if not blocking.empty:
        evidence = ";".join(
            f"{row['relative_path']}:{row['line_no']}"
            for row in blocking.to_dict(orient="records")
        )
        severity = "blocking"
        status = "blocking_positive_claims_found"
    elif not review.empty:
        evidence = ";".join(
            f"{row['relative_path']}:{row['line_no']}"
            for row in review.to_dict(orient="records")
        )
        severity = "pending"
        status = "author_review_needed"
    else:
        evidence = "No blocking positive claims detected."
        severity = "pass"
        status = "pass"
    _add_row(
        rows,
        blocker_id="claim_safety_audit::manuscript_wide",
        severity=severity,
        status=status,
        evidence=evidence,
        required_action="Resolve blocking or author-review claim safety rows before submission.",
    )
    return rows


def check_reference_gap_report(root: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    path = root / "manuscript/references/SCI_REFERENCE_GAP_REPORT.md"
    if not path.exists():
        _add_row(
            rows,
            blocker_id="reference_gap_report::missing",
            severity="blocking",
            status="missing",
            evidence="manuscript/references/SCI_REFERENCE_GAP_REPORT.md",
            required_action="Run python scripts/build_reference_package.py.",
        )
        return rows
    text = path.read_text(encoding="utf-8")
    unresolved = "REFERENCE_GAPS_FOUND" in text
    _add_row(
        rows,
        blocker_id="reference_gap_report::placeholders",
        severity="blocking" if unresolved else "pass",
        status="unresolved_placeholders" if unresolved else "pass",
        evidence="manuscript/references/SCI_REFERENCE_GAP_REPORT.md",
        required_action="Resolve all [REF: ...] placeholders before journal formatting.",
    )
    return rows


def check_main_figure_quality(root: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    path = root / "manuscript/figure_quality/MAIN_FIGURE_QUALITY_AUDIT.tsv"
    if not path.exists():
        _add_row(
            rows,
            blocker_id="main_figure_quality::missing",
            severity="blocking",
            status="missing",
            evidence="manuscript/figure_quality/MAIN_FIGURE_QUALITY_AUDIT.tsv",
            required_action="Run python scripts/check_main_figure_quality.py.",
        )
        return rows
    audit = pd.read_csv(path, sep="\t")
    if audit.empty or "status" not in audit.columns:
        _add_row(
            rows,
            blocker_id="main_figure_quality::invalid",
            severity="blocking",
            status="invalid_or_empty",
            evidence="manuscript/figure_quality/MAIN_FIGURE_QUALITY_AUDIT.tsv",
            required_action="Regenerate main figure quality audit.",
        )
        return rows
    failures = audit.loc[audit["status"].astype(str) != "pass"]
    if failures.empty:
        severity = "pass"
        status = "pass"
        evidence = "All main figure PDFs passed automated quality checks."
    else:
        severity = "blocking"
        status = "failed"
        evidence = ";".join(
            f"{row['figure_id']}:{row['notes']}"
            for row in failures.to_dict(orient="records")
        )
    _add_row(
        rows,
        blocker_id="main_figure_quality::pdfs_and_source_boundaries",
        severity=severity,
        status=status,
        evidence=evidence,
        required_action="Regenerate figures or fix source-map boundaries before submission.",
    )
    return rows


def check_supplementary_artifact_quality(root: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    path = root / "manuscript/supplementary_quality/SUPPLEMENTARY_ARTIFACT_AUDIT.tsv"
    if not path.exists():
        _add_row(
            rows,
            blocker_id="supplementary_artifacts::missing",
            severity="blocking",
            status="missing",
            evidence="manuscript/supplementary_quality/SUPPLEMENTARY_ARTIFACT_AUDIT.tsv",
            required_action="Run python scripts/check_supplementary_artifacts.py.",
        )
        return rows
    audit = pd.read_csv(path, sep="\t")
    if audit.empty or "status" not in audit.columns:
        _add_row(
            rows,
            blocker_id="supplementary_artifacts::invalid",
            severity="blocking",
            status="invalid_or_empty",
            evidence="manuscript/supplementary_quality/SUPPLEMENTARY_ARTIFACT_AUDIT.tsv",
            required_action="Regenerate supplementary artifact audit.",
        )
        return rows
    failures = audit.loc[audit["status"].astype(str) != "pass"]
    if failures.empty:
        severity = "pass"
        status = "pass"
        evidence = f"{len(audit)} supplementary artifacts passed readability checks."
    else:
        severity = "blocking"
        status = "failed"
        evidence = ";".join(
            f"{row['artifact_id']}:{row['notes']}"
            for row in failures.to_dict(orient="records")
        )
    _add_row(
        rows,
        blocker_id="supplementary_artifacts::manifest_readability",
        severity=severity,
        status=status,
        evidence=evidence,
        required_action="Regenerate or remove failing supplementary manifest entries before submission.",
    )
    return rows


def check_benchmark_result_contracts(root: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    path = root / "benchmarks/results/BENCHMARK_RESULT_CONTRACT_AUDIT.tsv"
    if not path.exists():
        _add_row(
            rows,
            blocker_id="benchmark_result_contracts::missing",
            severity="blocking",
            status="missing",
            evidence="benchmarks/results/BENCHMARK_RESULT_CONTRACT_AUDIT.tsv",
            required_action="Run python scripts/check_benchmark_result_contracts.py.",
        )
        return rows
    audit = pd.read_csv(path, sep="\t")
    if audit.empty or "status" not in audit.columns:
        _add_row(
            rows,
            blocker_id="benchmark_result_contracts::invalid",
            severity="blocking",
            status="invalid_or_empty",
            evidence="benchmarks/results/BENCHMARK_RESULT_CONTRACT_AUDIT.tsv",
            required_action="Regenerate benchmark result contract audit.",
        )
        return rows
    failures = audit.loc[audit["status"].astype(str) == "fail"]
    if failures.empty:
        severity = "pass"
        status = "pass"
        evidence = "No benchmark result contract failures detected."
    else:
        severity = "blocking"
        status = "failed"
        evidence = ";".join(
            f"{row['check_id']}:{row['evidence']}"
            for row in failures.to_dict(orient="records")
        )
    _add_row(
        rows,
        blocker_id="benchmark_result_contracts::tables_and_links",
        severity=severity,
        status=status,
        evidence=evidence,
        required_action="Resolve failed benchmark result contract checks before submission.",
    )
    return rows


def check_submission_provenance(root: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    path = root / "manuscript/provenance/SUBMISSION_PROVENANCE_AUDIT.tsv"
    if not path.exists():
        _add_row(
            rows,
            blocker_id="submission_provenance::missing",
            severity="blocking",
            status="missing",
            evidence="manuscript/provenance/SUBMISSION_PROVENANCE_AUDIT.tsv",
            required_action="Run python scripts/check_submission_provenance.py.",
        )
        return rows
    audit = pd.read_csv(path, sep="\t")
    if audit.empty or "status" not in audit.columns:
        _add_row(
            rows,
            blocker_id="submission_provenance::invalid",
            severity="blocking",
            status="invalid_or_empty",
            evidence="manuscript/provenance/SUBMISSION_PROVENANCE_AUDIT.tsv",
            required_action="Regenerate submission provenance audit.",
        )
        return rows
    failures = audit.loc[audit["status"].astype(str) == "fail"]
    if failures.empty:
        severity = "pass"
        status = "pass"
        evidence = "No local submission provenance failures detected."
    else:
        severity = "blocking"
        status = "failed"
        evidence = ";".join(
            f"{row['artifact_id']}:{row['notes']}"
            for row in failures.to_dict(orient="records")
        )
    _add_row(
        rows,
        blocker_id="submission_provenance::local_traceability",
        severity=severity,
        status=status,
        evidence=evidence,
        required_action="Resolve local provenance failures before submission.",
    )
    return rows


def check_method_reporting_readiness(root: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    path = root / "manuscript/method_reporting/METHOD_REPORTING_AUDIT.tsv"
    if not path.exists():
        _add_row(
            rows,
            blocker_id="method_reporting::missing",
            severity="blocking",
            status="missing",
            evidence="manuscript/method_reporting/METHOD_REPORTING_AUDIT.tsv",
            required_action="Run python scripts/check_method_reporting_readiness.py.",
        )
        return rows
    audit = pd.read_csv(path, sep="\t")
    if audit.empty or "status" not in audit.columns:
        _add_row(
            rows,
            blocker_id="method_reporting::invalid",
            severity="blocking",
            status="invalid_or_empty",
            evidence="manuscript/method_reporting/METHOD_REPORTING_AUDIT.tsv",
            required_action="Regenerate method reporting audit.",
        )
        return rows
    failures = audit.loc[audit["status"].astype(str) == "fail"]
    if failures.empty:
        severity = "pass"
        status = "pass"
        evidence = "No method-reporting failures detected."
    else:
        severity = "blocking"
        status = "failed"
        evidence = ";".join(
            f"{row['check_id']}:{row['evidence']}"
            for row in failures.to_dict(orient="records")
        )
    _add_row(
        rows,
        blocker_id="method_reporting::local_readiness",
        severity=severity,
        status=status,
        evidence=evidence,
        required_action="Resolve failed method-reporting checks before submission.",
    )
    return rows


def check_supergrok_hardening_gates(root: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    tool_path = root / "benchmarks/results/tool_comparison.csv"
    if tool_path.exists():
        tool = pd.read_csv(tool_path)
    else:
        tool = pd.DataFrame()
    target_datasets = {
        "gse154778_pdac_scrna",
        "gse72056_melanoma_scrna",
        "gse176078_brca_scrna",
    }
    required_tools = {"CellChat", "CellPhoneDB"}
    completed_pairs: set[tuple[str, str]] = set()
    if not tool.empty and {"dataset_id", "tool", "status"}.issubset(tool.columns):
        completed = tool.loc[tool["status"].astype(str).str.startswith("completed")]
        completed_pairs = {
            (str(row["dataset_id"]), str(row["tool"]))
            for row in completed.to_dict(orient="records")
        }
    missing_pairs = sorted(
        f"{dataset}:{tool_name}"
        for dataset in target_datasets
        for tool_name in required_tools
        if (dataset, tool_name) not in completed_pairs
    )
    _add_row(
        rows,
        blocker_id="supergrok_hardening::cellchat_cellphonedb",
        severity="blocking" if missing_pairs else "pass",
        status="missing_required_comparators" if missing_pairs else "pass",
        evidence=";".join(missing_pairs) if missing_pairs else "CellChat and CellPhoneDB completed for all target scRNA-seq datasets.",
        required_action="Run and import CellChat and CellPhoneDB for GSE72056, GSE154778, and GSE176078 or formally downgrade manuscript scope.",
    )

    claim_path = root / "manuscript/claim_hardening/CLAIM_HARDENING_AUDIT.tsv"
    if claim_path.exists():
        claim = pd.read_csv(claim_path, sep="\t")
        blocking = (
            claim.loc[claim["classification"].astype(str) == "blocking_risky_claim"]
            if not claim.empty and "classification" in claim.columns
            else pd.DataFrame()
        )
        status = "blocking_risky_claims" if not blocking.empty else "pass"
        evidence = (
            ";".join(
                f"{row['relative_path']}:{row['line_no']}:{row['pattern_id']}"
                for row in blocking.to_dict(orient="records")
            )
            if not blocking.empty
            else "Claim hardening audit has no blocking risky claims."
        )
        severity = "blocking" if not blocking.empty else "pass"
    else:
        status = "missing"
        evidence = "manuscript/claim_hardening/CLAIM_HARDENING_AUDIT.tsv"
        severity = "blocking"
    _add_row(
        rows,
        blocker_id="supergrok_hardening::claim_language",
        severity=severity,
        status=status,
        evidence=evidence,
        required_action="Run check_manuscript_claim_hardening.py and downgrade risky biological/mechanistic claims.",
    )

    reannotation_path = (
        root
        / "benchmarks/results/gse154778_pdac_scrna/reannotation/reannotation_readiness.csv"
    )
    if reannotation_path.exists():
        reannotation = pd.read_csv(reannotation_path)
        blockers = reannotation.loc[reannotation["status"].astype(str) != "pass"]
        status = "missing_reannotation_inputs_or_dependencies" if not blockers.empty else "pass"
        evidence = (
            ";".join(blockers["check_id"].astype(str).tolist())
            if not blockers.empty
            else "GSE154778 reannotation readiness checks pass."
        )
        severity = "blocking" if not blockers.empty else "pass"
    else:
        status = "missing"
        evidence = str(reannotation_path.relative_to(root))
        severity = "blocking"
    _add_row(
        rows,
        blocker_id="supergrok_hardening::gse154778_reannotation",
        severity=severity,
        status=status,
        evidence=evidence,
        required_action="Complete independent GSE154778 Scanpy/Seurat-style reannotation or downgrade Myeloid claim.",
    )

    sensitivity_path = root / "benchmarks/results/sensitivity/sensitivity_panel.csv"
    if sensitivity_path.exists():
        sensitivity = pd.read_csv(sensitivity_path)
        pending = (
            sensitivity["statistical_status"].astype(str).str.contains(
                "not_run|missing",
                case=False,
                na=False,
            )
            if "statistical_status" in sensitivity.columns
            else pd.Series([True])
        )
        status = "pending_statistical_sensitivity" if bool(pending.any()) else "pass"
        evidence = (
            f"{int(pending.sum())} pending sensitivity/statistical rows"
            if bool(pending.any())
            else "Sensitivity panel has no pending rows."
        )
        severity = "blocking" if bool(pending.any()) else "pass"
    else:
        status = "missing"
        evidence = str(sensitivity_path.relative_to(root))
        severity = "blocking"
    _add_row(
        rows,
        blocker_id="supergrok_hardening::sensitivity_statistics",
        severity=severity,
        status=status,
        evidence=evidence,
        required_action="Complete sensitivity panel, permutation/FDR reporting, and bootstrap CI summaries.",
    )

    novelty_path = root / "manuscript/novelty_overlap/SHEAFSIGNAL_NOVELTY_OVERLAP_TABLE.tsv"
    if novelty_path.exists():
        novelty = pd.read_csv(novelty_path, sep="\t")
        required_classes = {
            "standard_ccc_tools",
            "graph_signal_processing",
            "hodge_biology_omics",
            "cellular_sheaf_methods",
        }
        present = set(novelty.get("comparison_class", pd.Series(dtype=str)).astype(str))
        missing = sorted(required_classes.difference(present))
        status = "missing_required_comparison_classes" if missing else "pass"
        severity = "blocking" if missing else "pass"
        evidence = ";".join(missing) if missing else "Novelty overlap table covers required comparison classes."
    else:
        status = "missing"
        evidence = str(novelty_path.relative_to(root))
        severity = "blocking"
    _add_row(
        rows,
        blocker_id="supergrok_hardening::novelty_overlap",
        severity=severity,
        status=status,
        evidence=evidence,
        required_action="Complete formal novelty/overlap matrix with CCC, graph signal, Hodge and sheaf method comparisons.",
    )
    return rows


def build_blocker_table(root: Path) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    rows.extend(check_required_files(root))
    rows.extend(check_zenodo_doi(root))
    rows.extend(check_submission_checklist(root))
    rows.extend(check_submission_metadata(root))
    rows.extend(check_format_audit(root))
    rows.extend(check_claim_safety_audit(root))
    rows.extend(check_reference_gap_report(root))
    rows.extend(check_main_figure_quality(root))
    rows.extend(check_supplementary_artifact_quality(root))
    rows.extend(check_benchmark_result_contracts(root))
    rows.extend(check_submission_provenance(root))
    rows.extend(check_method_reporting_readiness(root))
    rows.extend(check_supergrok_hardening_gates(root))
    rows.extend(check_forbidden_positive_claims(root))
    table = pd.DataFrame(rows)
    severity_order = {"blocking": 0, "pending": 1, "pass": 2}
    table["_order"] = table["severity"].map(severity_order).fillna(3)
    return table.sort_values(["_order", "blocker_id"]).drop(columns=["_order"])


def build_go_no_go_report(blockers: pd.DataFrame) -> str:
    blocking = blockers.loc[blockers["severity"] == "blocking"]
    pending = blockers.loc[blockers["severity"] == "pending"]
    decision = (
        "NO_GO"
        if not blocking.empty
        else "GO_WITH_PENDING_ITEMS" if not pending.empty else "GO"
    )
    lines = [
        "# Nature Methods Final Submission Go/No-Go Report",
        "",
        f"Decision: `{decision}`",
        "",
        f"- Blocking items: {len(blocking)}",
        f"- Pending non-blocking items: {len(pending)}",
        f"- Passed checks: {int((blockers['severity'] == 'pass').sum())}",
        "",
        "## Blocking Items",
        "",
    ]
    if blocking.empty:
        lines.append("None.")
    else:
        for row in blocking.to_dict(orient="records"):
            lines.append(
                f"- `{row['blocker_id']}`: {row['status']}. "
                f"Action: {row['required_action']}"
            )
    lines.extend(["", "## Pending Items", ""])
    if pending.empty:
        lines.append("None.")
    else:
        for row in pending.to_dict(orient="records"):
            lines.append(
                f"- `{row['blocker_id']}`: {row['status']}. "
                f"Action: {row['required_action']}"
            )
    lines.extend(
        [
            "",
            "## Interpretation Boundary",
            "",
            "This report checks local readiness. It does not guarantee journal acceptance.",
        "A final submission still requires any listed author confirmations,",
        "submission-day journal-format recheck if delayed, and the Zenodo DOI",
        "if listed as blocking.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument(
        "--blockers-out", default="manuscript/FINAL_SUBMISSION_BLOCKERS.tsv"
    )
    parser.add_argument(
        "--report-out", default="manuscript/NATURE_METHODS_GO_NO_GO_REPORT.md"
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Write reports and return success even when blocking items remain.",
    )
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    blockers = build_blocker_table(root)
    blockers_out = root / args.blockers_out
    report_out = root / args.report_out
    blockers_out.parent.mkdir(parents=True, exist_ok=True)
    blockers.to_csv(blockers_out, sep="\t", index=False)
    _write_text_atomic(report_out, build_go_no_go_report(blockers))
    print(f"wrote {blockers_out}")
    print(f"wrote {report_out}")

    has_blocking = bool((blockers["severity"] == "blocking").any())
    if has_blocking and not args.report_only:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
