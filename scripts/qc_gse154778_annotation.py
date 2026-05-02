#!/usr/bin/env python
"""Generate GSE154778 annotation QC tables and supplement-ready figures."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

import _bootstrap  # noqa: F401
from sheafsignal.adapters import GSE154778_MARKERS


QC_NOTE = (
    "frozen Scanpy cluster-level marker annotation; frustration rankings are a "
    "computational hypothesis; Unknown and low-margin cells should not be used "
    "as strong biological conclusions"
)


def _setup_matplotlib():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def _require(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"Required GSE154778 QC input is missing: {path}")
    return path


def marker_heatmap_table(profiles: pd.DataFrame) -> pd.DataFrame:
    rows = []
    profile = profiles.set_index("cell_type")
    for marker_group, genes in GSE154778_MARKERS.items():
        for gene in genes:
            if gene not in profile.columns:
                continue
            for cell_type, value in profile[gene].items():
                rows.append(
                    {
                        "cell_type": cell_type,
                        "marker_group": marker_group,
                        "gene": gene,
                        "mean_expression": value,
                    }
                )
    return pd.DataFrame(rows)


def cell_type_counts_table(metadata: pd.DataFrame) -> pd.DataFrame:
    return (
        metadata.groupby(["cell_type", "lesion_type"], dropna=False)
        .size()
        .reset_index(name="n_cells")
        .sort_values(["cell_type", "lesion_type"])
    )


def annotation_confidence_table(metadata: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for cell_type, group in metadata.groupby("cell_type", dropna=False):
        rows.append(
            {
                "cell_type": cell_type,
                "n_cells": int(len(group)),
                "median_marker_score": float(group["marker_score"].median()),
                "median_marker_score_margin": float(group["marker_score_margin"].median()),
                "low_margin_fraction_lt_0_05": float((group["marker_score_margin"] < 0.05).mean()),
                "low_margin_fraction_lt_0_10": float((group["marker_score_margin"] < 0.10).mean()),
                "annotation_qc_note": QC_NOTE,
            }
        )
    return pd.DataFrame(rows).sort_values("n_cells", ascending=False)


def frustration_overlay_table(confidence: pd.DataFrame, hodge_scores: pd.DataFrame) -> pd.DataFrame:
    cell_scores = hodge_scores.loc[hodge_scores["scope"] == "cell_type"].copy()
    required = {"cell_type", "frustration_score", "outgoing_sheaf_energy", "incoming_sheaf_energy"}
    missing = required.difference(cell_scores.columns)
    if missing:
        raise ValueError(f"Hodge score table is missing columns: {sorted(missing)}")
    overlay = confidence.merge(
        cell_scores[
            [
                "cell_type",
                "frustration_score",
                "outgoing_sheaf_energy",
                "incoming_sheaf_energy",
                "curl_participation",
            ]
        ],
        on="cell_type",
        how="left",
    )
    overlay["annotation_qc_note"] = QC_NOTE
    return overlay.sort_values("frustration_score", ascending=False)


def plot_marker_heatmap(table: pd.DataFrame, output: Path) -> Path:
    plt = _setup_matplotlib()
    matrix = table.pivot_table(
        index="cell_type",
        columns="gene",
        values="mean_expression",
        aggfunc="mean",
        fill_value=0.0,
    )
    fig, ax = plt.subplots(figsize=(max(8, 0.32 * len(matrix.columns)), 4.8))
    image = ax.imshow(matrix.to_numpy(dtype=float), aspect="auto", cmap="viridis")
    ax.set_xticks(range(len(matrix.columns)))
    ax.set_xticklabels(matrix.columns, rotation=90, fontsize=7)
    ax.set_yticks(range(len(matrix.index)))
    ax.set_yticklabels(matrix.index, fontsize=9)
    ax.set_title("GSE154778 coarse marker expression by annotated cell type")
    cbar = fig.colorbar(image, ax=ax, fraction=0.025, pad=0.02)
    cbar.set_label("Mean expression")
    fig.tight_layout()
    fig.savefig(output)
    plt.close(fig)
    return output


def plot_cell_type_counts(table: pd.DataFrame, output: Path) -> Path:
    plt = _setup_matplotlib()
    pivot = table.pivot_table(
        index="cell_type",
        columns="lesion_type",
        values="n_cells",
        aggfunc="sum",
        fill_value=0,
    )
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    pivot.plot(kind="bar", stacked=True, ax=ax, color=["#4C78A8", "#F58518", "#54A24B"])
    ax.set_ylabel("Cells")
    ax.set_xlabel("")
    ax.set_title("GSE154778 annotated cell type counts")
    ax.legend(frameon=False, title="Lesion type")
    fig.tight_layout()
    fig.savefig(output)
    plt.close(fig)
    return output


def plot_annotation_confidence(metadata: pd.DataFrame, output: Path) -> Path:
    plt = _setup_matplotlib()
    cell_types = list(metadata["cell_type"].drop_duplicates())
    data = [
        metadata.loc[metadata["cell_type"] == cell_type, "marker_score_margin"].to_numpy(dtype=float)
        for cell_type in cell_types
    ]
    fig, ax = plt.subplots(figsize=(7.8, 4.6))
    ax.boxplot(data, tick_labels=cell_types, showfliers=False)
    ax.axhline(0.05, color="#D62728", linestyle="--", linewidth=1, label="margin = 0.05")
    ax.set_ylabel("Marker score margin")
    ax.set_title("GSE154778 marker annotation confidence")
    ax.tick_params(axis="x", rotation=30)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(output)
    plt.close(fig)
    return output


def plot_frustration_overlay(table: pd.DataFrame, output: Path) -> Path:
    plt = _setup_matplotlib()
    table = table.sort_values("frustration_score", ascending=False)
    fig, ax1 = plt.subplots(figsize=(8.0, 4.8))
    x = list(range(len(table)))
    ax1.bar(x, table["frustration_score"], color="#4C78A8", label="frustration_score")
    ax1.set_ylabel("Frustration score")
    ax1.set_xticks(x)
    ax1.set_xticklabels(table["cell_type"], rotation=30, ha="right")

    ax2 = ax1.twinx()
    ax2.plot(
        x,
        table["median_marker_score_margin"],
        color="#F58518",
        marker="o",
        label="median marker margin",
    )
    ax2.set_ylabel("Median marker margin")
    ax1.set_title("GSE154778 frustration signal over annotation confidence")
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, frameon=False, loc="upper right")
    fig.tight_layout()
    fig.savefig(output)
    plt.close(fig)
    return output


def append_figure_manifest(manifest_path: Path, figure_rows: list[dict[str, str]]) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    new_rows = pd.DataFrame(figure_rows)
    if manifest_path.exists():
        manifest = pd.read_csv(manifest_path, sep="\t")
        manifest = manifest.loc[~manifest["figure_id"].isin(new_rows["figure_id"])]
        manifest = pd.concat([manifest, new_rows], ignore_index=True)
    else:
        manifest = new_rows
    manifest.to_csv(manifest_path, sep="\t", index=False)


def run_qc(
    processed_dir: Path,
    benchmark_dir: Path,
    output_dir: Path,
    manifest_out: Path,
) -> dict[str, Path]:
    profiles = pd.read_csv(_require(processed_dir / "profiles.csv"))
    metadata = pd.read_csv(_require(processed_dir / "metadata.csv"))
    annotation_summary = pd.read_csv(_require(processed_dir / "annotation_summary.csv"))
    hodge_scores = pd.read_csv(_require(benchmark_dir / "results" / "hodge_decomposition_scores.csv"))

    required_meta = {"cell_id", "cell_type", "lesion_type", "marker_score", "marker_score_margin"}
    missing_meta = required_meta.difference(metadata.columns)
    if missing_meta:
        raise ValueError(f"GSE154778 metadata is missing columns: {sorted(missing_meta)}")

    output_dir.mkdir(parents=True, exist_ok=True)
    heatmap = marker_heatmap_table(profiles)
    counts = cell_type_counts_table(metadata)
    confidence = annotation_confidence_table(metadata)
    overlay = frustration_overlay_table(confidence, hodge_scores)

    paths = {
        "marker_heatmap_csv": output_dir / "marker_heatmap.csv",
        "cell_type_counts_csv": output_dir / "cell_type_counts.csv",
        "annotation_confidence_csv": output_dir / "annotation_confidence.csv",
        "frustration_annotation_overlay_csv": output_dir / "frustration_annotation_overlay.csv",
        "qc_summary_csv": output_dir / "qc_summary.csv",
        "marker_heatmap_pdf": output_dir / "marker_heatmap.pdf",
        "cell_type_counts_pdf": output_dir / "cell_type_counts.pdf",
        "annotation_confidence_pdf": output_dir / "annotation_confidence.pdf",
        "frustration_annotation_overlay_pdf": output_dir / "frustration_annotation_overlay.pdf",
    }

    heatmap.to_csv(paths["marker_heatmap_csv"], index=False)
    counts.to_csv(paths["cell_type_counts_csv"], index=False)
    confidence.to_csv(paths["annotation_confidence_csv"], index=False)
    overlay.to_csv(paths["frustration_annotation_overlay_csv"], index=False)

    top = overlay.sort_values("frustration_score", ascending=False).iloc[0]
    qc_summary = pd.DataFrame(
        [
            {
                "dataset_id": "gse154778_pdac_scrna",
                "annotation_method": "frozen Scanpy cluster-level marker annotation",
                "n_cells": int(len(metadata)),
                "n_cell_types": int(metadata["cell_type"].nunique()),
                "n_unknown_cells": int((metadata["cell_type"] == "Unknown").sum()),
                "low_margin_fraction_lt_0_05": float((metadata["marker_score_margin"] < 0.05).mean()),
                "top_frustration_cell_type": top["cell_type"],
                "top_frustration_score": top["frustration_score"],
                "interpretation_warning": QC_NOTE,
            }
        ]
    )
    qc_summary.to_csv(paths["qc_summary_csv"], index=False)

    # Keep annotation_summary loaded and checked; counts is recomputed from metadata.
    if annotation_summary.empty:
        raise ValueError("annotation_summary.csv is empty.")

    plot_marker_heatmap(heatmap, paths["marker_heatmap_pdf"])
    plot_cell_type_counts(counts, paths["cell_type_counts_pdf"])
    plot_annotation_confidence(metadata, paths["annotation_confidence_pdf"])
    plot_frustration_overlay(overlay, paths["frustration_annotation_overlay_pdf"])

    append_figure_manifest(
        manifest_out,
        [
            {
                "figure_id": "supp_gse154778_marker_heatmap",
                "path": str(paths["marker_heatmap_pdf"]),
                "source_results_dir": str(output_dir),
            },
            {
                "figure_id": "supp_gse154778_cell_type_counts",
                "path": str(paths["cell_type_counts_pdf"]),
                "source_results_dir": str(output_dir),
            },
            {
                "figure_id": "supp_gse154778_annotation_confidence",
                "path": str(paths["annotation_confidence_pdf"]),
                "source_results_dir": str(output_dir),
            },
            {
                "figure_id": "supp_gse154778_frustration_overlay",
                "path": str(paths["frustration_annotation_overlay_pdf"]),
                "source_results_dir": str(output_dir),
            },
        ],
    )
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--processed-dir", default="data/processed/gse154778_pdac_scrna")
    parser.add_argument("--benchmark-dir", default="benchmarks/results/gse154778_pdac_scrna")
    parser.add_argument("--output-dir", default="benchmarks/results/gse154778_pdac_scrna/qc")
    parser.add_argument("--manifest-out", default="manuscript/figure_manifest.tsv")
    args = parser.parse_args(argv)

    paths = run_qc(
        processed_dir=Path(args.processed_dir),
        benchmark_dir=Path(args.benchmark_dir),
        output_dir=Path(args.output_dir),
        manifest_out=Path(args.manifest_out),
    )
    for path in paths.values():
        print(f"wrote {path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
