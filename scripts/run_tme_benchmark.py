#!/usr/bin/env python
"""Run the standardized TME benchmark tables for SheafSignal."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

import _bootstrap  # noqa: F401
from sheafsignal.comparators import (
    LR_PRODUCT_BASELINE,
    align_sheaf_edges_with_comparator,
    comparator_summary,
    lr_product_baseline_from_sheaf_edges,
)
from sheafsignal.hodge import hodge_decomposition
from sheafsignal.manifest import load_dataset_manifest, validate_dataset_manifest
from sheafsignal.pipeline import run_pipeline, run_profile_pipeline
from sheafsignal.simulate import scenario_edges
from sheafsignal.spatial import run_spatial_hotspot_pipeline


EXTERNAL_COMPARATOR_TOOLS = ["CellChat", "CellPhoneDB", "NicheNet", "LIANA", "niche-DE"]
SCENARIOS = ["gradient_chain", "triangle_curl", "harmonic_ring", "mixed"]
PLACEHOLDER_COMPARATOR_STATUSES = {
    "not_run_requires_external_tool",
    "not_run_missing_sheafsignal_edges",
}


def _expected_component(scenario: str) -> str:
    return {
        "gradient_chain": "gradient_ratio",
        "triangle_curl": "curl_ratio",
        "harmonic_ring": "harmonic_ratio",
        "mixed": "mixed",
    }[scenario]


def write_component_recovery(results_dir: Path) -> Path:
    rows = []
    for scenario in SCENARIOS:
        edges = scenario_edges(scenario)
        _, scores = hodge_decomposition(edges)
        rows.append(
            {
                "scenario": scenario,
                "expected_dominant_component": _expected_component(scenario),
                **scores,
            }
        )
    output = results_dir / "component_recovery.csv"
    pd.DataFrame(rows).to_csv(output, index=False)
    return output


def _select_permutation_strata(metadata_path: Path) -> tuple[str | None, str]:
    if not metadata_path.exists():
        return None, "missing_metadata"
    try:
        metadata = pd.read_csv(metadata_path, nrows=5000)
    except Exception as exc:  # pragma: no cover - defensive for malformed external inputs
        return None, f"metadata_read_failed:{type(exc).__name__}"
    if "sample_id" not in metadata.columns:
        return None, "exploratory_no_sample_id"
    sample_ids = metadata["sample_id"].dropna().astype(str)
    if sample_ids.nunique() < 2:
        return None, "exploratory_single_sample"
    return "sample_id", "sample_stratified"


def _run_dataset(row: dict[str, object], results_dir: Path, n_permutations: int) -> dict[str, object]:
    dataset_id = str(row["dataset_id"])
    expression = Path(str(row["prepared_expression"]))
    metadata = Path(str(row["prepared_metadata"]))
    profile = expression.parent / "profiles.csv"
    has_expression = expression.exists() and metadata.exists()
    if not profile.exists() and not has_expression:
        return {
            "dataset_id": dataset_id,
            "modality": row.get("modality", ""),
            "disease": row.get("disease", ""),
            "status": "missing_prepared_data",
            "n_edges": 0,
            "n_cell_types": 0,
            "total_sheaf_energy": pd.NA,
            "gradient_ratio": pd.NA,
            "curl_ratio": pd.NA,
            "harmonic_ratio": pd.NA,
            "top_frustration_cell_type": "",
            "top_frustration_score": pd.NA,
        }

    project_dir = results_dir / dataset_id
    permutation_strata_col, permutation_design = _select_permutation_strata(metadata)
    if n_permutations > 0 and has_expression:
        result = run_pipeline(
            expression_path=expression,
            metadata_path=metadata,
            lr_db_path="metadata/tme_ligand_receptor.csv",
            gene_set_path="metadata/tme_pathway_genes.txt",
            project_dir=project_dir,
            make_plot=False,
            n_permutations=n_permutations,
            random_seed=1,
            permutation_strata_col=permutation_strata_col,
        )
        input_mode = "expression_with_permutation"
    elif profile.exists():
        result = run_profile_pipeline(
            profile_path=profile,
            lr_db_path="metadata/tme_ligand_receptor.csv",
            gene_set_path="metadata/tme_pathway_genes.txt",
            project_dir=project_dir,
            make_plot=False,
        )
        input_mode = "profile"
    else:
        result = run_pipeline(
            expression_path=expression,
            metadata_path=metadata,
            lr_db_path="metadata/tme_ligand_receptor.csv",
            gene_set_path="metadata/tme_pathway_genes.txt",
            project_dir=project_dir,
            make_plot=False,
            n_permutations=n_permutations,
            random_seed=1,
            permutation_strata_col=permutation_strata_col,
        )
        input_mode = "expression"
    scores = pd.read_csv(result.score_path)
    global_row = scores.loc[scores["scope"] == "global"].iloc[0]
    cell_rows = scores.loc[scores["scope"] == "cell_type"].copy()
    top = cell_rows.sort_values("frustration_score", ascending=False).iloc[0]
    return {
        "dataset_id": dataset_id,
        "modality": row.get("modality", ""),
        "disease": row.get("disease", ""),
        "status": "completed",
        "input_mode": input_mode,
        "n_edges": result.n_edges,
        "n_cell_types": result.n_cell_types,
        "total_sheaf_energy": global_row["total_sheaf_energy"],
        "gradient_ratio": global_row["gradient_ratio"],
        "curl_ratio": global_row["curl_ratio"],
        "harmonic_ratio": global_row["harmonic_ratio"],
        "top_frustration_cell_type": top["cell_type"],
        "top_frustration_score": top["frustration_score"],
        "n_permutations": n_permutations if has_expression else 0,
        "permutation_strata_col": permutation_strata_col or "",
        "permutation_design": permutation_design,
    }


def _run_lr_product_baseline(dataset_id: str, results_dir: Path) -> dict[str, object]:
    dataset_dir = results_dir / dataset_id
    sheaf_edge_path = dataset_dir / "results" / "sheaf_energy_by_edge.csv"
    comparator_dir = dataset_dir / "comparators"
    baseline_path = comparator_dir / "lr_product_baseline_edges.csv"
    aligned_path = comparator_dir / "sheafsignal_vs_lr_product_baseline.csv"

    if not sheaf_edge_path.exists():
        return {
            "dataset_id": dataset_id,
            "tool": LR_PRODUCT_BASELINE,
            "status": "not_run_missing_sheafsignal_edges",
            "comparison_level": "cell_type_edge",
            "edge_score_table": "",
            "aligned_edge_table": "",
            "n_edges": pd.NA,
            "spearman_sheaf_energy_vs_tool_score": pd.NA,
            "high_sheaf_low_tool_edges": pd.NA,
            "high_tool_low_sheaf_edges": pd.NA,
            "concordant_high_edges": pd.NA,
            "unaligned_edges": pd.NA,
            "notes": "LR-product baseline requires a completed SheafSignal edge table.",
        }

    comparator_dir.mkdir(parents=True, exist_ok=True)
    sheaf_edges = pd.read_csv(sheaf_edge_path)
    baseline = lr_product_baseline_from_sheaf_edges(sheaf_edges)
    aligned = align_sheaf_edges_with_comparator(sheaf_edges, baseline, tool=LR_PRODUCT_BASELINE)
    baseline.insert(0, "dataset_id", dataset_id)
    aligned.insert(0, "dataset_id", dataset_id)
    baseline.to_csv(baseline_path, index=False)
    aligned.to_csv(aligned_path, index=False)

    summary = comparator_summary(aligned)
    return {
        "dataset_id": dataset_id,
        "tool": LR_PRODUCT_BASELINE,
        "status": "completed",
        "comparison_level": "cell_type_edge",
        "edge_score_table": str(baseline_path),
        "aligned_edge_table": str(aligned_path),
        "notes": (
            "Internal conventional CCC baseline: ligand expression x receptor "
            "expression edge strength aligned against SheafSignal sheaf_energy."
        ),
        **summary,
    }


def write_tool_comparison(summary: pd.DataFrame, results_dir: Path) -> Path:
    rows = []
    for row in summary.to_dict(orient="records"):
        dataset_id = str(row["dataset_id"])
        rows.append(_run_lr_product_baseline(dataset_id, results_dir))
        for tool in EXTERNAL_COMPARATOR_TOOLS:
            rows.append(
                {
                    "dataset_id": dataset_id,
                    "tool": tool,
                    "status": "not_run_requires_external_tool",
                    "comparison_level": "cell_type_edge",
                    "edge_score_table": "",
                    "aligned_edge_table": "",
                    "n_edges": pd.NA,
                    "spearman_sheaf_energy_vs_tool_score": pd.NA,
                    "high_sheaf_low_tool_edges": pd.NA,
                    "high_tool_low_sheaf_edges": pd.NA,
                    "concordant_high_edges": pd.NA,
                    "unaligned_edges": pd.NA,
                    "notes": "Comparator adapter placeholder for publication benchmark.",
                }
            )
    output = results_dir / "tool_comparison.csv"
    table = pd.DataFrame(rows)
    table = _preserve_existing_external_comparators(table, output)
    table.to_csv(output, index=False)
    return output


def _preserve_existing_external_comparators(table: pd.DataFrame, output: Path) -> pd.DataFrame:
    """Keep completed external comparator imports when refreshing benchmarks."""
    if not output.exists():
        return table
    existing = pd.read_csv(output)
    required = {"dataset_id", "tool", "status"}
    if not required.issubset(existing.columns):
        return table

    protected = existing.loc[
        (existing["tool"] != LR_PRODUCT_BASELINE)
        & (~existing["status"].isin(PLACEHOLDER_COMPARATOR_STATUSES))
    ].copy()
    if protected.empty:
        return table

    columns = list(dict.fromkeys([*table.columns, *protected.columns]))
    refreshed = table.reindex(columns=columns)
    protected = protected.reindex(columns=columns)
    key_columns = ["dataset_id", "tool"]
    protected_keys = pd.MultiIndex.from_frame(protected[key_columns].astype(str))
    refreshed_keys = pd.MultiIndex.from_frame(refreshed[key_columns].astype(str))
    refreshed = refreshed.loc[~refreshed_keys.isin(protected_keys)]
    frames = [frame.dropna(axis=1, how="all") for frame in [refreshed, protected]]
    return pd.concat(frames, ignore_index=True).reindex(columns=columns)


def write_spatial_hotspots(
    manifest: pd.DataFrame,
    results_dir: Path,
    dataset_ids: set[str] | None = None,
) -> Path:
    results_dir.mkdir(parents=True, exist_ok=True)
    columns = [
        "dataset_id",
        "status",
        "spot_id",
        "x",
        "y",
        "frustration_score",
        "notes",
    ]
    rows = []
    spatial_rows = manifest.loc[manifest["benchmark_role"] == "public_spatial_benchmark"]
    if dataset_ids is not None:
        spatial_rows = spatial_rows.loc[spatial_rows["dataset_id"].astype(str).isin(dataset_ids)]
    for row in spatial_rows.to_dict(orient="records"):
        dataset_id = str(row["dataset_id"])
        expression = Path(str(row["prepared_expression"]))
        metadata = Path(str(row["prepared_metadata"]))
        if not expression.exists() or not metadata.exists():
            rows.append(
                {
                    "dataset_id": dataset_id,
                    "status": "missing_prepared_spatial_data",
                    "spot_id": "",
                    "x": pd.NA,
                    "y": pd.NA,
                    "frustration_score": pd.NA,
                    "notes": "Spatial hotspot export will run after Visium coordinates are prepared.",
                }
            )
            continue

        spatial_dir = results_dir / dataset_id / "spatial"
        _, hotspot_path, _ = run_spatial_hotspot_pipeline(
            expression_path=expression,
            metadata_path=metadata,
            lr_db_path="metadata/tme_ligand_receptor.csv",
            gene_set_path="metadata/tme_pathway_genes.txt",
            output_dir=spatial_dir,
            dataset_id=dataset_id,
        )
        rows.extend(pd.read_csv(hotspot_path).to_dict(orient="records"))
    output = results_dir / "spatial_frustration_hotspots.csv"
    pd.DataFrame(rows, columns=columns if not rows else None).to_csv(output, index=False)
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="metadata/datasets.tsv")
    parser.add_argument("--results-dir", default="benchmarks/results")
    parser.add_argument("--include-demo", action="store_true")
    parser.add_argument("--dataset-id", action="append", default=[])
    parser.add_argument("--n-permutations", type=int, default=0)
    parser.add_argument(
        "--manuscript-grade",
        action="store_true",
        help="Use the manuscript-grade default of 1000 stratified permutations when possible.",
    )
    args = parser.parse_args(argv)
    if args.manuscript_grade and args.n_permutations == 0:
        args.n_permutations = 1000

    validate_dataset_manifest(args.manifest, require_public_downloads=False)
    manifest = load_dataset_manifest(args.manifest)
    results_dir = Path(args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)

    component_path = write_component_recovery(results_dir)
    run_rows = manifest.loc[manifest["benchmark_role"].str.startswith("public_")].copy()
    if args.dataset_id:
        selected = set(args.dataset_id)
        run_rows = run_rows.loc[run_rows["dataset_id"].isin(selected)].copy()
    if args.include_demo:
        run_rows = pd.concat(
            [manifest.loc[manifest["dataset_id"] == "demo_synthetic"], run_rows],
            ignore_index=True,
        )

    summary = pd.DataFrame(
        [_run_dataset(row, results_dir, args.n_permutations) for row in run_rows.to_dict(orient="records")]
    )
    summary_path = results_dir / "public_tme_sheafsignal_summary.csv"
    summary.to_csv(summary_path, index=False)
    tool_path = write_tool_comparison(summary, results_dir)
    spatial_dataset_ids = set(run_rows["dataset_id"].astype(str).tolist()) if args.dataset_id else None
    spatial_path = write_spatial_hotspots(manifest, results_dir, dataset_ids=spatial_dataset_ids)

    print(f"wrote {component_path.resolve()}")
    print(f"wrote {summary_path.resolve()}")
    print(f"wrote {tool_path.resolve()}")
    print(f"wrote {spatial_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
