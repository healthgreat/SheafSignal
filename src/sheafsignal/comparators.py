from __future__ import annotations

import numpy as np
import pandas as pd


LR_PRODUCT_BASELINE = "LRProductBaseline"
SUPPORTED_AGGREGATIONS = {"sum", "mean", "max"}


def _descending_rank(values: pd.Series) -> pd.Series:
    return values.astype(float).rank(method="average", ascending=False)


def _descending_percentile(values: pd.Series) -> pd.Series:
    ranks = _descending_rank(values)
    n = len(ranks)
    if n <= 1:
        return pd.Series(np.ones(n), index=values.index, dtype=float)
    return 1.0 - ((ranks - 1.0) / float(n - 1))


def _split_lr_pairs(value: object) -> list[str]:
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "na"}:
        return []
    pairs = []
    for item in text.split(";"):
        item = item.strip()
        if item and item.lower() not in {"nan", "none", "na"}:
            pairs.append(item)
    return pairs


def _jaccard(left: set[str], right: set[str]) -> float:
    union = left.union(right)
    if not union:
        return np.nan
    return float(len(left.intersection(right)) / len(union))


def _rank_corr_by_axis(
    aligned_edges: pd.DataFrame,
    axis: str,
) -> float:
    valid = aligned_edges.dropna(subset=["sheaf_energy", "comparator_edge_score"]).copy()
    if valid.empty or axis not in valid.columns:
        return np.nan
    grouped = (
        valid.groupby(axis, dropna=False)
        .agg(
            sheaf_axis_score=("sheaf_energy", "max"),
            comparator_axis_score=("comparator_edge_score", "max"),
        )
        .reset_index()
    )
    if len(grouped) < 2:
        return np.nan
    return float(
        grouped["sheaf_axis_score"]
        .rank()
        .corr(grouped["comparator_axis_score"].rank())
    )


def top_lr_jaccard(aligned_edges: pd.DataFrame, top_n: int = 20) -> float:
    """Jaccard overlap between top SheafSignal and comparator LR pairs."""
    if top_n <= 0:
        raise ValueError("top_n must be positive.")
    sheaf_col = "sheaf_top_lr_pairs"
    comparator_cols = ["comparator_top_lr_pairs", "comparator_all_lr_pairs"]
    if sheaf_col not in aligned_edges.columns:
        return np.nan

    sheaf_pairs: list[str] = []
    sheaf_ranked = aligned_edges.dropna(subset=["sheaf_energy"]).sort_values(
        "sheaf_energy",
        ascending=False,
    )
    for value in sheaf_ranked[sheaf_col].tolist():
        sheaf_pairs.extend(_split_lr_pairs(value))
        if len(set(sheaf_pairs)) >= top_n:
            break

    comparator_pairs: list[str] = []
    comparator_ranked = aligned_edges.dropna(subset=["comparator_edge_score"]).sort_values(
        "comparator_edge_score",
        ascending=False,
    )
    for _, row in comparator_ranked.iterrows():
        for col in comparator_cols:
            if col in row.index:
                comparator_pairs.extend(_split_lr_pairs(row[col]))
        if len(set(comparator_pairs)) >= top_n:
            break

    return _jaccard(set(sheaf_pairs[:top_n]), set(comparator_pairs[:top_n]))


def lr_product_baseline_from_sheaf_edges(edges: pd.DataFrame) -> pd.DataFrame:
    """Extract a conventional LR-product edge score from SheafSignal edges.

    SheafSignal uses ligand expression x receptor expression as the input flow
    layer before adding pathway-gradient consistency. This helper exports that
    conventional communication strength as an explicit baseline comparator.
    """
    required = {"sender", "receiver", "communication_flow"}
    missing = required.difference(edges.columns)
    if missing:
        raise ValueError(f"Sheaf edge table is missing required columns: {sorted(missing)}")

    columns = [
        "sender",
        "receiver",
        "communication_flow",
        "n_lr_pairs_total",
        "n_lr_pairs_active",
        "top_lr_pairs",
        "mean_sender_ligand",
        "mean_receiver_receptor",
    ]
    present = [column for column in columns if column in edges.columns]
    out = edges[present].copy()
    out = out.rename(columns={"communication_flow": "comparator_edge_score"})
    out["tool"] = LR_PRODUCT_BASELINE
    out["comparator_edge_score_log1p"] = np.log1p(out["comparator_edge_score"].astype(float))
    out["comparator_score_rank"] = _descending_rank(out["comparator_edge_score"])
    out["comparator_score_percentile"] = _descending_percentile(out["comparator_edge_score"])
    return out.sort_values(
        ["comparator_edge_score", "sender", "receiver"],
        ascending=[False, True, True],
    ).reset_index(drop=True)


def standardize_external_comparator_edges(
    table: pd.DataFrame,
    *,
    tool: str,
    sender_col: str = "sender",
    receiver_col: str = "receiver",
    score_col: str = "score",
    ligand_col: str | None = None,
    receptor_col: str | None = None,
    aggregate: str = "max",
    score_ascending: bool = False,
) -> pd.DataFrame:
    """Convert an external CCC edge table to SheafSignal comparator schema.

    External tools differ in whether they report one row per cell-type edge or
    one row per ligand-receptor interaction. This function accepts either and
    aggregates duplicate sender-receiver rows to one score per directed edge.
    """
    aggregate = aggregate.lower()
    if aggregate not in SUPPORTED_AGGREGATIONS:
        raise ValueError(f"aggregate must be one of {sorted(SUPPORTED_AGGREGATIONS)}")

    required = {sender_col, receiver_col, score_col}
    missing = required.difference(table.columns)
    if missing:
        raise ValueError(f"External comparator table is missing columns: {sorted(missing)}")

    df = table.copy()
    df = df.rename(
        columns={
            sender_col: "sender",
            receiver_col: "receiver",
            score_col: "raw_comparator_edge_score",
        }
    )
    df["sender"] = df["sender"].astype(str)
    df["receiver"] = df["receiver"].astype(str)
    df["raw_comparator_edge_score"] = pd.to_numeric(
        df["raw_comparator_edge_score"],
        errors="coerce",
    )
    df = df.dropna(subset=["sender", "receiver", "raw_comparator_edge_score"])

    if score_ascending:
        max_score = float(df["raw_comparator_edge_score"].max()) if len(df) else 0.0
        df["comparator_edge_score"] = max_score - df["raw_comparator_edge_score"]
    else:
        df["comparator_edge_score"] = df["raw_comparator_edge_score"]

    if ligand_col and receptor_col and ligand_col in table.columns and receptor_col in table.columns:
        ligand_values = table.loc[df.index, ligand_col].astype(str)
        receptor_values = table.loc[df.index, receptor_col].astype(str)
        df["lr_pair"] = ligand_values + "->" + receptor_values
    else:
        df["lr_pair"] = ""

    grouped_rows = []
    for (sender, receiver), group in df.groupby(["sender", "receiver"], sort=False):
        scores = group["comparator_edge_score"].astype(float)
        if aggregate == "sum":
            edge_score = float(scores.sum())
        elif aggregate == "mean":
            edge_score = float(scores.mean())
        else:
            edge_score = float(scores.max())

        lr_pairs = ""
        all_lr_pairs = ""
        if group["lr_pair"].astype(bool).any():
            ranked = group.loc[group["lr_pair"].astype(bool)].sort_values(
                "comparator_edge_score",
                ascending=False,
            )
            unique_pairs = list(dict.fromkeys(ranked["lr_pair"].tolist()))
            lr_pairs = ";".join(unique_pairs[:5])
            all_lr_pairs = ";".join(unique_pairs)

        grouped_rows.append(
            {
                "sender": sender,
                "receiver": receiver,
                "comparator_edge_score": edge_score,
                "n_tool_rows": int(len(group)),
                "top_lr_pairs": lr_pairs,
                "all_lr_pairs": all_lr_pairs,
                "tool": tool,
            }
        )

    out = pd.DataFrame(grouped_rows)
    if out.empty:
        raise ValueError("External comparator table has no valid sender-receiver score rows.")
    out["comparator_edge_score_log1p"] = np.log1p(out["comparator_edge_score"].clip(lower=0))
    out["comparator_score_rank"] = _descending_rank(out["comparator_edge_score"])
    out["comparator_score_percentile"] = _descending_percentile(out["comparator_edge_score"])
    return out.sort_values(
        ["comparator_edge_score", "sender", "receiver"],
        ascending=[False, True, True],
    ).reset_index(drop=True)


def standardize_cellchat_edges(table: pd.DataFrame) -> pd.DataFrame:
    """Standardize CellChat subsetCommunication-style output."""
    required = {"source", "target", "prob"}
    missing = required.difference(table.columns)
    if missing:
        raise ValueError(f"CellChat table is missing columns: {sorted(missing)}")
    ligand_col = "ligand" if "ligand" in table.columns else None
    receptor_col = "receptor" if "receptor" in table.columns else None
    return standardize_external_comparator_edges(
        table,
        tool="CellChat",
        sender_col="source",
        receiver_col="target",
        score_col="prob",
        ligand_col=ligand_col,
        receptor_col=receptor_col,
        aggregate="sum",
    )


def _clean_cpdb_partner(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if ":" in text:
        text = text.split(":", 1)[1]
    return text.strip()


def standardize_cellphonedb_edges(
    table: pd.DataFrame,
    *,
    cell_pair_separator: str = "|",
) -> pd.DataFrame:
    """Standardize CellPhoneDB means/significant_means-style wide output."""
    metadata_cols = {
        "id_cp_interaction",
        "interacting_pair",
        "partner_a",
        "partner_b",
        "gene_a",
        "gene_b",
        "secreted",
        "receptor_a",
        "receptor_b",
        "annotation_strategy",
        "is_integrin",
        "rank",
        "classification",
        "directionality",
    }
    score_cols = [
        col
        for col in table.columns
        if col not in metadata_cols and cell_pair_separator in str(col)
    ]
    if not score_cols:
        raise ValueError("CellPhoneDB table has no sender|receiver score columns.")
    rows = []
    for row in table.to_dict(orient="records"):
        ligand = _clean_cpdb_partner(row.get("gene_a", "")) or _clean_cpdb_partner(
            row.get("partner_a", "")
        )
        receptor = _clean_cpdb_partner(row.get("gene_b", "")) or _clean_cpdb_partner(
            row.get("partner_b", "")
        )
        for score_col in score_cols:
            sender, receiver = str(score_col).split(cell_pair_separator, 1)
            rows.append(
                {
                    "sender": sender,
                    "receiver": receiver,
                    "score": row.get(score_col),
                    "ligand": ligand,
                    "receptor": receptor,
                }
            )
    return standardize_external_comparator_edges(
        pd.DataFrame(rows),
        tool="CellPhoneDB",
        sender_col="sender",
        receiver_col="receiver",
        score_col="score",
        ligand_col="ligand",
        receptor_col="receptor",
        aggregate="sum",
    )


def align_sheaf_edges_with_comparator(
    sheaf_edges: pd.DataFrame,
    comparator_edges: pd.DataFrame,
    tool: str = LR_PRODUCT_BASELINE,
) -> pd.DataFrame:
    """Align SheafSignal inconsistency metrics with comparator edge scores."""
    required_sheaf = {"sender", "receiver", "sheaf_energy"}
    missing_sheaf = required_sheaf.difference(sheaf_edges.columns)
    if missing_sheaf:
        raise ValueError(f"Sheaf edge table is missing required columns: {sorted(missing_sheaf)}")

    required_comparator = {"sender", "receiver", "comparator_edge_score"}
    missing_comparator = required_comparator.difference(comparator_edges.columns)
    if missing_comparator:
        raise ValueError(
            f"Comparator edge table is missing required columns: {sorted(missing_comparator)}"
        )

    sheaf_cols = [
        "sender",
        "receiver",
        "sheaf_energy",
        "sheaf_mismatch",
        "flow_z",
        "pathway_gradient_z",
        "directional_agreement",
        "curl_component",
        "harmonic_component",
        "top_lr_pairs",
    ]
    sheaf_present = [column for column in sheaf_cols if column in sheaf_edges.columns]
    sheaf = sheaf_edges[sheaf_present].copy()
    if "top_lr_pairs" in sheaf.columns:
        sheaf = sheaf.rename(columns={"top_lr_pairs": "sheaf_top_lr_pairs"})
    sheaf["sheaf_energy_rank"] = _descending_rank(sheaf["sheaf_energy"])
    sheaf["sheaf_energy_percentile"] = _descending_percentile(sheaf["sheaf_energy"])

    comparator_cols = [
        "sender",
        "receiver",
        "comparator_edge_score",
        "comparator_edge_score_log1p",
        "comparator_score_rank",
        "comparator_score_percentile",
        "n_lr_pairs_active",
        "top_lr_pairs",
        "all_lr_pairs",
        "n_tool_rows",
    ]
    comparator_present = [column for column in comparator_cols if column in comparator_edges.columns]
    comparator = comparator_edges[comparator_present].copy()
    comparator = comparator.rename(
        columns={
            "top_lr_pairs": "comparator_top_lr_pairs",
            "all_lr_pairs": "comparator_all_lr_pairs",
        }
    )

    aligned = sheaf.merge(
        comparator,
        on=["sender", "receiver"],
        how="outer",
        indicator="alignment_status",
    )
    aligned["tool"] = tool
    aligned["sheaf_minus_comparator_percentile"] = (
        aligned["sheaf_energy_percentile"] - aligned["comparator_score_percentile"]
    )
    aligned["discordance_class"] = [
        classify_edge_discordance(sheaf_pct, comparator_pct)
        for sheaf_pct, comparator_pct in zip(
            aligned["sheaf_energy_percentile"],
            aligned["comparator_score_percentile"],
        )
    ]
    return aligned.sort_values(
        ["sheaf_energy", "comparator_edge_score"],
        ascending=[False, False],
    ).reset_index(drop=True)


def classify_edge_discordance(sheaf_percentile: float, comparator_percentile: float) -> str:
    """Classify whether conventional LR strength and sheaf energy disagree."""
    if pd.isna(sheaf_percentile) or pd.isna(comparator_percentile):
        return "unaligned"
    if sheaf_percentile >= 0.75 and comparator_percentile <= 0.25:
        return "high_sheaf_low_comparator"
    if comparator_percentile >= 0.75 and sheaf_percentile <= 0.25:
        return "high_comparator_low_sheaf"
    if sheaf_percentile >= 0.75 and comparator_percentile >= 0.75:
        return "concordant_high"
    if sheaf_percentile <= 0.25 and comparator_percentile <= 0.25:
        return "concordant_low"
    return "intermediate"


def comparator_summary(aligned_edges: pd.DataFrame) -> dict[str, object]:
    """Summarize an edge-aligned comparator table."""
    required = {"sheaf_energy", "comparator_edge_score", "discordance_class"}
    missing = required.difference(aligned_edges.columns)
    if missing:
        raise ValueError(f"Aligned comparator table is missing required columns: {sorted(missing)}")

    valid = aligned_edges[["sheaf_energy", "comparator_edge_score"]].dropna()
    if len(valid) >= 2:
        rho = float(valid["sheaf_energy"].rank().corr(valid["comparator_edge_score"].rank()))
    else:
        rho = np.nan

    classes = aligned_edges["discordance_class"].value_counts().to_dict()
    top_lr_overlap = top_lr_jaccard(aligned_edges)
    return {
        "n_edges": int(len(aligned_edges)),
        "spearman_sheaf_energy_vs_tool_score": rho,
        "sender_rank_spearman": _rank_corr_by_axis(aligned_edges, "sender"),
        "receiver_rank_spearman": _rank_corr_by_axis(aligned_edges, "receiver"),
        "top_lr_jaccard": top_lr_overlap,
        "high_sheaf_low_tool_edges": int(classes.get("high_sheaf_low_comparator", 0)),
        "high_tool_low_sheaf_edges": int(classes.get("high_comparator_low_sheaf", 0)),
        "concordant_high_edges": int(classes.get("concordant_high", 0)),
        "unaligned_edges": int(classes.get("unaligned", 0)),
    }
