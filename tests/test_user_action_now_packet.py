import pandas as pd

from scripts.build_user_action_now_packet import build_action_rows, build_outputs, classify_decision


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


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

    _write(
        root / "external_ai_review_packet" / "EXTERNAL_BETA_REVIEW_TRIAGE_REPORT.md",
        "- Decision: `EXTERNAL_BETA_REVIEW_NO_RETURNED_REVIEWS`\n",
    )


def test_build_action_rows_extracts_current_blockers(tmp_path):
    _fixture(tmp_path)

    rows = build_action_rows(tmp_path)
    row_map = {row.item: row for row in rows}

    assert row_map["GitHub token / gh login"].current_status == (
        "github_token_api=valid_missing_workflow_scope; gh=not_logged_in"
    )
    assert row_map["Han Yan email and author contact consistency"].current_status == (
        "missing_current_author_email=1; extra_supplied_contacts=1"
    )
    assert row_map["Zenodo DOI"].priority == "P0"


def test_classify_decision_marks_p0_blockers(tmp_path):
    _fixture(tmp_path)
    rows = build_action_rows(tmp_path)

    assert classify_decision(rows) == "USER_ACTION_PACKET_READY_P0_BLOCKERS_REMAIN"


def test_build_outputs_writes_packet(tmp_path):
    _fixture(tmp_path)

    summary = build_outputs(tmp_path)

    assert summary["p0_rows"] == 4
    assert (tmp_path / summary["tsv"]).exists()
    assert (tmp_path / summary["report"]).exists()
