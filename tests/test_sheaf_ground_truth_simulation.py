from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sheafsignal.simulate import (
    independent_perturbation_edges,
    independent_perturbation_recovery,
    sheaf_ground_truth_edges,
    sheaf_ground_truth_recovery,
)


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
        "flow_gradient_product",
    }
    assert recovery["auroc"].notna().all()
    assert recovery["average_precision"].notna().all()


def test_ground_truth_recovery_includes_fair_flow_gradient_product_baseline():
    recovery = sheaf_ground_truth_recovery()
    row = recovery.set_index("method").loc["FlowGradientOpposition_product"]

    assert row["uses_lr_flow"]
    assert row["uses_pathway_state"]
    assert not row["uses_sheaf_residual"]


def test_residual_aligned_ground_truth_is_explicitly_labeled_as_definition_dependent():
    recovery = sheaf_ground_truth_recovery()

    assert set(recovery["simulation_task"]) == {"residual_aligned_ground_truth"}
    assert recovery["truth_depends_on_residual_definition"].all()


def test_independent_perturbation_edges_use_external_truth_mask():
    edges = independent_perturbation_edges()
    positives = edges.loc[edges["ground_truth_perturbed"]]

    assert len(edges) == 56
    assert len(positives) == 4
    assert set(positives["ground_truth_source"]) == {"predefined_external_perturbation_mask"}
    assert not edges["truth_depends_on_residual_definition"].any()


def test_independent_perturbation_recovery_reports_non_circular_task():
    recovery = independent_perturbation_recovery()
    scores = recovery.set_index("method")["average_precision"].to_dict()

    assert set(recovery["simulation_task"]) == {"independent_perturbation"}
    assert not recovery["truth_depends_on_residual_definition"].any()
    assert scores["SheafSignal_sheaf_energy"] >= scores["LRProductBaseline_communication_flow"]
    assert "FlowGradientOpposition_product" in scores
