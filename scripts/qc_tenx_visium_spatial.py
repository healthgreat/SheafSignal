#!/usr/bin/env python
"""Generate 10x breast Visium spatial hotspot QC tables and figures."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

import _bootstrap  # noqa: F401
from sheafsignal.io import read_expression, read_gene_set, read_ligand_receptor_db, read_metadata
from sheafsignal.spatial import compute_spatial_sheaf_edges, summarize_spatial_hotspots


QC_NOTE = (
    "marker-dominant Visium spot programs; use as spatial hotspot QC context, "
    "not as single-cell-level cell type proof"
)


def _setup_matplotlib():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def _require(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"Required Visium QC input is missing: {path}")
    return path


def marker_spot_counts_table(metadata: pd.DataFrame) -> pd.DataFrame:
    """Summarize marker-dominant spot-program support."""
    rows = []
    for cell_type, group in metadata.groupby("cell_type", dropna=False):
        rows.append(
            {
                "cell_type": str(cell_type),
                "n_spots": int(len(group)),
                "spot_fraction": float(len(group) / len(metadata)),
                "median_marker_score": float(group["marker_score"].median()),
                "median_marker_score_margin": float(group["marker_score_margin"].median()),
                "low_margin_fraction_lt_0_05": float((group["marker_score_margin"] < 0.05).mean()),
                "qc_note": QC_NOTE,
            }
        )
    return pd.DataFrame(rows).sort_values("n_spots", ascending=False)


def hotspot_marker_overlay_table(hotspots: pd.DataFrame) -> pd.DataFrame:
    """Aggregate spatial hotspot scores by marker-dominant spot program."""
    rows = []
    for cell_type, group in hotspots.groupby("cell_type", dropna=False):
        rows.append(
            {
                "cell_type": str(cell_type),
                "n_spots": int(len(group)),
                "total_frustration_score": float(group["frustration_score"].sum()),
                "mean_frustration_score": float(group["frustration_score"].mean()),
                "median_frustration_score": float(group["frustration_score"].median()),
                "p95_frustration_score": float(group["frustration_score"].quantile(0.95)),
                "top_hotspot_spot_id": str(
                    group.sort_values("frustration_score", ascending=False).iloc[0]["spot_id"]
                ),
                "qc_note": QC_NOTE,
            }
        )
    return pd.DataFrame(rows).sort_values("total_frustration_score", ascending=False)


def k_neighbors_sensitivity_table(
    expression: pd.DataFrame,
    metadata: pd.DataFrame,
    lr_db: pd.DataFrame,
    pathway_genes: list[str],
    dataset_id: str,
    k_values: list[int],
    reference_k: int,
    top_n: int = 50,
) -> pd.DataFrame:
    """Run spatial hotspot scoring across k-neighbor values."""
    if reference_k not in k_values:
        k_values = sorted(set(k_values + [reference_k]))
    if top_n <= 0:
        raise ValueError("top_n must be positive.")

    hotspot_by_k: dict[int, pd.DataFrame] = {}
    summary_rows = []
    for k in sorted(set(k_values)):
        edges = compute_spatial_sheaf_edges(
            expression=expression,
            metadata=metadata,
            lr_db=lr_db,
            pathway_genes=pathway_genes,
            k_neighbors=k,
        )
        hotspots = summarize_spatial_hotspots(edges, metadata, dataset_id=dataset_id)
        hotspot_by_k[k] = hotspots
        top = hotspots.iloc[0]
        summary_rows.append(
            {
                "dataset_id": dataset_id,
                "k_neighbors": int(k),
                "n_spots": int(metadata.shape[0]),
                "n_spatial_edges": int(edges.shape[0]),
                "total_spatial_sheaf_energy": float(edges["sheaf_energy"].sum()),
                "top_hotspot_spot_id": str(top["spot_id"]),
                "top_hotspot_score": float(top["frustration_score"]),
                "median_hotspot_score": float(hotspots["frustration_score"].median()),
                "p95_hotspot_score": float(hotspots["frustration_score"].quantile(0.95)),
            }
        )

    reference = hotspot_by_k[reference_k][["spot_id", "frustration_score"]].rename(
        columns={"frustration_score": "reference_frustration_score"}
    )
    reference_top = set(hotspot_by_k[reference_k].head(top_n)["spot_id"].astype(str))
    rows = []
    for row in summary_rows:
        k = int(row["k_neighbors"])
        current = hotspot_by_k[k][["spot_id", "frustration_score"]].rename(
            columns={"frustration_score": "current_frustration_score"}
        )
        merged = reference.merge(current, on="spot_id", how="inner")
        current_top = set(hotspot_by_k[k].head(top_n)["spot_id"].astype(str))
        row["reference_k_neighbors"] = int(reference_k)
        row[f"top_{top_n}_overlap_with_reference"] = float(
            len(reference_top.intersection(current_top)) / min(top_n, len(reference_top))
        )
        row["spearman_with_reference"] = float(
            merged["reference_frustration_score"].corr(
                merged["current_frustration_score"],
                method="spearman",
            )
        )
        row["qc_note"] = (
            "k-neighbor sensitivity for spot-level spatial sheaf hotspots; "
            "stable hotspot ranks support localization robustness"
        )
        rows.append(row)
    return pd.DataFrame(rows).sort_values("k_neighbors")


def plot_marker_spot_counts(table: pd.DataFrame, output: Path) -> Path:
    plt = _setup_matplotlib()
    table = table.sort_values("n_spots", ascending=True)
    colors = ["#4C78A8" if n >= 50 else "#D62728" for n in table["n_spots"]]
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    ax.barh(table["cell_type"], table["n_spots"], color=colors)
    ax.set_xlabel("In-tissue spots")
    ax.set_title("10x breast Visium marker-dominant spot programs")
    fig.tight_layout()
    fig.savefig(output)
    plt.close(fig)
    return output


def plot_hotspot_spatial_scatter(hotspots: pd.DataFrame, output: Path) -> Path:
    plt = _setup_matplotlib()
    fig, ax = plt.subplots(figsize=(6.4, 6.4))
    values = hotspots["frustration_score"].to_numpy(dtype=float)
    scatter = ax.scatter(
        hotspots["x"],
        -hotspots["y"],
        c=values,
        s=10,
        cmap="magma",
        linewidths=0,
    )
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title("10x breast Visium spatial frustration hotspots")
    cbar = fig.colorbar(scatter, ax=ax, fraction=0.035, pad=0.02)
    cbar.set_label("Spot frustration score")
    fig.tight_layout()
    fig.savefig(output)
    plt.close(fig)
    return output


def plot_hotspot_marker_overlay(table: pd.DataFrame, output: Path) -> Path:
    plt = _setup_matplotlib()
    table = table.sort_values("total_frustration_score", ascending=True)
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    ax.barh(table["cell_type"], table["total_frustration_score"], color="#4C78A8")
    ax.set_xlabel("Total spot-level frustration score")
    ax.set_title("Spatial hotspot burden by marker-dominant program")
    fig.tight_layout()
    fig.savefig(output)
    plt.close(fig)
    return output


def plot_k_neighbors_sensitivity(table: pd.DataFrame, output: Path, top_n: int = 50) -> Path:
    plt = _setup_matplotlib()
    fig, ax1 = plt.subplots(figsize=(7.0, 4.4))
    ax1.plot(
        table["k_neighbors"],
        table["spearman_with_reference"],
        marker="o",
        color="#4C78A8",
        label="Spearman vs reference",
    )
    ax1.set_xlabel("k neighbors")
    ax1.set_ylabel("Spearman correlation")
    ax1.set_ylim(0, 1.05)

    ax2 = ax1.twinx()
    overlap_col = f"top_{top_n}_overlap_with_reference"
    ax2.plot(
        table["k_neighbors"],
        table[overlap_col],
        marker="s",
        color="#F58518",
        label=f"Top {top_n} overlap",
    )
    ax2.set_ylabel(f"Top {top_n} overlap")
    ax2.set_ylim(0, 1.05)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, frameon=False, loc="lower right")
    ax1.set_title("10x breast Visium hotspot sensitivity to k neighbors")
    fig.tight_layout()
    fig.savefig(output)
    plt.close(fig)
    return output


def run_qc(
    expression_path: Path,
    metadata_path: Path,
    hotspot_path: Path,
    lr_db_path: Path,
    gene_set_path: Path,
    output_dir: Path,
    dataset_id: str,
    k_values: list[int],
    reference_k: int,
    top_n: int,
) -> dict[str, Path]:
    expression = read_expression(_require(expression_path))
    metadata = read_metadata(_require(metadata_path)).reset_index(drop=True)
    hotspots = pd.read_csv(_require(hotspot_path))
    lr_db = read_ligand_receptor_db(_require(lr_db_path))
    pathway_genes = read_gene_set(_require(gene_set_path))
    output_dir.mkdir(parents=True, exist_ok=True)

    counts = marker_spot_counts_table(metadata)
    overlay = hotspot_marker_overlay_table(hotspots)
    sensitivity = k_neighbors_sensitivity_table(
        expression=expression,
        metadata=metadata,
        lr_db=lr_db,
        pathway_genes=pathway_genes,
        dataset_id=dataset_id,
        k_values=k_values,
        reference_k=reference_k,
        top_n=top_n,
    )
    summary = pd.DataFrame(
        [
            {
                "dataset_id": dataset_id,
                "qc_scope": "Visium spatial hotspot QC",
                "n_spots": int(metadata.shape[0]),
                "n_marker_programs": int(metadata["cell_type"].nunique()),
                "reference_k_neighbors": int(reference_k),
                "top_hotspot_spot_id": str(hotspots.iloc[0]["spot_id"]),
                "top_hotspot_score": float(hotspots.iloc[0]["frustration_score"]),
                "min_spearman_across_k": float(sensitivity["spearman_with_reference"].min()),
                f"min_top_{top_n}_overlap_across_k": float(
                    sensitivity[f"top_{top_n}_overlap_with_reference"].min()
                ),
                "interpretation_warning": QC_NOTE,
            }
        ]
    )

    paths = {
        "marker_spot_counts_csv": output_dir / "marker_spot_counts.csv",
        "hotspot_marker_overlay_csv": output_dir / "hotspot_marker_overlay.csv",
        "k_neighbors_sensitivity_csv": output_dir / "k_neighbors_sensitivity.csv",
        "spatial_hotspot_qc_summary_csv": output_dir / "spatial_hotspot_qc_summary.csv",
        "marker_spot_counts_pdf": output_dir / "marker_spot_counts.pdf",
        "hotspot_spatial_scatter_pdf": output_dir / "hotspot_spatial_scatter.pdf",
        "hotspot_marker_overlay_pdf": output_dir / "hotspot_marker_overlay.pdf",
        "k_neighbors_sensitivity_pdf": output_dir / "k_neighbors_sensitivity.pdf",
    }
    counts.to_csv(paths["marker_spot_counts_csv"], index=False)
    overlay.to_csv(paths["hotspot_marker_overlay_csv"], index=False)
    sensitivity.to_csv(paths["k_neighbors_sensitivity_csv"], index=False)
    summary.to_csv(paths["spatial_hotspot_qc_summary_csv"], index=False)

    plot_marker_spot_counts(counts, paths["marker_spot_counts_pdf"])
    plot_hotspot_spatial_scatter(hotspots, paths["hotspot_spatial_scatter_pdf"])
    plot_hotspot_marker_overlay(overlay, paths["hotspot_marker_overlay_pdf"])
    plot_k_neighbors_sensitivity(
        sensitivity,
        paths["k_neighbors_sensitivity_pdf"],
        top_n=top_n,
    )
    return paths


def _parse_k_values(value: str) -> list[int]:
    parsed = [int(item.strip()) for item in value.split(",") if item.strip()]
    if not parsed:
        raise ValueError("At least one k-neighbor value is required.")
    if any(item <= 0 for item in parsed):
        raise ValueError("All k-neighbor values must be positive.")
    return sorted(set(parsed))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expression", default="data/processed/tenx_breast_visium/expression.csv")
    parser.add_argument("--metadata", default="data/processed/tenx_breast_visium/metadata.csv")
    parser.add_argument(
        "--hotspots",
        default="benchmarks/results/tenx_breast_visium/spatial/spatial_frustration_hotspots.csv",
    )
    parser.add_argument("--lr-db", default="metadata/tme_ligand_receptor.csv")
    parser.add_argument("--gene-set", default="metadata/tme_pathway_genes.txt")
    parser.add_argument("--output-dir", default="benchmarks/results/tenx_breast_visium/spatial/qc")
    parser.add_argument("--dataset-id", default="tenx_breast_visium")
    parser.add_argument("--k-values", default="4,6,8,10,12")
    parser.add_argument("--reference-k", type=int, default=6)
    parser.add_argument("--top-n", type=int, default=50)
    args = parser.parse_args(argv)

    paths = run_qc(
        expression_path=Path(args.expression),
        metadata_path=Path(args.metadata),
        hotspot_path=Path(args.hotspots),
        lr_db_path=Path(args.lr_db),
        gene_set_path=Path(args.gene_set),
        output_dir=Path(args.output_dir),
        dataset_id=args.dataset_id,
        k_values=_parse_k_values(args.k_values),
        reference_k=args.reference_k,
        top_n=args.top_n,
    )
    for path in paths.values():
        print(f"wrote {path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
