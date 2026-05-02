import pandas as pd

from scripts.build_if20_50_gap_report import (
    _status_point,
    build_gap_matrix,
    build_report,
    build_supplementation_plan,
    score_gates,
)


def test_status_point_handles_project_statuses():
    assert _status_point("green") == 1.0
    assert _status_point("green_yellow") == 0.8
    assert _status_point("yellow") == 0.55
    assert _status_point("red") == 0.0
    assert _status_point("fixed_round2_anything") == 1.0
    assert _status_point("partially_fixed_local_commit_public_remote_pending") == 0.55


def test_score_gates_separates_science_and_submission_infrastructure():
    gates = pd.DataFrame(
        [
            {"gate_id": "G01", "status": "green"},
            {"gate_id": "G06", "status": "green"},
            {"gate_id": "G11", "status": "yellow"},
            {"gate_id": "G12", "status": "red"},
        ]
    )

    score = score_gates(gates)

    assert score["scientific_percent"] == 100.0
    assert score["submission_infrastructure_percent"] < 50.0
    assert score["overall_percent"] < 80.0


def test_gap_matrix_flags_submission_blocking_gates():
    gates = pd.DataFrame(
        [
            {
                "gate_id": "G12",
                "area": "Zenodo DOI",
                "status": "red",
                "submission_blocker": "yes",
                "evidence": "missing DOI",
                "next_action": "mint DOI",
            }
        ]
    )
    rows = build_gap_matrix(
        gates,
        pd.DataFrame(),
        pd.DataFrame(),
        pd.DataFrame(),
        pd.DataFrame(),
    )

    assert rows[0]["if20_50_risk"] == "blocking"
    assert rows[0]["submission_blocker"] == "yes"


def test_supplementation_plan_contains_mandatory_and_optional_items():
    rows = build_supplementation_plan()

    mandatory = [row for row in rows if row["blocking"] == "yes"]
    optional = [row for row in rows if row["blocking"] == "no"]
    assert any("GitHub" in row["action"] for row in mandatory)
    assert any("GSE103322" in row["action"] for row in optional)


def test_report_contains_gantt_and_boundary(tmp_path):
    gates = pd.DataFrame(
        [
            {
                "gate_id": "G01",
                "status": "green",
                "area": "Formal sheaf core",
                "submission_blocker": "no",
            },
            {
                "gate_id": "G12",
                "status": "red",
                "area": "Zenodo DOI",
                "submission_blocker": "yes",
            },
        ]
    )
    report = build_report(tmp_path, gates, [], build_supplementation_plan())

    assert "```mermaid" in report
    assert "not acceptance probabilities" in report
    assert "Zenodo DOI" in report
