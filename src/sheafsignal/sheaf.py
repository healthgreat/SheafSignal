from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


EPS = 1e-12


@dataclass(frozen=True)
class SheafLaplacian:
    nodes: list[str]
    matrix: pd.DataFrame
    restrictions: pd.DataFrame


def build_restriction_table(edges: pd.DataFrame) -> pd.DataFrame:
    """Build the rank-one cellular sheaf restriction maps for directed CCC edges.

    Vertex stalks are one-dimensional pathway states. Edge stalks are
    one-dimensional communication observations. For edge u -> v, the coboundary
    is x_v - x_u, implemented with restrictions -1 and +1.
    """
    required = {"sender", "receiver"}
    missing = required.difference(edges.columns)
    if missing:
        raise ValueError(f"Edges are missing required columns: {sorted(missing)}")

    out = edges[["sender", "receiver"]].copy()
    out["edge_id"] = out["sender"].astype(str) + "->" + out["receiver"].astype(str)
    out["vertex_stalk"] = "R_pathway_state"
    out["edge_stalk"] = "R_communication_observation"
    out["restriction_sender"] = -1.0
    out["restriction_receiver"] = 1.0
    out["coboundary_orientation"] = "receiver_minus_sender"
    return out


def annotate_cellular_sheaf_edges(edges: pd.DataFrame) -> pd.DataFrame:
    """Annotate edges with formal sheaf coboundary residual and energy fields."""
    required = {
        "sender",
        "receiver",
        "flow_z",
        "pathway_gradient_z",
        "edge_weight",
    }
    missing = required.difference(edges.columns)
    if missing:
        raise ValueError(f"Edges are missing required columns: {sorted(missing)}")

    out = edges.copy()
    restrictions = build_restriction_table(out)
    out["edge_id"] = restrictions["edge_id"].to_numpy()
    out["vertex_stalk_dimension"] = 1
    out["edge_stalk_dimension"] = 1
    out["restriction_sender"] = restrictions["restriction_sender"].to_numpy(dtype=float)
    out["restriction_receiver"] = restrictions["restriction_receiver"].to_numpy(dtype=float)
    out["coboundary_orientation"] = restrictions["coboundary_orientation"].to_numpy()
    out["coboundary_expected_flow"] = out["pathway_gradient_z"].astype(float)
    out["sheaf_observed_flow"] = out["flow_z"].astype(float)
    out["sheaf_residual"] = out["sheaf_observed_flow"] - out["coboundary_expected_flow"]
    out["sheaf_mismatch"] = out["sheaf_residual"]
    out["sheaf_energy_unweighted"] = out["sheaf_residual"] ** 2
    out["sheaf_energy"] = out["edge_weight"].astype(float) * out["sheaf_energy_unweighted"]
    out["directional_agreement"] = (
        np.sign(out["sheaf_observed_flow"]) == np.sign(out["coboundary_expected_flow"])
    )
    return out


def sheaf_laplacian(edges: pd.DataFrame, weight_col: str = "edge_weight") -> SheafLaplacian:
    """Compute the weighted sheaf Laplacian B^T W B for the rank-one sheaf."""
    required = {"sender", "receiver", weight_col}
    missing = required.difference(edges.columns)
    if missing:
        raise ValueError(f"Edges are missing required columns: {sorted(missing)}")

    restrictions = build_restriction_table(edges)
    nodes = sorted(set(edges["sender"].astype(str)).union(edges["receiver"].astype(str)))
    node_index = {node: idx for idx, node in enumerate(nodes)}
    b = np.zeros((len(edges), len(nodes)), dtype=float)
    weights = edges[weight_col].astype(float).to_numpy()
    for edge_idx, row in enumerate(edges.itertuples(index=False)):
        sender = str(getattr(row, "sender"))
        receiver = str(getattr(row, "receiver"))
        b[edge_idx, node_index[sender]] = -1.0
        b[edge_idx, node_index[receiver]] = 1.0
    laplacian = b.T @ np.diag(weights) @ b
    matrix = pd.DataFrame(laplacian, index=nodes, columns=nodes)
    matrix.index.name = "cell_type"
    return SheafLaplacian(nodes=nodes, matrix=matrix, restrictions=restrictions)

