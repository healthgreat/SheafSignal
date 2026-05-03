import pandas as pd

from scripts.run_unblock_readiness_check import build_gate_rows, build_outputs, classify_decision


def _fixture(root):
    release = root / "release"
    release.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {"check_id": "github_token_api", "status": "valid_missing_workflow_scope"},
            {"check_id": "github_cli_auth", "status": "not_logged_in"},
            {"check_id": "zenodo_token_file", "status": "missing"},
            {"check_id": "zenodo_doi_placeholders", "status": "pending"},
        ]
    ).to_csv(release / "EXTERNAL_RELEASE_AUTHORIZATION_STATUS.tsv", sep="\t", index=False)
    pd.DataFrame(
        [
            {"priority": "P0", "item": "GitHub token"},
            {"priority": "P1", "item": "External review"},
        ]
    ).to_csv(release / "USER_ACTION_NOW_PACKET.tsv", sep="\t", index=False)
    pd.DataFrame(
        [
            {"field_id": "han_yan_email", "blocking": "yes"},
            {"field_id": "external_beta_review_return_path", "blocking": "no"},
        ]
    ).to_csv(release / "EXTERNAL_INPUT_INTAKE_STATUS.tsv", sep="\t", index=False)

    author_dir = root / "manuscript" / "submission_metadata"
    author_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {"item": "Han Yan email", "severity": "blocking"},
            {"item": "CRediT", "severity": "pending"},
        ]
    ).to_csv(author_dir / "AUTHOR_CONFIRMATION_PREFLIGHT_STATUS.tsv", sep="\t", index=False)
    pd.DataFrame(
        [
            {"name": "Han Yan", "action_needed": "blocking_missing_email"},
            {"name": "Extra Person", "action_needed": "confirm_not_author_or_update_author_line"},
        ]
    ).to_csv(author_dir / "AUTHOR_CONTACT_RECONCILIATION.tsv", sep="\t", index=False)

    manuscript = root / "manuscript"
    manuscript.mkdir(exist_ok=True)
    pd.DataFrame(
        [
            {"item": "release_blockers", "blocking": "yes"},
            {"item": "shareable_review_bundle", "blocking": "no"},
        ]
    ).to_csv(manuscript / "SHEAFSIGNAL_LIVE_GANTT_STATUS.tsv", sep="\t", index=False)


def test_build_gate_rows_detects_unblock_blockers(tmp_path):
    _fixture(tmp_path)

    rows = build_gate_rows(tmp_path)
    row_map = {row.gate: row for row in rows}

    assert row_map["github_publication_auth"].blocking == "yes"
    assert row_map["author_confirmation"].evidence == (
        "missing_author_email=1; extra_contacts=1"
    )
    assert row_map["short_user_action_packet"].status == "P0=1"
    assert row_map["external_input_intake"].status == "P0_missing=1"


def test_classify_decision_blocks_on_external_inputs(tmp_path):
    _fixture(tmp_path)
    rows = build_gate_rows(tmp_path)

    assert classify_decision(rows, []) == "UNBLOCK_READINESS_BLOCKED_EXTERNAL_INPUTS"


def test_build_outputs_writes_readiness_report_without_refresh(tmp_path):
    _fixture(tmp_path)

    summary = build_outputs(tmp_path, refresh=False)

    assert summary["decision"] == "UNBLOCK_READINESS_BLOCKED_EXTERNAL_INPUTS"
    assert summary["blocking_rows"] >= 1
    assert (tmp_path / summary["report"]).exists()
    assert (tmp_path / summary["tsv"]).exists()
