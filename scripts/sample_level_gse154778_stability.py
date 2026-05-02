#!/usr/bin/env python
"""Run sample-level GSE154778 Myeloid frustration robustness checks."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

import _bootstrap  # noqa: F401
from bootstrap_gse154778_stability import (
    _setup_matplotlib,
    read_selected_expression,
    resolve_gse154778_processed_dir,
    run_sheafsignal_on_profiles,
    update_figure_manifest,
)
from sheafsignal.io import read_gene_set, read_ligand_receptor_db


SAMPLE_NOTE = (
    "sample-level pseudobulk robustness under the current frozen annotation "
    "version; sparse sample-cell-type profiles are flagged"
)


def sample_profiles(expression: pd.DataFrame, metadata: pd.DataFrame) -> pd.DataFrame:
    aligned = metadata.set_index("cell_id").loc[expression.index]
    profiles = expression.groupby(aligned["cell_type"].astype(str)).mean()
    profiles.index.name = "cell_type"
    return profiles


def sample_level_frustration(
    *,
    expression: pd.DataFrame,
    metadata: pd.DataFrame,
    lr_db: pd.DataFrame,
    pathway_genes: list[str],
    min_cell_types: int,
    min_myeloid_cells: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    required = {"cell_id", "cell_type", "sample_id", "lesion_type"}
    missing = required.difference(metadata.columns)
    if missing:
        raise ValueError(f"metadata is missing required columns: {sorted(missing)}")

    common = expression.index.astype(str).intersection(metadata["cell_id"].astype(str))
    expression = expression.loc[common].copy()
    metadata = metadata.set_index("cell_id").loc[common].reset_index()
    metadata["cell_id"] = metadata["cell_id"].astype(str)

    rows = []
    for (sample_id, lesion_type), group in metadata.groupby(["sample_id", "lesion_type"], sort=True):
        expr = expression.loc[group["cell_id"].astype(str)]
        counts = group["cell_type"].astype(str).value_counts().to_dict()
        n_cell_types = len(counts)
        myeloid_cells = int(counts.get("Myeloid", 0))
        base = {
            "sample_id": sample_id,
            "lesion_type": lesion_type,
            "n_cells": int(len(group)),
            "n_cell_types": int(n_cell_types),
            "myeloid_n_cells": myeloid_cells,
            "myeloid_low_count_flag": myeloid_cells < min_myeloid_cells,
            "sample_note": SAMPLE_NOTE,
        }
        if n_cell_types < min_cell_types or myeloid_cells == 0:
            rows.append(
                {
                    **base,
                    "status": "skipped_insufficient_cell_types_or_no_myeloid",
                    "top_frustration_cell_type": "",
                    "myeloid_frustration_score": pd.NA,
                    "myeloid_frustration_rank": pd.NA,
                    "gradient_ratio": pd.NA,
                    "curl_ratio": pd.NA,
                    "harmonic_ratio": pd.NA,
                    "total_sheaf_energy": pd.NA,
                }
            )
            continue

        profiles = sample_profiles(expr, group)
        try:
            node_scores, global_scores = run_sheafsignal_on_profiles(profiles, lr_db, pathway_genes)
            node_scores = node_scores.sort_values("frustration_score", ascending=False).reset_index(drop=True)
            myeloid = node_scores.loc[node_scores["cell_type"] == "Myeloid"]
            if myeloid.empty:
                raise ValueError("Myeloid absent after profile aggregation")
            rows.append(
                {
                    **base,
                    "status": "completed",
                    "top_frustration_cell_type": node_scores.iloc[0]["cell_type"],
                    "myeloid_frustration_score": float(myeloid["frustration_score"].iloc[0]),
                    "myeloid_frustration_rank": int(myeloid.index[0] + 1),
                    "gradient_ratio": global_scores["gradient_ratio"],
                    "curl_ratio": global_scores["curl_ratio"],
                    "harmonic_ratio": global_scores["harmonic_ratio"],
                    "total_sheaf_energy": global_scores["total_sheaf_energy"],
                }
            )
        except Exception as exc:
            rows.append(
                {
                    **base,
                    "status": f"failed_{type(exc).__name__}",
                    "top_frustration_cell_type": "",
                    "myeloid_frustration_score": pd.NA,
                    "myeloid_frustration_rank": pd.NA,
                    "gradient_ratio": pd.NA,
                    "curl_ratio": pd.NA,
                    "harmonic_ratio": pd.NA,
                    "total_sheaf_energy": pd.NA,
                }
            )

    sample_table = pd.DataFrame(rows)
    summary_rows = []
    completed = sample_table.loc[sample_table["status"] == "completed"].copy()
    for lesion_type, group in completed.groupby("lesion_type", sort=True):
        adequate = group.loc[~group["myeloid_low_count_flag"]]
        summary_rows.append(_summarize_sample_group(lesion_type, group, adequate))
    summary_rows.append(_summarize_sample_group("all", completed, completed.loc[~completed["myeloid_low_count_flag"]]))
    summary = pd.DataFrame(summary_rows)
    return sample_table, summary


def _summarize_sample_group(label: str, group: pd.DataFrame, adequate: pd.DataFrame) -> dict[str, object]:
    if group.empty:
        return {
            "lesion_type": label,
            "n_completed_samples": 0,
            "n_myeloid_adequate_samples": 0,
            "myeloid_top_frequency_completed": pd.NA,
            "myeloid_top_frequency_adequate": pd.NA,
            "median_myeloid_frustration_completed": pd.NA,
            "median_myeloid_frustration_adequate": pd.NA,
            "sample_note": SAMPLE_NOTE,
        }
    return {
        "lesion_type": label,
        "n_completed_samples": int(len(group)),
        "n_myeloid_adequate_samples": int(len(adequate)),
        "myeloid_top_frequency_completed": float((group["top_frustration_cell_type"] == "Myeloid").mean()),
        "myeloid_top_frequency_adequate": (
            float((adequate["top_frustration_cell_type"] == "Myeloid").mean())
            if len(adequate)
            else pd.NA
        ),
        "median_myeloid_frustration_completed": float(group["myeloid_frustration_score"].median()),
        "median_myeloid_frustration_adequate": (
            float(adequate["myeloid_frustration_score"].median()) if len(adequate) else pd.NA
        ),
        "sample_note": SAMPLE_NOTE,
    }


def plot_sample_level(sample_table: pd.DataFrame, output: Path) -> Path:
    plt = _setup_matplotlib()
    table = sample_table.loc[sample_table["status"] == "completed"].copy()
    table = table.sort_values(["lesion_type", "sample_id"])
    colors = table["lesion_type"].map({"Primary": "#4C78A8", "Metastatic": "#F58518"}).fillna("#777777")
    fig, ax = plt.subplots(figsize=(8.0, 4.4))
    ax.bar(table["sample_id"], table["myeloid_frustration_score"], color=colors)
    ax.set_ylabel("Myeloid frustration score")
    ax.set_xlabel("Sample")
    ax.set_title("GSE154778 sample-level Myeloid frustration robustness")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output)
    plt.close(fig)
    return output


def run_sample_level(
    *,
    processed_dir: Path,
    raw_path: Path,
    lr_db_path: Path,
    gene_set_path: Path,
    output_dir: Path,
    figure_manifest: Path,
    min_cell_types: int,
    min_myeloid_cells: int,
    max_cells: int | None,
    chunksize: int,
) -> dict[str, Path]:
    expression = read_selected_expression(
        processed_dir=processed_dir,
        raw_path=raw_path,
        lr_db_path=lr_db_path,
        gene_set_path=gene_set_path,
        max_cells=max_cells,
        chunksize=chunksize,
    )
    metadata = pd.read_csv(processed_dir / "metadata.csv")
    lr_db = read_ligand_receptor_db(lr_db_path)
    pathway_genes = read_gene_set(gene_set_path)
    sample_table, summary = sample_level_frustration(
        expression=expression,
        metadata=metadata,
        lr_db=lr_db,
        pathway_genes=pathway_genes,
        min_cell_types=min_cell_types,
        min_myeloid_cells=min_myeloid_cells,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    sample_path = output_dir / "sample_level_frustration.csv"
    summary_path = output_dir / "sample_level_myeloid_stability_summary.csv"
    figure_path = output_dir / "sample_level_myeloid_stability.pdf"
    sample_table.to_csv(sample_path, index=False)
    summary.to_csv(summary_path, index=False)
    plot_sample_level(sample_table, figure_path)
    update_figure_manifest(
        figure_manifest,
        figure_path,
        figure_id="supp_gse154778_sample_level_myeloid_stability",
    )
    return {
        "sample_level": sample_path,
        "summary": summary_path,
        "figure": figure_path,
        "figure_manifest": figure_manifest,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-id", default="gse154778_pdac_scrna")
    parser.add_argument("--processed-dir", default=None)
    parser.add_argument(
        "--raw-path",
        default="data/external/gse154778_pdac_scrna/GSE154778_dgeMtx.csv.gz",
    )
    parser.add_argument("--lr-db", default="metadata/tme_ligand_receptor.csv")
    parser.add_argument("--gene-set", default="metadata/tme_pathway_genes.txt")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--figure-manifest", default="manuscript/figure_manifest.tsv")
    parser.add_argument("--min-cell-types", type=int, default=2)
    parser.add_argument("--min-myeloid-cells", type=int, default=20)
    parser.add_argument("--max-cells", type=int, default=None)
    parser.add_argument("--chunksize", type=int, default=2000)
    args = parser.parse_args(argv)

    dataset_id = args.dataset_id
    paths = run_sample_level(
        processed_dir=resolve_gse154778_processed_dir(dataset_id, args.processed_dir),
        raw_path=Path(args.raw_path),
        lr_db_path=Path(args.lr_db),
        gene_set_path=Path(args.gene_set),
        output_dir=Path(args.output_dir or f"benchmarks/results/{dataset_id}/stability"),
        figure_manifest=Path(args.figure_manifest),
        min_cell_types=args.min_cell_types,
        min_myeloid_cells=args.min_myeloid_cells,
        max_cells=args.max_cells,
        chunksize=args.chunksize,
    )
    for path in paths.values():
        print(f"wrote {path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
