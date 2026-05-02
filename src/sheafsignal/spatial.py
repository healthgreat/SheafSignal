from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from .core import EPS, zscore
from .io import read_expression, read_gene_set, read_ligand_receptor_db, read_metadata


def build_spatial_neighbor_edges(metadata: pd.DataFrame, k_neighbors: int = 6) -> pd.DataFrame:
    """Build directed k-nearest-neighbor edges between Visium spots."""
    if k_neighbors <= 0:
        raise ValueError("k_neighbors must be positive.")
    required = {"cell_id", "x", "y"}
    missing = required.difference(metadata.columns)
    if missing:
        raise ValueError(f"Spatial metadata is missing columns: {sorted(missing)}")

    meta = metadata.copy()
    meta["cell_id"] = meta["cell_id"].astype(str)
    coords = meta[["x", "y"]].astype(float).to_numpy()
    n_spots = len(meta)
    if n_spots < 2:
        raise ValueError("At least two spatial spots are required.")

    k = min(k_neighbors + 1, n_spots)
    tree = cKDTree(coords)
    distances, indices = tree.query(coords, k=k)
    if k == 1:
        distances = distances[:, None]
        indices = indices[:, None]

    rows = []
    spot_ids = meta["cell_id"].to_numpy(dtype=object)
    for source_idx in range(n_spots):
        for distance, target_idx in zip(distances[source_idx], indices[source_idx]):
            target_idx = int(target_idx)
            if target_idx == source_idx:
                continue
            rows.append(
                {
                    "sender": str(spot_ids[source_idx]),
                    "receiver": str(spot_ids[target_idx]),
                    "spatial_distance": float(distance),
                }
            )
    return pd.DataFrame(rows)


def compute_spatial_sheaf_edges(
    expression: pd.DataFrame,
    metadata: pd.DataFrame,
    lr_db: pd.DataFrame,
    pathway_genes: list[str],
    k_neighbors: int = 6,
) -> pd.DataFrame:
    """Compute spot-neighbor LR/pathway sheaf mismatch over a spatial graph."""
    common = expression.index.astype(str).intersection(metadata["cell_id"].astype(str))
    if len(common) == 0:
        raise ValueError("No overlapping spot IDs between expression and spatial metadata.")

    expression = expression.loc[common].copy()
    metadata = metadata.set_index("cell_id").loc[common].reset_index()

    present_pathway = [gene for gene in pathway_genes if gene in expression.columns]
    if not present_pathway:
        raise ValueError("None of the pathway genes are present in spatial expression.")

    lr = lr_db.copy()
    valid = lr["ligand"].isin(expression.columns) & lr["receptor"].isin(expression.columns)
    lr = lr.loc[valid].reset_index(drop=True)
    if lr.empty:
        raise ValueError("No LR pairs have both ligand and receptor in spatial expression.")

    pathway_raw = expression[present_pathway].mean(axis=1)
    pathway_score = pd.Series(zscore(pathway_raw), index=expression.index)
    neighbor_edges = build_spatial_neighbor_edges(metadata, k_neighbors=k_neighbors)

    ligands = lr["ligand"].astype(str).to_list()
    receptors = lr["receptor"].astype(str).to_list()
    weights = lr["weight"].astype(float).to_numpy()
    lr_names = [f"{ligand}->{receptor}" for ligand, receptor in zip(ligands, receptors)]

    rows = []
    for edge in neighbor_edges.itertuples(index=False):
        sender_values = expression.loc[edge.sender, ligands].to_numpy(dtype=float)
        receiver_values = expression.loc[edge.receiver, receptors].to_numpy(dtype=float)
        pair_strength = sender_values * receiver_values * weights
        communication = float(pair_strength.sum())
        active_idx = np.flatnonzero(pair_strength > 0)
        if active_idx.size:
            order = active_idx[np.argsort(pair_strength[active_idx])[::-1]]
            top = ";".join(lr_names[i] for i in order[:5])
        else:
            top = ""
        rows.append(
            {
                "sender": edge.sender,
                "receiver": edge.receiver,
                "spatial_distance": edge.spatial_distance,
                "communication_flow": communication,
                "n_lr_pairs_total": int(len(lr)),
                "n_lr_pairs_active": int(active_idx.size),
                "top_lr_pairs": top,
                "sender_pathway_score": float(pathway_score.loc[edge.sender]),
                "receiver_pathway_score": float(pathway_score.loc[edge.receiver]),
                "sender_pathway_score_raw": float(pathway_raw.loc[edge.sender]),
                "receiver_pathway_score_raw": float(pathway_raw.loc[edge.receiver]),
            }
        )

    edges = pd.DataFrame(rows)
    edges["pathway_gradient"] = edges["receiver_pathway_score"] - edges["sender_pathway_score"]
    edges["log_communication_flow"] = np.log1p(edges["communication_flow"].astype(float))
    edges["flow_z"] = zscore(edges["log_communication_flow"])
    edges["pathway_gradient_z"] = zscore(edges["pathway_gradient"])
    max_flow = float(edges["communication_flow"].max())
    edges["edge_weight"] = edges["communication_flow"] / max_flow if max_flow > EPS else 0.0
    edges["sheaf_mismatch"] = edges["flow_z"] - edges["pathway_gradient_z"]
    edges["sheaf_energy_unweighted"] = edges["sheaf_mismatch"] ** 2
    edges["sheaf_energy"] = edges["edge_weight"] * edges["sheaf_energy_unweighted"]
    edges["directional_agreement"] = np.sign(edges["flow_z"]) == np.sign(
        edges["pathway_gradient_z"]
    )
    return edges.sort_values("sheaf_energy", ascending=False).reset_index(drop=True)


def summarize_spatial_hotspots(
    edges: pd.DataFrame,
    metadata: pd.DataFrame,
    dataset_id: str,
) -> pd.DataFrame:
    """Summarize outgoing spatial sheaf energy as spot-level hotspots."""
    total_energy = float(edges["sheaf_energy"].sum())
    outgoing = (
        edges.groupby("sender")
        .agg(
            local_sheaf_energy=("sheaf_energy", "sum"),
            n_outgoing_edges=("receiver", "size"),
            mean_neighbor_distance=("spatial_distance", "mean"),
        )
        .reset_index()
        .rename(columns={"sender": "cell_id"})
    )
    outgoing["frustration_score"] = (
        outgoing["local_sheaf_energy"] / total_energy if total_energy > EPS else 0.0
    )

    keep_cols = [
        "cell_id",
        "spot_id",
        "x",
        "y",
        "array_row",
        "array_col",
        "cell_type",
        "marker_score",
        "marker_score_margin",
    ]
    meta_cols = [column for column in keep_cols if column in metadata.columns]
    hotspots = metadata[meta_cols].merge(outgoing, on="cell_id", how="left")
    hotspots["local_sheaf_energy"] = hotspots["local_sheaf_energy"].fillna(0.0)
    hotspots["frustration_score"] = hotspots["frustration_score"].fillna(0.0)
    hotspots["n_outgoing_edges"] = hotspots["n_outgoing_edges"].fillna(0).astype(int)
    hotspots["dataset_id"] = dataset_id
    hotspots["status"] = "completed"
    hotspots["notes"] = (
        "Spot-level spatial sheaf energy over k-nearest Visium neighbors; "
        "marker labels are dominant spot programs, not single-cell annotations."
    )
    rename = {"cell_id": "spot_id"} if "spot_id" not in hotspots.columns else {}
    hotspots = hotspots.rename(columns=rename)
    ordered = [
        "dataset_id",
        "status",
        "spot_id",
        "x",
        "y",
        "array_row",
        "array_col",
        "cell_type",
        "frustration_score",
        "local_sheaf_energy",
        "n_outgoing_edges",
        "mean_neighbor_distance",
        "marker_score",
        "marker_score_margin",
        "notes",
    ]
    return hotspots[ordered].sort_values("frustration_score", ascending=False)


def run_spatial_hotspot_pipeline(
    expression_path: str | Path,
    metadata_path: str | Path,
    lr_db_path: str | Path,
    gene_set_path: str | Path,
    output_dir: str | Path,
    dataset_id: str,
    k_neighbors: int = 6,
) -> tuple[Path, Path, Path]:
    """Run spatial sheaf hotspot scoring and write edge/hotspot/summary tables."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    expression = read_expression(expression_path)
    metadata = read_metadata(metadata_path).reset_index(drop=True)
    lr_db = read_ligand_receptor_db(lr_db_path)
    pathway_genes = read_gene_set(gene_set_path)

    edges = compute_spatial_sheaf_edges(
        expression=expression,
        metadata=metadata,
        lr_db=lr_db,
        pathway_genes=pathway_genes,
        k_neighbors=k_neighbors,
    )
    hotspots = summarize_spatial_hotspots(edges, metadata, dataset_id=dataset_id)
    summary = pd.DataFrame(
        [
            {
                "dataset_id": dataset_id,
                "status": "completed",
                "n_spots": int(metadata.shape[0]),
                "n_spatial_edges": int(edges.shape[0]),
                "total_spatial_sheaf_energy": float(edges["sheaf_energy"].sum()),
                "top_hotspot_spot_id": str(hotspots.iloc[0]["spot_id"]),
                "top_hotspot_score": float(hotspots.iloc[0]["frustration_score"]),
                "k_neighbors": int(k_neighbors),
            }
        ]
    )

    edge_path = output_dir / "spatial_sheaf_edges.csv"
    hotspot_path = output_dir / "spatial_frustration_hotspots.csv"
    summary_path = output_dir / "spatial_hotspot_summary.csv"
    edges.to_csv(edge_path, index=False)
    hotspots.to_csv(hotspot_path, index=False)
    summary.to_csv(summary_path, index=False)
    return edge_path, hotspot_path, summary_path
