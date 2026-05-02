#!/usr/bin/env python
"""Build the 10,000-permutation confirmatory subset gate for SheafSignal.

Author: SheafSignal contributors
Date: 2026-05-02
Purpose: pre-specify the smallest manuscript-relevant permutation subset that
needs a 10,000-permutation rerun before high-confidence 20-50 IF submission.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import pandas as pd


ROUND2_POOLED_FDR = Path("benchmarks/results/round2_hardening/pooled_fdr/pooled_fdr_audit.csv")
OUTPUT_DIR = Path("benchmarks/results/confirmatory_10000")
SUBSET_PATH = OUTPUT_DIR / "confirmatory_permutation_subset.tsv"
READINESS_PATH = OUTPUT_DIR / "confirmatory_permutation_readiness.tsv"
COMMANDS_PATH = OUTPUT_DIR / "run_confirmatory_10000_commands.sh"
REPORT_PATH = OUTPUT_DIR / "CONFIRMATORY_PERMUTATION_STATUS.md"

TARGET_N_PERMUTATIONS = 10000
CONFIRMATORY_DATASET = "gse154778_pdac_scrna"
CONFIRMATORY_RESULT_ROOT = OUTPUT_DIR / CONFIRMATORY_DATASET / "results"

TARGET_TESTS = [
    {
        "priority": 1,
        "family": "global_metrics",
        "label": "curl_ratio",
        "claim_role": "real_data_global_component_diagnostic",
        "interpretation_boundary": (
            "Report only as fitted graph decomposition diagnostic; do not call it validated tumor feedback."
        ),
    },
    {
        "priority": 2,
        "family": "node_frustration",
        "label": "Myeloid",
        "claim_role": "gse154778_myeloid_supplement_hypothesis",
        "interpretation_boundary": (
            "May remain supplement-level computational hypothesis only; do not promote to main biological driver."
        ),
    },
    {
        "priority": 3,
        "family": "edge_sheaf_energy",
        "label": "Myeloid->Tumor/Epithelial",
        "claim_role": "edge_level_descriptive_example",
        "interpretation_boundary": (
            "Use only as edge-level descriptive example if confirmatory FDR remains stable."
        ),
    },
    {
        "priority": 4,
        "family": "edge_curl",
        "label": "Myeloid->CAF/Fibroblast",
        "claim_role": "edge_curl_diagnostic_example",
        "interpretation_boundary": (
            "Use only as curl-like diagnostic example; not as a validated feedback mechanism."
        ),
    },
]

PERMUTATION_TABLES = {
    "edge_sheaf_energy": ("sheaf_energy_permutation_pvalues.csv", "sheaf_energy_empirical_p"),
    "edge_curl": ("sheaf_energy_permutation_pvalues.csv", "curl_empirical_p"),
    "node_frustration": ("frustration_permutation_pvalues.csv", "frustration_empirical_p"),
    "global_metrics": ("global_permutation_pvalues.csv", "empirical_p"),
}


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


def _read_optional_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _source_n_permutations(root: Path, source_table: str, family: str, label: str) -> int:
    path = root / source_table
    table = _read_optional_csv(path)
    if table.empty or "n_permutations" not in table.columns:
        return 0
    if family in {"edge_sheaf_energy", "edge_curl"} and "edge_id" in table.columns:
        table = table.loc[table["edge_id"].astype(str) == label]
    elif family == "node_frustration" and "cell_type" in table.columns:
        table = table.loc[table["cell_type"].astype(str) == label]
    elif family == "global_metrics" and "metric" in table.columns:
        table = table.loc[table["metric"].astype(str) == label]
    if table.empty:
        return 0
    return int(pd.to_numeric(table["n_permutations"], errors="coerce").max())


def _confirmatory_lookup(root: Path) -> dict[tuple[str, str], dict[str, object]]:
    rows: dict[tuple[str, str], dict[str, object]] = {}
    for family, (filename, p_col) in PERMUTATION_TABLES.items():
        table = _read_optional_csv(root / CONFIRMATORY_RESULT_ROOT / filename)
        if table.empty or p_col not in table.columns:
            continue
        for _, row in table.iterrows():
            label = str(row.get("edge_id") or row.get("cell_type") or row.get("metric"))
            n_perm = int(pd.to_numeric(row.get("n_permutations", 0), errors="coerce") or 0)
            fdr_col = {
                "edge_sheaf_energy": "sheaf_energy_fdr",
                "edge_curl": "curl_fdr",
                "node_frustration": "frustration_fdr",
                "global_metrics": "fdr",
            }[family]
            rows[(family, label)] = {
                "confirmatory_p_value": row[p_col],
                "confirmatory_fdr": row.get(fdr_col, pd.NA),
                "confirmatory_n_permutations": n_perm,
            }
    return rows


def build_subset(root: Path) -> list[dict[str, object]]:
    pooled = _read_optional_csv(root / ROUND2_POOLED_FDR)
    confirmatory = _confirmatory_lookup(root)
    rows = []
    for target in TARGET_TESTS:
        family = target["family"]
        label = target["label"]
        match = pooled.loc[
            (pooled["dataset_id"].astype(str) == CONFIRMATORY_DATASET)
            & (pooled["family"].astype(str) == family)
            & (pooled["label"].astype(str) == label)
        ]
        if match.empty:
            current = {
                "p_value": pd.NA,
                "pooled_fdr_within_family": pd.NA,
                "pooled_fdr_all_tests": pd.NA,
                "source_table": "",
            }
        else:
            current = match.iloc[0].to_dict()
        current_n = _source_n_permutations(
            root,
            str(current.get("source_table", "")),
            family,
            label,
        )
        confirmed = confirmatory.get((family, label), {})
        confirmatory_n = int(confirmed.get("confirmatory_n_permutations", 0) or 0)
        if confirmatory_n >= TARGET_N_PERMUTATIONS:
            result_status = "completed_10000"
        elif confirmatory_n > 0:
            result_status = "partial_below_target"
        else:
            result_status = "ready_not_run"
        rows.append(
            {
                "test_id": f"{family}:{label}",
                "dataset_id": CONFIRMATORY_DATASET,
                "priority": target["priority"],
                "family": family,
                "label": label,
                "current_p_value": current.get("p_value", pd.NA),
                "current_family_fdr": current.get("pooled_fdr_within_family", pd.NA),
                "current_all_tests_fdr": current.get("pooled_fdr_all_tests", pd.NA),
                "current_n_permutations": current_n,
                "target_n_permutations": TARGET_N_PERMUTATIONS,
                "confirmatory_p_value": confirmed.get("confirmatory_p_value", pd.NA),
                "confirmatory_fdr": confirmed.get("confirmatory_fdr", pd.NA),
                "confirmatory_n_permutations": confirmatory_n,
                "confirmatory_result_status": result_status,
                "claim_role": target["claim_role"],
                "interpretation_boundary": target["interpretation_boundary"],
                "source_table": current.get("source_table", ""),
            }
        )
    return rows


def classify_decision(rows: list[dict[str, object]]) -> str:
    if not rows:
        return "CONFIRMATORY_10000_BLOCKED_NO_TARGETS"
    if any(int(row["current_n_permutations"]) < 1000 for row in rows):
        return "CONFIRMATORY_10000_BLOCKED_BASELINE_BELOW_1000"
    if all(row["confirmatory_result_status"] == "completed_10000" for row in rows):
        return "CONFIRMATORY_10000_COMPLETED"
    if any(row["confirmatory_result_status"] == "partial_below_target" for row in rows):
        return "CONFIRMATORY_10000_PARTIAL_BELOW_TARGET"
    return "CONFIRMATORY_10000_READY_NOT_RUN"


def build_readiness_rows(decision: str, rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "check_id": "baseline_1000_exists",
            "status": "pass"
            if rows and all(int(row["current_n_permutations"]) >= 1000 for row in rows)
            else "fail",
            "evidence": f"{len(rows)} target tests with current n_permutations >= 1000",
            "required_action": "Keep 1000-permutation Round2 outputs as baseline evidence.",
        },
        {
            "check_id": "confirmatory_10000_completed",
            "status": "pass" if decision == "CONFIRMATORY_10000_COMPLETED" else "pending",
            "evidence": decision,
            "required_action": (
                "Run the command file before final high-confidence 20-50 IF submission "
                "if stronger p-value resolution is needed."
            ),
        },
        {
            "check_id": "claim_promotion_gate",
            "status": "pass_with_boundary",
            "evidence": "No row allows biological driver or clinical claims without extra evidence.",
            "required_action": "Keep Myeloid supplement-only unless independent review and stronger validation pass.",
        },
    ]


def build_commands() -> str:
    return "\n".join(
        [
            "#!/usr/bin/env bash",
            "set -euo pipefail",
            "",
            "# Long-running confirmatory run. Use tmux/nohup in WSL and disable Windows sleep.",
            "python scripts/run_tme_benchmark.py \\",
            "  --dataset-id gse154778_pdac_scrna \\",
            "  --results-dir benchmarks/results/confirmatory_10000 \\",
            "  --n-permutations 10000",
            "",
            "python scripts/build_pooled_fdr_audit.py \\",
            "  --results-root benchmarks/results/confirmatory_10000 \\",
            "  --output-dir benchmarks/results/confirmatory_10000/pooled_fdr",
            "",
            "python scripts/build_confirmatory_permutation_subset.py",
            "",
        ]
    )


def build_report(decision: str, rows: list[dict[str, object]]) -> str:
    target_lines = [
        (
            f"- `{row['test_id']}`: current p={row['current_p_value']}, "
            f"family FDR={row['current_family_fdr']}, current n={row['current_n_permutations']}, "
            f"confirmatory status `{row['confirmatory_result_status']}`."
        )
        for row in rows
    ]
    return "\n".join(
        [
            "# Confirmatory 10,000-Permutation Subset Status",
            "",
            f"- Decision: `{decision}`",
            f"- Target dataset: `{CONFIRMATORY_DATASET}`",
            f"- Target permutations: `{TARGET_N_PERMUTATIONS}`",
            "- Current role: `pre-specified_confirmatory_subset_local_ready`",
            "",
            "## Target Tests",
            "",
            *target_lines,
            "",
            "## Interpretation Boundary",
            "",
            "This file pre-specifies the smallest confirmatory subset for a higher-resolution "
            "10,000-permutation pass. The current state is not allowed to promote Myeloid, "
            "curl-like, or edge-level real-data signals into biological mechanism claims. "
            "A completed 10,000-permutation run may improve statistical defensibility, but "
            "it still does not create clinical, therapeutic, or causal evidence.",
            "",
            "## Run Command",
            "",
            f"Use `{COMMANDS_PATH.as_posix()}`. Because this is a long-running computation, "
            "run it in WSL with `tmux` or `nohup`, keep Windows sleep disabled, and keep "
            "the current 1000-permutation outputs unchanged as the baseline evidence.",
            "",
        ]
    )


def build_outputs(root: Path) -> dict[str, object]:
    root = root.resolve()
    rows = build_subset(root)
    decision = classify_decision(rows)
    _write_tsv_atomic(root / SUBSET_PATH, rows)
    _write_tsv_atomic(root / READINESS_PATH, build_readiness_rows(decision, rows))
    _write_text_atomic(root / COMMANDS_PATH, build_commands())
    _write_text_atomic(root / REPORT_PATH, build_report(decision, rows))
    return {
        "decision": decision,
        "n_targets": len(rows),
        "output_dir": OUTPUT_DIR.as_posix(),
        "report_path": REPORT_PATH.as_posix(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args(argv)

    summary = build_outputs(Path(args.root))
    print(summary["decision"])
    print(f"Targets: {summary['n_targets']}")
    print(f"Output: {summary['output_dir']}")
    print(f"Report: {summary['report_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
