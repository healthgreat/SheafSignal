#!/usr/bin/env python
"""Bootstrap GSE154778 SheafSignal frustration stability."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

import _bootstrap  # noqa: F401
from sheafsignal.adapters import genes_required_for_sheafsignal, read_gse154778_selected_genes
from sheafsignal.core import (
    build_directed_lr_edges,
    compute_node_frustration,
    compute_pathway_scores,
    compute_sheaf_energy,
)
from sheafsignal.hodge import attach_hodge_components, hodge_decomposition
from sheafsignal.io import read_gene_set, read_ligand_receptor_db


BOOTSTRAP_NOTE = (
    "bootstrap over the current frozen annotation version; top frustration "
    "source is a computational stability result, not an independently validated "
    "biological conclusion"
)


def _setup_matplotlib():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def _require(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"Required bootstrap input is missing: {path}")
    return path


def read_selected_expression(
    *,
    processed_dir: Path,
    raw_path: Path,
    lr_db_path: Path,
    gene_set_path: Path,
    max_cells: int | None,
    chunksize: int,
) -> pd.DataFrame:
    required_genes = genes_required_for_sheafsignal(lr_db_path, gene_set_path)
    if raw_path.exists():
        return read_gse154778_selected_genes(
            raw_path,
            genes=required_genes,
            max_cells=max_cells,
            chunksize=chunksize,
        )

    expression_path = _require(processed_dir / "expression.csv")

    def usecols(column: str) -> bool:
        return column == "cell_id" or column in required_genes

    expression = pd.read_csv(expression_path, usecols=usecols)
    if max_cells is not None:
        expression = expression.head(max_cells)
    expression = expression.set_index("cell_id")
    expression.index = expression.index.astype(str)
    return expression.apply(pd.to_numeric, errors="coerce").fillna(0.0)


def bootstrap_profiles(
    expression: pd.DataFrame,
    metadata: pd.DataFrame,
    rng: np.random.Generator,
    cell_type_col: str = "cell_type",
) -> pd.DataFrame:
    metadata = metadata.set_index("cell_id").loc[expression.index].reset_index()
    rows = []
    for cell_type, group in metadata.groupby(cell_type_col, sort=True):
        cell_ids = group["cell_id"].astype(str).to_numpy()
        sampled = rng.choice(cell_ids, size=len(cell_ids), replace=True)
        profile = expression.loc[sampled].mean(axis=0)
        profile.name = str(cell_type)
        rows.append(profile)
    profiles = pd.DataFrame(rows)
    profiles.index.name = "cell_type"
    return profiles


def run_sheafsignal_on_profiles(
    profiles: pd.DataFrame,
    lr_db: pd.DataFrame,
    pathway_genes: list[str],
) -> tuple[pd.DataFrame, dict[str, float]]:
    pathway_scores = compute_pathway_scores(profiles, pathway_genes)
    edges = build_directed_lr_edges(profiles, lr_db)
    edges = compute_sheaf_energy(edges, pathway_scores)
    pair_components, global_scores = hodge_decomposition(edges, flow_col="sheaf_residual")
    edges = attach_hodge_components(edges, pair_components)
    node_scores = compute_node_frustration(edges)
    return node_scores, {
        **global_scores,
        "total_sheaf_energy": float(edges["sheaf_energy"].sum()),
    }


def bootstrap_stability(
    *,
    expression: pd.DataFrame,
    metadata: pd.DataFrame,
    lr_db: pd.DataFrame,
    pathway_genes: list[str],
    n_bootstraps: int,
    random_seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if n_bootstraps <= 0:
        raise ValueError("n_bootstraps must be positive.")

    common = expression.index.astype(str).intersection(metadata["cell_id"].astype(str))
    if len(common) == 0:
        raise ValueError("No overlapping cell IDs between expression and metadata.")
    expression = expression.loc[common].copy()
    metadata = metadata.set_index("cell_id").loc[common].reset_index()
    metadata["cell_id"] = metadata["cell_id"].astype(str)

    rng = np.random.default_rng(random_seed)
    node_rows = []
    global_rows = []
    for iteration in range(1, n_bootstraps + 1):
        profiles = bootstrap_profiles(expression, metadata, rng)
        node_scores, global_scores = run_sheafsignal_on_profiles(profiles, lr_db, pathway_genes)
        node_scores = node_scores.sort_values("frustration_score", ascending=False).reset_index(drop=True)
        top_cell_type = node_scores.iloc[0]["cell_type"]
        for rank, row in enumerate(node_scores.itertuples(index=False), start=1):
            node_rows.append(
                {
                    "bootstrap": iteration,
                    "cell_type": row.cell_type,
                    "frustration_score": row.frustration_score,
                    "frustration_rank": rank,
                    "is_top_frustration_source": row.cell_type == top_cell_type,
                    "outgoing_sheaf_energy": row.outgoing_sheaf_energy,
                    "incoming_sheaf_energy": row.incoming_sheaf_energy,
                    "curl_participation": row.curl_participation,
                    "bootstrap_note": BOOTSTRAP_NOTE,
                }
            )
        global_rows.append(
            {
                "bootstrap": iteration,
                "top_frustration_cell_type": top_cell_type,
                "total_sheaf_energy": global_scores["total_sheaf_energy"],
                "gradient_ratio": global_scores["gradient_ratio"],
                "curl_ratio": global_scores["curl_ratio"],
                "harmonic_ratio": global_scores["harmonic_ratio"],
                "bootstrap_note": BOOTSTRAP_NOTE,
            }
        )

    node_table = pd.DataFrame(node_rows)
    global_table = pd.DataFrame(global_rows)
    summary_rows = []
    for cell_type, group in node_table.groupby("cell_type", sort=True):
        summary_rows.append(
            {
                "cell_type": cell_type,
                "n_bootstraps": int(n_bootstraps),
                "top_frequency": float(group["is_top_frustration_source"].mean()),
                "mean_frustration_score": float(group["frustration_score"].mean()),
                "median_frustration_score": float(group["frustration_score"].median()),
                "q025_frustration_score": float(group["frustration_score"].quantile(0.025)),
                "q975_frustration_score": float(group["frustration_score"].quantile(0.975)),
                "median_frustration_rank": float(group["frustration_rank"].median()),
                "bootstrap_note": BOOTSTRAP_NOTE,
            }
        )
    summary = pd.DataFrame(summary_rows).sort_values(
        ["top_frequency", "median_frustration_score"],
        ascending=[False, False],
    )
    return node_table, global_table, summary


def plot_bootstrap_summary(summary: pd.DataFrame, output: Path) -> Path:
    plt = _setup_matplotlib()
    table = summary.sort_values("top_frequency", ascending=True)
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    ax.barh(table["cell_type"], table["top_frequency"], color="#4C78A8")
    ax.set_xlim(0, 1.0)
    ax.set_xlabel("Top frustration source frequency")
    ax.set_ylabel("Cell type")
    ax.set_title("GSE154778 frustration-source bootstrap stability")
    for idx, value in enumerate(table["top_frequency"]):
        ax.text(min(value + 0.02, 0.98), idx, f"{value:.2f}", va="center", fontsize=8)
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output)
    plt.close(fig)
    return output


def update_figure_manifest(
    manifest_path: Path,
    figure_path: Path,
    figure_id: str = "supp_gse154778_bootstrap_frustration_stability",
) -> Path:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "figure_id": figure_id,
        "path": str(figure_path),
        "source_results_dir": str(figure_path.parent),
    }
    if manifest_path.exists():
        manifest = pd.read_csv(manifest_path, sep="\t")
        manifest = manifest.loc[manifest["figure_id"] != entry["figure_id"]].copy()
    else:
        manifest = pd.DataFrame(columns=["figure_id", "path", "source_results_dir"])
    manifest = pd.concat([manifest, pd.DataFrame([entry])], ignore_index=True)
    manifest.to_csv(manifest_path, sep="\t", index=False)
    return manifest_path


def run_bootstrap(
    *,
    processed_dir: Path,
    raw_path: Path,
    lr_db_path: Path,
    gene_set_path: Path,
    output_dir: Path,
    figure_manifest: Path,
    n_bootstraps: int,
    random_seed: int,
    max_cells: int | None,
    chunksize: int,
) -> dict[str, Path]:
    metadata_path = _require(processed_dir / "metadata.csv")
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

    node_table, global_table, summary = bootstrap_stability(
        expression=expression,
        metadata=metadata,
        lr_db=lr_db,
        pathway_genes=pathway_genes,
        n_bootstraps=n_bootstraps,
        random_seed=random_seed,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    node_path = output_dir / "bootstrap_frustration_by_cell_type.csv"
    global_path = output_dir / "bootstrap_global_scores.csv"
    summary_path = output_dir / "bootstrap_frustration_summary.csv"
    figure_path = output_dir / "bootstrap_frustration_stability.pdf"
    node_table.to_csv(node_path, index=False)
    global_table.to_csv(global_path, index=False)
    summary.to_csv(summary_path, index=False)
    plot_bootstrap_summary(summary, figure_path)
    update_figure_manifest(figure_manifest, figure_path)

    return {
        "node_table": node_path,
        "global_table": global_path,
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
    parser.add_argument("--n-bootstraps", type=int, default=100)
    parser.add_argument("--random-seed", type=int, default=1)
    parser.add_argument("--max-cells", type=int, default=None)
    parser.add_argument("--chunksize", type=int, default=2000)
    args = parser.parse_args(argv)

    dataset_id = args.dataset_id
    processed_dir = Path(args.processed_dir or f"data/processed/{dataset_id}")
    output_dir = Path(args.output_dir or f"benchmarks/results/{dataset_id}/stability")
    paths = run_bootstrap(
        processed_dir=processed_dir,
        raw_path=Path(args.raw_path),
        lr_db_path=Path(args.lr_db),
        gene_set_path=Path(args.gene_set),
        output_dir=output_dir,
        figure_manifest=Path(args.figure_manifest),
        n_bootstraps=args.n_bootstraps,
        random_seed=args.random_seed,
        max_cells=args.max_cells,
        chunksize=args.chunksize,
    )
    for path in paths.values():
        print(f"wrote {path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
