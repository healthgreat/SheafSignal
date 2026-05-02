from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sheafsignal.hodge import hodge_decomposition
from sheafsignal.simulate import scenario_edges


def test_harmonic_ring_is_harmonic_dominated():
    edges = scenario_edges("harmonic_ring")
    _, scores = hodge_decomposition(edges)
    assert scores["harmonic_ratio"] > 0.99


def test_gradient_chain_simulation_is_gradient_dominated():
    edges = scenario_edges("gradient_chain")
    _, scores = hodge_decomposition(edges)
    assert scores["gradient_ratio"] > 0.99
