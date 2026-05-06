from pathlib import Path
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sheafsignal.sheaf import (
    build_lr_channel_restriction_table,
    build_lr_channel_sheaf,
    lr_channel_sheaf_laplacian,
    summarize_lr_channel_sheaf,
)


def _profiles() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "L1": [9.0, 2.0, 1.0],
            "R1": [1.0, 8.0, 2.0],
            "L2": [1.0, 7.0, 2.0],
            "R2": [8.0, 1.0, 6.0],
        },
        index=["A", "B", "C"],
    )


def _lr_db() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ligand": ["L1", "L2"],
            "receptor": ["R1", "R2"],
            "weight": [1.0, 0.5],
        }
    )


def _pathway_scores() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "cell_type": ["A", "B", "C"],
            "pathway_score": [1.0, -1.0, 0.0],
            "pathway_score_raw": [3.0, 0.0, 1.5],
        }
    )


def test_lr_channel_restrictions_are_higher_rank_and_channel_specific():
    table = build_lr_channel_restriction_table(_profiles(), _lr_db(), _pathway_scores())

    assert table["vertex_stalk_dimension"].nunique() == 1
    assert table["vertex_stalk_dimension"].iloc[0] == 2
    assert table["channel_id"].nunique() == 2
    assert table["restriction_type"].eq("lr_expression_scaled_channel_map").all()
    assert not np.allclose(table["restriction_sender"].to_numpy(dtype=float), -1.0)
    assert not np.allclose(table["restriction_receiver"].to_numpy(dtype=float), 1.0)
    assert table.groupby(["sender", "receiver"])["channel_id"].nunique().max() == 2


def test_lr_channel_laplacian_uses_node_channel_coordinates():
    table = build_lr_channel_restriction_table(_profiles(), _lr_db(), _pathway_scores())
    laplacian = lr_channel_sheaf_laplacian(table)

    assert laplacian.shape == (6, 6)
    assert "A|lr1:L1->R1" in laplacian.index
    assert "B|lr2:L2->R2" in laplacian.index
    assert np.allclose(laplacian.to_numpy(), laplacian.to_numpy().T)


def test_lr_channel_edge_summary_aggregates_channel_residuals():
    table = build_lr_channel_restriction_table(_profiles(), _lr_db(), _pathway_scores())
    summary = summarize_lr_channel_sheaf(table)

    assert {
        "higher_rank_sheaf_energy",
        "mean_channel_sheaf_residual",
        "max_abs_channel_sheaf_residual",
        "n_lr_channels",
    }.issubset(summary.columns)
    assert summary["higher_rank_sheaf_energy"].ge(0).all()
    assert summary["n_lr_channels"].max() == 2


def test_build_lr_channel_sheaf_contract_returns_all_outputs():
    result = build_lr_channel_sheaf(_profiles(), _lr_db(), _pathway_scores())

    assert len(result.node_channels) == 6
    assert not result.channel_table.empty
    assert not result.edge_summary.empty
    assert result.laplacian.shape == (6, 6)
