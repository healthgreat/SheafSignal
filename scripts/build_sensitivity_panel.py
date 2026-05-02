#!/usr/bin/env python
"""Build sensitivity tables for edge-threshold and statistical hardening."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

import _bootstrap  # noqa: F401
from sheafsignal.core import compute_node_frustration
from sheafsignal.hodge import attach_hodge_components, hodge_decomposition
from sheafsignal.stats import benjamini_hochberg


THRESHOLD_QUANTILES = [0.0, 0.25, 0.5, 0.75]


def _write_text_atomic(path: Path, text: str) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def _rank_stability(reference: pd.DataFrame, current: pd.DataFrame) -> float:
    ref = reference[["sender", "receiver", "sheaf_energy"]].rename(
        columns={"sheaf_energy": "reference_energy"}
    )
    cur = current[["sender", "receiver", "sheaf_energy"]].rename(
        columns={"sheaf_energy": "current_energy"}
    )
    aligned = ref.merge(cur, on=["sender", "receiver"], how="inner")
    if len(aligned) < 2:
        return pd.NA
    return float(aligned["reference_energy"].rank().corr(aligned["current_energy"].rank()))


def edge_threshold_sensitivity(dataset_id: str, edge_path: Path) -> list[dict[str, object]]:
    edges = pd.read_csv(edge_path)
    rows = []
    for quantile in THRESHOLD_QUANTILES:
        threshold = float(edges["communication_flow"].quantile(quantile))
        subset = edges.loc[edges["communication_flow"] >= threshold].copy()
        if subset.empty:
            continue
        pair_components, scores = hodge_decomposition(subset, flow_col="flow_z")
        subset = attach_hodge_components(subset, pair_components)
        node = compute_node_frustration(subset)
        top = node.sort_values("frustration_score", ascending=False).iloc[0]
        rows.append(
            {
                "dataset_id": dataset_id,
                "sensitivity_axis": "edge_threshold",
                "parameter": f"communication_flow_quantile_{quantile:g}",
                "parameter_value": threshold,
                "n_edges": int(len(subset)),
                "top_frustration_cell_type": top["cell_type"],
                "top_frustration_score": float(top["frustration_score"]),
                "gradient_ratio": scores["gradient_ratio"],
                "curl_ratio": scores["curl_ratio"],
                "harmonic_ratio": scores["harmonic_ratio"],
                "edge_rank_spearman_vs_baseline": _rank_stability(edges, subset),
                "statistical_status": "edge_threshold_recomputed",
            }
        )
    return rows


def permutation_fdr_summary(dataset_id: str, dataset_dir: Path) -> list[dict[str, object]]:
    rows = []
    candidate_paths = [
        dataset_dir / "results" / "sheaf_energy_permutation_pvalues.csv",
        dataset_dir / "results" / "permutation_edge_statistics.csv",
        dataset_dir / "statistics" / "permutation_edge_statistics.csv",
    ]
    existing = [path for path in candidate_paths if path.exists()]
    if not existing:
        return [
            {
                "dataset_id": dataset_id,
                "sensitivity_axis": "permutation_fdr",
                "parameter": "permutation_edge_statistics",
                "parameter_value": "missing",
                "n_edges": pd.NA,
                "top_frustration_cell_type": "",
                "top_frustration_score": pd.NA,
                "gradient_ratio": pd.NA,
                "curl_ratio": pd.NA,
                "harmonic_ratio": pd.NA,
                "edge_rank_spearman_vs_baseline": pd.NA,
                "statistical_status": "not_run_requires_permutation_statistics",
            }
        ]
    stats = pd.read_csv(existing[0])
    p_col = "sheaf_energy_empirical_p"
    if p_col not in stats.columns:
        return []
    fdr = benjamini_hochberg(stats[p_col])
    rows.append(
        {
            "dataset_id": dataset_id,
            "sensitivity_axis": "permutation_fdr",
            "parameter": p_col,
            "parameter_value": "BH",
            "n_edges": int(len(stats)),
            "top_frustration_cell_type": "",
            "top_frustration_score": pd.NA,
            "gradient_ratio": pd.NA,
            "curl_ratio": pd.NA,
            "harmonic_ratio": pd.NA,
            "edge_rank_spearman_vs_baseline": pd.NA,
            "statistical_status": f"min_fdr={float(pd.Series(fdr).min()):.4g}",
        }
    )
    return rows


def build_sensitivity_panel(results_dir: Path, output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    summary_path = results_dir / "public_tme_sheafsignal_summary.csv"
    summary = pd.read_csv(summary_path) if summary_path.exists() else pd.DataFrame()
    completed_ids = (
        summary.loc[summary["status"].astype(str) == "completed", "dataset_id"].astype(str).tolist()
        if not summary.empty
        else []
    )
    for dataset_id in completed_ids:
        dataset_dir = results_dir / dataset_id
        edge_path = dataset_dir / "results" / "sheaf_energy_by_edge.csv"
        if edge_path.exists():
            rows.extend(edge_threshold_sensitivity(dataset_id, edge_path))
        rows.extend(permutation_fdr_summary(dataset_id, dataset_dir))

    table = pd.DataFrame(rows)
    table_path = output_dir / "sensitivity_panel.csv"
    report_path = output_dir / "SENSITIVITY_PANEL_REPORT.md"
    table.to_csv(table_path, index=False)
    pending = (
        table["statistical_status"].astype(str).str.contains("not_run|missing", case=False).sum()
        if not table.empty
        else 0
    )
    lines = [
        "# Sensitivity Panel Report",
        "",
        f"- Completed datasets represented: {len(set(completed_ids))}",
        f"- Sensitivity rows: {len(table)}",
        f"- Pending statistical rows: {int(pending)}",
        "- Boundary: this panel currently covers edge-threshold stability and permutation/BH-FDR summaries; LR-resource and pathway-resource sweeps remain separate hardening tasks.",
        "",
    ]
    _write_text_atomic(report_path, "\n".join(lines))
    return {"table": table_path, "report": report_path}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", default="benchmarks/results")
    parser.add_argument("--output-dir", default="benchmarks/results/sensitivity")
    args = parser.parse_args(argv)
    paths = build_sensitivity_panel(Path(args.results_dir), Path(args.output_dir))
    for path in paths.values():
        print(f"wrote {path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
