#!/usr/bin/env python
"""Build pooled BH-FDR families across SheafSignal permutation result tables."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

import _bootstrap  # noqa: F401
from sheafsignal.stats import benjamini_hochberg


FAMILIES = {
    "edge_sheaf_energy": ("sheaf_energy_permutation_pvalues.csv", "sheaf_energy_empirical_p"),
    "edge_curl": ("sheaf_energy_permutation_pvalues.csv", "curl_empirical_p"),
    "node_frustration": ("frustration_permutation_pvalues.csv", "frustration_empirical_p"),
    "global_metrics": ("global_permutation_pvalues.csv", "empirical_p"),
}


def collect_pvalues(results_root: Path) -> pd.DataFrame:
    rows = []
    for dataset_dir in sorted(path for path in results_root.iterdir() if path.is_dir()):
        result_dir = dataset_dir / "results"
        if not result_dir.exists():
            continue
        for family, (filename, p_col) in FAMILIES.items():
            path = result_dir / filename
            if not path.exists():
                continue
            table = pd.read_csv(path)
            if p_col not in table.columns:
                continue
            for idx, row in table.iterrows():
                label = row.get("edge_id") or row.get("cell_type") or row.get("metric") or str(idx)
                rows.append(
                    {
                        "dataset_id": dataset_dir.name,
                        "family": family,
                        "label": label,
                        "p_value": row[p_col],
                        "source_table": str(path),
                    }
                )
    return pd.DataFrame(rows)


def build_pooled_fdr(results_root: Path, output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    table = collect_pvalues(results_root)
    if not table.empty:
        table["pooled_fdr_within_family"] = pd.NA
        for family, idx in table.groupby("family").groups.items():
            table.loc[idx, "pooled_fdr_within_family"] = benjamini_hochberg(
                table.loc[idx, "p_value"].astype(float).to_numpy()
            )
        table["pooled_fdr_all_tests"] = benjamini_hochberg(table["p_value"].astype(float).to_numpy())
    output = output_dir / "pooled_fdr_audit.csv"
    report = output_dir / "POOLED_FDR_AUDIT_REPORT.md"
    table.to_csv(output, index=False)
    if table.empty:
        lines = ["# Pooled FDR Audit", "", "No permutation p-values were found."]
    else:
        summary = (
            table.groupby("family", dropna=False)
            .agg(
                n_tests=("p_value", "size"),
                min_p=("p_value", "min"),
                min_pooled_fdr_within_family=("pooled_fdr_within_family", "min"),
            )
            .reset_index()
        )
        lines = [
            "# Pooled FDR Audit",
            "",
            f"- Result root: `{results_root}`",
            f"- Tests collected: {len(table)}",
            "",
            "## Families",
            "",
        ]
        for row in summary.itertuples(index=False):
            lines.append(
                f"- `{row.family}`: n={row.n_tests}, min_p={row.min_p:.4g}, "
                f"min_family_fdr={row.min_pooled_fdr_within_family:.4g}"
            )
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"table": output, "report": report}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", default="benchmarks/results")
    parser.add_argument("--output-dir", default="benchmarks/results/pooled_fdr")
    args = parser.parse_args(argv)
    paths = build_pooled_fdr(Path(args.results_root), Path(args.output_dir))
    for path in paths.values():
        print(f"wrote {path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

