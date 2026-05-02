from scripts.build_post_unblock_release_pipeline import (
    build_gate_snapshot,
    build_pipeline_steps,
    classify_decision,
    run_orchestrator,
    write_outputs,
)


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_minimal_gate_files(root, github_status="valid_missing_workflow_scope"):
    _write(
        root / "release" / "EXTERNAL_RELEASE_AUTHORIZATION_STATUS.tsv",
        "check_id\tseverity\tstatus\tevidence\trequired_action\tvalidation_command\n"
        f"github_token_api\tblocking\t{github_status}\tx\tx\tx\n"
        "github_cli_auth\tblocking\tnot_logged_in\tx\tx\tx\n",
    )
    _write(
        root / "release" / "ZENODO_UPLOAD_PREFLIGHT_STATUS.tsv",
        "check_id\tseverity\tstatus\tevidence\trequired_action\n"
        "zenodo_archive_sha256\tpass\tpass\tx\tNone\n",
    )
    _write(
        root
        / "manuscript"
        / "submission_metadata"
        / "AUTHOR_CONFIRMATION_PREFLIGHT_STATUS.tsv",
        "item\tseverity\tstatus\tcurrent_value\trequired_confirmation\towner\n",
    )
    _write(
        root / "release" / "RELEASE_UNBLOCKER_MATRIX.tsv",
        "gate_id\tpriority\towner\tcurrent_status\tevidence\trequired_action\t"
        "validation_command\tunlocks\tclaim_boundary\n"
        "G01_github_auth\tblocking\tuser_then_codex\tvalid_missing_workflow_scope\t"
        "x\tx\tx\tx\tx\n",
    )


def test_gate_snapshot_reads_current_statuses(tmp_path):
    _write_minimal_gate_files(tmp_path)

    snapshot = build_gate_snapshot(tmp_path)

    assert snapshot["github_token_api"] == "valid_missing_workflow_scope"
    assert snapshot["zenodo_archive_sha256"] == "pass"
    assert snapshot["active_release_blockers"] == 1


def test_classify_blocks_missing_github_workflow_scope(tmp_path):
    _write_minimal_gate_files(tmp_path)
    snapshot = build_gate_snapshot(tmp_path)

    decision = classify_decision(snapshot, "10.5281/zenodo.12345", True)

    assert decision == "POST_UNBLOCK_PIPELINE_BLOCKED_GITHUB_TOKEN"


def test_classify_ready_when_gates_and_doi_are_available(tmp_path):
    _write_minimal_gate_files(tmp_path, github_status="valid")
    snapshot = build_gate_snapshot(tmp_path)

    decision = classify_decision(snapshot, "10.5281/zenodo.12345", True)

    assert decision == "POST_UNBLOCK_PIPELINE_READY_TO_EXECUTE"


def test_pipeline_plan_contains_publish_finalize_and_audits():
    steps = build_pipeline_steps("10.5281/zenodo.12345", publish_release=True)
    step_ids = {step.step_id for step in steps}

    assert "publish_github_release" in step_ids
    assert "finalize_zenodo_doi" in step_ids
    assert "clean_export_preflight" in step_ids
    assert "refresh_distance_report" in step_ids


def test_orchestrator_report_writes_outputs_without_execution(tmp_path):
    _write_minimal_gate_files(tmp_path)
    decision, results = run_orchestrator(
        tmp_path,
        doi="10.5281/zenodo.12345",
        execute=False,
        publish_release=False,
        require_author_ready=True,
    )
    outputs = write_outputs(
        tmp_path,
        build_pipeline_steps("10.5281/zenodo.12345", publish_release=False),
        decision,
        build_gate_snapshot(tmp_path),
        results,
        execute=False,
    )

    assert decision == "POST_UNBLOCK_PIPELINE_BLOCKED_GITHUB_TOKEN"
    assert results == []
    assert outputs["plan"].exists()
    assert outputs["report"].exists()
