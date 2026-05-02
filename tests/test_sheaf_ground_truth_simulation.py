from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sheafsignal.simulate import sheaf_ground_truth_edges, sheaf_ground_truth_recovery


def test_sheaf_ground_truth_edges_include_known_inconsistent_edges():
    edges = sheaf_ground_truth_edges()
    positives = edges.loc[edges["ground_truth_inconsistent"]]
    assert len(edges) == 12
    assert len(positives) == 3
    assert {"C3->C0", "C3->C1", "C2->C0"}.issubset(set(positives["edge_id"]))


def test_sheaf_energy_outperforms_lr_flow_on_ground_truth_recovery():
    recovery = sheaf_ground_truth_recovery()
    scores = recovery.set_index("method")["average_precision"].to_dict()
    assert scores["SheafSignal_sheaf_energy"] > scores["LRProductBaseline_communication_flow"]


def test_ground_truth_recovery_reports_required_baseline_families():
    recovery = sheaf_ground_truth_recovery()
    assert set(recovery["baseline_family"]) == {
        "sheaf_residual",
        "lr_intensity",
        "pathway_gradient",
        "hodge_only",
        "graph_centrality",
        "graph_smoothness",
    }
    assert recovery["auroc"].notna().all()
    assert recovery["average_precision"].notna().all()


def test_sheaf_energy_outperforms_non_sheaf_baselines_on_ground_truth_recovery():
    recovery = sheaf_ground_truth_recovery()
    scores = recovery.set_index("method")["average_precision"].to_dict()
    sheaf_score = scores["SheafSignal_sheaf_energy"]
    non_sheaf_scores = [
        score for method, score in scores.items() if method != "SheafSignal_sheaf_energy"
    ]
    assert sheaf_score > max(non_sheaf_scores)
