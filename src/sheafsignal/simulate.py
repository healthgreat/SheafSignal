from __future__ import annotations

import numpy as np
import pandas as pd

from .core import build_directed_lr_edges, compute_pathway_scores, compute_sheaf_energy
from .hodge import attach_hodge_components, hodge_decomposition
from .sheaf import build_lr_channel_sheaf


def gradient_chain(n_nodes: int = 5, magnitude: float = 1.0) -> pd.DataFrame:
    """Create a tree flow that should be gradient dominated."""
    if n_nodes < 2:
        raise ValueError("n_nodes must be at least 2.")
    nodes = [f"C{i}" for i in range(n_nodes)]
    rows = []
    for i in range(n_nodes - 1):
        rows.append({"sender": nodes[i], "receiver": nodes[i + 1], "flow_z": magnitude})
    return pd.DataFrame(rows)


def triangle_curl(magnitude: float = 1.0) -> pd.DataFrame:
    """Create a filled triangle cycle that should be curl dominated."""
    return pd.DataFrame(
        [
            {"sender": "A", "receiver": "B", "flow_z": magnitude},
            {"sender": "B", "receiver": "C", "flow_z": magnitude},
            {"sender": "C", "receiver": "A", "flow_z": magnitude},
        ]
    )


def harmonic_ring(n_nodes: int = 5, magnitude: float = 1.0) -> pd.DataFrame:
    """Create an unfilled ring cycle that should be harmonic dominated."""
    if n_nodes < 4:
        raise ValueError("n_nodes must be at least 4 for an unfilled ring.")
    nodes = [f"R{i}" for i in range(n_nodes)]
    rows = []
    for i in range(n_nodes):
        rows.append({"sender": nodes[i], "receiver": nodes[(i + 1) % n_nodes], "flow_z": magnitude})
    return pd.DataFrame(rows)


def mixed_flow(seed: int = 1, noise_sd: float = 0.1) -> pd.DataFrame:
    """Create a mixed graph with gradient, curl, and harmonic structure."""
    rng = np.random.default_rng(seed)
    parts = [
        gradient_chain(n_nodes=4, magnitude=1.0),
        triangle_curl(magnitude=0.8),
        harmonic_ring(n_nodes=5, magnitude=0.6),
    ]
    prefixes = ["G", "T", "H"]
    shifted = []
    for prefix, part in zip(prefixes, parts):
        part = part.copy()
        part["sender"] = prefix + "_" + part["sender"].astype(str)
        part["receiver"] = prefix + "_" + part["receiver"].astype(str)
        shifted.append(part)

    out = pd.concat(shifted, ignore_index=True)
    out["flow_z"] = out["flow_z"] + rng.normal(0.0, noise_sd, size=len(out))
    return out


def scenario_edges(scenario: str, seed: int = 1, noise_sd: float = 0.0) -> pd.DataFrame:
    """Return directed flow edges for a named simulation scenario."""
    scenario = scenario.lower()
    if scenario == "gradient_chain":
        edges = gradient_chain()
    elif scenario == "triangle_curl":
        edges = triangle_curl()
    elif scenario == "harmonic_ring":
        edges = harmonic_ring()
    elif scenario == "mixed":
        edges = mixed_flow(seed=seed, noise_sd=noise_sd)
    else:
        raise ValueError(
            "scenario must be one of: gradient_chain, triangle_curl, harmonic_ring, mixed"
        )

    if noise_sd > 0 and scenario != "mixed":
        rng = np.random.default_rng(seed)
        edges = edges.copy()
        edges["flow_z"] = edges["flow_z"] + rng.normal(0.0, noise_sd, size=len(edges))
    return edges


def sheaf_ground_truth_profiles(noise_sd: float = 0.0, seed: int = 1) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    """Create synthetic profiles with known LR/pathway inconsistency edges."""
    rng = np.random.default_rng(seed)
    profiles = pd.DataFrame(
        {
            "L_forward": [6.0, 4.0, 2.0, 0.5],
            "R_forward": [0.5, 2.0, 4.0, 6.0],
            "L_reverse": [0.5, 1.0, 2.0, 8.0],
            "R_reverse": [8.0, 2.0, 1.0, 0.5],
            "PATH_A": [0.0, 1.0, 2.0, 3.0],
            "PATH_B": [0.0, 1.0, 2.0, 3.0],
        },
        index=["C0", "C1", "C2", "C3"],
    )
    if noise_sd > 0:
        profiles = profiles + rng.normal(0.0, noise_sd, size=profiles.shape)
        profiles = profiles.clip(lower=0.0)
    profiles.index.name = "cell_type"
    lr_db = pd.DataFrame(
        {
            "ligand": ["L_forward", "L_reverse"],
            "receptor": ["R_forward", "R_reverse"],
            "weight": [1.0, 1.0],
        }
    )
    return profiles, lr_db, ["PATH_A", "PATH_B"]


def independent_perturbation_profiles(
    noise_sd: float = 0.0,
    seed: int = 1,
) -> tuple[pd.DataFrame, pd.DataFrame, list[str], set[tuple[str, str]]]:
    """Create profiles where truth labels come from a predefined perturbation mask.

    The positive edges are externally specified sender/receiver pairs. They are
    not selected by thresholding the SheafSignal residual after the fact. A
    high-flow concordant decoy is included so LR intensity alone is not a
    sufficient ground-truth definition.
    """
    rng = np.random.default_rng(seed)
    profiles = pd.DataFrame(
        {
            "L_perturb": [8.0, 7.0, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2],
            "R_perturb": [0.2, 0.2, 8.0, 7.0, 0.2, 0.2, 0.2, 0.2],
            "L_decoy": [0.2, 0.2, 0.2, 0.2, 8.0, 7.0, 0.2, 0.2],
            "R_decoy": [0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 8.0, 7.0],
            "PATH_A": [3.0, 3.0, 0.0, 0.0, 0.0, 0.0, 3.0, 3.0],
            "PATH_B": [3.0, 3.0, 0.0, 0.0, 0.0, 0.0, 3.0, 3.0],
        },
        index=[
            "P_sender_0",
            "P_sender_1",
            "P_recv_0",
            "P_recv_1",
            "D_low_0",
            "D_low_1",
            "D_high_0",
            "D_high_1",
        ],
    )
    if noise_sd > 0:
        profiles = profiles + rng.normal(0.0, noise_sd, size=profiles.shape)
        profiles = profiles.clip(lower=0.0)
    profiles.index.name = "cell_type"
    lr_db = pd.DataFrame(
        {
            "ligand": ["L_perturb", "L_decoy"],
            "receptor": ["R_perturb", "R_decoy"],
            "weight": [1.0, 1.0],
        }
    )
    truth = {
        ("P_sender_0", "P_recv_0"),
        ("P_sender_0", "P_recv_1"),
        ("P_sender_1", "P_recv_0"),
        ("P_sender_1", "P_recv_1"),
    }
    return profiles, lr_db, ["PATH_A", "PATH_B"], truth


def sheaf_ground_truth_edges(noise_sd: float = 0.0, seed: int = 1) -> pd.DataFrame:
    """Run SheafSignal primitives on synthetic profiles and attach truth labels."""
    profiles, lr_db, pathway_genes = sheaf_ground_truth_profiles(noise_sd=noise_sd, seed=seed)
    pathway_scores = compute_pathway_scores(profiles, pathway_genes)
    edges = build_directed_lr_edges(profiles, lr_db)
    edges = compute_sheaf_energy(edges, pathway_scores)
    truth = {("C3", "C0"), ("C3", "C1"), ("C2", "C0")}
    edges["ground_truth_inconsistent"] = [
        (str(row.sender), str(row.receiver)) in truth for row in edges.itertuples(index=False)
    ]
    return edges


def independent_perturbation_edges(noise_sd: float = 0.0, seed: int = 1) -> pd.DataFrame:
    """Run SheafSignal primitives on independent perturbation profiles."""
    profiles, lr_db, pathway_genes, truth = independent_perturbation_profiles(
        noise_sd=noise_sd,
        seed=seed,
    )
    pathway_scores = compute_pathway_scores(profiles, pathway_genes)
    edges = build_directed_lr_edges(profiles, lr_db)
    edges = compute_sheaf_energy(edges, pathway_scores)
    edges["ground_truth_perturbed"] = [
        (str(row.sender), str(row.receiver)) in truth for row in edges.itertuples(index=False)
    ]
    edges["ground_truth_source"] = "predefined_external_perturbation_mask"
    edges["truth_depends_on_residual_definition"] = False
    return edges


def binary_auroc(labels: pd.Series | np.ndarray, scores: pd.Series | np.ndarray) -> float:
    """Compute AUROC without requiring scikit-learn."""
    y = np.asarray(labels, dtype=bool)
    s = np.asarray(scores, dtype=float)
    pos = s[y]
    neg = s[~y]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    wins = 0.0
    for value in pos:
        wins += float(np.sum(value > neg))
        wins += 0.5 * float(np.sum(value == neg))
    return wins / (len(pos) * len(neg))


def binary_average_precision(labels: pd.Series | np.ndarray, scores: pd.Series | np.ndarray) -> float:
    """Compute average precision for binary labels."""
    y = np.asarray(labels, dtype=bool)
    s = np.asarray(scores, dtype=float)
    if y.sum() == 0:
        return float("nan")
    order = np.argsort(s)[::-1]
    y_sorted = y[order]
    cumulative_pos = np.cumsum(y_sorted)
    precision = cumulative_pos / (np.arange(len(y_sorted)) + 1)
    return float(np.sum(precision[y_sorted]) / y.sum())


def hodge_only_non_gradient_score(edges: pd.DataFrame) -> pd.Series:
    """Score edges by non-gradient Hodge magnitude without using pathway mismatch."""
    pair_components, _ = hodge_decomposition(edges, flow_col="flow_z")
    attached = attach_hodge_components(edges, pair_components)
    score = attached["curl_component"].abs() + attached["harmonic_component"].abs()
    return pd.Series(score.to_numpy(dtype=float), index=edges.index)


def endpoint_centrality_score(edges: pd.DataFrame) -> pd.Series:
    """Score edges by endpoint communication strength without pathway information."""
    out_strength = edges.groupby("sender")["communication_flow"].sum().to_dict()
    in_strength = edges.groupby("receiver")["communication_flow"].sum().to_dict()
    values = [
        float(out_strength.get(row.sender, 0.0) + in_strength.get(row.receiver, 0.0))
        for row in edges.itertuples(index=False)
    ]
    return pd.Series(values, index=edges.index)


def graph_smoothness_score(edges: pd.DataFrame) -> pd.Series:
    """Score edges by weighted pathway-signal variation on the LR graph."""
    values = edges["edge_weight"].astype(float) * (edges["pathway_gradient_z"].astype(float) ** 2)
    return pd.Series(values.to_numpy(dtype=float), index=edges.index)


def flow_gradient_opposition_score(edges: pd.DataFrame) -> pd.Series:
    """Score edges by direct LR-flow/pathway-gradient opposition.

    This deliberately simple baseline combines the same two scalar ingredients
    used by the residual, without invoking sheaf terminology.
    """
    values = -(edges["flow_z"].astype(float) * edges["pathway_gradient_z"].astype(float))
    return pd.Series(values.to_numpy(dtype=float), index=edges.index)


def higher_rank_lr_channel_sheaf_score(
    edges: pd.DataFrame,
    profiles: pd.DataFrame,
    lr_db: pd.DataFrame,
    pathway_scores: pd.DataFrame,
) -> pd.Series:
    """Score directed edges by higher-rank LR-channel-specific sheaf energy."""
    lr_channel_sheaf = build_lr_channel_sheaf(profiles, lr_db, pathway_scores)
    merged = edges[["sender", "receiver"]].merge(
        lr_channel_sheaf.edge_summary[
            ["sender", "receiver", "higher_rank_sheaf_energy"]
        ],
        on=["sender", "receiver"],
        how="left",
    )
    return pd.Series(
        merged["higher_rank_sheaf_energy"].fillna(0.0).to_numpy(dtype=float),
        index=edges.index,
    )


def sheaf_ground_truth_recovery(noise_sd: float = 0.0, seed: int = 1) -> pd.DataFrame:
    """Compare SheafSignal energy against LR, Hodge-only, centrality, and smoothness baselines."""
    profiles, lr_db, pathway_genes = sheaf_ground_truth_profiles(noise_sd=noise_sd, seed=seed)
    pathway_scores = compute_pathway_scores(profiles, pathway_genes)
    edges = sheaf_ground_truth_edges(noise_sd=noise_sd, seed=seed)
    labels = edges["ground_truth_inconsistent"]
    rows = []
    method_specs = [
        {
            "method": "SheafSignal_sheaf_energy",
            "baseline_family": "sheaf_residual",
            "scores": edges["sheaf_energy"],
            "uses_lr_flow": True,
            "uses_pathway_state": True,
            "uses_sheaf_residual": True,
            "score_description": "weighted squared residual between LR flow and pathway coboundary",
        },
        {
            "method": "LRProductBaseline_communication_flow",
            "baseline_family": "lr_intensity",
            "scores": edges["communication_flow"],
            "uses_lr_flow": True,
            "uses_pathway_state": False,
            "uses_sheaf_residual": False,
            "score_description": "raw ligand-receptor product communication intensity",
        },
        {
            "method": "Absolute_pathway_gradient",
            "baseline_family": "pathway_gradient",
            "scores": edges["pathway_gradient_z"].abs(),
            "uses_lr_flow": False,
            "uses_pathway_state": True,
            "uses_sheaf_residual": False,
            "score_description": "absolute pathway-state gradient without LR-flow mismatch",
        },
        {
            "method": "HodgeOnly_non_gradient_flow",
            "baseline_family": "hodge_only",
            "scores": hodge_only_non_gradient_score(edges),
            "uses_lr_flow": True,
            "uses_pathway_state": False,
            "uses_sheaf_residual": False,
            "score_description": "curl plus harmonic magnitude from communication flow only",
        },
        {
            "method": "GraphCentrality_endpoint_strength",
            "baseline_family": "graph_centrality",
            "scores": endpoint_centrality_score(edges),
            "uses_lr_flow": True,
            "uses_pathway_state": False,
            "uses_sheaf_residual": False,
            "score_description": "sender out-strength plus receiver in-strength on LR graph",
        },
        {
            "method": "GraphSmoothness_pathway_signal",
            "baseline_family": "graph_smoothness",
            "scores": graph_smoothness_score(edges),
            "uses_lr_flow": True,
            "uses_pathway_state": True,
            "uses_sheaf_residual": False,
            "score_description": "edge-weighted squared pathway difference on LR graph",
        },
        {
            "method": "FlowGradientOpposition_product",
            "baseline_family": "flow_gradient_product",
            "scores": flow_gradient_opposition_score(edges),
            "uses_lr_flow": True,
            "uses_pathway_state": True,
            "uses_sheaf_residual": False,
            "score_description": "negative product of LR-flow z-score and pathway-gradient z-score",
        },
        {
            "method": "HigherRankLRChannelSheaf_energy",
            "baseline_family": "higher_rank_lr_channel_sheaf",
            "scores": higher_rank_lr_channel_sheaf_score(
                edges,
                profiles,
                lr_db,
                pathway_scores,
            ),
            "uses_lr_flow": True,
            "uses_pathway_state": True,
            "uses_sheaf_residual": True,
            "score_description": "sum of LR-channel-specific higher-rank sheaf energies per edge",
        },
    ]
    for spec in method_specs:
        scores = pd.Series(spec["scores"], index=edges.index).astype(float)
        rows.append(
            {
                "method": spec["method"],
                "baseline_family": spec["baseline_family"],
                "noise_sd": noise_sd,
                "seed": seed,
                "n_edges": int(len(edges)),
                "n_positive_edges": int(labels.sum()),
                "simulation_task": "residual_aligned_ground_truth",
                "ground_truth_source": "predefined_high_to_low_pathway_edge_mask",
                "truth_depends_on_residual_definition": True,
                "auroc": binary_auroc(labels, scores),
                "average_precision": binary_average_precision(labels, scores),
                "uses_lr_flow": bool(spec["uses_lr_flow"]),
                "uses_pathway_state": bool(spec["uses_pathway_state"]),
                "uses_sheaf_residual": bool(spec["uses_sheaf_residual"]),
                "score_description": spec["score_description"],
            }
        )
    return pd.DataFrame(rows)


def independent_perturbation_recovery(noise_sd: float = 0.0, seed: int = 1) -> pd.DataFrame:
    """Evaluate recovery of a perturbation mask not defined by residual thresholding."""
    profiles, lr_db, pathway_genes, _ = independent_perturbation_profiles(
        noise_sd=noise_sd,
        seed=seed,
    )
    pathway_scores = compute_pathway_scores(profiles, pathway_genes)
    edges = independent_perturbation_edges(noise_sd=noise_sd, seed=seed)
    labels = edges["ground_truth_perturbed"]
    rows = []
    method_specs = [
        {
            "method": "SheafSignal_sheaf_energy",
            "baseline_family": "sheaf_residual",
            "scores": edges["sheaf_energy"],
            "uses_lr_flow": True,
            "uses_pathway_state": True,
            "uses_sheaf_residual": True,
            "score_description": "weighted squared residual between LR flow and pathway coboundary",
        },
        {
            "method": "LRProductBaseline_communication_flow",
            "baseline_family": "lr_intensity",
            "scores": edges["communication_flow"],
            "uses_lr_flow": True,
            "uses_pathway_state": False,
            "uses_sheaf_residual": False,
            "score_description": "raw ligand-receptor product communication intensity",
        },
        {
            "method": "Absolute_pathway_gradient",
            "baseline_family": "pathway_gradient",
            "scores": edges["pathway_gradient_z"].abs(),
            "uses_lr_flow": False,
            "uses_pathway_state": True,
            "uses_sheaf_residual": False,
            "score_description": "absolute pathway-state gradient without LR-flow mismatch",
        },
        {
            "method": "HodgeOnly_non_gradient_flow",
            "baseline_family": "hodge_only",
            "scores": hodge_only_non_gradient_score(edges),
            "uses_lr_flow": True,
            "uses_pathway_state": False,
            "uses_sheaf_residual": False,
            "score_description": "curl plus harmonic magnitude from communication flow only",
        },
        {
            "method": "GraphCentrality_endpoint_strength",
            "baseline_family": "graph_centrality",
            "scores": endpoint_centrality_score(edges),
            "uses_lr_flow": True,
            "uses_pathway_state": False,
            "uses_sheaf_residual": False,
            "score_description": "sender out-strength plus receiver in-strength on LR graph",
        },
        {
            "method": "GraphSmoothness_pathway_signal",
            "baseline_family": "graph_smoothness",
            "scores": graph_smoothness_score(edges),
            "uses_lr_flow": True,
            "uses_pathway_state": True,
            "uses_sheaf_residual": False,
            "score_description": "edge-weighted squared pathway difference on LR graph",
        },
        {
            "method": "FlowGradientOpposition_product",
            "baseline_family": "flow_gradient_product",
            "scores": flow_gradient_opposition_score(edges),
            "uses_lr_flow": True,
            "uses_pathway_state": True,
            "uses_sheaf_residual": False,
            "score_description": "negative product of LR-flow z-score and pathway-gradient z-score",
        },
        {
            "method": "HigherRankLRChannelSheaf_energy",
            "baseline_family": "higher_rank_lr_channel_sheaf",
            "scores": higher_rank_lr_channel_sheaf_score(
                edges,
                profiles,
                lr_db,
                pathway_scores,
            ),
            "uses_lr_flow": True,
            "uses_pathway_state": True,
            "uses_sheaf_residual": True,
            "score_description": "sum of LR-channel-specific higher-rank sheaf energies per edge",
        },
    ]
    for spec in method_specs:
        scores = pd.Series(spec["scores"], index=edges.index).astype(float)
        rows.append(
            {
                "method": spec["method"],
                "baseline_family": spec["baseline_family"],
                "noise_sd": noise_sd,
                "seed": seed,
                "n_edges": int(len(edges)),
                "n_positive_edges": int(labels.sum()),
                "simulation_task": "independent_perturbation",
                "ground_truth_source": "predefined_external_perturbation_mask",
                "truth_depends_on_residual_definition": False,
                "auroc": binary_auroc(labels, scores),
                "average_precision": binary_average_precision(labels, scores),
                "uses_lr_flow": bool(spec["uses_lr_flow"]),
                "uses_pathway_state": bool(spec["uses_pathway_state"]),
                "uses_sheaf_residual": bool(spec["uses_sheaf_residual"]),
                "score_description": spec["score_description"],
            }
        )
    return pd.DataFrame(rows)
