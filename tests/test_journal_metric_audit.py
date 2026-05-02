from pathlib import Path

import pandas as pd

from scripts.build_journal_metric_audit import (
    AUDIT_PATH,
    JOURNAL_ROWS,
    REPORT_PATH,
    build_outputs,
    build_report,
    classify_decision,
)


def test_journal_metric_rows_use_publisher_sources_for_jif():
    assert JOURNAL_ROWS
    assert {row["metric_source_type"] for row in JOURNAL_ROWS} == {"publisher_official"}
    assert any(row["journal"] == "Nature Methods" for row in JOURNAL_ROWS)


def test_open_web_cas_boundary_requires_final_submission_check():
    decision = classify_decision([dict(row) for row in JOURNAL_ROWS])

    assert decision == "JOURNAL_METRIC_AUDIT_IF_VERIFIED_CAS_WARNING_NEEDS_FINAL_CHECK"


def test_decision_allows_ready_only_when_cas_and_warning_are_official():
    rows = [
        {
            **dict(JOURNAL_ROWS[0]),
            "open_web_cas_zone_status": "officially_verified_current_cas_zone",
            "warning_list_status": "official_current_warning_status_verified",
        }
    ]

    assert classify_decision(rows) == "JOURNAL_METRIC_AUDIT_READY"


def test_report_states_metric_and_warning_boundaries():
    report = build_report([dict(row) for row in JOURNAL_ROWS])

    assert "publisher or Springer Nature official metric pages" in report
    assert "not a substitute for the official CAS partition platform" in report
    assert "warning-list" in report


def test_build_outputs_writes_audit_and_report(tmp_path: Path):
    summary = build_outputs(tmp_path)

    audit_path = tmp_path / AUDIT_PATH
    report_path = tmp_path / REPORT_PATH
    assert summary["decision"] == "JOURNAL_METRIC_AUDIT_IF_VERIFIED_CAS_WARNING_NEEDS_FINAL_CHECK"
    assert audit_path.exists()
    assert report_path.exists()

    table = pd.read_csv(audit_path, sep="\t")
    assert set(table["journal"]).issuperset({"Nature Methods", "Molecular Cancer"})
    assert "CAS-zone" in report_path.read_text(encoding="utf-8")
