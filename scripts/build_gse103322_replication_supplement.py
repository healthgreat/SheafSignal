#!/usr/bin/env python
"""Build a GSE103322 replication-supplement readiness report.

Author: SheafSignal contributors
Date: 2026-05-02
Purpose: keep the HNSCC GSE103322 public dataset as an explicit replication
and generality check without overpromoting it into the main comparator or
biological-claim scope.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import pandas as pd


DATASET_ID = "gse103322_hnsc_scrna"
RESULT_ROOT = Path("benchmarks/results") / DATASET_ID
PROCESSED_ROOT = Path("data/processed") / DATASET_ID
OUTPUT_DIR = RESULT_ROOT / "replication"

PUBLIC_SUMMARY_PATH = Path("benchmarks/results/public_tme_sheafsignal_summary.csv")
METADATA_PATH = PROCESSED_ROOT / "metadata.csv"
ANNOTATION_SUMMARY_PATH = PROCESSED_ROOT / "annotation_summary.csv"
GLOBAL_PERMUTATION_PATH = RESULT_ROOT / "results/global_permutation_pvalues.csv"
NODE_PERMUTATION_PATH = RESULT_ROOT / "results/frustration_permutation_pvalues.csv"
EDGE_PATH = RESULT_ROOT / "results/sheaf_energy_by_edge.csv"
LR_ALIGNMENT_PATH = RESULT_ROOT / "comparators/sheafsignal_vs_lr_product_baseline.csv"
CELLCHAT_STATUS_PATH = RESULT_ROOT / "comparators/cellchat_run/cellchat_run_status.tsv"

SUMMARY_PATH = OUTPUT_DIR / "gse103322_replication_summary.tsv"
READINESS_PATH = OUTPUT_DIR / "gse103322_replication_readiness.tsv"
BOUNDARY_PATH = OUTPUT_DIR / "gse103322_claim_boundary.tsv"
COMMANDS_PATH = OUTPUT_DIR / "run_gse103322_replication_1000_commands.sh"
REPORT_PATH = OUTPUT_DIR / "GSE103322_REPLICATION_SUPPLEMENT_REPORT.md"


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


def _read_optional_csv(path: Path, sep: str = ",") -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, sep=sep)


def _first_numeric(table: pd.DataFrame, row_col: str, row_value: str, value_col: str) -> float | None:
    if table.empty or row_col not in table.columns or value_col not in table.columns:
        return None
    match = table.loc[table[row_col].astype(str) == row_value]
    if match.empty:
        return None
    value = pd.to_numeric(match.iloc[0][value_col], errors="coerce")
    if pd.isna(value):
        return None
    return float(value)


def _min_permutation_count(*tables: pd.DataFrame) -> int:
    counts = []
    for table in tables:
        if not table.empty and "n_permutations" in table.columns:
            values = pd.to_numeric(table["n_permutations"], errors="coerce").dropna()
            if not values.empty:
                counts.append(int(values.min()))
    return min(counts) if counts else 0


def _strata_status(*tables: pd.DataFrame) -> str:
    values = []
    for table in tables:
        if not table.empty and "permutation_strata_col" in table.columns:
            series = table["permutation_strata_col"].fillna("").astype(str)
            values.extend(item for item in series.tolist() if item)
    if not values:
        return "missing_or_unstratified"
    if set(values) == {"sample_id"}:
        return "sample_id_stratified"
    return ";".join(sorted(set(values)))


def _cellchat_status(root: Path) -> str:
    path = root / CELLCHAT_STATUS_PATH
    if not path.exists():
        return "not_run"
    status = _read_optional_csv(path, sep="\t")
    if status.empty:
        return "status_file_empty"
    if {"status", "missing_dependency"}.issubset(status.columns):
        return "missing_dependency"
    if "status" in status.columns:
        return ";".join(status["status"].astype(str).tolist())
    return "status_unknown"


def _lr_spearman(alignment: pd.DataFrame) -> float | None:
    required = {"sheaf_energy", "comparator_edge_score"}
    if alignment.empty or not required.issubset(alignment.columns):
        return None
    corr = alignment["sheaf_energy"].corr(alignment["comparator_edge_score"], method="spearman")
    if pd.isna(corr):
        return None
    return float(corr)


def build_summary(root: Path) -> list[dict[str, object]]:
    public = _read_optional_csv(root / PUBLIC_SUMMARY_PATH)
    metadata = _read_optional_csv(root / METADATA_PATH)
    annotation = _read_optional_csv(root / ANNOTATION_SUMMARY_PATH)
    global_perm = _read_optional_csv(root / GLOBAL_PERMUTATION_PATH)
    node_perm = _read_optional_csv(root / NODE_PERMUTATION_PATH)
    edges = _read_optional_csv(root / EDGE_PATH)
    lr_alignment = _read_optional_csv(root / LR_ALIGNMENT_PATH)

    public_row = public.loc[public.get("dataset_id", pd.Series(dtype=str)).astype(str) == DATASET_ID]
    if public_row.empty:
        public_values: dict[str, object] = {}
    else:
        public_values = public_row.iloc[0].to_dict()

    if not node_perm.empty:
        top_node = node_perm.sort_values("observed_frustration_score", ascending=False).iloc[0]
        top_node_type = str(top_node["cell_type"])
        top_node_score = float(top_node["observed_frustration_score"])
        top_node_fdr = float(top_node["frustration_fdr"])
    else:
        top_node_type = ""
        top_node_score = pd.NA
        top_node_fdr = pd.NA

    rows = [
        {
            "dataset_id": DATASET_ID,
            "benchmark_status": public_values.get("status", "missing_public_summary"),
            "n_cells": int(len(metadata)) if not metadata.empty else 0,
            "n_samples": int(metadata["sample_id"].nunique()) if "sample_id" in metadata.columns else 0,
            "n_patients": int(metadata["patient_id"].nunique()) if "patient_id" in metadata.columns else 0,
            "n_cell_types": int(metadata["cell_type"].nunique()) if "cell_type" in metadata.columns else 0,
            "lesion_types": ";".join(sorted(metadata["lesion_type"].dropna().astype(str).unique()))
            if "lesion_type" in metadata.columns
            else "",
            "annotation_rows": int(len(annotation)),
            "n_edges": int(len(edges)) if not edges.empty else int(public_values.get("n_edges", 0) or 0),
            "top_frustration_cell_type_public_summary": public_values.get(
                "top_frustration_cell_type", ""
            ),
            "top_frustration_score_public_summary": public_values.get(
                "top_frustration_score", pd.NA
            ),
            "top_node_frustration_cell_type": top_node_type,
            "top_node_frustration_score": top_node_score,
            "top_node_frustration_fdr": top_node_fdr,
            "global_curl_ratio": _first_numeric(global_perm, "metric", "curl_ratio", "observed"),
            "global_curl_fdr": _first_numeric(global_perm, "metric", "curl_ratio", "fdr"),
            "min_n_permutations": _min_permutation_count(global_perm, node_perm),
            "permutation_strata_status": _strata_status(global_perm, node_perm),
            "lr_product_spearman": _lr_spearman(lr_alignment),
            "cellchat_status": _cellchat_status(root),
        }
    ]
    return rows


def classify_decision(summary: dict[str, object]) -> str:
    if summary.get("benchmark_status") != "completed":
        return "GSE103322_REPLICATION_BLOCKED_NO_COMPLETED_BENCHMARK"
    if int(summary.get("n_cells", 0) or 0) == 0:
        return "GSE103322_REPLICATION_BLOCKED_NO_METADATA"
    min_perm = int(summary.get("min_n_permutations", 0) or 0)
    strata = str(summary.get("permutation_strata_status", ""))
    if min_perm >= 1000 and strata == "sample_id_stratified":
        return "GSE103322_REPLICATION_SUPPLEMENT_READY"
    return "GSE103322_REPLICATION_EXPLORATORY_READY_RERUN_RECOMMENDED"


def build_readiness_rows(summary: dict[str, object], decision: str) -> list[dict[str, object]]:
    min_perm = int(summary.get("min_n_permutations", 0) or 0)
    strata = str(summary.get("permutation_strata_status", ""))
    return [
        {
            "check_id": "benchmark_completed",
            "status": "pass" if summary.get("benchmark_status") == "completed" else "fail",
            "evidence": summary.get("benchmark_status", ""),
            "required_action": "Run SheafSignal benchmark before using GSE103322 as replication.",
        },
        {
            "check_id": "metadata_support",
            "status": "pass" if int(summary.get("n_cells", 0) or 0) > 0 else "fail",
            "evidence": (
                f"n_cells={summary.get('n_cells')}; n_samples={summary.get('n_samples')}; "
                f"n_patients={summary.get('n_patients')}"
            ),
            "required_action": "Keep author-derived annotation and sample support visible.",
        },
        {
            "check_id": "permutation_grade",
            "status": "pass" if min_perm >= 1000 and strata == "sample_id_stratified" else "warn",
            "evidence": f"min_n_permutations={min_perm}; strata={strata}",
            "required_action": (
                "Rerun with 1000 sample-stratified permutations before treating GSE103322 "
                "as supplement-grade statistical replication."
            ),
        },
        {
            "check_id": "comparator_boundary",
            "status": "pass_with_boundary",
            "evidence": (
                f"LRProductBaseline Spearman={summary.get('lr_product_spearman')}; "
                f"CellChat status={summary.get('cellchat_status')}"
            ),
            "required_action": (
                "Keep GSE103322 outside primary comparator-completeness claims unless full "
                "CellChat/CellPhoneDB/LIANA/NicheNet imports are completed."
            ),
        },
        {
            "check_id": "decision",
            "status": "pass_with_boundary" if "EXPLORATORY_READY" in decision else "pass",
            "evidence": decision,
            "required_action": "Use current GSE103322 only as exploratory generality check until rerun.",
        },
    ]


def build_boundary_rows() -> list[dict[str, str]]:
    return [
        {
            "claim_area": "allowed",
            "wording": (
                "GSE103322 provides an independent HNSCC public-data workflow replication "
                "showing SheafSignal can run on another TME cohort."
            ),
            "condition": "Allowed with current exploratory boundary.",
        },
        {
            "claim_area": "allowed_after_rerun",
            "wording": (
                "After 1000 sample-stratified permutations, GSE103322 may be used as a "
                "supplement-grade statistical replication if the gate passes."
            ),
            "condition": "Requires min_n_permutations >= 1000 and sample_id strata.",
        },
        {
            "claim_area": "forbidden",
            "wording": (
                "Do not claim Endothelial, Myeloid, or any HNSCC cell type is a validated "
                "frustration driver from current GSE103322 outputs."
            ),
            "condition": "Current node FDR and comparator scope do not support mechanism claims.",
        },
        {
            "claim_area": "forbidden",
            "wording": (
                "Do not include GSE103322 in primary comparator-completeness claims while "
                "CellChat/CellPhoneDB/LIANA/NicheNet scope remains incomplete or exploratory."
            ),
            "condition": "Primary comparator scope remains GSE72056/GSE154778/GSE176078.",
        },
    ]


def build_commands() -> str:
    return "\n".join(
        [
            "#!/usr/bin/env bash",
            "set -euo pipefail",
            "",
            "# Long-running supplement-grade rerun. Use tmux/nohup in WSL and disable Windows sleep.",
            "python scripts/run_tme_benchmark.py \\",
            "  --dataset-id gse103322_hnsc_scrna \\",
            "  --results-dir benchmarks/results/gse103322_replication_1000 \\",
            "  --n-permutations 1000",
            "",
            "python scripts/build_pooled_fdr_audit.py \\",
            "  --results-root benchmarks/results/gse103322_replication_1000 \\",
            "  --output-dir benchmarks/results/gse103322_replication_1000/pooled_fdr",
            "",
            "python scripts/build_gse103322_replication_supplement.py",
            "",
        ]
    )


def build_report(summary: dict[str, object], decision: str) -> str:
    return "\n".join(
        [
            "# GSE103322 Replication Supplement Report",
            "",
            f"- Decision: `{decision}`",
            f"- Dataset: `{DATASET_ID}`",
            f"- Cells / samples / patients: `{summary.get('n_cells')}` / "
            f"`{summary.get('n_samples')}` / `{summary.get('n_patients')}`",
            f"- Cell types: `{summary.get('n_cell_types')}`",
            f"- Lesion types: `{summary.get('lesion_types')}`",
            f"- Current top node frustration cell type: `{summary.get('top_node_frustration_cell_type')}`",
            f"- Current top node frustration FDR: `{summary.get('top_node_frustration_fdr')}`",
            f"- Global curl ratio / FDR: `{summary.get('global_curl_ratio')}` / "
            f"`{summary.get('global_curl_fdr')}`",
            f"- Current permutation grade: n=`{summary.get('min_n_permutations')}`, "
            f"strata=`{summary.get('permutation_strata_status')}`",
            f"- LRProductBaseline Spearman: `{summary.get('lr_product_spearman')}`",
            f"- CellChat status: `{summary.get('cellchat_status')}`",
            "",
            "## Interpretation",
            "",
            "GSE103322 is useful as an independent HNSCC public-data workflow replication, "
            "but the current outputs are exploratory. The existing permutation tables use "
            "100 permutations and are not sample-stratified, even though metadata contains "
            "sample and patient identifiers. Therefore GSE103322 should not be used for "
            "main-text biological source claims or primary comparator-completeness claims.",
            "",
            "## Required Upgrade For Supplement-Grade Replication",
            "",
            f"Run `{COMMANDS_PATH.as_posix()}` to regenerate a 1000-permutation, "
            "sample-stratified GSE103322 supplement candidate. Keep the primary comparator "
            "claim restricted to GSE72056/GSE154778/GSE176078 unless full external comparator "
            "imports are completed for GSE103322.",
            "",
        ]
    )


def build_outputs(root: Path) -> dict[str, object]:
    root = root.resolve()
    summary_rows = build_summary(root)
    summary = summary_rows[0]
    decision = classify_decision(summary)
    _write_tsv_atomic(root / SUMMARY_PATH, summary_rows)
    _write_tsv_atomic(root / READINESS_PATH, build_readiness_rows(summary, decision))
    _write_tsv_atomic(root / BOUNDARY_PATH, build_boundary_rows())
    _write_text_atomic(root / COMMANDS_PATH, build_commands())
    _write_text_atomic(root / REPORT_PATH, build_report(summary, decision))
    return {
        "decision": decision,
        "n_cells": summary.get("n_cells", 0),
        "n_samples": summary.get("n_samples", 0),
        "report_path": REPORT_PATH.as_posix(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args(argv)

    summary = build_outputs(Path(args.root))
    print(summary["decision"])
    print(f"Cells: {summary['n_cells']}")
    print(f"Samples: {summary['n_samples']}")
    print(f"Report: {summary['report_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
