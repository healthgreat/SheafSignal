import pandas as pd

from scripts.apply_journal_submission_day_check import (
    apply_response,
    build_template_rows,
    classify_decision,
    write_template,
)


def _audit_rows():
    return [
        {
            "journal": "Nature Methods",
            "route_decision": "keep_primary",
            "jif_2024": "32.1",
            "five_year_jif_2024": "51.7",
            "metric_source_url": "https://www.nature.com/nature-portfolio/about/journal-metrics",
        },
        {
            "journal": "Molecular Cancer",
            "route_decision": "fallback",
            "jif_2024": "33.9",
            "five_year_jif_2024": "35.9",
            "metric_source_url": "https://molecular-cancer.biomedcentral.com/",
        },
    ]


def test_template_rows_preserve_journal_targets():
    rows = build_template_rows(_audit_rows())

    assert rows[0]["journal"] == "Nature Methods"
    assert rows[0]["selected_target"] == "yes_or_no"
    assert rows[0]["confirmed_for_submission"] == "fill_yes_no"


def test_decision_template_and_apply_states():
    rows = build_template_rows(_audit_rows())

    assert (
        classify_decision(rows, applied=False)
        == "JOURNAL_SUBMISSION_DAY_CHECK_TEMPLATE_READY"
    )
    assert (
        classify_decision(rows, applied=True)
        == "JOURNAL_SUBMISSION_DAY_CHECK_APPLIED_NO_TARGET_SELECTED"
    )
    rows[0]["selected_target"] = "yes"
    assert (
        classify_decision(rows, applied=True)
        == "JOURNAL_SUBMISSION_DAY_CHECK_TARGET_PENDING"
    )
    rows[0]["confirmed_for_submission"] = "yes"
    assert classify_decision(rows, applied=True) == "JOURNAL_SUBMISSION_DAY_CHECK_READY"


def test_decision_blocks_selected_target_when_not_verified():
    rows = build_template_rows(_audit_rows())
    rows[0]["selected_target"] = "yes"
    rows[0]["confirmed_for_submission"] = "no"

    assert classify_decision(rows, applied=True) == "JOURNAL_SUBMISSION_DAY_CHECK_TARGET_BLOCKED"


def test_write_template_and_apply_response(tmp_path):
    audit = tmp_path / "manuscript" / "journal_metric_audit" / "JOURNAL_METRIC_AUDIT.tsv"
    audit.parent.mkdir(parents=True)
    pd.DataFrame(_audit_rows()).to_csv(audit, sep="\t", index=False)

    response = (
        "manuscript/journal_metric_audit/JOURNAL_SUBMISSION_DAY_CHECK_TEMPLATE.tsv"
    )
    report = "manuscript/journal_metric_audit/JOURNAL_SUBMISSION_DAY_CHECK_REPORT.md"
    outputs = write_template(tmp_path, audit.relative_to(tmp_path), response, report)
    table = pd.read_csv(outputs["response"], sep="\t", dtype=str).fillna("")
    table.loc[table["journal"] == "Nature Methods", "selected_target"] = "yes"
    table.loc[table["journal"] == "Nature Methods", "confirmed_for_submission"] = "yes"
    table.loc[table["journal"] == "Nature Methods", "official_cas_zone"] = "CAS 1区 Top"
    table.loc[table["journal"] == "Nature Methods", "official_warning_status"] = "not warning"
    table.to_csv(outputs["response"], sep="\t", index=False)

    apply_response(tmp_path, outputs["response"].relative_to(tmp_path), report)

    text = (tmp_path / report).read_text(encoding="utf-8")
    assert "JOURNAL_SUBMISSION_DAY_CHECK_READY" in text
