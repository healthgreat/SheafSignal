#!/usr/bin/env python
"""GSE154778 Scanpy reannotation readiness and optional execution scaffold."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import warnings

import numpy as np
import pandas as pd

import _bootstrap  # noqa: F401
from sheafsignal.adapters import GSE154778_MARKERS, parse_gse154778_cell_id


OPTIONAL_PACKAGES = ["scanpy", "anndata", "scrublet", "leidenalg", "igraph"]
RESOLUTIONS = (0.2, 0.4, 0.6, 0.8, 1.0, 1.2)


def _write_text_atomic(path: Path, text: str) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def _append_progress(path: Path, message: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(message + "\n")


def package_present(package: str) -> bool:
    return importlib.util.find_spec(package) is not None


def read_gse154778_full_gene_matrix(
    raw_path: Path,
    *,
    max_cells: int | None = None,
    max_genes: int | None = None,
) -> pd.DataFrame:
    """Read GSE154778 genes x cells CSV.gz and return cells x genes."""
    read_kwargs: dict[str, object] = {"index_col": 0, "compression": "infer"}
    if max_cells is not None:
        if max_cells <= 0:
            raise ValueError("max_cells must be positive when provided.")
        header = pd.read_csv(raw_path, nrows=0, compression="infer")
        read_kwargs["usecols"] = list(header.columns[: max_cells + 1])
    genes_by_cells = pd.read_csv(raw_path, **read_kwargs)
    if max_genes is not None:
        if max_genes <= 0:
            raise ValueError("max_genes must be positive when provided.")
        genes_by_cells = genes_by_cells.iloc[:max_genes, :]
    genes_by_cells.index = genes_by_cells.index.astype(str)
    genes_by_cells.columns = genes_by_cells.columns.astype(str)
    cells_by_genes = genes_by_cells.transpose()
    cells_by_genes.index.name = "cell_id"
    return cells_by_genes.apply(pd.to_numeric, errors="coerce").fillna(0.0)


def build_gse154778_h5ad(
    *,
    raw_path: Path,
    current_metadata_path: Path,
    output_h5ad: Path,
    max_cells: int | None = None,
    max_genes: int | None = None,
) -> Path:
    """Build a full-gene or bounded-smoke AnnData object for reannotation."""
    import anndata as ad
    from scipy import sparse

    expression = read_gse154778_full_gene_matrix(
        raw_path,
        max_cells=max_cells,
        max_genes=max_genes,
    )
    obs = pd.DataFrame(index=expression.index.astype(str))
    obs.index.name = "cell_id"
    parsed = obs.index.to_series().map(parse_gse154778_cell_id).apply(pd.Series)
    parsed.index = obs.index
    obs = pd.concat([obs, parsed], axis=1)
    if current_metadata_path.exists():
        current = pd.read_csv(current_metadata_path)
        if "cell_id" in current.columns:
            current["cell_id"] = current["cell_id"].astype(str)
            current = current.set_index("cell_id")
            obs = obs.join(
                current.add_prefix("coarse_"),
                how="left",
            )
    var = pd.DataFrame(index=expression.columns.astype(str))
    var.index.name = "gene_symbol"
    adata = ad.AnnData(
        X=sparse.csr_matrix(expression.to_numpy(dtype=np.float32)),
        obs=obs,
        var=var,
    )
    adata.var_names_make_unique()
    output_h5ad.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = output_h5ad.with_suffix(output_h5ad.suffix + ".tmp")
    adata.write_h5ad(tmp_path)
    tmp_path.replace(output_h5ad)
    return output_h5ad


def _matrix_sum_per_cell(matrix) -> np.ndarray:
    summed = matrix.sum(axis=1)
    return np.asarray(summed).ravel()


def _matrix_nonzero_per_cell(matrix) -> np.ndarray:
    counts = (matrix > 0).sum(axis=1)
    return np.asarray(counts).ravel()


def _matrix_gene_variance(matrix) -> np.ndarray:
    mean = np.asarray(matrix.mean(axis=0)).ravel()
    if hasattr(matrix, "power"):
        mean_sq = np.asarray(matrix.power(2).mean(axis=0)).ravel()
    else:
        mean_sq = np.asarray(np.square(matrix).mean(axis=0)).ravel()
    return mean_sq - np.square(mean)


def _score_marker_programs(adata, marker_sets: dict[str, list[str]]) -> None:
    import scanpy as sc

    genes = set(adata.var_names.astype(str))
    for label, markers in marker_sets.items():
        available = [gene for gene in markers if gene in genes]
        key = f"score_{label.replace('/', '_').replace(' ', '_')}"
        if available:
            sc.tl.score_genes(adata, gene_list=available, score_name=key, use_raw=False)
        else:
            adata.obs[key] = 0.0


def _marker_gene_set(marker_sets: dict[str, list[str]]) -> set[str]:
    return {marker for markers in marker_sets.values() for marker in markers}


def _label_clusters_from_marker_scores(
    adata,
    *,
    cluster_key: str,
    marker_sets: dict[str, list[str]],
) -> pd.DataFrame:
    score_keys = {
        label: f"score_{label.replace('/', '_').replace(' ', '_')}"
        for label in marker_sets
    }
    rows = []
    grouped = adata.obs.groupby(cluster_key, observed=True)
    for cluster, frame in grouped:
        means = {label: float(frame[key].mean()) for label, key in score_keys.items()}
        ordered = sorted(means.items(), key=lambda item: item[1], reverse=True)
        top_label, top_score = ordered[0]
        second_score = ordered[1][1] if len(ordered) > 1 else 0.0
        margin = top_score - second_score
        label = top_label if margin >= 0.05 or top_score > 0 else "Unknown"
        rows.append(
            {
                "cluster": cluster,
                "reannotated_cell_type": label,
                "top_marker_score": top_score,
                "marker_score_margin": margin,
                "n_cells": int(len(frame)),
            }
        )
    return pd.DataFrame(rows)


def run_scanpy_reannotation(
    *,
    h5ad_path: Path,
    output_dir: Path,
    n_top_genes: int = 2000,
    resolutions: tuple[float, ...] = RESOLUTIONS,
    run_scrublet: bool = True,
    preselect_genes: int | None = None,
    max_pcs: int = 30,
    annotation_version: str = "scanpy_full_v1",
) -> dict[str, Path]:
    """Run a bounded Scanpy reannotation workflow and export reviewer-facing tables."""
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="CUDA path could not be detected",
            category=UserWarning,
        )
        import scanpy as sc

    output_dir.mkdir(parents=True, exist_ok=True)
    progress_path = output_dir / "progress.log"
    _append_progress(progress_path, f"start h5ad={h5ad_path}")
    adata = sc.read_h5ad(h5ad_path)
    _append_progress(progress_path, f"loaded n_obs={adata.n_obs} n_vars={adata.n_vars}")
    adata.obs["n_counts_raw"] = _matrix_sum_per_cell(adata.X)
    adata.obs["n_genes_raw"] = _matrix_nonzero_per_cell(adata.X)
    _append_progress(progress_path, "computed raw qc metrics")

    if run_scrublet:
        import scrublet as scr

        try:
            scrub = scr.Scrublet(adata.X)
            with warnings.catch_warnings():
                warnings.filterwarnings(
                    "ignore",
                    message="invalid value encountered in sqrt",
                    category=RuntimeWarning,
                )
                scores, predicted = scrub.scrub_doublets()
            adata.obs["scrublet_score"] = scores
            adata.obs["scrublet_predicted_doublet"] = predicted
            scrublet_status = "completed"
        except Exception as exc:  # pragma: no cover - defensive for small matrices
            adata.obs["scrublet_score"] = np.nan
            adata.obs["scrublet_predicted_doublet"] = False
            scrublet_status = f"failed:{type(exc).__name__}"
    else:
        adata.obs["scrublet_score"] = np.nan
        adata.obs["scrublet_predicted_doublet"] = False
        scrublet_status = "skipped_by_user"
    _append_progress(progress_path, f"scrublet_status={scrublet_status}")

    sc.pp.filter_cells(adata, min_genes=50)
    sc.pp.filter_genes(adata, min_cells=3)
    _append_progress(progress_path, f"filtered n_obs={adata.n_obs} n_vars={adata.n_vars}")
    gene_preselection_status = "not_applied"
    if preselect_genes is not None and adata.n_vars > preselect_genes:
        if preselect_genes <= 0:
            raise ValueError("preselect_genes must be positive when provided.")
        marker_genes = _marker_gene_set(GSE154778_MARKERS)
        variances = _matrix_gene_variance(adata.X)
        top_n = min(preselect_genes, adata.n_vars)
        top_idx = np.argsort(variances)[-top_n:]
        selected = set(adata.var_names[top_idx].astype(str))
        selected.update(gene for gene in marker_genes if gene in set(adata.var_names))
        selected_mask = adata.var_names.astype(str).isin(selected)
        adata = adata[:, selected_mask].copy()
        gene_preselection_status = (
            f"variance_top_{top_n}_plus_markers;selected={adata.n_vars}"
        )
    _append_progress(progress_path, f"gene_preselection_status={gene_preselection_status}")
    sc.pp.normalize_total(adata, target_sum=1e4)
    sc.pp.log1p(adata)
    _append_progress(progress_path, "normalized_log1p")
    sc.pp.highly_variable_genes(
        adata,
        n_top_genes=min(n_top_genes, max(1, adata.n_vars)),
        flavor="cell_ranger",
    )
    if "highly_variable" in adata.var.columns and adata.var["highly_variable"].any():
        marker_mask = adata.var_names.astype(str).isin(_marker_gene_set(GSE154778_MARKERS))
        adata = adata[:, adata.var["highly_variable"] | marker_mask].copy()
    _append_progress(progress_path, f"hvg_subset n_obs={adata.n_obs} n_vars={adata.n_vars}")
    n_comps = min(max_pcs, max(1, adata.n_obs - 1), max(1, adata.n_vars - 1))
    sc.tl.pca(
        adata,
        n_comps=n_comps,
        svd_solver="randomized",
        random_state=42,
        zero_center=False,
    )
    _append_progress(progress_path, f"pca n_comps={n_comps}")
    sc.pp.neighbors(adata, n_neighbors=min(15, max(2, adata.n_obs - 1)), n_pcs=n_comps)
    _append_progress(progress_path, "neighbors")
    for resolution in resolutions:
        key = f"leiden_{str(resolution).replace('.', '_')}"
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message="In the future, the default backend for leiden",
                category=FutureWarning,
            )
            sc.tl.leiden(adata, resolution=resolution, key_added=key, random_state=42)
        _append_progress(progress_path, f"leiden resolution={resolution}")

    _score_marker_programs(adata, GSE154778_MARKERS)
    _append_progress(progress_path, "marker_scores")
    primary_cluster_key = "leiden_0_6"
    cluster_labels = _label_clusters_from_marker_scores(
        adata,
        cluster_key=primary_cluster_key,
        marker_sets=GSE154778_MARKERS,
    )
    label_map = cluster_labels.set_index("cluster")["reannotated_cell_type"].to_dict()
    adata.obs["scanpy_reannotated_cell_type"] = adata.obs[primary_cluster_key].map(label_map)
    adata.obs["annotation_version"] = annotation_version

    cell_annotations = adata.obs.reset_index().rename(columns={"index": "cell_id"})
    if "cell_id" not in cell_annotations.columns:
        cell_annotations = cell_annotations.rename(columns={cell_annotations.columns[0]: "cell_id"})
    cluster_path = output_dir / "scanpy_cluster_marker_labels.csv"
    cell_path = output_dir / "scanpy_cell_annotations.csv"
    h5ad_out = output_dir / "gse154778_scanpy_reannotated.h5ad"
    run_summary_path = output_dir / "scanpy_reannotation_run_summary.csv"
    coverage_path = output_dir / "scanpy_sample_lesion_annotation_counts.csv"
    cluster_labels.to_csv(cluster_path, index=False)
    cell_annotations.to_csv(cell_path, index=False)
    group_cols = [
        column
        for column in ["sample_id", "lesion_type", "scanpy_reannotated_cell_type"]
        if column in cell_annotations.columns
    ]
    if group_cols:
        (
            cell_annotations.groupby(group_cols, dropna=False)
            .size()
            .reset_index(name="n_cells")
            .to_csv(coverage_path, index=False)
        )
    else:
        pd.DataFrame(columns=["n_cells"]).to_csv(coverage_path, index=False)
    adata.write_h5ad(h5ad_out)
    _append_progress(progress_path, f"wrote_h5ad={h5ad_out}")
    pd.DataFrame(
        [
            {
                "h5ad_input": str(h5ad_path),
                "n_cells_after_filter": int(adata.n_obs),
                "n_genes_after_filter": int(adata.n_vars),
                "n_top_genes": n_top_genes,
                "gene_preselection_status": gene_preselection_status,
                "max_pcs": max_pcs,
                "resolution_sweep": ";".join(str(value) for value in resolutions),
                "primary_cluster_key": primary_cluster_key,
                "scrublet_status": scrublet_status,
                "annotation_version": annotation_version,
                "n_samples_after_filter": (
                    int(adata.obs["sample_id"].nunique()) if "sample_id" in adata.obs.columns else 0
                ),
                "lesion_types_after_filter": (
                    ";".join(sorted(adata.obs["lesion_type"].dropna().astype(str).unique()))
                    if "lesion_type" in adata.obs.columns
                    else ""
                ),
                "dataset_scale": "full" if int(adata.n_obs) >= 10000 else "smoke",
                "status": "completed",
            }
        ]
    ).to_csv(run_summary_path, index=False)
    return {
        "cluster_labels": cluster_path,
        "cell_annotations": cell_path,
        "reannotated_h5ad": h5ad_out,
        "run_summary": run_summary_path,
        "coverage": coverage_path,
    }


def build_reannotation_readiness(
    *,
    raw_path: Path,
    processed_dir: Path,
    output_dir: Path,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for package in OPTIONAL_PACKAGES:
        rows.append(
            {
                "check_id": f"python_package::{package}",
                "status": "pass" if package_present(package) else "missing_dependency",
                "evidence": package,
                "required_action": f"Install {package} in the isolated reannotation environment.",
            }
        )
    for check_id, path, action in [
        (
            "raw_processed_geo_matrix",
            raw_path,
            "Download GSE154778_dgeMtx.csv.gz before full-gene reannotation.",
        ),
        (
            "current_metadata",
            processed_dir / "metadata.csv",
            "Prepare current GSE154778 metadata before reannotation comparison.",
        ),
    ]:
        rows.append(
            {
                "check_id": check_id,
                "status": "pass" if path.exists() else "missing_input",
                "evidence": str(path),
                "required_action": action,
            }
        )
    table = pd.DataFrame(rows)
    table_path = output_dir / "reannotation_readiness.csv"
    report_path = output_dir / "GSE154778_REANNOTATION_READINESS_REPORT.md"
    table.to_csv(table_path, index=False)
    blockers = table.loc[table["status"] != "pass"]
    lines = [
        "# GSE154778 Reannotation Readiness Report",
        "",
        f"- Checks: {len(table)}",
        f"- Blocking/missing checks: {len(blockers)}",
        "- Boundary: Myeloid remains annotation-dependent until Scanpy/Seurat-style independent reannotation is completed.",
        "",
        "## Missing Items",
        "",
    ]
    if blockers.empty:
        lines.append("None. The environment is ready for full Scanpy reannotation.")
    else:
        for row in blockers.to_dict(orient="records"):
            lines.append(
                f"- `{row['check_id']}` `{row['status']}`: {row['required_action']}"
            )
    lines.append("")
    _write_text_atomic(report_path, "\n".join(lines))
    return {"readiness": table_path, "report": report_path}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--raw-path",
        default="data/external/gse154778_pdac_scrna/GSE154778_dgeMtx.csv.gz",
    )
    parser.add_argument("--processed-dir", default="data/processed/gse154778_pdac_scrna")
    parser.add_argument(
        "--output-dir",
        default="benchmarks/results/gse154778_pdac_scrna/reannotation",
    )
    parser.add_argument(
        "--h5ad-path",
        default="data/processed/checkpoints/gse154778_pdac_scrna_full_gene.h5ad",
    )
    parser.add_argument("--build-h5ad", action="store_true")
    parser.add_argument("--run-scanpy", action="store_true")
    parser.add_argument("--max-cells", type=int, default=None)
    parser.add_argument("--max-genes", type=int, default=None)
    parser.add_argument("--n-top-genes", type=int, default=2000)
    parser.add_argument("--skip-scrublet", action="store_true")
    parser.add_argument("--preselect-genes", type=int, default=None)
    parser.add_argument("--max-pcs", type=int, default=30)
    parser.add_argument("--annotation-version", default="scanpy_full_v1")
    args = parser.parse_args(argv)
    paths = build_reannotation_readiness(
        raw_path=Path(args.raw_path),
        processed_dir=Path(args.processed_dir),
        output_dir=Path(args.output_dir),
    )
    if args.build_h5ad:
        paths["h5ad"] = build_gse154778_h5ad(
            raw_path=Path(args.raw_path),
            current_metadata_path=Path(args.processed_dir) / "metadata.csv",
            output_h5ad=Path(args.h5ad_path),
            max_cells=args.max_cells,
            max_genes=args.max_genes,
        )
    if args.run_scanpy:
        if not Path(args.h5ad_path).exists():
            raise FileNotFoundError(
                f"Run with --build-h5ad first or provide --h5ad-path: {args.h5ad_path}"
            )
        paths.update(
            run_scanpy_reannotation(
                h5ad_path=Path(args.h5ad_path),
                output_dir=Path(args.output_dir),
                n_top_genes=args.n_top_genes,
                run_scrublet=not args.skip_scrublet,
                preselect_genes=args.preselect_genes,
                max_pcs=args.max_pcs,
                annotation_version=args.annotation_version,
            )
        )
    for path in paths.values():
        print(f"wrote {path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
