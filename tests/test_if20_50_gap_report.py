import pandas as pd

from scripts.build_if20_50_gap_report import (
    _status_point,
    build_gap_matrix,
    build_report,
    build_supplementation_plan,
    beta_review_packet_status,
    clean_preflight_status,
    confirmatory_permutation_status,
    gse103322_replication_status,
    live_release_summary,
    external_beta_review_triage_status,
    shareable_review_bundle_status,
    author_response_template_status,
    journal_submission_day_check_status,
    journal_metric_audit_status,
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
    assert "Journal metric audit" in report
    assert "Journal submission-day check" in report
    assert "External beta review packet" in report
    assert "External beta review triage" in report
    assert "Shareable review bundle" in report
    assert "Author response template" in report
    assert "10,000-permutation confirmatory subset" in report
    assert "GSE103322 replication supplement" in report
    assert "Live Release And Author Gates" in report


def test_live_release_summary_reads_unblocker_and_status_counts(tmp_path):
    release = tmp_path / "release"
    author = tmp_path / "manuscript" / "submission_metadata"
    release.mkdir(parents=True)
    author.mkdir(parents=True)
    (release / "RELEASE_UNBLOCKER_MATRIX.tsv").write_text(
        "gate_id\tpriority\towner\tcurrent_status\trequired_action\tvalidation_command\n"
        "G01_github_auth\tblocking\tuser_then_codex\tvalid_missing_workflow_scope\t"
        "Regenerate token\tpython scripts/check_external_release_authorization.py\n"
        "S01_external_beta_review\tstrengthening\tuser_or_codex_packet\t"
        "recommended_not_required\tSend review packet\tmanual\n",
        encoding="utf-8",
    )
    (release / "EXTERNAL_RELEASE_AUTHORIZATION_STATUS.tsv").write_text(
        "check_id\tseverity\tstatus\tevidence\trequired_action\tvalidation_command\n"
        "github_token_api\tblocking\tvalid_missing_workflow_scope\tx\tx\tx\n",
        encoding="utf-8",
    )
    (release / "ZENODO_UPLOAD_PREFLIGHT_STATUS.tsv").write_text(
        "check_id\tseverity\tstatus\tevidence\trequired_action\n"
        "zenodo_archive_sha256\tpass\tpass\tx\tNone\n"
        "zenodo_token_file\tpending\tpending\tx\tx\n",
        encoding="utf-8",
    )
    (author / "AUTHOR_CONFIRMATION_PREFLIGHT_STATUS.tsv").write_text(
        "item\tseverity\tstatus\tcurrent_value\trequired_confirmation\towner\n"
        "Han Yan email\tblocking\tblocking_author_confirmation\tmissing\tx\tauthors\n",
        encoding="utf-8",
    )

    summary = live_release_summary(tmp_path)

    assert summary["blocking_total"] == 1
    assert summary["blocking_active"] == 1
    assert summary["external_auth_counts"] == {"valid_missing_workflow_scope": 1}
    assert summary["zenodo_preflight_counts"] == {"pass": 1, "pending": 1}
    assert summary["author_preflight_counts"] == {"blocking": 1}


def test_clean_preflight_status_reads_pass_report(tmp_path):
    report = tmp_path / "release" / "clean_clone_preflight" / "CLEAN_CLONE_PREFLIGHT_REPORT.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        "- Decision: `CLEAN_CLONE_PREFLIGHT_PASS_LOCAL_EXPORT`\n",
        encoding="utf-8",
    )

    assert clean_preflight_status(tmp_path) == "local_clean_export_pass"


def test_journal_metric_audit_status_reads_final_check_boundary(tmp_path):
    report = tmp_path / "manuscript" / "journal_metric_audit" / "JOURNAL_METRIC_AUDIT_REPORT.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        "- Decision: `JOURNAL_METRIC_AUDIT_IF_VERIFIED_CAS_WARNING_NEEDS_FINAL_CHECK`\n",
        encoding="utf-8",
    )

    assert (
        journal_metric_audit_status(tmp_path)
        == "publisher_if_verified_cas_warning_final_check_required"
    )


def test_journal_submission_day_check_status_reads_template_ready(tmp_path):
    report = (
        tmp_path
        / "manuscript"
        / "journal_metric_audit"
        / "JOURNAL_SUBMISSION_DAY_CHECK_REPORT.md"
    )
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        "- Decision: `JOURNAL_SUBMISSION_DAY_CHECK_TEMPLATE_READY`\n",
        encoding="utf-8",
    )

    assert journal_submission_day_check_status(tmp_path) == "template_ready"


def test_beta_review_packet_status_reads_ready_boundary(tmp_path):
    report = (
        tmp_path
        / "external_ai_review_packet"
        / "beta_review_packet_2026-05-02"
        / "01_BETA_REVIEW_PACKET_STATUS.md"
    )
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        "- Decision: `BETA_REVIEW_PACKET_READY_LOCAL_EXTERNAL_REVIEWS_PENDING`\n",
        encoding="utf-8",
    )

    assert beta_review_packet_status(tmp_path) == "packet_ready_external_reviews_pending"


def test_external_beta_review_triage_status_reads_no_returned_reviews(tmp_path):
    report = tmp_path / "external_ai_review_packet" / "EXTERNAL_BETA_REVIEW_TRIAGE_REPORT.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        "- Decision: `EXTERNAL_BETA_REVIEW_NO_RETURNED_REVIEWS`\n",
        encoding="utf-8",
    )

    assert external_beta_review_triage_status(tmp_path) == "no_returned_external_reviews"


def test_shareable_review_bundle_status_reads_ready_report(tmp_path):
    report = (
        tmp_path
        / "external_ai_review_packet"
        / "shareable_review_bundle"
        / "SHAREABLE_REVIEW_BUNDLE_REPORT.md"
    )
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("- Decision: `SHAREABLE_REVIEW_BUNDLE_READY`\n", encoding="utf-8")

    assert shareable_review_bundle_status(tmp_path) == "ready"


def test_author_response_template_status_reads_template_ready(tmp_path):
    report = (
        tmp_path
        / "manuscript"
        / "submission_metadata"
        / "AUTHOR_CONFIRMATION_RESPONSE_APPLY_REPORT.md"
    )
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        "- Decision: `AUTHOR_CONFIRMATION_RESPONSE_TEMPLATE_READY`\n",
        encoding="utf-8",
    )

    assert author_response_template_status(tmp_path) == "template_ready"


def test_confirmatory_permutation_status_reads_ready_boundary(tmp_path):
    report = tmp_path / "benchmarks" / "results" / "confirmatory_10000" / (
        "CONFIRMATORY_PERMUTATION_STATUS.md"
    )
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("- Decision: `CONFIRMATORY_10000_READY_NOT_RUN`\n", encoding="utf-8")

    assert confirmatory_permutation_status(tmp_path) == "pre_specified_ready_not_run"


def test_gse103322_replication_status_reads_exploratory_boundary(tmp_path):
    report = tmp_path / "benchmarks" / "results" / "gse103322_hnsc_scrna" / "replication" / (
        "GSE103322_REPLICATION_SUPPLEMENT_REPORT.md"
    )
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        "- Decision: `GSE103322_REPLICATION_EXPLORATORY_READY_RERUN_RECOMMENDED`\n",
        encoding="utf-8",
    )

    assert gse103322_replication_status(tmp_path) == "exploratory_ready_rerun_recommended"
