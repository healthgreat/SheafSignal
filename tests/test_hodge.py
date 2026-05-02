from pathlib import Path
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sheafsignal.hodge import hodge_decomposition


def test_triangle_cycle_is_curl_dominated():
    edges = pd.DataFrame(
        {
            "sender": ["A", "B", "C"],
            "receiver": ["B", "C", "A"],
            "flow_z": [1.0, 1.0, 1.0],
        }
    )
    _, scores = hodge_decomposition(edges, flow_col="flow_z")
    assert scores["curl_ratio"] > 0.99
    assert scores["gradient_ratio"] < 1e-10


def test_tree_flow_is_gradient_dominated():
    edges = pd.DataFrame(
        {
            "sender": ["A", "B"],
            "receiver": ["B", "C"],
            "flow_z": [1.0, 1.0],
        }
    )
    _, scores = hodge_decomposition(edges, flow_col="flow_z")
    assert scores["gradient_ratio"] > 0.99
    assert scores["curl_ratio"] == 0.0
