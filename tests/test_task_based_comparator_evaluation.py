from pathlib import Path
import importlib.util


def _load_script():
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts" / "run_task_based_comparator_evaluation.py"
    spec = importlib.util.spec_from_file_location("run_task_based_comparator_evaluation", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_task_based_comparator_evaluation_marks_primary_independent_task():
    script = _load_script()

    table = script.build_task_evaluation(seed=1, noise_values=[0.0])

    primary = table.loc[table["task_is_primary"]]
    assert set(primary["simulation_task"]) == {"independent_perturbation"}
    assert not primary["truth_depends_on_residual_definition"].any()
    assert "HigherRankLRChannelSheaf_energy" in set(primary["method"])
    assert "FlowGradientOpposition_product" in set(primary["method"])


def test_task_based_comparator_script_writes_table_and_report(tmp_path):
    script = _load_script()

    assert script.main(["--out-dir", str(tmp_path), "--noise-sd", "0.0"]) == 0

    assert (tmp_path / "comparator_task_recovery.csv").exists()
    report = tmp_path / "comparator_task_recovery.md"
    assert report.exists()
    assert "TASK_BASED_COMPARATOR_EVALUATION_READY" in report.read_text(encoding="utf-8")
