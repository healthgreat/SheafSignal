from pathlib import Path

from scripts.build_submission_unblocker_handoff import (
    build_handoff_actions,
    build_report,
    write_outputs,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_build_handoff_actions_reads_live_blockers(tmp_path):
    _write(
        tmp_path / "release" / "EXTERNAL_RELEASE_AUTHORIZATION_STATUS.tsv",
        "check_id\tseverity\tstatus\tevidence\trequired_action\tvalidation_command\n"
        "github_token_api\tblocking\tvalid_missing_workflow_scope\tx\tx\tx\n"
        "github_cli_auth\tblocking\tnot_logged_in\tx\tx\tx\n",
    )
    _write(
        tmp_path / "release" / "ZENODO_UPLOAD_PREFLIGHT_STATUS.tsv",
        "check_id\tseverity\tstatus\tevidence\trequired_action\n"
        "zenodo_archive_sha256\tpass\tpass\tx\tNone\n"
        "zenodo_token_file\tpending\tpending\tx\tx\n",
    )
    _write(
        tmp_path
        / "manuscript"
        / "submission_metadata"
        / "AUTHOR_CONFIRMATION_PREFLIGHT_STATUS.tsv",
        "item\tseverity\tstatus\tcurrent_value\trequired_confirmation\towner\n"
        "Han Yan email\tblocking\tblocking_author_confirmation\tmissing\tx\tauthors\n"
        "CRediT roles\tpending\tdraft_pending_author_confirmation\tx\tx\tauthors\n",
    )
    _write(
        tmp_path / "release" / "RELEASE_UNBLOCKER_MATRIX.tsv",
        "gate_id\tpriority\towner\tcurrent_status\tevidence\trequired_action\t"
        "validation_command\tunlocks\tclaim_boundary\n"
        "G01_github_auth\tblocking\tuser_then_codex\tvalid_missing_workflow_scope\t"
        "x\tx\tx\tx\tx\n",
    )

    actions = build_handoff_actions(tmp_path)

    github_action = next(action for action in actions if "GitHub token" in action.action_item)
    zenodo_action = next(action for action in actions if "Zenodo DOI" in action.action_item)
    author_action = next(action for action in actions if "Author-owned" in action.action_item)
    assert "valid_missing_workflow_scope" in github_action.current_status
    assert "zenodo_token_file=pending" in zenodo_action.current_status
    assert "blocking=1" in author_action.current_status
    assert sum(action.priority == "P0" for action in actions) == 3


def test_handoff_report_contains_no_token_secret_and_outputs(tmp_path):
    actions = build_handoff_actions(tmp_path)
    report = build_report(actions)
    outputs = write_outputs(tmp_path, actions)

    assert "D:\\secrets\\github_token.txt" in report
    assert "Do not paste the token" in report
    assert "SUBMISSION_EXTERNAL_ACTIONS_REQUIRED" in report
    assert "build_post_unblock_release_pipeline.py" in report
    assert "AUTHOR_CONFIRMATION_RESPONSE_TEMPLATE.tsv" in report
    assert outputs["tsv"].exists()
    assert outputs["report"].exists()
