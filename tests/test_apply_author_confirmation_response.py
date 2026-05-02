import pandas as pd

from scripts.apply_author_confirmation_response import (
    apply_responses,
    build_response_template,
    classify_decision,
    write_template,
    apply_response_file,
)


def _checklist_rows():
    return [
        {
            "item": "Han Yan email",
            "current_value": "missing_email",
            "required_confirmation": "Provide final email",
            "status": "blocking_author_confirmation",
            "owner": "authors",
        },
        {
            "item": "ORCID IDs",
            "current_value": "not_provided",
            "required_confirmation": "Optional",
            "status": "optional_author_metadata",
            "owner": "authors",
        },
    ]


def test_build_response_template_preserves_items():
    template = build_response_template(_checklist_rows())

    assert template[0]["item"] == "Han Yan email"
    assert template[0]["confirmed"] == "fill_yes_no_or_skip"
    assert "final_value" in template[0]


def test_apply_responses_confirms_and_updates_value():
    response_rows = [
        {
            "item": "Han Yan email",
            "confirmed": "yes",
            "final_value": "hanyan@example.org",
            "notes": "",
        },
        {
            "item": "ORCID IDs",
            "confirmed": "skip",
            "final_value": "",
            "notes": "",
        },
    ]

    updated, audit = apply_responses(_checklist_rows(), response_rows)

    assert updated[0]["status"] == "confirmed"
    assert updated[0]["current_value"] == "hanyan@example.org"
    assert updated[1]["status"] == "optional_author_metadata"
    assert classify_decision(audit, applied=True) == "AUTHOR_CONFIRMATION_RESPONSE_APPLIED"


def test_apply_responses_marks_author_blocked_no_response():
    response_rows = [
        {
            "item": "Han Yan email",
            "confirmed": "no",
            "final_value": "",
            "notes": "not approved",
        }
    ]

    updated, audit = apply_responses(_checklist_rows(), response_rows)

    assert updated[0]["status"] == "blocked_by_author_response"
    assert classify_decision(audit, applied=True) == "AUTHOR_CONFIRMATION_RESPONSE_APPLIED_AUTHOR_BLOCKED"


def test_write_template_and_apply_file(tmp_path):
    checklist = tmp_path / "manuscript" / "submission_metadata" / "AUTHOR_CONFIRMATION_CHECKLIST.tsv"
    checklist.parent.mkdir(parents=True)
    pd.DataFrame(_checklist_rows()).to_csv(checklist, sep="\t", index=False)

    outputs = write_template(
        tmp_path,
        checklist.relative_to(tmp_path),
        "manuscript/submission_metadata/AUTHOR_CONFIRMATION_RESPONSE_TEMPLATE.tsv",
        "manuscript/submission_metadata/AUTHOR_CONFIRMATION_RESPONSE_APPLY_REPORT.md",
    )
    response = outputs["response"]
    table = pd.read_csv(response, sep="\t", dtype=str).fillna("")
    table.loc[table["item"] == "Han Yan email", "confirmed"] = "yes"
    table.loc[table["item"] == "Han Yan email", "final_value"] = "hanyan@example.org"
    table.to_csv(response, sep="\t", index=False)

    apply_response_file(
        tmp_path,
        checklist.relative_to(tmp_path),
        response.relative_to(tmp_path),
        "manuscript/submission_metadata/AUTHOR_CONFIRMATION_RESPONSE_APPLY_REPORT.md",
    )

    updated = pd.read_csv(checklist, sep="\t")
    assert updated.loc[updated["item"] == "Han Yan email", "status"].iloc[0] == "confirmed"
