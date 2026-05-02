#!/usr/bin/env python
"""Run GSE154778 SheafSignal analysis stratified by lesion type."""

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


STRATIFIED_NOTE = (
    "lesion-stratified analysis under the current frozen annotation version; "
    "low-count cell types should not be used for strong biological conclusions"
)


def profiles_for_stratum(
    expression: pd.DataFrame,
    metadata: pd.DataFrame,
    *,
    lesion_type: str,
    min_cells_per_type: int,
) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    subset = metadata.loc[metadata["lesion_type"].astype(str) == str(lesion_type)].copy()
    if subset.empty:
        raise ValueError(f"No cells found for lesion_type={lesion_type!r}.")

    common = expression.index.astype(str).intersection(subset["cell_id"].astype(str))
    if len(common) == 0:
        raise ValueError(f"No expression rows overlap lesion_type={lesion_type!r}.")

    subset = subset.set_index("cell_id").loc[common].reset_index()
    expr = expression.loc[common]
    counts = (
        subset.groupby("cell_type", dropna=False)
        .size()
        .reset_index(name="n_cells")
        .sort_values("cell_type")
    )
    low = counts.loc[counts["n_cells"] < min_cells_per_type, "cell_type"].astype(str).tolist()
    warning = ""
    if low:
        warning = (
            f"cell types below min_cells_per_type={min_cells_per_type}: "
            + ";".join(low)
        )

    profiles = expr.groupby(subset.set_index("cell_id").loc[expr.index, "cell_type"].astype(str)).mean()
    profiles.index.name = "cell_type"
    return profiles, counts, warning


def run_lesion_stratified(
    *,
    expression: pd.DataFrame,
    metadata: pd.DataFrame,
    lr_db: pd.DataFrame,
    pathway_genes: list[str],
    min_cells_per_type: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    required_columns = {"cell_id", "cell_type", "lesion_type"}
    missing = required_columns.difference(metadata.columns)
    if missing:
        raise ValueError(f"metadata is missing required columns: {sorted(missing)}")

    summary_rows = []
    node_rows = []
    edge_rows = []
    for lesion_type in sorted(metadata["lesion_type"].astype(str).dropna().unique()):
        profiles, counts, warning = profiles_for_stratum(
            expression,
            metadata,
            lesion_type=lesion_type,
            min_cells_per_type=min_cells_per_type,
        )
        if len(profiles) < 2:
            summary_rows.append(
                {
                    "lesion_type": lesion_type,
                    "status": "skipped_lt_2_cell_types",
                    "n_cells": int(counts["n_cells"].sum()),
                    "n_cell_types": int(len(profiles)),
                    "top_frustration_cell_type": "",
                    "top_frustration_score": pd.NA,
                    "gradient_ratio": pd.NA,
                    "curl_ratio": pd.NA,
                    "harmonic_ratio": pd.NA,
                    "total_sheaf_energy": pd.NA,
                    "low_count_warning": warning,
                    "interpretation_note": STRATIFIED_NOTE,
                }
            )
            continue

        node_scores, global_scores = run_sheafsignal_on_profiles(profiles, lr_db, pathway_genes)
        top = node_scores.sort_values("frustration_score", ascending=False).iloc[0]
        summary_rows.append(
            {
                "lesion_type": lesion_type,
                "status": "completed",
                "n_cells": int(counts["n_cells"].sum()),
                "n_cell_types": int(len(profiles)),
                "top_frustration_cell_type": top["cell_type"],
                "top_frustration_score": top["frustration_score"],
                "gradient_ratio": global_scores["gradient_ratio"],
                "curl_ratio": global_scores["curl_ratio"],
                "harmonic_ratio": global_scores["harmonic_ratio"],
                "total_sheaf_energy": global_scores["total_sheaf_energy"],
                "low_count_warning": warning,
                "interpretation_note": STRATIFIED_NOTE,
            }
        )

        count_map = counts.set_index("cell_type")["n_cells"].to_dict()
        for rank, row in enumerate(node_scores.itertuples(index=False), start=1):
            node_rows.append(
                {
                    "lesion_type": lesion_type,
                    "cell_type": row.cell_type,
                    "n_cells": int(count_map.get(row.cell_type, 0)),
                    "frustration_rank": rank,
                    "frustration_score": row.frustration_score,
                    "outgoing_sheaf_energy": row.outgoing_sheaf_energy,
                    "incoming_sheaf_energy": row.incoming_sheaf_energy,
                    "curl_participation": row.curl_participation,
                    "low_count_flag": int(count_map.get(row.cell_type, 0)) < min_cells_per_type,
                    "interpretation_note": STRATIFIED_NOTE,
                }
            )

        # Recompute edge table for export with lesion label.
        from sheafsignal.core import build_directed_lr_edges, compute_pathway_scores, compute_sheaf_energy
        from sheafsignal.hodge import attach_hodge_components, hodge_decomposition

        pathway_scores = compute_pathway_scores(profiles, pathway_genes)
        edges = compute_sheaf_energy(build_directed_lr_edges(profiles, lr_db), pathway_scores)
        pair_components, _ = hodge_decomposition(edges, flow_col="sheaf_residual")
        edges = attach_hodge_components(edges, pair_components)
        edges.insert(0, "lesion_type", lesion_type)
        edge_rows.append(edges)

    summary = pd.DataFrame(summary_rows).sort_values("lesion_type")
    nodes = pd.DataFrame(node_rows).sort_values(["lesion_type", "frustration_rank"])
    edges = pd.concat(edge_rows, ignore_index=True) if edge_rows else pd.DataFrame()
    return summary, nodes, edges


def plot_lesion_frustration(nodes: pd.DataFrame, output: Path) -> Path:
    plt = _setup_matplotlib()
    table = nodes.copy()
    lesion_types = table["lesion_type"].drop_duplicates().tolist()
    cell_types = table["cell_type"].drop_duplicates().tolist()
    pivot = table.pivot(index="cell_type", columns="lesion_type", values="frustration_score")
    pivot = pivot.reindex(cell_types)

    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    x = range(len(pivot.index))
    width = 0.8 / max(len(lesion_types), 1)
    for idx, lesion_type in enumerate(lesion_types):
        values = pivot[lesion_type].fillna(0.0)
        ax.bar(
            [i + (idx - (len(lesion_types) - 1) / 2) * width for i in x],
            values,
            width=width,
            label=lesion_type,
        )
    ax.set_xticks(list(x))
    ax.set_xticklabels(pivot.index, rotation=35, ha="right")
    ax.set_ylabel("Frustration score")
    ax.set_title("GSE154778 lesion-stratified frustration sources")
    ax.legend(frameon=False)
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output)
    plt.close(fig)
    return output


def run_stratified_analysis(
    *,
    processed_dir: Path,
    raw_path: Path,
    lr_db_path: Path,
    gene_set_path: Path,
    output_dir: Path,
    figure_manifest: Path,
    min_cells_per_type: int,
    max_cells: int | None,
    chunksize: int,
) -> dict[str, Path]:
    metadata_path = processed_dir / "metadata.csv"
    if not metadata_path.exists():
        raise FileNotFoundError(f"Required metadata is missing: {metadata_path}")

    expression = read_selected_expression(
        processed_dir=processed_dir,
        raw_path=raw_path,
        lr_db_path=lr_db_path,
        gene_set_path=gene_set_path,
        max_cells=max_cells,
        chunksize=chunksize,
    )
    metadata = pd.read_csv(metadata_path)
    lr_db = read_ligand_receptor_db(lr_db_path)
    pathway_genes = read_gene_set(gene_set_path)

    summary, nodes, edges = run_lesion_stratified(
        expression=expression,
        metadata=metadata,
        lr_db=lr_db,
        pathway_genes=pathway_genes,
        min_cells_per_type=min_cells_per_type,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "lesion_sheafsignal_summary.csv"
    node_path = output_dir / "lesion_frustration_by_cell_type.csv"
    edge_path = output_dir / "lesion_edge_sheaf_energy.csv"
    figure_path = output_dir / "lesion_frustration_scores.pdf"
    summary.to_csv(summary_path, index=False)
    nodes.to_csv(node_path, index=False)
    edges.to_csv(edge_path, index=False)
    plot_lesion_frustration(nodes, figure_path)
    update_figure_manifest(
        figure_manifest,
        figure_path,
        figure_id="supp_gse154778_lesion_frustration_scores",
    )

    return {
        "summary": summary_path,
        "nodes": node_path,
        "edges": edge_path,
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
    parser.add_argument("--min-cells-per-type", type=int, default=20)
    parser.add_argument("--max-cells", type=int, default=None)
    parser.add_argument("--chunksize", type=int, default=2000)
    args = parser.parse_args(argv)

    dataset_id = args.dataset_id
    processed_dir = resolve_gse154778_processed_dir(dataset_id, args.processed_dir)
    output_dir = Path(args.output_dir or f"benchmarks/results/{dataset_id}/stratified")
    paths = run_stratified_analysis(
        processed_dir=processed_dir,
        raw_path=Path(args.raw_path),
        lr_db_path=Path(args.lr_db),
        gene_set_path=Path(args.gene_set),
        output_dir=output_dir,
        figure_manifest=Path(args.figure_manifest),
        min_cells_per_type=args.min_cells_per_type,
        max_cells=args.max_cells,
        chunksize=args.chunksize,
    )
    for path in paths.values():
        print(f"wrote {path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
