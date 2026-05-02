from pathlib import Path
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sheafsignal.core import compute_sheaf_energy
from sheafsignal.sheaf import build_restriction_table, sheaf_laplacian


def test_cellular_sheaf_residual_matches_legacy_mismatch():
    edges = pd.DataFrame(
        {
            "sender": ["A", "B"],
            "receiver": ["B", "A"],
            "communication_flow": [10.0, 2.0],
            "n_lr_pairs_total": [1, 1],
            "n_lr_pairs_active": [1, 1],
            "top_lr_pairs": ["L->R", "L->R"],
            "mean_sender_ligand": [1.0, 1.0],
            "mean_receiver_receptor": [1.0, 1.0],
        }
    )
    pathway_scores = pd.DataFrame(
        {
            "cell_type": ["A", "B"],
            "pathway_score_raw": [0.0, 1.0],
            "pathway_score": [-1.0, 1.0],
        }
    )

    out = compute_sheaf_energy(edges, pathway_scores)

    legacy = out["flow_z"] - out["pathway_gradient_z"]
    assert np.allclose(out["sheaf_residual"], legacy)
    assert np.allclose(out["sheaf_mismatch"], out["sheaf_residual"])
    assert {"restriction_sender", "restriction_receiver", "coboundary_expected_flow"}.issubset(
        out.columns
    )


def test_restriction_table_and_laplacian_are_rank_one_sheaf_contract():
    edges = pd.DataFrame(
        {
            "sender": ["A", "B"],
            "receiver": ["B", "C"],
            "edge_weight": [1.0, 2.0],
        }
    )

    restrictions = build_restriction_table(edges)
    laplacian = sheaf_laplacian(edges)

    assert list(restrictions["restriction_sender"]) == [-1.0, -1.0]
    assert list(restrictions["restriction_receiver"]) == [1.0, 1.0]
    assert laplacian.matrix.shape == (3, 3)
    assert np.allclose(laplacian.matrix.to_numpy(), laplacian.matrix.to_numpy().T)
    assert np.isclose(laplacian.matrix.loc["B", "B"], 3.0)

