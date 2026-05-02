#!/usr/bin/env python
"""Build a reviewer-facing beta-review packet for SheafSignal.

Author: SheafSignal contributors
Date: 2026-05-02
Purpose: make external AI or human beta review reproducible by giving every
reviewer the same evidence index, checklist, and response form.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path


OUTPUT_DIR = Path("external_ai_review_packet/beta_review_packet_2026-05-02")
README_PATH = OUTPUT_DIR / "00_README_FOR_REVIEWERS.md"
SUMMARY_PATH = OUTPUT_DIR / "01_BETA_REVIEW_PACKET_STATUS.md"
EVIDENCE_INDEX_PATH = OUTPUT_DIR / "02_EVIDENCE_FILE_INDEX.tsv"
CHECKLIST_PATH = OUTPUT_DIR / "03_REVIEWER_CHECKLIST.tsv"
AI_PROMPT_PATH = OUTPUT_DIR / "04_AI_REVIEW_PROMPT.md"
REVIEW_FORM_PATH = OUTPUT_DIR / "05_REVIEW_FORM_TEMPLATE.md"
MANIFEST_PATH = OUTPUT_DIR / "06_PACKET_MANIFEST.tsv"


EVIDENCE_ITEMS = [
    {
        "category": "orientation",
        "label": "Current dashboard",
        "path": "manuscript/SHEAFSIGNAL_STATUS_DASHBOARD_2026-05-02.md",
        "why": "One-page status, allowed claims, blockers, and current Gantt.",
        "required": "yes",
    },
    {
        "category": "journal_route",
        "label": "IF 20-50 distance report",
        "path": "manuscript/IF20_50_DISTANCE_REPORT.md",
        "why": "Current readiness indices, hard blockers, and optional strengthening.",
        "required": "yes",
    },
    {
        "category": "journal_route",
        "label": "Journal metric audit",
        "path": "manuscript/journal_metric_audit/JOURNAL_METRIC_AUDIT_REPORT.md",
        "why": "Publisher JIF evidence and CAS/warning-list boundary.",
        "required": "yes",
    },
    {
        "category": "review_history",
        "label": "Round 1 response matrix",
        "path": "external_ai_review_packet/round1_review_response_matrix.tsv",
        "why": "Fatal/major reviewer concerns and current fix/downgrade status.",
        "required": "yes",
    },
    {
        "category": "review_history",
        "label": "Round 2 hardening status",
        "path": "external_ai_review_packet/ROUND2_HARDENING_STATUS_2026-05-02.md",
        "why": "Compact summary of the formal sheaf, reannotation, statistics, and claim hardening.",
        "required": "yes",
    },
    {
        "category": "gates",
        "label": "Status gates",
        "path": "manuscript/SHEAFSIGNAL_STATUS_GATES_2026-05-02.tsv",
        "why": "Machine-readable green/yellow/red gate table.",
        "required": "yes",
    },
    {
        "category": "gates",
        "label": "Final submission blockers",
        "path": "manuscript/FINAL_SUBMISSION_BLOCKERS.tsv",
        "why": "Remaining submission blockers and owner boundaries.",
        "required": "yes",
    },
    {
        "category": "methods",
        "label": "Method reporting audit",
        "path": "manuscript/method_reporting/METHOD_REPORTING_REPORT.md",
        "why": "Algorithm, data, comparator, reference, and release reporting readiness.",
        "required": "yes",
    },
    {
        "category": "methods",
        "label": "Novelty overlap report",
        "path": "manuscript/novelty_overlap/SHEAFSIGNAL_NOVELTY_OVERLAP_REPORT.md",
        "why": "Formal overlap boundary against CCC, GSP, Hodge, and sheaf-literature categories.",
        "required": "yes",
    },
    {
        "category": "statistics",
        "label": "Benchmark result contract report",
        "path": "benchmarks/results/BENCHMARK_RESULT_CONTRACT_REPORT.md",
        "why": "Checks simulation, public benchmark summaries, comparator links, and claim gates.",
        "required": "yes",
    },
    {
        "category": "statistics",
        "label": "Simulation recovery table",
        "path": "benchmarks/results/simulation/sheaf_ground_truth_recovery.csv",
        "why": "Ground-truth recovery comparison against LR, pathway, Hodge, centrality, and smoothness baselines.",
        "required": "yes",
    },
    {
        "category": "single_cell",
        "label": "GSE154778 reannotation readiness",
        "path": "benchmarks/results/gse154778_pdac_scrna/reannotation/GSE154778_REANNOTATION_READINESS_REPORT.md",
        "why": "Full Scanpy annotation readiness and coverage boundaries.",
        "required": "yes",
    },
    {
        "category": "single_cell",
        "label": "Comparator scope report",
        "path": "manuscript/comparator_scope/COMPARATOR_SCOPE_REPORT.md",
        "why": "Defines exactly which comparator claims are allowed.",
        "required": "yes",
    },
    {
        "category": "spatial",
        "label": "Visium scope report",
        "path": "manuscript/visium_scope/VISIUM_SCOPE_REPORT.md",
        "why": "Prevents spot-level spatial output from being overinterpreted as cell-type source biology.",
        "required": "yes",
    },
    {
        "category": "claims",
        "label": "Claim safety audit",
        "path": "manuscript/CLAIM_SAFETY_AUDIT_REPORT.md",
        "why": "Manuscript-wide overclaim scan.",
        "required": "yes",
    },
    {
        "category": "figures",
        "label": "Main figure quality audit",
        "path": "manuscript/figure_quality/MAIN_FIGURE_QUALITY_REPORT.md",
        "why": "Checks renderability and evidence-source boundaries for main figures.",
        "required": "yes",
    },
    {
        "category": "reproducibility",
        "label": "Environment lock report",
        "path": "envs/ENVIRONMENT_LOCK_REPORT.md",
        "why": "Pinned Python environment readiness.",
        "required": "yes",
    },
    {
        "category": "reproducibility",
        "label": "Local clean-export preflight",
        "path": "release/clean_clone_preflight/CLEAN_CLONE_PREFLIGHT_REPORT.md",
        "why": "Local clean-export reproduction evidence before public clone.",
        "required": "yes",
    },
    {
        "category": "reproducibility",
        "label": "Git release readiness",
        "path": "release/GIT_RELEASE_READINESS_REPORT.md",
        "why": "Public GitHub remote/tag boundary.",
        "required": "yes",
    },
    {
        "category": "reproducibility",
        "label": "Release metadata placeholder report",
        "path": "release/RELEASE_METADATA_PLACEHOLDER_REPORT.md",
        "why": "Zenodo DOI, GitHub URL, and author metadata placeholders.",
        "required": "yes",
    },
    {
        "category": "manuscript",
        "label": "SCI manuscript v2",
        "path": "manuscript/SCI_MANUSCRIPT_V2_POLISHED.md",
        "why": "Current manuscript text to be reviewed for novelty, claims, and journal fit.",
        "required": "yes",
    },
    {
        "category": "manuscript",
        "label": "Supplementary information draft",
        "path": "manuscript/nature_methods_package/10_supplementary_information_draft.md",
        "why": "Supplementary method, dataset, and QC framing.",
        "required": "yes",
    },
]


CHECKLIST_ROWS = [
    {
        "review_area": "Methods",
        "priority": "fatal_if_failed",
        "question": "Does the implemented rank-one cellular sheaf object justify the manuscript's sheaf-valued method framing?",
        "evidence": "src/sheafsignal/sheaf.py; manuscript/novelty_overlap/SHEAFSIGNAL_NOVELTY_OVERLAP_REPORT.md",
        "expected_reviewer_output": "State whether the mathematical object is sufficiently distinct or should be downgraded.",
    },
    {
        "review_area": "Methods",
        "priority": "fatal_if_failed",
        "question": "Is Hodge decomposition correctly applied to sheaf_residual for the primary frustration result?",
        "evidence": "manuscript/SHEAFSIGNAL_STATUS_GATES_2026-05-02.tsv; benchmarks/results/BENCHMARK_RESULT_CONTRACT_REPORT.md",
        "expected_reviewer_output": "Identify any mismatch between algorithm implementation and manuscript claims.",
    },
    {
        "review_area": "Simulation",
        "priority": "major",
        "question": "Does the simulation benchmark prove added information beyond LR score, pathway gradient, Hodge-only, centrality, and graph-smoothness baselines?",
        "evidence": "benchmarks/results/simulation/sheaf_ground_truth_recovery.csv",
        "expected_reviewer_output": "List missing baselines or power/sensitivity analyses needed for 20-50 IF.",
    },
    {
        "review_area": "SingleCell",
        "priority": "fatal_if_failed",
        "question": "Is GSE154778 annotation validation sufficient after scanpy_full_v1, and is the Myeloid claim correctly downgraded?",
        "evidence": "benchmarks/results/gse154778_pdac_scrna/reannotation/GSE154778_REANNOTATION_READINESS_REPORT.md; manuscript/CLAIM_SAFETY_AUDIT_REPORT.md",
        "expected_reviewer_output": "Decide whether Myeloid can remain supplement-only or must be removed.",
    },
    {
        "review_area": "Statistics",
        "priority": "fatal_if_failed",
        "question": "Are sample-stratified permutations, pooled FDR, and bootstrap/stability outputs enough for descriptive computational claims?",
        "evidence": "manuscript/SHEAFSIGNAL_STATUS_GATES_2026-05-02.tsv; benchmarks/results/BENCHMARK_RESULT_CONTRACT_REPORT.md",
        "expected_reviewer_output": "Specify whether a 10,000-permutation subset is mandatory before submission.",
    },
    {
        "review_area": "Comparators",
        "priority": "fatal_if_failed",
        "question": "Is the completed primary scRNA comparator scope enough, and are unsupported broad-superiority claims absent?",
        "evidence": "manuscript/comparator_scope/COMPARATOR_SCOPE_REPORT.md; manuscript/CLAIM_SAFETY_AUDIT_REPORT.md",
        "expected_reviewer_output": "List any comparator tool still required for the stated claims.",
    },
    {
        "review_area": "Spatial",
        "priority": "major",
        "question": "Is the Visium section safely limited to hotspot demonstration without cell-type source claims?",
        "evidence": "manuscript/visium_scope/VISIUM_SCOPE_REPORT.md",
        "expected_reviewer_output": "Flag any sentence that implies histology/deconvolution-backed cell types.",
    },
    {
        "review_area": "Reproducibility",
        "priority": "fatal_if_failed",
        "question": "Would a reviewer be able to reproduce the core demo from a clean public clone after GitHub/Zenodo are inserted?",
        "evidence": "envs/ENVIRONMENT_LOCK_REPORT.md; release/clean_clone_preflight/CLEAN_CLONE_PREFLIGHT_REPORT.md; release/GIT_RELEASE_READINESS_REPORT.md",
        "expected_reviewer_output": "Identify remaining clean-clone risks.",
    },
    {
        "review_area": "Submission",
        "priority": "fatal_if_failed",
        "question": "Are GitHub URL, Zenodo DOI, author metadata, and submission-day checks correctly treated as blockers?",
        "evidence": "manuscript/FINAL_SUBMISSION_BLOCKERS.tsv; release/RELEASE_METADATA_PLACEHOLDER_REPORT.md",
        "expected_reviewer_output": "Confirm no final release should occur before these are real.",
    },
    {
        "review_area": "JournalFit",
        "priority": "major",
        "question": "Given the current evidence, is Nature Methods still the best first route, or should the package be aimed at another 20-50 IF journal?",
        "evidence": "manuscript/IF20_50_DISTANCE_REPORT.md; manuscript/journal_metric_audit/JOURNAL_METRIC_AUDIT_REPORT.md",
        "expected_reviewer_output": "Rank Nature Methods, Nature Biotechnology, Molecular Cancer, Nature Cancer, and fallback options.",
    },
]


GENERATED_FILES = [
    README_PATH,
    SUMMARY_PATH,
    EVIDENCE_INDEX_PATH,
    CHECKLIST_PATH,
    AI_PROMPT_PATH,
    REVIEW_FORM_PATH,
]


def _write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def _write_tsv_atomic(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    fieldnames = list(rows[0].keys()) if rows else ["item"]
    with tmp_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    tmp_path.replace(path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _extract_decision(root: Path, rel_path: str) -> str:
    path = root / rel_path
    if not path.exists():
        return "missing"
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "Decision:" in line:
            clean = line.strip().lstrip("- ").strip()
            if "`" in clean:
                parts = clean.split("`")
                if len(parts) >= 3:
                    return parts[1]
            return clean.replace("Decision:", "").strip()
    return "decision_not_found"


def build_evidence_index(root: Path) -> list[dict[str, object]]:
    rows = []
    for item in EVIDENCE_ITEMS:
        path = root / item["path"]
        exists = path.exists()
        rows.append(
            {
                **item,
                "exists": "yes" if exists else "no",
                "size_bytes": path.stat().st_size if exists else 0,
                "sha256": _sha256(path) if exists and path.is_file() else "NA",
            }
        )
    return rows


def classify_packet(evidence_rows: list[dict[str, object]]) -> str:
    missing_required = [
        row
        for row in evidence_rows
        if row.get("required") == "yes" and row.get("exists") != "yes"
    ]
    if missing_required:
        return "BETA_REVIEW_PACKET_BLOCKED_MISSING_REQUIRED_EVIDENCE"
    return "BETA_REVIEW_PACKET_READY_LOCAL_EXTERNAL_REVIEWS_PENDING"


def build_readme() -> str:
    return "\n".join(
        [
            "# SheafSignal External Beta Review Packet",
            "",
            "This packet is designed for critical external review before any 20-50 IF submission.",
            "It does not claim the manuscript is submission-ready. Reviewers should focus on fatal",
            "and near-fatal risks that would cause desk rejection or major rejection.",
            "",
            "## How To Review",
            "",
            "1. Start with `01_BETA_REVIEW_PACKET_STATUS.md`.",
            "2. Use `02_EVIDENCE_FILE_INDEX.tsv` to locate source files.",
            "3. Answer every row in `03_REVIEWER_CHECKLIST.tsv`.",
            "4. If using another AI system, paste `04_AI_REVIEW_PROMPT.md` and attach or quote the listed evidence files.",
            "5. Return comments using `05_REVIEW_FORM_TEMPLATE.md`.",
            "",
            "## Boundary",
            "",
            "The packet is a local review aid. It does not replace public GitHub release, Zenodo DOI,",
            "author metadata finalization, or final public clean-clone reproduction.",
            "",
        ]
    )


def build_summary(root: Path, decision: str, evidence_rows: list[dict[str, object]]) -> str:
    missing = [row for row in evidence_rows if row["exists"] != "yes"]
    return "\n".join(
        [
            "# Beta Review Packet Status",
            "",
            f"- Decision: `{decision}`",
            "- Review status: `packet_ready_but_no_external_reviews_returned`",
            f"- Evidence files indexed: `{len(evidence_rows)}`",
            f"- Missing indexed evidence files: `{len(missing)}`",
            f"- IF distance decision: `{_extract_decision(root, 'manuscript/IF20_50_DISTANCE_REPORT.md')}`",
            f"- Git release decision: `{_extract_decision(root, 'release/GIT_RELEASE_READINESS_REPORT.md')}`",
            f"- Zenodo/release placeholder decision: `{_extract_decision(root, 'release/RELEASE_METADATA_PLACEHOLDER_REPORT.md')}`",
            "",
            "## Direct Review Request",
            "",
            "Reviewers should judge whether SheafSignal is defensible as a 20-50 IF methods manuscript",
            "candidate after the stated claim downgrades. They should not judge it as a final submission",
            "until GitHub, Zenodo DOI, author metadata, and public clean-clone reproduction are complete.",
            "",
            "## Key Questions",
            "",
            "- Is the formal sheaf/Hodge construction genuinely implemented and described without overclaiming?",
            "- Are GSE154778, Visium, and comparator claims correctly bounded?",
            "- Are the statistics sufficient for descriptive computational claims?",
            "- What must be fixed before Nature Methods presubmission versus before a safer 20-50 IF submission?",
            "",
        ]
    )


def build_ai_prompt() -> str:
    checklist = "\n".join(
        f"- [{row['review_area']}] {row['question']} Evidence: {row['evidence']}"
        for row in CHECKLIST_ROWS
    )
    return "\n".join(
        [
            "# Copy-Paste Prompt For External AI Review",
            "",
            "You are acting as a critical methods-journal reviewer for the SheafSignal manuscript package.",
            "Do not be polite for its own sake. Identify fatal and near-fatal weaknesses first.",
            "Use only the evidence files provided by the authors, and clearly separate direct evidence,",
            "reasonable inference, and speculation.",
            "",
            "The current target is a 20-50 IF methods manuscript route, with Nature Methods as a stretch/primary",
            "methods fit and safer fallback routes if the evidence does not support that level.",
            "",
            "Please answer these checklist items:",
            "",
            checklist,
            "",
            "Return your review in this structure:",
            "",
            "1. Editorial decision: accept / minor / major / reject / not ready.",
            "2. Top 5 fatal or near-fatal concerns.",
            "3. Required fixes before any 20-50 IF submission.",
            "4. Claims that must be downgraded or removed.",
            "5. Best-fit journals and why.",
            "6. Short final verdict on distance to submission readiness.",
            "",
        ]
    )


def build_review_form() -> str:
    return "\n".join(
        [
            "# External Beta Review Form",
            "",
            "- Reviewer name or model:",
            "- Date:",
            "- Evidence files reviewed:",
            "- Overall decision: `not_ready` / `major_revision` / `presubmission_candidate` / `submission_candidate`",
            "",
            "## Fatal Concerns",
            "",
            "| Concern | Evidence file | Required fix | Blocks 20-50 IF? |",
            "|---|---|---|---|",
            "|  |  |  |  |",
            "",
            "## Major Concerns",
            "",
            "| Concern | Evidence file | Required fix | Priority |",
            "|---|---|---|---|",
            "|  |  |  |  |",
            "",
            "## Claim Downgrades",
            "",
            "| Current claim | Recommended wording | Reason |",
            "|---|---|---|",
            "|  |  |  |",
            "",
            "## Journal Fit",
            "",
            "| Journal | Fit score 1-5 | Main risk | Recommendation |",
            "|---|---:|---|---|",
            "| Nature Methods |  |  |  |",
            "| Nature Biotechnology |  |  |  |",
            "| Molecular Cancer |  |  |  |",
            "| Nature Cancer |  |  |  |",
            "| Other |  |  |  |",
            "",
        ]
    )


def build_manifest(root: Path) -> list[dict[str, object]]:
    rows = []
    for rel_path in GENERATED_FILES:
        path = root / rel_path
        exists = path.exists()
        rows.append(
            {
                "file": rel_path.as_posix(),
                "exists": "yes" if exists else "no",
                "size_bytes": path.stat().st_size if exists else 0,
                "sha256": _sha256(path) if exists and path.is_file() else "NA",
            }
        )
    return rows


def build_outputs(root: Path) -> dict[str, object]:
    root = root.resolve()
    evidence_rows = build_evidence_index(root)
    decision = classify_packet(evidence_rows)

    _write_text_atomic(root / README_PATH, build_readme())
    _write_text_atomic(root / SUMMARY_PATH, build_summary(root, decision, evidence_rows))
    _write_tsv_atomic(root / EVIDENCE_INDEX_PATH, evidence_rows)
    _write_tsv_atomic(root / CHECKLIST_PATH, CHECKLIST_ROWS)
    _write_text_atomic(root / AI_PROMPT_PATH, build_ai_prompt())
    _write_text_atomic(root / REVIEW_FORM_PATH, build_review_form())
    _write_tsv_atomic(root / MANIFEST_PATH, build_manifest(root))

    return {
        "decision": decision,
        "evidence_files": len(evidence_rows),
        "missing_required": sum(
            1
            for row in evidence_rows
            if row.get("required") == "yes" and row.get("exists") != "yes"
        ),
        "output_dir": OUTPUT_DIR.as_posix(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args(argv)

    summary = build_outputs(Path(args.root))
    print(summary["decision"])
    print(f"Evidence files: {summary['evidence_files']}")
    print(f"Missing required: {summary['missing_required']}")
    print(f"Output: {summary['output_dir']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
