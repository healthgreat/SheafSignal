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


@dataclass(frozen=True)
class LRChannelSheaf:
    node_channels: list[str]
    channel_table: pd.DataFrame
    edge_summary: pd.DataFrame
    laplacian: pd.DataFrame


def _zscore(values: pd.Series | np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    mean = np.nanmean(arr)
    std = np.nanstd(arr)
    if not np.isfinite(std) or std < EPS:
        return np.zeros_like(arr, dtype=float)
    return (arr - mean) / std


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


def build_lr_channel_restriction_table(
    profiles: pd.DataFrame,
    lr_db: pd.DataFrame,
    pathway_scores: pd.DataFrame,
    min_channel_flow: float = 0.0,
    allow_self: bool = False,
) -> pd.DataFrame:
    """Build higher-rank LR-channel-specific sheaf restriction rows.

    Vertex stalks are R^m, one coordinate per valid ligand-receptor channel.
    Each directed edge stalk contains the active LR channels on that edge.
    Sender and receiver restrictions are expression-dependent coefficients,
    so they vary by LR channel and edge instead of collapsing to +/-1.
    """
    required_lr = {"ligand", "receptor"}
    missing_lr = required_lr.difference(lr_db.columns)
    if missing_lr:
        raise ValueError(f"LR database is missing required columns: {sorted(missing_lr)}")
    required_scores = {"cell_type", "pathway_score"}
    missing_scores = required_scores.difference(pathway_scores.columns)
    if missing_scores:
        raise ValueError(f"Pathway scores are missing columns: {sorted(missing_scores)}")
    if min_channel_flow < 0:
        raise ValueError("min_channel_flow must be non-negative.")

    lr = lr_db.copy()
    lr["ligand"] = lr["ligand"].astype(str)
    lr["receptor"] = lr["receptor"].astype(str)
    if "weight" not in lr.columns:
        lr["weight"] = 1.0
    lr["weight"] = pd.to_numeric(lr["weight"], errors="coerce").fillna(1.0)
    lr = lr.loc[lr["ligand"].isin(profiles.columns) & lr["receptor"].isin(profiles.columns)]
    lr = lr.reset_index(drop=True)
    if lr.empty:
        raise ValueError("No LR channels have both ligand and receptor in profiles.")

    profiles = profiles.copy()
    profiles.index = profiles.index.astype(str)
    profiles.columns = profiles.columns.astype(str)
    score_map = pathway_scores.set_index("cell_type")["pathway_score"].astype(float).to_dict()
    missing_cell_types = sorted(set(profiles.index.astype(str)).difference(score_map))
    if missing_cell_types:
        raise ValueError(f"Missing pathway scores for cell types: {missing_cell_types}")

    rows = []
    cell_types = profiles.index.astype(str).to_list()
    for channel_idx, lr_row in enumerate(lr.itertuples(index=False), start=1):
        ligand = str(getattr(lr_row, "ligand"))
        receptor = str(getattr(lr_row, "receptor"))
        weight = float(getattr(lr_row, "weight"))
        lr_pair = f"{ligand}->{receptor}"
        channel_id = f"lr{channel_idx}:{lr_pair}"
        max_ligand = max(float(profiles[ligand].max()), EPS)
        max_receptor = max(float(profiles[receptor].max()), EPS)
        for sender in cell_types:
            sender_ligand = float(profiles.loc[sender, ligand])
            sender_restriction = sender_ligand / max_ligand
            for receiver in cell_types:
                if not allow_self and sender == receiver:
                    continue
                receiver_receptor = float(profiles.loc[receiver, receptor])
                receiver_restriction = receiver_receptor / max_receptor
                observed = sender_ligand * receiver_receptor * weight
                if observed <= min_channel_flow:
                    continue
                sender_state = float(score_map[sender])
                receiver_state = float(score_map[receiver])
                expected_raw = receiver_restriction * receiver_state - (
                    sender_restriction * sender_state
                )
                edge_id = f"{sender}->{receiver}"
                rows.append(
                    {
                        "edge_id": edge_id,
                        "sender": sender,
                        "receiver": receiver,
                        "channel_id": channel_id,
                        "lr_pair": lr_pair,
                        "ligand": ligand,
                        "receptor": receptor,
                        "edge_stalk_coordinate": channel_idx,
                        "vertex_stalk_dimension": int(len(lr)),
                        "edge_stalk_dimension": "n_active_lr_channels",
                        "sender_vertex_coordinate": channel_id,
                        "receiver_vertex_coordinate": channel_id,
                        "sender_ligand_expression": sender_ligand,
                        "receiver_receptor_expression": receiver_receptor,
                        "lr_weight": weight,
                        "channel_observed_flow": observed,
                        "restriction_sender": -sender_restriction,
                        "restriction_receiver": receiver_restriction,
                        "sender_pathway_state": sender_state,
                        "receiver_pathway_state": receiver_state,
                        "channel_expected_flow_raw": expected_raw,
                        "restriction_type": "lr_expression_scaled_channel_map",
                    }
                )

    if not rows:
        raise ValueError("No LR-channel sheaf rows passed min_channel_flow threshold.")

    out = pd.DataFrame(rows)
    out["channel_observed_flow_z"] = _zscore(np.log1p(out["channel_observed_flow"]))
    out["channel_expected_flow_z"] = _zscore(out["channel_expected_flow_raw"])
    out["channel_sheaf_residual"] = (
        out["channel_observed_flow_z"] - out["channel_expected_flow_z"]
    )
    max_flow = max(float(out["channel_observed_flow"].max()), EPS)
    out["channel_edge_weight"] = out["channel_observed_flow"] / max_flow
    out["channel_sheaf_energy"] = out["channel_edge_weight"] * (
        out["channel_sheaf_residual"] ** 2
    )
    return out


def summarize_lr_channel_sheaf(channel_table: pd.DataFrame) -> pd.DataFrame:
    """Aggregate LR-channel-specific residuals back to directed cell-type edges."""
    required = {
        "sender",
        "receiver",
        "channel_sheaf_energy",
        "channel_sheaf_residual",
        "channel_observed_flow",
    }
    missing = required.difference(channel_table.columns)
    if missing:
        raise ValueError(f"Channel table is missing required columns: {sorted(missing)}")
    grouped = channel_table.groupby(["sender", "receiver"], sort=True)
    summary = grouped.agg(
        higher_rank_sheaf_energy=("channel_sheaf_energy", "sum"),
        mean_channel_sheaf_residual=("channel_sheaf_residual", "mean"),
        max_abs_channel_sheaf_residual=(
            "channel_sheaf_residual",
            lambda values: float(np.max(np.abs(values))),
        ),
        n_lr_channels=("channel_id", "nunique"),
        total_channel_observed_flow=("channel_observed_flow", "sum"),
    )
    summary = summary.reset_index()
    summary["edge_id"] = summary["sender"].astype(str) + "->" + summary["receiver"].astype(str)
    return summary.sort_values("higher_rank_sheaf_energy", ascending=False).reset_index(
        drop=True
    )


def lr_channel_sheaf_laplacian(channel_table: pd.DataFrame) -> pd.DataFrame:
    """Compute B^T W B for the LR-channel-specific higher-rank sheaf."""
    required = {
        "sender",
        "receiver",
        "channel_id",
        "restriction_sender",
        "restriction_receiver",
        "channel_edge_weight",
    }
    missing = required.difference(channel_table.columns)
    if missing:
        raise ValueError(f"Channel table is missing required columns: {sorted(missing)}")

    node_channels = sorted(
        set(channel_table["sender"].astype(str) + "|" + channel_table["channel_id"].astype(str))
        | set(channel_table["receiver"].astype(str) + "|" + channel_table["channel_id"].astype(str))
    )
    node_index = {node_channel: idx for idx, node_channel in enumerate(node_channels)}
    b = np.zeros((len(channel_table), len(node_channels)), dtype=float)
    weights = channel_table["channel_edge_weight"].astype(float).to_numpy()
    for row_idx, row in enumerate(channel_table.itertuples(index=False)):
        channel_id = str(getattr(row, "channel_id"))
        sender_key = f"{getattr(row, 'sender')}|{channel_id}"
        receiver_key = f"{getattr(row, 'receiver')}|{channel_id}"
        b[row_idx, node_index[sender_key]] = float(getattr(row, "restriction_sender"))
        b[row_idx, node_index[receiver_key]] = float(getattr(row, "restriction_receiver"))
    laplacian = b.T @ np.diag(weights) @ b
    matrix = pd.DataFrame(laplacian, index=node_channels, columns=node_channels)
    matrix.index.name = "cell_type|lr_channel"
    return matrix


def build_lr_channel_sheaf(
    profiles: pd.DataFrame,
    lr_db: pd.DataFrame,
    pathway_scores: pd.DataFrame,
    min_channel_flow: float = 0.0,
    allow_self: bool = False,
) -> LRChannelSheaf:
    """Construct the higher-rank LR-channel-specific sheaf contract."""
    channel_table = build_lr_channel_restriction_table(
        profiles=profiles,
        lr_db=lr_db,
        pathway_scores=pathway_scores,
        min_channel_flow=min_channel_flow,
        allow_self=allow_self,
    )
    edge_summary = summarize_lr_channel_sheaf(channel_table)
    laplacian = lr_channel_sheaf_laplacian(channel_table)
    return LRChannelSheaf(
        node_channels=list(laplacian.index.astype(str)),
        channel_table=channel_table,
        edge_summary=edge_summary,
        laplacian=laplacian,
    )


def annotate_cellular_sheaf_edges(edges: pd.DataFrame) -> pd.DataFrame:
    """Annotate edges with legacy rank-one sheaf residual and energy fields."""
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
    """Compute B^T W B for the legacy rank-one sheaf contract."""
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
