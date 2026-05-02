from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .sheaf import annotate_cellular_sheaf_edges


EPS = 1e-12


@dataclass(frozen=True)
class ProfileResult:
    profiles: pd.DataFrame
    n_cells_by_type: pd.Series


def zscore(values: pd.Series | np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    mean = np.nanmean(arr)
    std = np.nanstd(arr)
    if not np.isfinite(std) or std < EPS:
        return np.zeros_like(arr, dtype=float)
    return (arr - mean) / std


def normalize_expression(expr: pd.DataFrame, method: str = "cpm_log1p") -> pd.DataFrame:
    """Normalize expression values."""
    method = method.lower()
    expr = expr.astype(float)

    if method == "none":
        return expr.copy()
    if method == "log1p":
        return np.log1p(expr)
    if method == "cpm_log1p":
        lib_size = expr.sum(axis=1).replace(0, np.nan)
        scaled = expr.div(lib_size, axis=0).fillna(0.0) * 1e4
        return np.log1p(scaled)
    raise ValueError("method must be one of: none, log1p, cpm_log1p")


def make_cell_type_profiles(
    expr: pd.DataFrame,
    metadata: pd.DataFrame,
    cell_type_col: str = "cell_type",
) -> ProfileResult:
    """Aggregate a cells x genes matrix to cell-type means."""
    if cell_type_col not in metadata.columns:
        raise ValueError(f"Metadata must contain '{cell_type_col}'.")

    common = expr.index.astype(str).intersection(metadata.index.astype(str))
    if len(common) == 0:
        raise ValueError("No overlapping cell IDs between expression and metadata.")

    expr_aligned = expr.loc[common]
    meta_aligned = metadata.loc[common]
    cell_type = meta_aligned[cell_type_col].astype(str)

    profiles = expr_aligned.groupby(cell_type).mean()
    counts = cell_type.value_counts().sort_index()
    profiles.index.name = "cell_type"
    return ProfileResult(profiles=profiles, n_cells_by_type=counts)


def compute_pathway_scores(
    profiles: pd.DataFrame,
    pathway_genes: list[str],
) -> pd.DataFrame:
    """Compute cell-type pathway scores from mean expression of pathway genes."""
    present = [gene for gene in pathway_genes if gene in profiles.columns]
    missing = [gene for gene in pathway_genes if gene not in profiles.columns]
    if not present:
        raise ValueError("None of the pathway genes are present in expression matrix.")

    raw = profiles[present].mean(axis=1)
    scores = pd.DataFrame(
        {
            "cell_type": raw.index.astype(str),
            "pathway_score_raw": raw.to_numpy(dtype=float),
            "pathway_score": zscore(raw),
            "n_pathway_genes_used": len(present),
            "n_pathway_genes_missing": len(missing),
        }
    )
    return scores


def build_directed_lr_edges(
    profiles: pd.DataFrame,
    lr_db: pd.DataFrame,
    min_communication: float = 0.0,
    allow_self: bool = False,
) -> pd.DataFrame:
    """Build a directed cell-type communication graph from LR products."""
    lr = lr_db.copy()
    valid = lr["ligand"].isin(profiles.columns) & lr["receptor"].isin(profiles.columns)
    lr = lr.loc[valid].reset_index(drop=True)
    if lr.empty:
        raise ValueError("No LR pairs have both ligand and receptor in expression matrix.")

    ligands = lr["ligand"].to_list()
    receptors = lr["receptor"].to_list()
    weights = lr["weight"].astype(float).to_numpy()
    lr_names = [f"{ligand}->{receptor}" for ligand, receptor in zip(ligands, receptors)]

    rows = []
    cell_types = profiles.index.astype(str).to_list()
    for sender in cell_types:
        sender_ligands = profiles.loc[sender, ligands].to_numpy(dtype=float)
        for receiver in cell_types:
            if not allow_self and sender == receiver:
                continue
            receiver_receptors = profiles.loc[receiver, receptors].to_numpy(dtype=float)
            pair_strength = sender_ligands * receiver_receptors * weights
            communication = float(np.sum(pair_strength))
            if communication <= min_communication:
                continue

            active_idx = np.flatnonzero(pair_strength > 0)
            if active_idx.size:
                order = active_idx[np.argsort(pair_strength[active_idx])[::-1]]
                top = ";".join(lr_names[i] for i in order[:5])
            else:
                top = ""

            rows.append(
                {
                    "sender": sender,
                    "receiver": receiver,
                    "communication_flow": communication,
                    "n_lr_pairs_total": int(len(lr)),
                    "n_lr_pairs_active": int(active_idx.size),
                    "top_lr_pairs": top,
                    "mean_sender_ligand": float(np.mean(sender_ligands)),
                    "mean_receiver_receptor": float(np.mean(receiver_receptors)),
                }
            )

    if not rows:
        raise ValueError("No communication edges passed min_communication threshold.")
    return pd.DataFrame(rows)


def compute_sheaf_energy(edges: pd.DataFrame, pathway_scores: pd.DataFrame) -> pd.DataFrame:
    """Add edge-level sheaf consistency metrics."""
    score_map = pathway_scores.set_index("cell_type")["pathway_score"].to_dict()
    raw_map = pathway_scores.set_index("cell_type")["pathway_score_raw"].to_dict()

    out = edges.copy()
    out["sender_pathway_score"] = out["sender"].map(score_map)
    out["receiver_pathway_score"] = out["receiver"].map(score_map)
    out["sender_pathway_score_raw"] = out["sender"].map(raw_map)
    out["receiver_pathway_score_raw"] = out["receiver"].map(raw_map)

    if out[["sender_pathway_score", "receiver_pathway_score"]].isna().any().any():
        raise ValueError("At least one edge references a cell type without pathway score.")

    out["pathway_gradient"] = out["receiver_pathway_score"] - out["sender_pathway_score"]
    out["log_communication_flow"] = np.log1p(out["communication_flow"].astype(float))
    out["flow_z"] = zscore(out["log_communication_flow"])
    out["pathway_gradient_z"] = zscore(out["pathway_gradient"])

    max_flow = float(out["communication_flow"].max())
    if max_flow < EPS:
        out["edge_weight"] = 0.0
    else:
        out["edge_weight"] = out["communication_flow"] / max_flow

    out = annotate_cellular_sheaf_edges(out)
    return out.sort_values("sheaf_energy", ascending=False).reset_index(drop=True)


def compute_node_frustration(edges: pd.DataFrame) -> pd.DataFrame:
    """Summarize sender and receiver contributions to sheaf energy."""
    nodes = sorted(set(edges["sender"]).union(edges["receiver"]))
    total_energy = float(edges["sheaf_energy"].sum())
    total_curl = float(np.abs(edges.get("curl_component", 0.0)).sum())

    rows = []
    for node in nodes:
        outgoing = edges.loc[edges["sender"] == node, "sheaf_energy"].sum()
        incoming = edges.loc[edges["receiver"] == node, "sheaf_energy"].sum()
        if "curl_component" in edges.columns:
            curl_participation = np.abs(
                edges.loc[(edges["sender"] == node) | (edges["receiver"] == node), "curl_component"]
            ).sum()
        else:
            curl_participation = 0.0

        rows.append(
            {
                "cell_type": node,
                "frustration_score": outgoing / total_energy if total_energy > EPS else 0.0,
                "outgoing_sheaf_energy": float(outgoing),
                "incoming_sheaf_energy": float(incoming),
                "curl_participation": (
                    float(curl_participation) / total_curl if total_curl > EPS else 0.0
                ),
                "n_outgoing_edges": int((edges["sender"] == node).sum()),
                "n_incoming_edges": int((edges["receiver"] == node).sum()),
            }
        )

    return pd.DataFrame(rows).sort_values("frustration_score", ascending=False)
