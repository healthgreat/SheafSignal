from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sheafsignal.core import (
    build_directed_lr_edges,
    compute_pathway_scores,
    compute_sheaf_energy,
    make_cell_type_profiles,
)


def test_make_cell_type_profiles_is_invariant_to_cell_order():
    expression = pd.DataFrame(
        {
            "L1": [10.0, 14.0, 1.0, 3.0],
            "R1": [2.0, 4.0, 8.0, 10.0],
        },
        index=["cell_a1", "cell_a2", "cell_b1", "cell_b2"],
    )
    metadata = pd.DataFrame(
        {"cell_type": ["A", "A", "B", "B"]},
        index=expression.index,
    )
    shuffled = ["cell_b2", "cell_a1", "cell_b1", "cell_a2"]

    original = make_cell_type_profiles(expression, metadata)
    permuted = make_cell_type_profiles(expression.loc[shuffled], metadata.loc[shuffled])

    pd.testing.assert_frame_equal(original.profiles, permuted.profiles)
    pd.testing.assert_series_equal(original.n_cells_by_type, permuted.n_cells_by_type)


def test_compute_pathway_scores_counts_missing_genes_and_blocks_all_missing():
    profiles = pd.DataFrame(
        {"P1": [1.0, 3.0], "P2": [2.0, 4.0]},
        index=["A", "B"],
    )

    scores = compute_pathway_scores(profiles, ["P1", "ABSENT"])

    assert scores["n_pathway_genes_used"].nunique() == 1
    assert scores["n_pathway_genes_used"].iloc[0] == 1
    assert scores["n_pathway_genes_missing"].iloc[0] == 1
    with pytest.raises(ValueError, match="None of the pathway genes"):
        compute_pathway_scores(profiles, ["ABSENT"])


def test_build_directed_lr_edges_respects_threshold_and_self_edges():
    profiles = pd.DataFrame(
        {
            "L1": [5.0, 1.0],
            "R1": [1.0, 4.0],
            "L2": [0.0, 2.0],
            "R2": [2.0, 0.0],
        },
        index=["A", "B"],
    )
    lr_db = pd.DataFrame(
        {
            "ligand": ["L1", "L2", "MISSING"],
            "receptor": ["R1", "R2", "R1"],
            "weight": [1.0, 2.0, 1.0],
        }
    )

    edges = build_directed_lr_edges(
        profiles,
        lr_db,
        min_communication=10.0,
        allow_self=False,
    )

    assert list(edges[["sender", "receiver"]].itertuples(index=False, name=None)) == [
        ("A", "B")
    ]
    assert edges.loc[0, "communication_flow"] == 20.0
    assert edges.loc[0, "n_lr_pairs_total"] == 2
    assert edges.loc[0, "top_lr_pairs"] == "L1->R1"


def test_compute_sheaf_energy_is_nonnegative_and_symmetric_for_reversed_edges():
    edges = pd.DataFrame(
        {
            "sender": ["A", "B"],
            "receiver": ["B", "A"],
            "communication_flow": [5.0, 5.0],
            "n_lr_pairs_total": [1, 1],
            "n_lr_pairs_active": [1, 1],
            "top_lr_pairs": ["L1->R1", "L1->R1"],
            "mean_sender_ligand": [1.0, 1.0],
            "mean_receiver_receptor": [1.0, 1.0],
        }
    )
    pathway_scores = pd.DataFrame(
        {
            "cell_type": ["A", "B"],
            "pathway_score_raw": [0.0, 10.0],
            "pathway_score": [-1.0, 1.0],
            "n_pathway_genes_used": [1, 1],
            "n_pathway_genes_missing": [0, 0],
        }
    )

    out = compute_sheaf_energy(edges, pathway_scores)
    by_edge = out.set_index(["sender", "receiver"])

    assert np.all(by_edge["sheaf_energy"] >= 0)
    assert by_edge.loc[("A", "B"), "sheaf_energy"] == pytest.approx(
        by_edge.loc[("B", "A"), "sheaf_energy"]
    )
    assert by_edge.loc[("A", "B"), "sheaf_residual"] == pytest.approx(
        -by_edge.loc[("B", "A"), "sheaf_residual"]
    )


def test_compute_sheaf_energy_blocks_unknown_pathway_cell_type():
    edges = pd.DataFrame(
        {"sender": ["A"], "receiver": ["B"], "communication_flow": [1.0]}
    )
    pathway_scores = pd.DataFrame(
        {"cell_type": ["A"], "pathway_score_raw": [0.0], "pathway_score": [0.0]}
    )

    with pytest.raises(ValueError, match="without pathway score"):
        compute_sheaf_energy(edges, pathway_scores)
