from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from .core import (
    build_directed_lr_edges,
    compute_node_frustration,
    compute_pathway_scores,
    compute_sheaf_energy,
    make_cell_type_profiles,
    normalize_expression,
)
from .hodge import attach_hodge_components, hodge_decomposition
from .io import read_expression, read_gene_set, read_ligand_receptor_db, read_metadata
from .plotting import plot_communication_network
from .provenance import write_provenance
from .sheaf import build_lr_channel_sheaf, sheaf_laplacian
from .stats import permutation_test


@dataclass(frozen=True)
class PipelineResult:
    edge_path: Path
    score_path: Path
    figure_path: Path | None
    edge_permutation_path: Path | None
    node_permutation_path: Path | None
    global_permutation_path: Path | None
    provenance_path: Path | None
    n_edges: int
    n_cell_types: int


def _assemble_score_table(
    global_scores: dict[str, float],
    node_scores: pd.DataFrame,
    total_sheaf_energy: float,
    communication_global_scores: dict[str, float] | None = None,
) -> pd.DataFrame:
    communication_global_scores = communication_global_scores or {}
    rows = [
        {
            "scope": "global",
            "cell_type": "all",
            "gradient_ratio": global_scores["gradient_ratio"],
            "curl_ratio": global_scores["curl_ratio"],
            "harmonic_ratio": global_scores["harmonic_ratio"],
            "frustration_gradient_ratio": global_scores["gradient_ratio"],
            "frustration_curl_ratio": global_scores["curl_ratio"],
            "frustration_harmonic_ratio": global_scores["harmonic_ratio"],
            "communication_gradient_ratio": communication_global_scores.get("gradient_ratio", np.nan),
            "communication_curl_ratio": communication_global_scores.get("curl_ratio", np.nan),
            "communication_harmonic_ratio": communication_global_scores.get("harmonic_ratio", np.nan),
            "frustration_score": np.nan,
            "outgoing_sheaf_energy": np.nan,
            "incoming_sheaf_energy": np.nan,
            "curl_participation": np.nan,
            "total_sheaf_energy": total_sheaf_energy,
            "total_flow_energy": global_scores["total_flow_energy"],
            "n_pair_edges": global_scores["n_pair_edges"],
            "n_triangles": global_scores["n_triangles"],
        }
    ]

    for row in node_scores.itertuples(index=False):
        rows.append(
            {
                "scope": "cell_type",
                "cell_type": row.cell_type,
                "gradient_ratio": np.nan,
                "curl_ratio": np.nan,
                "harmonic_ratio": np.nan,
                "frustration_gradient_ratio": np.nan,
                "frustration_curl_ratio": np.nan,
                "frustration_harmonic_ratio": np.nan,
                "communication_gradient_ratio": np.nan,
                "communication_curl_ratio": np.nan,
                "communication_harmonic_ratio": np.nan,
                "frustration_score": row.frustration_score,
                "outgoing_sheaf_energy": row.outgoing_sheaf_energy,
                "incoming_sheaf_energy": row.incoming_sheaf_energy,
                "curl_participation": row.curl_participation,
                "total_sheaf_energy": total_sheaf_energy,
                "total_flow_energy": global_scores["total_flow_energy"],
                "n_pair_edges": global_scores["n_pair_edges"],
                "n_triangles": global_scores["n_triangles"],
            }
        )
    return pd.DataFrame(rows)


def _attach_prefixed_hodge_components(
    edges: pd.DataFrame,
    pair_components: pd.DataFrame,
    prefix: str,
) -> pd.DataFrame:
    attached = attach_hodge_components(edges, pair_components)
    rename = {
        "pair_net_flow": f"{prefix}_pair_net_flow",
        "gradient_component": f"{prefix}_gradient_component",
        "curl_component": f"{prefix}_curl_component",
        "harmonic_component": f"{prefix}_harmonic_component",
    }
    keep = [column for column in rename if column in attached.columns]
    extras = attached[["sender", "receiver", *keep]].rename(columns=rename)
    return edges.merge(extras, on=["sender", "receiver"], how="left")


def _attach_dual_hodge(edges: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, float], dict[str, float]]:
    communication_pairs, communication_scores = hodge_decomposition(edges, flow_col="flow_z")
    edges = _attach_prefixed_hodge_components(edges, communication_pairs, "communication_hodge")

    frustration_pairs, frustration_scores = hodge_decomposition(edges, flow_col="sheaf_residual")
    edges = attach_hodge_components(edges, frustration_pairs)
    for column in ["gradient_component", "curl_component", "harmonic_component", "pair_net_flow"]:
        if column in edges.columns:
            edges[f"frustration_hodge_{column}"] = edges[column]
    return edges, frustration_scores, communication_scores


def _write_sheaf_contract_tables(
    edges: pd.DataFrame,
    results_dir: Path,
    profiles: pd.DataFrame | None = None,
    lr_db: pd.DataFrame | None = None,
    pathway_scores: pd.DataFrame | None = None,
) -> tuple[Path, Path]:
    sheaf = sheaf_laplacian(edges)
    restriction_path = results_dir / "cellular_sheaf_restrictions.csv"
    laplacian_path = results_dir / "cellular_sheaf_laplacian.csv"
    sheaf.restrictions.to_csv(restriction_path, index=False)
    sheaf.matrix.to_csv(laplacian_path)
    if profiles is not None and lr_db is not None and pathway_scores is not None:
        lr_channel_sheaf = build_lr_channel_sheaf(
            profiles=profiles,
            lr_db=lr_db,
            pathway_scores=pathway_scores,
        )
        lr_channel_sheaf.channel_table.to_csv(
            results_dir / "lr_channel_sheaf_restrictions.csv",
            index=False,
        )
        lr_channel_sheaf.edge_summary.to_csv(
            results_dir / "lr_channel_sheaf_edge_summary.csv",
            index=False,
        )
        lr_channel_sheaf.laplacian.to_csv(results_dir / "lr_channel_sheaf_laplacian.csv")
    return restriction_path, laplacian_path


def _metadata_annotation_version(metadata: pd.DataFrame) -> str:
    for column in ["annotation_version", "reannotation_version"]:
        if column in metadata.columns:
            values = sorted(set(metadata[column].dropna().astype(str)))
            if values:
                return ";".join(values)
    return "unversioned"


def _run_from_profiles(
    profiles: pd.DataFrame,
    lr_db: pd.DataFrame,
    pathway_genes: list[str],
    project_dir: str | Path = ".",
    min_communication: float = 0.0,
    allow_self: bool = False,
    make_plot: bool = True,
    profile_path: str | Path | None = None,
    lr_db_path: str | Path | None = None,
    gene_set_path: str | Path | None = None,
) -> PipelineResult:
    project_dir = Path(project_dir)
    results_dir = project_dir / "results"
    figures_dir = project_dir / "figures"
    results_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    profiles = profiles.copy()
    profiles.index = profiles.index.astype(str)
    profiles.columns = profiles.columns.astype(str)
    pathway_scores = compute_pathway_scores(profiles, pathway_genes)

    edges = build_directed_lr_edges(
        profiles,
        lr_db,
        min_communication=min_communication,
        allow_self=allow_self,
    )
    edges = compute_sheaf_energy(edges, pathway_scores)
    edges, global_scores, communication_global_scores = _attach_dual_hodge(edges)
    node_scores = compute_node_frustration(edges)
    score_table = _assemble_score_table(
        global_scores=global_scores,
        node_scores=node_scores,
        total_sheaf_energy=float(edges["sheaf_energy"].sum()),
        communication_global_scores=communication_global_scores,
    )

    edge_path = results_dir / "sheaf_energy_by_edge.csv"
    score_path = results_dir / "hodge_decomposition_scores.csv"
    provenance_path = results_dir / "provenance.json"
    edges.to_csv(edge_path, index=False)
    score_table.to_csv(score_path, index=False)
    _write_sheaf_contract_tables(
        edges,
        results_dir,
        profiles=profiles,
        lr_db=lr_db,
        pathway_scores=pathway_scores,
    )
    write_provenance(
        provenance_path,
        inputs={
            "profiles": profile_path,
            "ligand_receptor_db": lr_db_path,
            "gene_set": gene_set_path,
        },
        parameters={
            "input_mode": "profile",
            "min_communication": min_communication,
            "allow_self": allow_self,
            "primary_hodge_flow_col": "sheaf_residual",
            "secondary_hodge_flow_col": "flow_z",
            "higher_rank_sheaf": "lr_channel_expression_scaled_restrictions",
            "higher_rank_sheaf_outputs": (
                "lr_channel_sheaf_restrictions.csv;"
                "lr_channel_sheaf_edge_summary.csv;"
                "lr_channel_sheaf_laplacian.csv"
            ),
        },
    )

    figure_path = None
    if make_plot:
        figure_path = figures_dir / "communication_curl_network.pdf"
        plot_communication_network(edges, node_scores, figure_path)

    return PipelineResult(
        edge_path=edge_path,
        score_path=score_path,
        figure_path=figure_path,
        edge_permutation_path=None,
        node_permutation_path=None,
        global_permutation_path=None,
        provenance_path=provenance_path,
        n_edges=int(len(edges)),
        n_cell_types=int(len(profiles)),
    )


def run_profile_pipeline(
    profile_path: str | Path,
    lr_db_path: str | Path,
    gene_set_path: str | Path,
    project_dir: str | Path = ".",
    min_communication: float = 0.0,
    allow_self: bool = False,
    make_plot: bool = True,
) -> PipelineResult:
    """Run SheafSignal from a cell-type x genes profile matrix."""
    profiles = pd.read_csv(profile_path, index_col=0)
    lr_db = read_ligand_receptor_db(lr_db_path)
    pathway_genes = read_gene_set(gene_set_path)
    return _run_from_profiles(
        profiles=profiles,
        lr_db=lr_db,
        pathway_genes=pathway_genes,
        project_dir=project_dir,
        min_communication=min_communication,
        allow_self=allow_self,
        make_plot=make_plot,
        profile_path=profile_path,
        lr_db_path=lr_db_path,
        gene_set_path=gene_set_path,
    )


def run_pipeline(
    expression_path: str | Path,
    metadata_path: str | Path,
    lr_db_path: str | Path,
    gene_set_path: str | Path,
    project_dir: str | Path = ".",
    cell_type_col: str = "cell_type",
    normalize: str = "cpm_log1p",
    min_communication: float = 0.0,
    allow_self: bool = False,
    make_plot: bool = True,
    n_permutations: int = 0,
    random_seed: int = 1,
    permutation_strata_col: str | None = None,
) -> PipelineResult:
    """Run the SheafSignal MVP pipeline."""
    project_dir = Path(project_dir)
    results_dir = project_dir / "results"
    figures_dir = project_dir / "figures"
    results_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    expression = read_expression(expression_path)
    metadata = read_metadata(metadata_path)
    lr_db = read_ligand_receptor_db(lr_db_path)
    pathway_genes = read_gene_set(gene_set_path)

    expression = normalize_expression(expression, method=normalize)
    profile_result = make_cell_type_profiles(expression, metadata, cell_type_col=cell_type_col)
    pathway_scores = compute_pathway_scores(profile_result.profiles, pathway_genes)

    edges = build_directed_lr_edges(
        profile_result.profiles,
        lr_db,
        min_communication=min_communication,
        allow_self=allow_self,
    )
    edges = compute_sheaf_energy(edges, pathway_scores)

    edges, global_scores, communication_global_scores = _attach_dual_hodge(edges)
    node_scores = compute_node_frustration(edges)
    score_table = _assemble_score_table(
        global_scores=global_scores,
        node_scores=node_scores,
        total_sheaf_energy=float(edges["sheaf_energy"].sum()),
        communication_global_scores=communication_global_scores,
    )

    edge_permutation_path = None
    node_permutation_path = None
    global_permutation_path = None
    if n_permutations > 0:
        permutation_result = permutation_test(
            expression=expression,
            metadata=metadata,
            lr_db=lr_db,
            pathway_genes=pathway_genes,
            observed_edges=edges,
            observed_node_scores=node_scores,
            observed_global_scores=global_scores,
            cell_type_col=cell_type_col,
            min_communication=min_communication,
            allow_self=allow_self,
            n_permutations=n_permutations,
            seed=random_seed,
            strata_col=permutation_strata_col,
        )

        edge_permutation_path = results_dir / "sheaf_energy_permutation_pvalues.csv"
        node_permutation_path = results_dir / "frustration_permutation_pvalues.csv"
        global_permutation_path = results_dir / "global_permutation_pvalues.csv"
        permutation_result.edge_statistics.to_csv(edge_permutation_path, index=False)
        permutation_result.node_statistics.to_csv(node_permutation_path, index=False)
        permutation_result.global_statistics.to_csv(global_permutation_path, index=False)

        edge_stat_cols = [
            "sender",
            "receiver",
            "null_sheaf_energy_mean",
            "null_sheaf_energy_sd",
            "sheaf_energy_empirical_p",
            "sheaf_energy_fdr",
            "curl_empirical_p",
            "curl_fdr",
            "n_permutations",
        ]
        edges = edges.merge(
            permutation_result.edge_statistics[edge_stat_cols],
            on=["sender", "receiver"],
            how="left",
        )

        score_table = score_table.merge(
            permutation_result.node_statistics[
                [
                    "cell_type",
                    "null_frustration_score_mean",
                    "null_frustration_score_sd",
                    "frustration_empirical_p",
                    "frustration_fdr",
                    "n_permutations",
                ]
            ],
            on="cell_type",
            how="left",
        )

    edge_path = results_dir / "sheaf_energy_by_edge.csv"
    score_path = results_dir / "hodge_decomposition_scores.csv"
    provenance_path = results_dir / "provenance.json"
    edges.to_csv(edge_path, index=False)
    score_table.to_csv(score_path, index=False)
    _write_sheaf_contract_tables(
        edges,
        results_dir,
        profiles=profile_result.profiles,
        lr_db=lr_db,
        pathway_scores=pathway_scores,
    )
    write_provenance(
        provenance_path,
        inputs={
            "expression": expression_path,
            "metadata": metadata_path,
            "ligand_receptor_db": lr_db_path,
            "gene_set": gene_set_path,
        },
        parameters={
            "input_mode": "expression",
            "cell_type_col": cell_type_col,
            "normalize": normalize,
            "min_communication": min_communication,
            "allow_self": allow_self,
            "n_permutations": n_permutations,
            "random_seed": random_seed,
            "permutation_strata_col": permutation_strata_col or "",
            "primary_hodge_flow_col": "sheaf_residual",
            "secondary_hodge_flow_col": "flow_z",
            "higher_rank_sheaf": "lr_channel_expression_scaled_restrictions",
            "higher_rank_sheaf_outputs": (
                "lr_channel_sheaf_restrictions.csv;"
                "lr_channel_sheaf_edge_summary.csv;"
                "lr_channel_sheaf_laplacian.csv"
            ),
        },
        annotation_version=_metadata_annotation_version(metadata),
    )

    figure_path = None
    if make_plot:
        figure_path = figures_dir / "communication_curl_network.pdf"
        plot_communication_network(edges, node_scores, figure_path)

    return PipelineResult(
        edge_path=edge_path,
        score_path=score_path,
        figure_path=figure_path,
        edge_permutation_path=edge_permutation_path,
        node_permutation_path=node_permutation_path,
        global_permutation_path=global_permutation_path,
        provenance_path=provenance_path,
        n_edges=int(len(edges)),
        n_cell_types=int(len(profile_result.profiles)),
    )
