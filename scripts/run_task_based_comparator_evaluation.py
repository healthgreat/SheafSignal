#!/usr/bin/env python
"""Run task-based comparator evaluation on synthetic perturbation recovery."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

import _bootstrap  # noqa: F401
from sheafsignal.simulate import (
    independent_perturbation_recovery,
    sheaf_ground_truth_recovery,
)


def build_task_evaluation(seed: int, noise_values: list[float]) -> pd.DataFrame:
    rows = []
    for noise_sd in noise_values:
        independent = independent_perturbation_recovery(noise_sd=noise_sd, seed=seed)
        independent["task_is_primary"] = True
        rows.append(independent)

        residual_aligned = sheaf_ground_truth_recovery(noise_sd=noise_sd, seed=seed)
        residual_aligned["task_is_primary"] = False
        rows.append(residual_aligned)

    table = pd.concat(rows, ignore_index=True)
    table["evaluation_type"] = "task_based_ground_truth_recovery"
    table["claim_boundary"] = table["truth_depends_on_residual_definition"].map(
        {
            True: "definition_dependent_supporting_only",
            False: "independent_task_primary_simulation",
        }
    )
    return table


def write_task_evaluation_report(table: pd.DataFrame, output_path: Path) -> Path:
    report_path = output_path.with_suffix(".md")
    primary = table.loc[table["task_is_primary"]].copy()
    best_rows = (
        primary.sort_values(["noise_sd", "average_precision"], ascending=[True, False])
        .groupby("noise_sd")
        .head(3)
    )
    lines = [
        "# Task-Based Comparator Evaluation Report",
        "",
        "- Decision: `TASK_BASED_COMPARATOR_EVALUATION_READY`",
        f"- Output table: `{output_path.as_posix()}`",
        "- Primary task: `independent_perturbation`",
        "- Boundary: primary simulation truth labels are predefined perturbation edges, not residual-thresholded edges.",
        "",
        "## Top Methods By Noise Level",
        "",
        "| noise_sd | method | average_precision | auroc | baseline_family |",
        "|---|---|---:|---:|---|",
    ]
    for row in best_rows.to_dict(orient="records"):
        lines.append(
            f"| {row['noise_sd']} | `{row['method']}` | "
            f"{float(row['average_precision']):.4f} | {float(row['auroc']):.4f} | "
            f"`{row['baseline_family']}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation Boundary",
            "",
            "This task-based comparison reduces the circular-ground-truth concern, but it does not by itself prove that the higher-rank sheaf is superior to every simple LR-flow/pathway-gradient product baseline. That claim must be supported by harder perturbation tasks or downgraded.",
            "",
        ]
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="benchmarks/results")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--noise-sd", type=float, action="append", default=[0.0, 0.05, 0.1])
    args = parser.parse_args(argv)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    output = out_dir / "comparator_task_recovery.csv"
    table = build_task_evaluation(seed=args.seed, noise_values=args.noise_sd)
    table.to_csv(output, index=False)
    report = write_task_evaluation_report(table, output)
    print("TASK_BASED_COMPARATOR_EVALUATION_READY")
    print(f"Output: {output}")
    print(f"Report: {report}")
    print(f"Rows: {len(table)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
