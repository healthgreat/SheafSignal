import pandas as pd
import pytest

from sheafsignal.comparators import (
    LR_PRODUCT_BASELINE,
    align_sheaf_edges_with_comparator,
    comparator_summary,
    lr_product_baseline_from_sheaf_edges,
    standardize_cellchat_edges,
    standardize_cellphonedb_edges,
    standardize_external_comparator_edges,
)


def _toy_sheaf_edges() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "sender": ["A", "B", "C", "A"],
            "receiver": ["B", "C", "A", "C"],
            "communication_flow": [10.0, 1.0, 7.0, 2.0],
            "sheaf_energy": [0.2, 9.0, 1.0, 8.0],
            "sheaf_mismatch": [0.1, 3.0, 1.0, 2.5],
            "flow_z": [1.0, -1.0, 0.7, -0.2],
            "pathway_gradient_z": [0.9, 2.0, 0.1, -1.5],
            "directional_agreement": [True, False, True, False],
            "n_lr_pairs_active": [2, 1, 2, 1],
            "top_lr_pairs": ["L1->R1", "L2->R2", "L1->R1", "L3->R3"],
        }
    )


def test_lr_product_baseline_exports_ranked_edge_scores():
    baseline = lr_product_baseline_from_sheaf_edges(_toy_sheaf_edges())

    assert baseline.iloc[0]["sender"] == "A"
    assert baseline.iloc[0]["receiver"] == "B"
    assert baseline.iloc[0]["comparator_edge_score"] == 10.0
    assert baseline.iloc[0]["comparator_score_rank"] == 1.0
    assert baseline.iloc[0]["comparator_score_percentile"] == 1.0
    assert set(baseline["tool"]) == {LR_PRODUCT_BASELINE}


def test_align_sheaf_edges_with_comparator_marks_discordant_edges():
    sheaf = _toy_sheaf_edges()
    baseline = lr_product_baseline_from_sheaf_edges(sheaf)
    aligned = align_sheaf_edges_with_comparator(sheaf, baseline)

    classes = set(aligned["discordance_class"])
    assert "high_sheaf_low_comparator" in classes
    assert "high_comparator_low_sheaf" in classes
    assert "sheaf_minus_comparator_percentile" in aligned.columns

    summary = comparator_summary(aligned)
    assert summary["n_edges"] == 4
    assert summary["high_sheaf_low_tool_edges"] == 1
    assert summary["high_tool_low_sheaf_edges"] == 1
    assert "sender_rank_spearman" in summary
    assert "receiver_rank_spearman" in summary
    assert "top_lr_jaccard" in summary


def test_lr_product_baseline_requires_communication_flow():
    with pytest.raises(ValueError, match="communication_flow"):
        lr_product_baseline_from_sheaf_edges(pd.DataFrame({"sender": ["A"], "receiver": ["B"]}))


def test_standardize_external_comparator_edges_aggregates_lr_rows():
    external = pd.DataFrame(
        {
            "source": ["A", "A", "B"],
            "target": ["B", "B", "C"],
            "prob": [0.2, 0.8, 0.4],
            "ligand": ["L1", "L2", "L3"],
            "receptor": ["R1", "R2", "R3"],
        }
    )
    standardized = standardize_external_comparator_edges(
        external,
        tool="CellChat",
        sender_col="source",
        receiver_col="target",
        score_col="prob",
        ligand_col="ligand",
        receptor_col="receptor",
        aggregate="sum",
    )

    first = standardized.iloc[0]
    assert first["sender"] == "A"
    assert first["receiver"] == "B"
    assert first["comparator_edge_score"] == pytest.approx(1.0)
    assert first["n_tool_rows"] == 2
    assert first["top_lr_pairs"] == "L2->R2;L1->R1"
    assert first["all_lr_pairs"] == "L2->R2;L1->R1"


def test_standardize_cellchat_edges_uses_sum_probability():
    raw = pd.DataFrame(
        {
            "source": ["A", "A", "B"],
            "target": ["B", "B", "A"],
            "ligand": ["L1", "L2", "L3"],
            "receptor": ["R1", "R2", "R3"],
            "prob": [0.1, 0.3, 0.2],
        }
    )

    standardized = standardize_cellchat_edges(raw)

    ab = standardized.loc[
        (standardized["sender"] == "A") & (standardized["receiver"] == "B")
    ].iloc[0]
    assert ab["comparator_edge_score"] == pytest.approx(0.4)
    assert ab["top_lr_pairs"] == "L2->R2;L1->R1"
    assert set(standardized["tool"]) == {"CellChat"}


def test_standardize_cellphonedb_edges_melts_cell_pair_columns():
    raw = pd.DataFrame(
        {
            "interacting_pair": ["L1_R1", "L2_R2"],
            "gene_a": ["L1", "L2"],
            "gene_b": ["R1", ""],
            "partner_b": ["simple:R1", "complex:FLT1_complex"],
            "A|B": [0.2, 0.5],
            "B|A": [0.1, 0.0],
        }
    )

    standardized = standardize_cellphonedb_edges(raw)

    ab = standardized.loc[
        (standardized["sender"] == "A") & (standardized["receiver"] == "B")
    ].iloc[0]
    assert ab["comparator_edge_score"] == pytest.approx(0.7)
    assert ab["top_lr_pairs"] == "L2->FLT1_complex;L1->R1"
    assert set(standardized["tool"]) == {"CellPhoneDB"}
