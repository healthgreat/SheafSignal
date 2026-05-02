from pathlib import Path

from scripts.run_clean_clone_preflight import (
    CommandResult,
    _assert_demo_outputs,
    _build_report,
    _classify,
    _python_env,
)


def test_classify_passes_only_when_all_commands_succeed():
    ok = CommandResult("ok", "cmd", ".", 0, 0.1, "stdout", "")
    fail = CommandResult("fail", "cmd", ".", 1, 0.1, "", "stderr")

    assert _classify([ok]) == "CLEAN_CLONE_PREFLIGHT_PASS_LOCAL_EXPORT"
    assert _classify([ok, fail]) == "CLEAN_CLONE_PREFLIGHT_FAIL"


def test_python_env_prepends_clean_src(tmp_path):
    env = _python_env(tmp_path)

    assert str(tmp_path / "src") in env["PYTHONPATH"].split(";")[0]
    assert env["PYTHONUNBUFFERED"] == "1"


def test_assert_demo_outputs_detects_missing_files(tmp_path):
    result = _assert_demo_outputs(tmp_path)

    assert result.returncode == 1
    assert "missing" in result.stderr_tail


def test_assert_demo_outputs_passes_for_expected_files(tmp_path):
    for rel in [
        "results/sheaf_energy_by_edge.csv",
        "results/hodge_decomposition_scores.csv",
        "results/cellular_sheaf_restrictions.csv",
        "results/cellular_sheaf_laplacian.csv",
        "results/provenance.json",
        "results/sheaf_energy_permutation_pvalues.csv",
        "results/frustration_permutation_pvalues.csv",
        "results/global_permutation_pvalues.csv",
    ]:
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("ok\n", encoding="utf-8")

    result = _assert_demo_outputs(tmp_path)

    assert result.returncode == 0
    assert "all expected" in result.stdout_tail


def test_report_states_local_export_boundary():
    result = CommandResult("pytest", "python -m pytest", ".", 0, 1.0, "ok", "")
    report = _build_report(
        decision="CLEAN_CLONE_PREFLIGHT_PASS_LOCAL_EXPORT",
        root=Path("repo"),
        commit="abc123",
        branch="codex/test",
        results=[result],
    )

    assert "current Git `HEAD`" in report
    assert "not a substitute for a final public-GitHub clean clone" in report
