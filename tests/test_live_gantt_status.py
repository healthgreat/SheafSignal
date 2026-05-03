import pandas as pd

from scripts.build_live_gantt_status import (
    build_outputs,
    build_report,
    build_status_rows,
    classify_decision,
)


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _fixture(root):
    _write(
        root / "manuscript" / "IF20_50_DISTANCE_REPORT.md",
        "- Decision: `IF20_50_SCIENTIFICALLY_HARDENED_EXTERNAL_RELEASE_BLOCKED`\n"
        "- Overall readiness index: `79.3%`\n"
        "- Scientific/method hardening index: `97.0%`\n"
        "- Submission infrastructure index: `44.5%`\n",
    )
    release_dir = root / "release"
    release_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "gate_id": "G01",
                "priority": "blocking",
                "owner": "user_then_codex",
                "current_status": "valid_missing_workflow_scope",
                "required_action": "Regenerate token",
            }
        ]
    ).to_csv(release_dir / "RELEASE_UNBLOCKER_MATRIX.tsv", sep="\t", index=False)

    author_dir = root / "manuscript" / "submission_metadata"
    author_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {"item": "Han Yan email", "severity": "blocking"},
            {"item": "CRediT", "severity": "pending"},
        ]
    ).to_csv(
        author_dir / "AUTHOR_CONFIRMATION_PREFLIGHT_STATUS.tsv",
        sep="\t",
        index=False,
    )
    _write(
        root / "external_ai_review_packet" / "EXTERNAL_BETA_REVIEW_TRIAGE_REPORT.md",
        "- Decision: `EXTERNAL_BETA_REVIEW_NO_RETURNED_REVIEWS`\n",
    )
    _write(
        root / "manuscript" / "submission_metadata" / "AUTHOR_CONTACT_RECONCILIATION_REPORT.md",
        "- Decision: `AUTHOR_CONTACT_RECONCILIATION_BLOCKED_MISSING_EMAIL`\n",
    )
    _write(
        root
        / "external_ai_review_packet"
        / "shareable_review_bundle"
        / "SHAREABLE_REVIEW_BUNDLE_REPORT.md",
        "- Decision: `SHAREABLE_REVIEW_BUNDLE_READY`\n",
    )
    _write(
        root / "release" / "USER_ACTION_NOW_PACKET_ZH.md",
        "- Decision: `USER_ACTION_PACKET_READY_P0_BLOCKERS_REMAIN`\n",
    )
    _write(
        root / "release" / "EXTERNAL_INPUT_INTAKE_REPORT.md",
        "- Decision: `EXTERNAL_INPUT_INTAKE_P0_MISSING`\n",
    )
    _write(
        root / "release" / "UNBLOCK_READINESS_REPORT.md",
        "- Decision: `UNBLOCK_READINESS_BLOCKED_EXTERNAL_INPUTS`\n",
    )
    _write(
        root
        / "manuscript"
        / "journal_metric_audit"
        / "JOURNAL_SUBMISSION_DAY_CHECK_REPORT.md",
        "- Decision: `JOURNAL_SUBMISSION_DAY_CHECK_TEMPLATE_READY`\n",
    )


def test_live_status_rows_detect_blockers(tmp_path):
    _fixture(tmp_path)

    rows = build_status_rows(tmp_path)
    row_map = {row.item: row for row in rows}

    assert row_map["release_blockers"].status == "1 active"
    assert row_map["author_confirmation"].status == "blocking=1; pending=1"
    assert row_map["author_contact_reconciliation"].blocking == "yes"
    assert row_map["shareable_review_bundle"].status == "SHAREABLE_REVIEW_BUNDLE_READY"
    assert row_map["user_action_now_packet"].status == "USER_ACTION_PACKET_READY_P0_BLOCKERS_REMAIN"
    assert row_map["external_input_intake"].status == "EXTERNAL_INPUT_INTAKE_P0_MISSING"
    assert row_map["unblock_readiness_runner"].blocking == "no"


def test_report_contains_mermaid_and_distance_metrics(tmp_path):
    _fixture(tmp_path)
    rows = build_status_rows(tmp_path)
    report = build_report(tmp_path, rows)

    assert "```mermaid" in report
    assert "97.0%" in report
    assert "44.5%" in report
    assert "does not guarantee acceptance" in report


def test_classify_decision_blocks_external_and_author_gates(tmp_path):
    _fixture(tmp_path)
    rows = build_status_rows(tmp_path)
    if_text = (tmp_path / "manuscript" / "IF20_50_DISTANCE_REPORT.md").read_text(
        encoding="utf-8"
    )

    assert classify_decision(rows, if_text) == "LIVE_STATUS_EXTERNAL_AND_AUTHOR_GATES_BLOCK_SUBMISSION"


def test_build_outputs_writes_report_and_tsv(tmp_path):
    _fixture(tmp_path)

    summary = build_outputs(tmp_path)

    assert summary["rows"] >= 7
    assert summary["blocking_rows"] >= 2
    assert (tmp_path / summary["report"]).exists()
    assert (tmp_path / summary["tsv"]).exists()
