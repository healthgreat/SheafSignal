#!/usr/bin/env python
"""Audit benchmark result table contracts for SheafSignal.

Author: SheafSignal contributors
Date: 2026-05-01
Purpose: verify that manuscript-facing benchmark result tables have stable
schemas, valid metric ranges, and traceable comparator files before submission.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


EXPECTED_PUBLIC_DATASETS = {
    "gse72056_melanoma_scrna",
    "gse154778_pdac_scrna",
    "gse176078_brca_scrna",
    "tenx_breast_visium",
}
EXPECTED_COMPONENT_SCENARIOS = {
    "gradient_chain": "gradient_ratio",
    "triangle_curl": "curl_ratio",
    "harmonic_ring": "harmonic_ratio",
    "mixed": "mixed",
}
EXPECTED_SPATIAL_K = {4, 6, 8, 10, 12}
RATIO_COLUMNS = ["gradient_ratio", "curl_ratio", "harmonic_ratio"]


def _write_text_atomic(path: Path, text: str) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def _write_table_atomic(path: Path, table: pd.DataFrame) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    table.to_csv(tmp_path, sep="\t", index=False)
    tmp_path.replace(path)


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _add_check(
    rows: list[dict[str, str]],
    *,
    check_id: str,
    domain: str,
    status: str,
    evidence: str,
    required_action: str,
) -> None:
    rows.append(
        {
            "check_id": check_id,
            "domain": domain,
            "status": status,
            "evidence": evidence,
            "required_action": required_action,
        }
    )


def _missing_columns(table: pd.DataFrame, columns: list[str]) -> list[str]:
    return [column for column in columns if column not in table.columns]


def _as_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def _finite_between(table: pd.DataFrame, columns: list[str], low: float, high: float) -> bool:
    for column in columns:
        values = _as_numeric(table[column])
        if values.isna().any() or (values < low).any() or (values > high).any():
            return False
    return True


def _rel_path_exists(root: Path, rel_text: object) -> bool:
    text = str(rel_text).strip()
    if not text or text.lower() == "nan":
        return False
    path = Path(text.replace("\\", "/"))
    if not path.is_absolute():
        path = root / path
    return path.exists()


def _ratio_rows_sum_to_one(table: pd.DataFrame, tolerance: float = 1e-6) -> bool:
    sums = table[RATIO_COLUMNS].apply(pd.to_numeric, errors="coerce").sum(axis=1)
    return bool(((sums - 1.0).abs() <= tolerance).all())


def _check_component_recovery(root: Path, rows: list[dict[str, str]]) -> None:
    path = root / "benchmarks/results/component_recovery.csv"
    table = _read_csv(path)
    required = [
        "scenario",
        "expected_dominant_component",
        *RATIO_COLUMNS,
        "total_flow_energy",
        "n_pair_edges",
        "n_triangles",
    ]
    missing = _missing_columns(table, required)
    _add_check(
        rows,
        check_id="component_recovery_schema",
        domain="simulation",
        status="pass" if not table.empty and not missing else "fail",
        evidence="missing_columns=" + ";".join(missing) if missing else f"rows={len(table)}",
        required_action="Regenerate component_recovery.csv with the expected schema.",
    )
    if table.empty or missing:
        return

    scenarios = set(table["scenario"].astype(str))
    missing_scenarios = sorted(set(EXPECTED_COMPONENT_SCENARIOS) - scenarios)
    numeric_ok = _finite_between(table, RATIO_COLUMNS, 0.0, 1.0)
    numeric_ok = numeric_ok and (_as_numeric(table["total_flow_energy"]) > 0).all()
    numeric_ok = numeric_ok and (_as_numeric(table["n_pair_edges"]) > 0).all()
    sums_ok = _ratio_rows_sum_to_one(table)
    dominant_failures: list[str] = []
    for scenario, expected in EXPECTED_COMPONENT_SCENARIOS.items():
        if scenario not in scenarios or expected == "mixed":
            continue
        value = float(table.loc[table["scenario"] == scenario, expected].iloc[0])
        if value < 0.99:
            dominant_failures.append(f"{scenario}:{expected}={value:.4f}")
    status = (
        "pass"
        if not missing_scenarios and numeric_ok and sums_ok and not dominant_failures
        else "fail"
    )
    evidence_parts = [
        f"missing_scenarios={';'.join(missing_scenarios) or 'none'}",
        f"numeric_ok={numeric_ok}",
        f"ratio_sums_ok={sums_ok}",
        f"dominant_failures={';'.join(dominant_failures) or 'none'}",
    ]
    _add_check(
        rows,
        check_id="component_recovery_metric_contract",
        domain="simulation",
        status=status,
        evidence=";".join(evidence_parts),
        required_action="Fix simulation recovery outputs before using Figure 2 claims.",
    )


def _check_public_summary(root: Path, rows: list[dict[str, str]]) -> None:
    path = root / "benchmarks/results/public_tme_sheafsignal_summary.csv"
    table = _read_csv(path)
    required = [
        "dataset_id",
        "status",
        "n_edges",
        "n_cell_types",
        "total_sheaf_energy",
        *RATIO_COLUMNS,
        "top_frustration_cell_type",
        "top_frustration_score",
    ]
    missing = _missing_columns(table, required)
    _add_check(
        rows,
        check_id="public_tme_summary_schema",
        domain="public_benchmark",
        status="pass" if not table.empty and not missing else "fail",
        evidence="missing_columns=" + ";".join(missing) if missing else f"rows={len(table)}",
        required_action="Regenerate public_tme_sheafsignal_summary.csv with expected columns.",
    )
    if table.empty or missing:
        return

    public = table.loc[table["dataset_id"].astype(str).isin(EXPECTED_PUBLIC_DATASETS)]
    missing_datasets = sorted(EXPECTED_PUBLIC_DATASETS - set(public["dataset_id"].astype(str)))
    completed = public["status"].astype(str).eq("completed").all()
    numeric_ok = (
        (_as_numeric(public["n_edges"]) > 0).all()
        and (_as_numeric(public["n_cell_types"]) >= 2).all()
        and (_as_numeric(public["total_sheaf_energy"]) > 0).all()
        and _finite_between(public, RATIO_COLUMNS, 0.0, 1.0)
        and _ratio_rows_sum_to_one(public)
        and (_as_numeric(public["top_frustration_score"]) >= 0).all()
    )
    status = "pass" if not missing_datasets and completed and numeric_ok else "fail"
    _add_check(
        rows,
        check_id="public_tme_summary_metric_contract",
        domain="public_benchmark",
        status=status,
        evidence=(
            f"public_rows={len(public)};missing_datasets={';'.join(missing_datasets) or 'none'};"
            f"completed={completed};numeric_ok={numeric_ok}"
        ),
        required_action="Regenerate public TME benchmark summary before manuscript use.",
    )


def _check_tool_comparison(root: Path, rows: list[dict[str, str]]) -> None:
    path = root / "benchmarks/results/tool_comparison.csv"
    table = _read_csv(path)
    required = [
        "dataset_id",
        "tool",
        "status",
        "edge_score_table",
        "aligned_edge_table",
        "n_edges",
        "spearman_sheaf_energy_vs_tool_score",
        "high_sheaf_low_tool_edges",
        "high_tool_low_sheaf_edges",
        "concordant_high_edges",
        "unaligned_edges",
    ]
    missing = _missing_columns(table, required)
    _add_check(
        rows,
        check_id="tool_comparison_schema",
        domain="comparator",
        status="pass" if not table.empty and not missing else "fail",
        evidence="missing_columns=" + ";".join(missing) if missing else f"rows={len(table)}",
        required_action="Regenerate tool_comparison.csv with expected comparator columns.",
    )
    if table.empty or missing:
        return

    completed = table.loc[
        (table["dataset_id"].astype(str) != "demo_synthetic")
        & table["status"].astype(str).str.startswith("completed")
    ].copy()
    if completed.empty:
        _add_check(
            rows,
            check_id="completed_comparator_metric_contract",
            domain="comparator",
            status="fail",
            evidence="no completed public comparator rows",
            required_action="Run and import comparator outputs before claiming comparator evidence.",
        )
        return
    numeric_ok = (
        (_as_numeric(completed["n_edges"]) > 0).all()
        and _finite_between(completed, ["spearman_sheaf_energy_vs_tool_score"], -1.0, 1.0)
    )
    count_columns = [
        "high_sheaf_low_tool_edges",
        "high_tool_low_sheaf_edges",
        "concordant_high_edges",
        "unaligned_edges",
    ]
    count_ok = all((_as_numeric(completed[column]) >= 0).all() for column in count_columns)
    missing_files = []
    for row in completed.to_dict(orient="records"):
        for column in ["edge_score_table", "aligned_edge_table"]:
            if not _rel_path_exists(root, row[column]):
                missing_files.append(f"{row['dataset_id']}:{row['tool']}:{column}")
    status = "pass" if numeric_ok and count_ok and not missing_files else "fail"
    _add_check(
        rows,
        check_id="completed_comparator_metric_contract",
        domain="comparator",
        status=status,
        evidence=(
            f"completed_rows={len(completed)};numeric_ok={numeric_ok};count_ok={count_ok};"
            f"missing_files={';'.join(missing_files) or 'none'}"
        ),
        required_action="Fix completed comparator rows or their linked edge tables.",
    )

    tool_counts = completed.groupby("tool")["dataset_id"].nunique().to_dict()
    coverage_ok = (
        tool_counts.get("LRProductBaseline", 0) >= 4
        and tool_counts.get("LIANA", 0) >= 3
        and tool_counts.get("NicheNet", 0) >= 3
        and tool_counts.get("MechanisticTargetPrior", 0) >= 3
    )
    _add_check(
        rows,
        check_id="comparator_coverage_contract",
        domain="comparator",
        status="pass" if coverage_ok else "warning",
        evidence=";".join(f"{tool}={count}" for tool, count in sorted(tool_counts.items())),
        required_action="Keep comparator claims bounded or add missing external comparator runs.",
    )


def _check_claim_gate(root: Path, rows: list[dict[str, str]]) -> None:
    path = root / "benchmarks/results/gse154778_pdac_scrna/qc/claim_gating_by_cell_type.csv"
    table = _read_csv(path)
    required = [
        "cell_type",
        "claim_gate",
        "total_n_cells",
        "min_lesion_n_cells",
        "min_lesion_n_samples",
        "manuscript_use",
        "expression_mode_top_cell_type",
        "mode_consistency_status",
    ]
    missing = _missing_columns(table, required)
    if table.empty or missing:
        _add_check(
            rows,
            check_id="gse154778_claim_gate_contract",
            domain="claim_boundary",
            status="fail",
            evidence="missing_columns=" + ";".join(missing) if missing else "table_empty",
            required_action="Regenerate GSE154778 claim-gating output.",
        )
        return
    main_claims = sorted(
        table.loc[table["claim_gate"].astype(str) == "main_claim", "cell_type"]
        .astype(str)
        .tolist()
    )
    myeloid = table.loc[table["cell_type"].astype(str) == "Myeloid"]
    myeloid_downgraded = (
        len(myeloid) == 1
        and str(myeloid.iloc[0]["claim_gate"]) != "main_claim"
        and str(myeloid.iloc[0]["mode_consistency_status"])
        == "discordant_with_expression_mode_top"
    )
    no_unvalidated_main_claims = main_claims == []
    status = "pass" if no_unvalidated_main_claims and myeloid_downgraded else "fail"
    _add_check(
        rows,
        check_id="gse154778_claim_gate_contract",
        domain="claim_boundary",
        status=status,
        evidence=(
            f"main_claim_cell_types={';'.join(main_claims)};"
            f"myeloid_downgraded={myeloid_downgraded}"
        ),
        required_action=(
            "Do not promote any GSE154778 cell type to a main biological source "
            "claim until lesion, annotation, and expression-mode permutation/FDR "
            "gates agree."
        ),
    )


def _check_spatial_sensitivity(root: Path, rows: list[dict[str, str]]) -> None:
    path = root / "benchmarks/results/tenx_breast_visium/spatial/qc/k_neighbors_sensitivity.csv"
    table = _read_csv(path)
    required = [
        "dataset_id",
        "k_neighbors",
        "n_spots",
        "n_spatial_edges",
        "total_spatial_sheaf_energy",
        "top_50_overlap_with_reference",
        "spearman_with_reference",
    ]
    missing = _missing_columns(table, required)
    if table.empty or missing:
        _add_check(
            rows,
            check_id="visium_spatial_sensitivity_contract",
            domain="spatial_qc",
            status="fail",
            evidence="missing_columns=" + ";".join(missing) if missing else "table_empty",
            required_action="Regenerate Visium k-neighbor sensitivity output.",
        )
        return
    observed_k = set(_as_numeric(table["k_neighbors"]).astype(int).tolist())
    missing_k = sorted(EXPECTED_SPATIAL_K - observed_k)
    numeric_ok = (
        (_as_numeric(table["n_spots"]) > 0).all()
        and (_as_numeric(table["n_spatial_edges"]) > 0).all()
        and (_as_numeric(table["total_spatial_sheaf_energy"]) > 0).all()
        and _finite_between(table, ["top_50_overlap_with_reference"], 0.0, 1.0)
        and _finite_between(table, ["spearman_with_reference"], -1.0, 1.0)
    )
    min_overlap = float(_as_numeric(table["top_50_overlap_with_reference"]).min())
    min_spearman = float(_as_numeric(table["spearman_with_reference"]).min())
    stable = min_overlap >= 0.8 and min_spearman >= 0.9
    status = "pass" if not missing_k and numeric_ok and stable else "warning"
    _add_check(
        rows,
        check_id="visium_spatial_sensitivity_contract",
        domain="spatial_qc",
        status=status,
        evidence=(
            f"missing_k={';'.join(map(str, missing_k)) or 'none'};numeric_ok={numeric_ok};"
            f"min_overlap={min_overlap:.4f};min_spearman={min_spearman:.4f}"
        ),
        required_action="Keep spatial claims bounded or regenerate k-neighbor sensitivity analysis.",
    )


def build_benchmark_contract_audit(root: Path) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    _check_component_recovery(root, rows)
    _check_public_summary(root, rows)
    _check_tool_comparison(root, rows)
    _check_claim_gate(root, rows)
    _check_spatial_sensitivity(root, rows)
    return pd.DataFrame(rows)


def build_benchmark_contract_report(audit: pd.DataFrame) -> str:
    failures = audit.loc[audit["status"].astype(str) == "fail"]
    warnings = audit.loc[audit["status"].astype(str) == "warning"]
    decision = (
        "BENCHMARK_RESULT_CONTRACT_FAIL"
        if not failures.empty
        else "BENCHMARK_RESULT_CONTRACT_PASS_WITH_WARNINGS"
        if not warnings.empty
        else "BENCHMARK_RESULT_CONTRACT_PASS"
    )
    lines = [
        "# Benchmark Result Contract Audit",
        "",
        f"Decision: `{decision}`",
        "",
        f"- Checks: {len(audit)}",
        f"- Failures: {len(failures)}",
        f"- Warnings: {len(warnings)}",
        "",
        "## Checks Requiring Attention",
        "",
    ]
    if failures.empty and warnings.empty:
        lines.append("None.")
    else:
        for row in pd.concat([failures, warnings]).to_dict(orient="records"):
            lines.append(
                f"- `{row['check_id']}` `{row['status']}`: {row['evidence']} "
                f"Action: {row['required_action']}"
            )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This audit checks result table integrity and linked comparator files.",
            "It does not create new benchmark results and does not validate broader",
            "biological or clinical conclusions beyond the existing claim gates.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument(
        "--audit-out",
        default="benchmarks/results/BENCHMARK_RESULT_CONTRACT_AUDIT.tsv",
    )
    parser.add_argument(
        "--report-out",
        default="benchmarks/results/BENCHMARK_RESULT_CONTRACT_REPORT.md",
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Write outputs and return success even when contract checks fail.",
    )
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    audit_out = root / args.audit_out
    report_out = root / args.report_out
    audit_out.parent.mkdir(parents=True, exist_ok=True)
    audit = build_benchmark_contract_audit(root)
    _write_table_atomic(audit_out, audit)
    _write_text_atomic(report_out, build_benchmark_contract_report(audit))
    print(f"wrote {audit_out}")
    print(f"wrote {report_out}")
    has_failures = bool((audit["status"].astype(str) == "fail").any())
    if has_failures and not args.report_only:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
