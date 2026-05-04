from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .core import (
    build_directed_lr_edges,
    compute_node_frustration,
    compute_pathway_scores,
    compute_sheaf_energy,
    make_cell_type_profiles,
)
from .hodge import attach_hodge_components, hodge_decomposition


EPS = 1e-12


@dataclass(frozen=True)
class PermutationResult:
    edge_statistics: pd.DataFrame
    node_statistics: pd.DataFrame
    global_statistics: pd.DataFrame
    n_permutations_requested: int
    n_permutations_completed: int
    n_permutations_skipped: int


def benjamini_hochberg(pvalues: pd.Series | np.ndarray) -> np.ndarray:
    """Benjamini-Hochberg FDR correction that preserves NaN positions."""
    values = np.asarray(pvalues, dtype=float)
    adjusted = np.full(values.shape, np.nan, dtype=float)
    valid = np.isfinite(values)
    if valid.sum() == 0:
        return adjusted

    p = values[valid]
    order = np.argsort(p)
    ranked = p[order]
    m = float(len(ranked))
    q = ranked * m / np.arange(1, len(ranked) + 1)
    q = np.minimum.accumulate(q[::-1])[::-1]
    q = np.clip(q, 0.0, 1.0)

    valid_indices = np.flatnonzero(valid)
    adjusted[valid_indices[order]] = q
    return adjusted


def _edge_id(sender: pd.Series, receiver: pd.Series) -> pd.Series:
    return sender.astype(str) + "->" + receiver.astype(str)


def _compute_edges_for_metadata(
    expression: pd.DataFrame,
    metadata: pd.DataFrame,
    lr_db: pd.DataFrame,
    pathway_genes: list[str],
    cell_type_col: str,
    min_communication: float,
    allow_self: bool,
) -> pd.DataFrame:
    profile_result = make_cell_type_profiles(expression, metadata, cell_type_col=cell_type_col)
    pathway_scores = compute_pathway_scores(profile_result.profiles, pathway_genes)
    edges = build_directed_lr_edges(
        profile_result.profiles,
        lr_db,
        min_communication=min_communication,
        allow_self=allow_self,
    )
    edges = compute_sheaf_energy(edges, pathway_scores)
    return edges


def _permuted_labels(
    metadata: pd.DataFrame,
    cell_type_col: str,
    strata_col: str | None,
    rng: np.random.Generator,
) -> np.ndarray:
    labels = metadata[cell_type_col].astype(str).to_numpy()
    shuffled = labels.copy()

    if strata_col is None:
        rng.shuffle(shuffled)
        return shuffled

    if strata_col not in metadata.columns:
        raise ValueError(f"Permutation strata column '{strata_col}' is not in metadata.")

    strata = metadata[strata_col].astype(str).to_numpy()
    for stratum in pd.unique(strata):
        idx = np.flatnonzero(strata == stratum)
        if idx.size <= 1:
            continue
        stratum_labels = shuffled[idx].copy()
        rng.shuffle(stratum_labels)
        shuffled[idx] = stratum_labels
    return shuffled


def permutation_test(
    expression: pd.DataFrame,
    metadata: pd.DataFrame,
    lr_db: pd.DataFrame,
    pathway_genes: list[str],
    observed_edges: pd.DataFrame,
    observed_node_scores: pd.DataFrame,
    observed_global_scores: dict[str, float],
    cell_type_col: str = "cell_type",
    min_communication: float = 0.0,
    allow_self: bool = False,
    n_permutations: int = 100,
    seed: int = 1,
    strata_col: str | None = None,
) -> PermutationResult:
    """Cell-label permutation test for SheafSignal edge and node scores.

    The null model shuffles cell-type labels across cells while preserving the
    original cell-type label counts. This tests whether the observed local
    consistency/frustration structure is stronger than expected from expression
    profiles assigned to random cell-type labels.
    """
    if n_permutations <= 0:
        empty = pd.DataFrame()
        return PermutationResult(empty, empty, empty, n_permutations, 0, 0)
    if cell_type_col not in metadata.columns:
        raise ValueError(f"Metadata must contain '{cell_type_col}'.")

    rng = np.random.default_rng(seed)
    observed_edges = observed_edges.copy()
    observed_edges["edge_id"] = _edge_id(observed_edges["sender"], observed_edges["receiver"])
    observed_energy = observed_edges.set_index("edge_id")["sheaf_energy"]
    observed_curl = observed_edges.set_index("edge_id")["curl_component"].abs()

    observed_node = observed_node_scores.set_index("cell_type")
    observed_global = {
        "total_sheaf_energy": float(observed_edges["sheaf_energy"].sum()),
        "gradient_ratio": float(observed_global_scores["gradient_ratio"]),
        "curl_ratio": float(observed_global_scores["curl_ratio"]),
        "harmonic_ratio": float(observed_global_scores["harmonic_ratio"]),
    }

    edge_energy_ge = pd.Series(0, index=observed_energy.index, dtype=int)
    edge_curl_ge = pd.Series(0, index=observed_curl.index, dtype=int)
    edge_energy_sum = pd.Series(0.0, index=observed_energy.index, dtype=float)
    edge_energy_sum_sq = pd.Series(0.0, index=observed_energy.index, dtype=float)

    node_frustration_ge = pd.Series(0, index=observed_node.index, dtype=int)
    node_frustration_sum = pd.Series(0.0, index=observed_node.index, dtype=float)
    node_frustration_sum_sq = pd.Series(0.0, index=observed_node.index, dtype=float)

    global_ge = {key: 0 for key in observed_global}
    global_sum = {key: 0.0 for key in observed_global}
    global_sum_sq = {key: 0.0 for key in observed_global}
    completed = 0
    skipped = 0

    for _ in range(n_permutations):
        permuted_metadata = metadata.copy()
        permuted_metadata[cell_type_col] = _permuted_labels(
            metadata=metadata,
            cell_type_col=cell_type_col,
            strata_col=strata_col,
            rng=rng,
        )

        try:
            perm_edges = _compute_edges_for_metadata(
                expression=expression,
                metadata=permuted_metadata,
                lr_db=lr_db,
                pathway_genes=pathway_genes,
                cell_type_col=cell_type_col,
                min_communication=min_communication,
                allow_self=allow_self,
            )
        except ValueError:
            skipped += 1
            continue

        pair_components, perm_global_scores = hodge_decomposition(
            perm_edges,
            flow_col="sheaf_residual",
        )
        perm_edges = attach_hodge_components(perm_edges, pair_components)
        perm_node_scores = compute_node_frustration(perm_edges)

        perm_edges = perm_edges.copy()
        perm_edges["edge_id"] = _edge_id(perm_edges["sender"], perm_edges["receiver"])
        perm_energy = perm_edges.set_index("edge_id")["sheaf_energy"].reindex(
            observed_energy.index, fill_value=0.0
        )
        perm_curl = perm_edges.set_index("edge_id")["curl_component"].abs().reindex(
            observed_curl.index, fill_value=0.0
        )

        edge_energy_ge += (perm_energy >= observed_energy - EPS).astype(int)
        edge_curl_ge += (perm_curl >= observed_curl - EPS).astype(int)
        edge_energy_sum += perm_energy
        edge_energy_sum_sq += perm_energy**2

        perm_node = perm_node_scores.set_index("cell_type")["frustration_score"].reindex(
            observed_node.index, fill_value=0.0
        )
        obs_node_frustration = observed_node["frustration_score"]
        node_frustration_ge += (perm_node >= obs_node_frustration - EPS).astype(int)
        node_frustration_sum += perm_node
        node_frustration_sum_sq += perm_node**2

        perm_global = {
            "total_sheaf_energy": float(perm_edges["sheaf_energy"].sum()),
            "gradient_ratio": float(perm_global_scores["gradient_ratio"]),
            "curl_ratio": float(perm_global_scores["curl_ratio"]),
            "harmonic_ratio": float(perm_global_scores["harmonic_ratio"]),
        }
        for key, observed_value in observed_global.items():
            value = perm_global[key]
            global_ge[key] += int(value >= observed_value - EPS)
            global_sum[key] += value
            global_sum_sq[key] += value**2

        completed += 1

    if completed == 0:
        raise ValueError("No successful permutations were completed.")

    edge_energy_p = (edge_energy_ge + 1) / (completed + 1)
    edge_curl_p = (edge_curl_ge + 1) / (completed + 1)
    edge_energy_mean = edge_energy_sum / completed
    edge_energy_var = (edge_energy_sum_sq / completed) - edge_energy_mean**2
    edge_statistics = pd.DataFrame(
        {
            "edge_id": observed_energy.index,
            "sender": observed_edges.set_index("edge_id").loc[observed_energy.index, "sender"].values,
            "receiver": observed_edges.set_index("edge_id").loc[
                observed_energy.index, "receiver"
            ].values,
            "observed_sheaf_energy": observed_energy.values,
            "null_sheaf_energy_mean": edge_energy_mean.values,
            "null_sheaf_energy_sd": np.sqrt(np.maximum(edge_energy_var.values, 0.0)),
            "sheaf_energy_empirical_p": edge_energy_p.values,
            "sheaf_energy_fdr": benjamini_hochberg(edge_energy_p.values),
            "observed_abs_curl_component": observed_curl.values,
            "observed_abs_frustration_curl_component": observed_curl.values,
            "curl_empirical_p": edge_curl_p.values,
            "curl_fdr": benjamini_hochberg(edge_curl_p.values),
            "n_permutations": completed,
            "n_permutations_requested": n_permutations,
            "n_permutations_skipped": skipped,
            "permutation_strata_col": strata_col or "",
        }
    )

    node_p = (node_frustration_ge + 1) / (completed + 1)
    node_mean = node_frustration_sum / completed
    node_var = (node_frustration_sum_sq / completed) - node_mean**2
    node_statistics = pd.DataFrame(
        {
            "cell_type": observed_node.index,
            "observed_frustration_score": observed_node["frustration_score"].values,
            "null_frustration_score_mean": node_mean.values,
            "null_frustration_score_sd": np.sqrt(np.maximum(node_var.values, 0.0)),
            "frustration_empirical_p": node_p.values,
            "frustration_fdr": benjamini_hochberg(node_p.values),
            "n_permutations": completed,
            "n_permutations_requested": n_permutations,
            "n_permutations_skipped": skipped,
            "permutation_strata_col": strata_col or "",
        }
    )

    global_rows = []
    for key, observed_value in observed_global.items():
        null_mean = global_sum[key] / completed
        null_var = (global_sum_sq[key] / completed) - null_mean**2
        p_value = (global_ge[key] + 1) / (completed + 1)
        global_rows.append(
            {
                "metric": key,
                "observed": observed_value,
                "null_mean": null_mean,
                "null_sd": float(np.sqrt(max(null_var, 0.0))),
                "empirical_p": p_value,
                "n_permutations": completed,
                "n_permutations_requested": n_permutations,
                "n_permutations_skipped": skipped,
                "permutation_strata_col": strata_col or "",
            }
        )
    global_statistics = pd.DataFrame(global_rows)
    global_statistics["fdr"] = benjamini_hochberg(global_statistics["empirical_p"].values)

    return PermutationResult(
        edge_statistics=edge_statistics,
        node_statistics=node_statistics,
        global_statistics=global_statistics,
        n_permutations_requested=n_permutations,
        n_permutations_completed=completed,
        n_permutations_skipped=skipped,
    )
