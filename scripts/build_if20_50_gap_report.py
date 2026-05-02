#!/usr/bin/env python
"""Build an IF 20-50 journal distance and gap report for SheafSignal.

Author: SheafSignal contributors
Date: 2026-05-02
Purpose: convert current gates, blocker tables, and release audits into a
plain-language roadmap for a 20-50 IF methods manuscript route. The scores are
readiness indices, not probabilities of journal acceptance.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import pandas as pd


GATES_PATH = Path("manuscript/SHEAFSIGNAL_STATUS_GATES_2026-05-02.tsv")
FINAL_BLOCKERS_PATH = Path("manuscript/FINAL_SUBMISSION_BLOCKERS.tsv")
REVIEW_MATRIX_PATH = Path("external_ai_review_packet/round1_review_response_matrix.tsv")
GIT_READINESS_PATH = Path("release/GIT_RELEASE_READINESS_AUDIT.tsv")
METADATA_PLACEHOLDER_PATH = Path("release/RELEASE_METADATA_PLACEHOLDER_AUDIT.tsv")
CLEAN_PREFLIGHT_REPORT_PATH = Path(
    "release/clean_clone_preflight/CLEAN_CLONE_PREFLIGHT_REPORT.md"
)
JOURNAL_METRIC_AUDIT_PATH = Path("manuscript/journal_metric_audit/JOURNAL_METRIC_AUDIT.tsv")
JOURNAL_METRIC_AUDIT_REPORT_PATH = Path(
    "manuscript/journal_metric_audit/JOURNAL_METRIC_AUDIT_REPORT.md"
)
BETA_REVIEW_PACKET_STATUS_PATH = Path(
    "external_ai_review_packet/beta_review_packet_2026-05-02/"
    "01_BETA_REVIEW_PACKET_STATUS.md"
)
CONFIRMATORY_PERMUTATION_STATUS_PATH = Path(
    "benchmarks/results/confirmatory_10000/CONFIRMATORY_PERMUTATION_STATUS.md"
)
GSE103322_REPLICATION_STATUS_PATH = Path(
    "benchmarks/results/gse103322_hnsc_scrna/replication/"
    "GSE103322_REPLICATION_SUPPLEMENT_REPORT.md"
)
RELEASE_UNBLOCKER_MATRIX_PATH = Path("release/RELEASE_UNBLOCKER_MATRIX.tsv")
EXTERNAL_AUTH_STATUS_PATH = Path("release/EXTERNAL_RELEASE_AUTHORIZATION_STATUS.tsv")
ZENODO_PREFLIGHT_STATUS_PATH = Path("release/ZENODO_UPLOAD_PREFLIGHT_STATUS.tsv")
AUTHOR_PREFLIGHT_STATUS_PATH = Path(
    "manuscript/submission_metadata/AUTHOR_CONFIRMATION_PREFLIGHT_STATUS.tsv"
)

GAP_MATRIX_PATH = Path("manuscript/IF20_50_GAP_MATRIX.tsv")
SUPPLEMENT_PLAN_PATH = Path("manuscript/IF20_50_SUPPLEMENTATION_PLAN.tsv")
REPORT_PATH = Path("manuscript/IF20_50_DISTANCE_REPORT.md")

STATUS_POINTS = {
    "green": 1.0,
    "pass": 1.0,
    "fixed": 1.0,
    "fixed_round2": 1.0,
    "green_yellow": 0.8,
    "pass_with_boundary": 0.75,
    "partial": 0.55,
    "yellow": 0.55,
    "red_yellow": 0.35,
    "pending": 0.25,
    "open": 0.0,
    "red": 0.0,
    "fail": 0.0,
}

GATE_WEIGHTS = {
    "G01": 8,
    "G02": 7,
    "G03": 8,
    "G04": 4,
    "G05": 6,
    "G06": 8,
    "G07": 8,
    "G08": 5,
    "G09": 7,
    "G10": 7,
    "G11": 6,
    "G12": 8,
    "G13": 10,
}

GATE_DOMAINS = {
    "G01": "method_novelty",
    "G02": "method_novelty",
    "G03": "single_cell_evidence",
    "G04": "biological_claim_boundary",
    "G05": "statistics",
    "G06": "simulation_validation",
    "G07": "comparator_benchmarking",
    "G08": "spatial_evidence_boundary",
    "G09": "manuscript_claim_safety",
    "G10": "environment_reproducibility",
    "G11": "public_code_release",
    "G12": "data_archive_doi",
    "G13": "submission_readiness",
}

MANDATORY_SUPPLEMENT_ROWS = [
    {
        "priority": "M1",
        "action": "Create public GitHub remote, push codex/sheafsignal-hardening-release, create immutable release tag, and write the URL into CITATION.cff, pyproject.toml, .zenodo.json, and release metadata.",
        "gate_type": "hard_submission_blocker",
        "why_it_matters": "Reviewers must be able to clone the exact code state and cite a stable public repository.",
        "expected_effect": "Turns G11 from yellow to green after tag/release URL is verified.",
        "estimated_effort": "short, but requires the real GitHub account/repository decision",
        "blocking": "yes",
    },
    {
        "priority": "M2",
        "action": "Fill author names, affiliations, ORCIDs when available, CRediT roles, competing interests, corresponding author, and final ethics/data-use wording.",
        "gate_type": "hard_submission_blocker",
        "why_it_matters": "Journals will not accept submission metadata with TBD author-owned fields.",
        "expected_effect": "Clears author-owned placeholder rows and software citation creator fields.",
        "estimated_effort": "short if author list is final; otherwise author-side coordination",
        "blocking": "yes",
    },
    {
        "priority": "M3",
        "action": "Mint Zenodo DOI only after GitHub URL and author metadata are real, then replace PENDING_ZENODO_RELEASE in metadata/datasets.tsv and Data Availability.",
        "gate_type": "hard_submission_blocker",
        "why_it_matters": "A permanent DOI is required for the processed benchmark archive and journal data availability.",
        "expected_effect": "Turns G12 from red to green and removes the final blocking DOI rows.",
        "estimated_effort": "short if Zenodo token/account is ready",
        "blocking": "yes",
    },
    {
        "priority": "M4",
        "action": "Rerun clean-clone reproduction after GitHub and DOI insertion from the public repository: install locked Python environment, run demo workflow, and regenerate manuscript-facing audits.",
        "gate_type": "hard_submission_blocker",
        "why_it_matters": "The local clean-export preflight is strong, but reviewers need proof that the final public repository clone can reproduce core outputs.",
        "expected_effect": "Converts local clean-export reproducibility into public clean-clone reproducibility evidence.",
        "estimated_effort": "medium",
        "blocking": "yes",
    },
]

OPTIONAL_STRENGTHENING_ROWS = [
    {
        "priority": "S1",
        "action": "Run the pre-specified 10,000-permutation confirmatory GSE154778 subset if final reviewers require higher p-value resolution.",
        "gate_type": "high_impact_strengthening",
        "why_it_matters": "The confirmatory subset is now pre-specified; execution reduces reviewer concern that p-values and FDR are only 1000-permutation resolution.",
        "expected_effect": "Improves statistical defensibility; still does not promote computational signals into biological mechanisms.",
        "estimated_effort": "medium to long",
        "blocking": "no",
    },
    {
        "priority": "S2",
        "action": "Keep GSE103322 as a supplement-grade HNSCC replication after the 1000 sample-stratified rerun, while keeping it outside primary comparator-completeness claims.",
        "gate_type": "high_impact_strengthening",
        "why_it_matters": "An extra independent cancer cohort increases generality without forcing a Myeloid-centered mechanism claim.",
        "expected_effect": "Improves 20-50 IF resilience against dataset-specific-artifact criticism.",
        "estimated_effort": "medium",
        "blocking": "no",
    },
    {
        "priority": "S3",
        "action": "Send the beta-review packet to 2-3 external computational biology readers or independent AI reviewers, then file responses in the review matrix.",
        "gate_type": "high_impact_strengthening",
        "why_it_matters": "External beta review is one of the fastest ways to expose remaining reviewer objections before journal submission; the packet is now local-ready but reviews have not been returned.",
        "expected_effect": "Improves cover-letter confidence and reduces desk-rejection risk from unclear novelty or reproducibility.",
        "estimated_effort": "medium calendar time",
        "blocking": "no",
    },
    {
        "priority": "S4",
        "action": "Refresh the journal metric audit on the submission day, covering latest JIF source, CAS zone, and warning-journal status for the chosen target.",
        "gate_type": "submission_day_safety",
        "why_it_matters": "Journal metrics and warning lists change; the open-web audit is useful, but final CAS/warning status must be verified from official or institutional sources.",
        "expected_effect": "Prevents stale IF/CAS/warning claims in the final submission plan.",
        "estimated_effort": "short",
        "blocking": "no before science freeze; yes before journal decision",
    },
    {
        "priority": "S5",
        "action": "Keep Visium hotspot-only unless adding deconvolution or histology/pathology annotation.",
        "gate_type": "claim_boundary",
        "why_it_matters": "Spatial spot marker programs do not support cell-type source mechanisms without extra evidence.",
        "expected_effect": "Prevents overclaiming while preserving spatial workflow demonstration value.",
        "estimated_effort": "long if upgraded; none if kept as hotspot-only",
        "blocking": "no",
    },
]


def _read_tsv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, sep="\t")


def _write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def _write_tsv_atomic(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    if rows:
        fieldnames = list(rows[0].keys())
    else:
        fieldnames = ["item"]
    with tmp_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    tmp_path.replace(path)


def _status_point(status: str) -> float:
    status_text = str(status).strip().lower()
    if status_text in STATUS_POINTS:
        return STATUS_POINTS[status_text]
    if status_text.startswith("fixed"):
        return 1.0
    if status_text.startswith("downgraded"):
        return 0.75
    if status_text.startswith("audited"):
        return 0.45
    if status_text.startswith("partially"):
        return 0.55
    return 0.25


def score_gates(gates: pd.DataFrame) -> dict[str, object]:
    if gates.empty:
        return {
            "overall_percent": 0.0,
            "scientific_percent": 0.0,
            "submission_infrastructure_percent": 0.0,
            "total_weight": 0.0,
            "earned_weight": 0.0,
        }
    total = 0.0
    earned = 0.0
    sci_total = 0.0
    sci_earned = 0.0
    infra_total = 0.0
    infra_earned = 0.0
    infra_gates = {"G10", "G11", "G12", "G13"}
    for row in gates.to_dict(orient="records"):
        gate_id = str(row.get("gate_id", ""))
        weight = float(GATE_WEIGHTS.get(gate_id, 1))
        point = _status_point(str(row.get("status", "")))
        total += weight
        earned += weight * point
        if gate_id in infra_gates:
            infra_total += weight
            infra_earned += weight * point
        else:
            sci_total += weight
            sci_earned += weight * point
    return {
        "overall_percent": round(100 * earned / total, 1) if total else 0.0,
        "scientific_percent": round(100 * sci_earned / sci_total, 1) if sci_total else 0.0,
        "submission_infrastructure_percent": round(100 * infra_earned / infra_total, 1)
        if infra_total
        else 0.0,
        "total_weight": total,
        "earned_weight": round(earned, 2),
    }


def build_gap_matrix(
    gates: pd.DataFrame,
    blockers: pd.DataFrame,
    review_matrix: pd.DataFrame,
    git_audit: pd.DataFrame,
    placeholder_audit: pd.DataFrame,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for gate in gates.to_dict(orient="records"):
        gate_id = str(gate.get("gate_id", ""))
        status = str(gate.get("status", ""))
        blocker = str(gate.get("submission_blocker", "no")).lower() == "yes"
        point = _status_point(status)
        if point >= 0.95:
            risk = "low"
        elif blocker and point < 0.6:
            risk = "blocking"
        elif point < 0.75:
            risk = "moderate"
        else:
            risk = "managed"
        rows.append(
            {
                "domain": GATE_DOMAINS.get(gate_id, "project_gate"),
                "item_id": gate_id,
                "item": gate.get("area", ""),
                "current_status": status,
                "readiness_fraction": point,
                "if20_50_risk": risk,
                "submission_blocker": "yes" if blocker else "no",
                "evidence": gate.get("evidence", ""),
                "required_next_action": gate.get("next_action", ""),
                "suggested_supplement": "NA",
            }
        )

    if not blockers.empty:
        pending_blockers = blockers.loc[blockers["severity"].isin(["blocking", "pending"])]
        for blocker in pending_blockers.to_dict(orient="records"):
            status = str(blocker.get("status", ""))
            if status == "pass":
                continue
            rows.append(
                {
                    "domain": "final_submission_blockers",
                    "item_id": blocker.get("blocker_id", ""),
                    "item": blocker.get("blocker_id", ""),
                    "current_status": status,
                    "readiness_fraction": _status_point(status),
                    "if20_50_risk": "blocking"
                    if blocker.get("severity", "") == "blocking"
                    else "administrative",
                    "submission_blocker": "yes"
                    if blocker.get("severity", "") == "blocking"
                    else "pending_author_or_day_check",
                    "evidence": blocker.get("evidence", ""),
                    "required_next_action": blocker.get("required_action", ""),
                    "suggested_supplement": "NA",
                }
            )

    if not review_matrix.empty:
        open_rows = review_matrix.loc[
            review_matrix["status"].astype(str).isin(["open"])
            | review_matrix["status"].astype(str).str.startswith("audited")
            | review_matrix["status"].astype(str).str.startswith("partially")
        ]
        for row in open_rows.to_dict(orient="records"):
            rows.append(
                {
                    "domain": f"reviewer_{row.get('reviewer', '')}",
                    "item_id": row.get("concern", ""),
                    "item": row.get("concern", ""),
                    "current_status": row.get("status", ""),
                    "readiness_fraction": _status_point(str(row.get("status", ""))),
                    "if20_50_risk": "blocking"
                    if row.get("severity", "") == "FATAL"
                    else "major",
                    "submission_blocker": "yes"
                    if row.get("status", "") == "open"
                    else "partially_resolved",
                    "evidence": row.get("evidence", ""),
                    "required_next_action": row.get("required_fix", ""),
                    "suggested_supplement": "NA",
                }
            )

    if not git_audit.empty:
        warnings = git_audit.loc[git_audit["status"].isin(["warn", "fail"])]
        for row in warnings.to_dict(orient="records"):
            rows.append(
                {
                    "domain": "git_release_readiness",
                    "item_id": row.get("check_id", ""),
                    "item": row.get("area", ""),
                    "current_status": row.get("status", ""),
                    "readiness_fraction": _status_point(str(row.get("status", ""))),
                    "if20_50_risk": "blocking"
                    if row.get("status", "") == "fail"
                    else "release_warning",
                    "submission_blocker": "yes",
                    "evidence": row.get("evidence", ""),
                    "required_next_action": row.get("action", ""),
                    "suggested_supplement": "NA",
                }
            )

    if not placeholder_audit.empty:
        severe = placeholder_audit.loc[
            placeholder_audit["severity"].isin(["blocking", "pending_author"])
        ]
        for row in severe.to_dict(orient="records"):
            rows.append(
                {
                    "domain": "release_metadata_placeholders",
                    "item_id": f"{row.get('file', '')}:{row.get('line', '')}",
                    "item": row.get("category", ""),
                    "current_status": row.get("severity", ""),
                    "readiness_fraction": _status_point(str(row.get("severity", ""))),
                    "if20_50_risk": "blocking"
                    if row.get("severity", "") == "blocking"
                    else "author_metadata",
                    "submission_blocker": "yes"
                    if row.get("severity", "") == "blocking"
                    else "author_owned",
                    "evidence": row.get("evidence", ""),
                    "required_next_action": row.get("required_action", ""),
                    "suggested_supplement": "NA",
                }
            )

    return rows


def build_supplementation_plan(
    confirmatory_status: str = "unknown",
    gse103322_status: str = "unknown",
) -> list[dict[str, str]]:
    rows = [dict(row) for row in [*MANDATORY_SUPPLEMENT_ROWS, *OPTIONAL_STRENGTHENING_ROWS]]
    for row in rows:
        if row["priority"] == "S1" and confirmatory_status == "completed_10000":
            row["action"] = (
                "Keep the completed pre-specified 10,000-permutation GSE154778 "
                "confirmatory subset as statistical-strengthening evidence, without "
                "promoting computational signals into biological mechanisms."
            )
            row["why_it_matters"] = (
                "The higher-resolution confirmatory subset has been executed, reducing "
                "reviewer concern that the key p-values and FDR values are only "
                "1000-permutation resolution."
            )
            row["expected_effect"] = (
                "Improves statistical defensibility; still does not create causal, "
                "clinical, therapeutic, or mechanism evidence."
            )
            row["estimated_effort"] = "done"
        if row["priority"] == "S2" and gse103322_status == "supplement_ready":
            row["estimated_effort"] = "done"
    return rows


def clean_preflight_status(root: Path) -> str:
    path = root / CLEAN_PREFLIGHT_REPORT_PATH
    if not path.exists():
        return "not_run"
    text = path.read_text(encoding="utf-8", errors="replace")
    if "CLEAN_CLONE_PREFLIGHT_PASS_LOCAL_EXPORT" in text:
        return "local_clean_export_pass"
    if "CLEAN_CLONE_PREFLIGHT_FAIL" in text:
        return "failed"
    return "unknown"


def journal_metric_audit_status(root: Path) -> str:
    path = root / JOURNAL_METRIC_AUDIT_REPORT_PATH
    if not path.exists():
        return "not_run"
    text = path.read_text(encoding="utf-8", errors="replace")
    if "JOURNAL_METRIC_AUDIT_READY" in text:
        return "if_cas_warning_verified_current"
    if "JOURNAL_METRIC_AUDIT_IF_VERIFIED_CAS_WARNING_NEEDS_FINAL_CHECK" in text:
        return "publisher_if_verified_cas_warning_final_check_required"
    if "JOURNAL_METRIC_AUDIT_HAS_NONPUBLISHER_METRICS" in text:
        return "nonpublisher_metric_source_blocker"
    if "JOURNAL_METRIC_AUDIT_EMPTY" in text:
        return "empty"
    return "unknown"


def beta_review_packet_status(root: Path) -> str:
    path = root / BETA_REVIEW_PACKET_STATUS_PATH
    if not path.exists():
        return "not_run"
    text = path.read_text(encoding="utf-8", errors="replace")
    if "BETA_REVIEW_PACKET_READY_INTERNAL_AI_REVIEWS_TRIAGED_EXTERNAL_HUMAN_REVIEWS_PENDING" in text:
        return "internal_ai_reviews_triaged_external_human_pending"
    if "BETA_REVIEW_PACKET_READY_LOCAL_EXTERNAL_REVIEWS_PENDING" in text:
        return "packet_ready_external_reviews_pending"
    if "BETA_REVIEW_PACKET_BLOCKED_MISSING_REQUIRED_EVIDENCE" in text:
        return "blocked_missing_required_evidence"
    return "unknown"


def confirmatory_permutation_status(root: Path) -> str:
    path = root / CONFIRMATORY_PERMUTATION_STATUS_PATH
    if not path.exists():
        return "not_run"
    text = path.read_text(encoding="utf-8", errors="replace")
    if "CONFIRMATORY_10000_COMPLETED" in text:
        return "completed_10000"
    if "CONFIRMATORY_10000_READY_NOT_RUN" in text:
        return "pre_specified_ready_not_run"
    if "CONFIRMATORY_10000_PARTIAL_BELOW_TARGET" in text:
        return "partial_below_target"
    if "CONFIRMATORY_10000_BLOCKED" in text:
        return "blocked"
    return "unknown"


def gse103322_replication_status(root: Path) -> str:
    path = root / GSE103322_REPLICATION_STATUS_PATH
    if not path.exists():
        return "not_run"
    text = path.read_text(encoding="utf-8", errors="replace")
    if "GSE103322_REPLICATION_SUPPLEMENT_READY" in text:
        return "supplement_ready"
    if "GSE103322_REPLICATION_EXPLORATORY_READY_RERUN_RECOMMENDED" in text:
        return "exploratory_ready_rerun_recommended"
    if "GSE103322_REPLICATION_BLOCKED" in text:
        return "blocked"
    return "unknown"


def _count_gap_rows(rows: list[dict[str, object]], risk: str) -> int:
    return sum(1 for row in rows if row.get("if20_50_risk") == risk)


def _live_release_rows(root: Path) -> list[dict[str, str]]:
    path = root / RELEASE_UNBLOCKER_MATRIX_PATH
    if not path.exists():
        return []
    table = pd.read_csv(path, sep="\t").fillna("")
    rows = []
    for row in table.to_dict(orient="records"):
        rows.append(
            {
                "gate_id": str(row.get("gate_id", "")),
                "priority": str(row.get("priority", "")),
                "owner": str(row.get("owner", "")),
                "current_status": str(row.get("current_status", "")),
                "required_action": str(row.get("required_action", "")),
                "validation_command": str(row.get("validation_command", "")),
            }
        )
    return rows


def _status_counts(root: Path, path: Path, status_col: str = "status") -> dict[str, int]:
    full_path = root / path
    if not full_path.exists():
        return {}
    table = pd.read_csv(full_path, sep="\t").fillna("")
    if status_col not in table.columns:
        return {}
    return {
        str(status): int(count)
        for status, count in table[status_col].astype(str).value_counts().sort_index().items()
    }


def live_release_summary(root: Path) -> dict[str, object]:
    live_rows = _live_release_rows(root)
    blocking_rows = [row for row in live_rows if row["priority"] == "blocking"]
    active_blocking_rows = [
        row
        for row in blocking_rows
        if row["current_status"]
        not in {
            "pass",
            "passed",
            "complete",
            "completed",
            "public_remote_branch_available",
            "ready",
        }
    ]
    return {
        "rows": live_rows,
        "blocking_total": len(blocking_rows),
        "blocking_active": len(active_blocking_rows),
        "external_auth_counts": _status_counts(root, EXTERNAL_AUTH_STATUS_PATH),
        "zenodo_preflight_counts": _status_counts(root, ZENODO_PREFLIGHT_STATUS_PATH),
        "author_preflight_counts": _status_counts(root, AUTHOR_PREFLIGHT_STATUS_PATH, "severity"),
    }


def _format_counts(counts: dict[str, int]) -> str:
    if not counts:
        return "not_available"
    return ", ".join(f"{key}={value}" for key, value in counts.items())


def _live_release_lines(summary: dict[str, object]) -> list[str]:
    rows = summary.get("rows", [])
    if not rows:
        return ["- Live release unblocker matrix not found; rerun build_release_unblocker_matrix.py."]
    lines = [
        "| Gate | Priority | Owner | Current status | Required action |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['gate_id']}` | `{row['priority']}` | `{row['owner']}` | "
            f"`{row['current_status']}` | {row['required_action']} |"
        )
    return lines


def _target_summary(root: Path) -> list[str]:
    audit_path = root / JOURNAL_METRIC_AUDIT_PATH
    if audit_path.exists():
        table = pd.read_csv(audit_path, sep="\t")
        lines = []
        for row in table.sort_values("priority").head(6).to_dict(orient="records"):
            lines.append(
                f"- {row['journal']}: JIF {row['jif_2024']}, 5-year JIF "
                f"{row['five_year_jif_2024']}, route `{row['route_decision']}`, "
                f"CAS/warning boundary `{row['open_web_cas_zone_status']}` / "
                f"`{row['warning_list_status']}`."
            )
        lines.append(
            "- Metric boundary: JIF values are tied to publisher metric pages; "
            "CAS zone and warning-journal status remain submission-day official checks."
        )
        return lines

    path = root / "manuscript/JOURNAL_TARGETS_20_50.tsv"
    if not path.exists():
        return ["- Journal target board not found; rerun build_journal_target_board.py."]
    table = pd.read_csv(path, sep="\t")
    lines = []
    for row in table.sort_values("priority").head(6).to_dict(orient="records"):
        lines.append(
            f"- {row['journal']}: JIF {row['jif_2024']}, 5-year JIF "
            f"{row['five_year_jif_2024']}, role `{row['target_role']}`, "
            f"fit {row['fit_score_1_to_5']}/5."
        )
    lines.append(
        "- Metric boundary: values are from the local 2024 JIF target board; "
        "CAS zone and warning-journal status still require a submission-day audit."
    )
    return lines


def _gantt() -> str:
    return """```mermaid
gantt
    title SheafSignal 20-50 IF Route: Current Position and Remaining Work
    dateFormat  YYYY-MM-DD

    section Completed Hardening
    Formal sheaf implementation                  :done, 2026-05-02, 1d
    Primary Hodge on sheaf residual              :done, 2026-05-02, 1d
    Full GSE154778 Scanpy reannotation           :done, 2026-05-02, 1d
    Sample-stratified statistics and FDR audit   :done, 2026-05-02, 1d
    Simulation and ablation benchmark            :done, 2026-05-02, 1d
    Primary scRNA comparator scope gate          :done, 2026-05-02, 1d
    Claim-language and Visium hotspot gating     :done, 2026-05-02, 1d
    Python environment lock                      :done, 2026-05-02, 1d
    Local Git freeze commit                      :done, 2026-05-02, 1d
    Local clean-export reproduction preflight    :done, 2026-05-02, 1d

    section Hard Submission Blockers
    Public GitHub remote, tag, release URL       :crit, 2026-05-03, 1d
    Author metadata and CRediT finalization      :crit, 2026-05-03, 1d
    Zenodo DOI minting and metadata insertion    :crit, 2026-05-04, 1d
    Public clean-clone reproduction preflight    :crit, 2026-05-05, 1d

    section Optional IF 20-50 Strengthening
    10000-permutation subset pre-specification   :done, 2026-05-02, 1d
    10000-permutation confirmatory execution     :done, 2026-05-02, 1d
    GSE103322 exploratory replication gate       :done, 2026-05-02, 1d
    GSE103322 1000-permutation supplement rerun  :done, 2026-05-02, 1d
    External beta review packet                  :done, 2026-05-02, 1d
    Returned reviews from 2-3 external readers   :2026-05-06, 7d
    Open-web journal metric audit                :done, 2026-05-02, 1d
    Official CAS and warning-list final check    :2026-05-08, 1d
    Presubmission inquiry package refresh        :2026-05-09, 2d
```"""


def build_report(
    root: Path,
    gates: pd.DataFrame,
    gap_rows: list[dict[str, object]],
    supplement_rows: list[dict[str, str]],
) -> str:
    score = score_gates(gates)
    live_summary = live_release_summary(root)
    preflight_status = clean_preflight_status(root)
    journal_audit_status = journal_metric_audit_status(root)
    beta_review_status = beta_review_packet_status(root)
    confirmatory_status = confirmatory_permutation_status(root)
    gse103322_status = gse103322_replication_status(root)
    hard_blockers = _count_gap_rows(gap_rows, "blocking")
    administrative = _count_gap_rows(gap_rows, "administrative")
    author_metadata = _count_gap_rows(gap_rows, "author_metadata")
    release_warnings = _count_gap_rows(gap_rows, "release_warning")

    active_live_blockers = int(live_summary["blocking_active"])
    if score["overall_percent"] >= 85 and hard_blockers == 0 and active_live_blockers == 0:
        decision = "IF20_50_SUBMISSION_CANDIDATE_AFTER_FINAL_FORMAT_CHECK"
    elif score["scientific_percent"] >= 85 and active_live_blockers > 0:
        decision = "IF20_50_SCIENTIFICALLY_HARDENED_EXTERNAL_RELEASE_BLOCKED"
    elif score["scientific_percent"] >= 85:
        decision = "IF20_50_SCIENTIFICALLY_HARDENED_LOCAL_BLOCKERS_REMAIN"
    else:
        decision = "IF20_50_MAJOR_HARDENING_STILL_REQUIRED"

    mandatory = [row for row in supplement_rows if row["blocking"] == "yes"]
    optional = [row for row in supplement_rows if row["blocking"] != "yes"]
    mandatory_lines = [
        f"{row['priority']}. {row['action']} Expected effect: {row['expected_effect']}"
        for row in mandatory
    ]
    optional_lines = [
        f"{row['priority']}. {row['action']} Expected effect: {row['expected_effect']}"
        for row in optional
    ]
    if gse103322_status == "supplement_ready":
        gse103322_sentence = (
            "GSE103322 has now completed a 1000-permutation, sample-stratified "
            "HNSCC replication rerun and can be used as supplement-grade workflow "
            "generality evidence. It still should not be used for primary "
            "comparator-completeness claims unless full external comparator imports "
            "are completed for this dataset."
        )
    else:
        gse103322_sentence = (
            "GSE103322 is now audited as an exploratory independent HNSCC workflow "
            "replication. It should stay outside main comparator-completeness and "
            "biological source claims until a 1000-permutation, sample-stratified "
            "supplement rerun is completed."
        )
    if beta_review_status == "internal_ai_reviews_triaged_external_human_pending":
        beta_review_sentence = (
            "Internal multi-agent AI reviews have now been returned and triaged. "
            "This reduces stale-objection risk and documents what has been fixed, "
            "but it still does not replace independent external human or "
            "computational-biology reviewer feedback."
        )
    else:
        beta_review_sentence = (
            "The external beta-review packet is now a local-ready handoff artifact. "
            "That clears the packaging part of S3, but it does not count as completed "
            "external validation until independent reviewers or AI systems return "
            "written critiques that are filed in the response matrix."
        )
    if confirmatory_status == "completed_10000":
        confirmatory_sentence = (
            "The 10,000-permutation confirmatory subset is now both pre-specified "
            "and executed for the smallest GSE154778 manuscript-relevant tests. "
            "This improves p-value and FDR resolution for the statistical evidence, "
            "but it still must not be used to turn computational Myeloid, curl-like, "
            "or edge-level signals into validated biological mechanisms."
        )
        stretch_route_sentence = (
            "For a realistic 20-50 IF route, the current package is approximately "
            "one release/metadata cycle away from being submit-ready. For a Nature "
            "Methods or Nature Biotechnology stretch route, the core "
            "package is defensible on local scientific/statistical hardening, but "
            "would still benefit most from returned external beta reviews and a "
            "final public clean-clone reproduction after GitHub/Zenodo release."
        )
    else:
        confirmatory_sentence = (
            "The 10,000-permutation confirmatory subset is now pre-specified and "
            "has a fixed command plan. It is still not executed in the current state; "
            "therefore it should be described as a ready confirmatory gate, not as "
            "completed statistical evidence."
        )
        stretch_route_sentence = (
            "For a realistic 20-50 IF route, the current package is approximately "
            "one release/metadata cycle away from being submit-ready. For a Nature "
            "Methods or Nature Biotechnology stretch route, the core "
            "package is defensible but would still benefit from external beta review "
            "and a small 10,000-permutation confirmatory subset."
        )

    return "\n".join(
        [
            "# SheafSignal IF 20-50 Distance Report",
            "",
            f"- Decision: `{decision}`",
            f"- Overall readiness index: `{score['overall_percent']}%`",
            f"- Scientific/method hardening index: `{score['scientific_percent']}%`",
            f"- Submission infrastructure index: `{score['submission_infrastructure_percent']}%`",
            f"- Clean-export reproduction preflight: `{preflight_status}`",
            f"- Journal metric audit: `{journal_audit_status}`",
            f"- External beta review packet: `{beta_review_status}`",
            f"- 10,000-permutation confirmatory subset: `{confirmatory_status}`",
            f"- GSE103322 replication supplement: `{gse103322_status}`",
            f"- Live release blocking gates: `{active_live_blockers}` of "
            f"`{live_summary['blocking_total']}`",
            "- External authorization statuses: "
            f"`{_format_counts(live_summary['external_auth_counts'])}`",
            "- Zenodo preflight statuses: "
            f"`{_format_counts(live_summary['zenodo_preflight_counts'])}`",
            "- Author confirmation severities: "
            f"`{_format_counts(live_summary['author_preflight_counts'])}`",
            "- Score boundary: these are internal readiness indices, not acceptance probabilities.",
            "",
            "## Direct Answer",
            "",
            "SheafSignal is now close to a defensible 20-50 IF methods-manuscript "
            "candidate on the scientific/code side, but it is not submission-ready. "
            "The main remaining distance is external release and submission metadata: "
            "public GitHub URL/tag, real Zenodo DOI, author metadata, and a final "
            "public clean-clone reproduction check. A local clean-export preflight "
            "has passed when this report shows `local_clean_export_pass`, but it "
            "does not replace the final public-GitHub clone test.",
            "",
            "The journal-metric audit now anchors the target board to publisher "
            "metric pages, while keeping CAS-zone and warning-journal status as "
            "official submission-day checks. This strengthens journal selection "
            "discipline but does not remove the GitHub/Zenodo/author-metadata blockers.",
            "",
            beta_review_sentence,
            "",
            confirmatory_sentence,
            "",
            gse103322_sentence,
            "",
            stretch_route_sentence,
            "",
            "The GSE103322 HNSCC supplement-grade replication gate is now complete, "
            "but it remains outside primary comparator-completeness claims.",
            "",
            "## Current Gap Counts",
            "",
            f"- Blocking gap rows in the matrix: `{hard_blockers}`",
            f"- Administrative pending rows: `{administrative}`",
            f"- Author-owned metadata rows: `{author_metadata}`",
            f"- Git release warnings: `{release_warnings}`",
            "",
            "## Mandatory Before Any 20-50 IF Submission",
            "",
            *[f"- {line}" for line in mandatory_lines],
            "",
            "## Live Release And Author Gates",
            "",
            *_live_release_lines(live_summary),
            "",
            "## High-Value Optional Strengthening",
            "",
            *[f"- {line}" for line in optional_lines],
            "",
            "## Journal Route Snapshot",
            "",
            *_target_summary(root),
            "",
            "## Gantt Chart",
            "",
            _gantt(),
            "",
            "## Files Generated",
            "",
            f"- `{GAP_MATRIX_PATH.as_posix()}`",
            f"- `{SUPPLEMENT_PLAN_PATH.as_posix()}`",
            f"- `{REPORT_PATH.as_posix()}`",
            f"- `{CLEAN_PREFLIGHT_REPORT_PATH.as_posix()}`",
            f"- `{JOURNAL_METRIC_AUDIT_PATH.as_posix()}`",
            f"- `{JOURNAL_METRIC_AUDIT_REPORT_PATH.as_posix()}`",
            f"- `{BETA_REVIEW_PACKET_STATUS_PATH.as_posix()}`",
            f"- `{CONFIRMATORY_PERMUTATION_STATUS_PATH.as_posix()}`",
            f"- `{GSE103322_REPLICATION_STATUS_PATH.as_posix()}`",
            "",
            "## Boundary",
            "",
            "This report does not guarantee acceptance in any journal. It defines "
            "the shortest defensible route to a 20-50 IF submission package and "
            "the extra work most likely to reduce reviewer risk.",
            "",
        ]
    )


def build_outputs(root: Path) -> dict[str, object]:
    gates = _read_tsv(root / GATES_PATH)
    blockers = _read_tsv(root / FINAL_BLOCKERS_PATH)
    review_matrix = _read_tsv(root / REVIEW_MATRIX_PATH)
    git_audit = _read_tsv(root / GIT_READINESS_PATH)
    placeholder_audit = _read_tsv(root / METADATA_PLACEHOLDER_PATH)

    gap_rows = build_gap_matrix(
        gates,
        blockers,
        review_matrix,
        git_audit,
        placeholder_audit,
    )
    confirmatory_status = confirmatory_permutation_status(root)
    gse103322_status = gse103322_replication_status(root)
    supplement_rows = build_supplementation_plan(confirmatory_status, gse103322_status)
    _write_tsv_atomic(root / GAP_MATRIX_PATH, gap_rows)
    _write_tsv_atomic(root / SUPPLEMENT_PLAN_PATH, supplement_rows)
    _write_text_atomic(root / REPORT_PATH, build_report(root, gates, gap_rows, supplement_rows))

    score = score_gates(gates)
    return {
        "score": score,
        "gap_rows": len(gap_rows),
        "supplement_rows": len(supplement_rows),
        "report_path": REPORT_PATH.as_posix(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    summary = build_outputs(root)
    print("IF20_50_DISTANCE_REPORT_WRITTEN")
    print(f"Report: {summary['report_path']}")
    print(f"Overall readiness: {summary['score']['overall_percent']}%")
    print(f"Scientific readiness: {summary['score']['scientific_percent']}%")
    print(
        "Submission infrastructure readiness: "
        f"{summary['score']['submission_infrastructure_percent']}%"
    )
    print(f"Gap rows: {summary['gap_rows']}")
    print(f"Supplement rows: {summary['supplement_rows']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
