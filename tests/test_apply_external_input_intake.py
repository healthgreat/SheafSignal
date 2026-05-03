import pandas as pd

from scripts.apply_external_input_intake import (
    build_outputs,
    classify_decision,
    derive_author_response,
)


def _intake(field_id, user_value="", notes=""):
    return {
        "field_id": field_id,
        "user_value": user_value,
        "notes": notes,
    }


def _response(item, current_value="current"):
    return {
        "item": item,
        "current_value": current_value,
        "required_confirmation": "confirm",
        "owner": "authors",
        "confirmed": "fill_yes_no_or_skip",
        "final_value": "",
        "notes": "",
    }


def test_derive_author_response_marks_missing_required_inputs_pending():
    rows, audit = derive_author_response(
        [_intake("han_yan_email", ""), _intake("extra_contacts_decision", "")],
        [_response("Han Yan email"), _response("author order")],
    )
    row_map = {row.item: row for row in rows}

    assert row_map["Han Yan email"].confirmed == "fill_yes_no_or_skip"
    assert row_map["author order"].confirmed == "fill_yes_no_or_skip"
    assert classify_decision(audit) == "AUTHOR_RESPONSE_FROM_INTAKE_PARTIAL"


def test_derive_author_response_translates_completed_author_fields():
    intake_rows = [
        _intake("han_yan_email", "han.yan@example.org"),
        _intake("equal_contribution_wording", "Han Yan and Yi Miao contributed equally."),
        _intake("extra_contacts_decision", "not_authors"),
        _intake("author_order_approved", "yes"),
        _intake("credit_roles_approved", "yes"),
        _intake("funding_statement_approved", "yes"),
        _intake("competing_interests_approved", "yes"),
        _intake("ethics_data_use_approved", "yes"),
        _intake("github_public_release_approved", "yes"),
        _intake("zenodo_deposition_approved", "yes"),
    ]
    response_rows = [
        _response("Han Yan email"),
        _response("equal contribution note"),
        _response("author order"),
        _response("affiliations"),
        _response("CRediT roles"),
        _response("funding acquisition", "Not reported"),
        _response("competing interests", "The authors declare no competing interests"),
        _response("ethics data-use", "Public data only"),
        _response("public GitHub release"),
        _response("Zenodo deposition"),
        _response("ORCID IDs"),
    ]

    rows, audit = derive_author_response(intake_rows, response_rows)
    row_map = {row.item: row for row in rows}

    assert row_map["Han Yan email"].final_value == "han.yan@example.org"
    assert row_map["author order"].confirmed == "yes"
    assert row_map["public GitHub release"].confirmed == "yes"
    assert classify_decision(audit) == "AUTHOR_RESPONSE_FROM_INTAKE_READY"


def test_expand_author_line_keeps_author_order_pending():
    rows, _ = derive_author_response(
        [
            _intake("extra_contacts_decision", "expand_author_line"),
            _intake("author_order_approved", "yes"),
        ],
        [_response("author order")],
    )
    row_map = {row.item: row for row in rows}

    assert row_map["author order"].confirmed == "fill_yes_no_or_skip"
    assert "author line must be updated" in row_map["author order"].notes


def test_build_outputs_writes_derived_response(tmp_path):
    intake = tmp_path / "release" / "EXTERNAL_INPUT_INTAKE_TEMPLATE.tsv"
    response = (
        tmp_path
        / "manuscript"
        / "submission_metadata"
        / "AUTHOR_CONFIRMATION_RESPONSE_TEMPLATE.tsv"
    )
    intake.parent.mkdir(parents=True, exist_ok=True)
    response.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([_intake("han_yan_email", "han.yan@example.org")]).to_csv(
        intake, sep="\t", index=False
    )
    pd.DataFrame([_response("Han Yan email"), _response("ORCID IDs")]).to_csv(
        response, sep="\t", index=False
    )

    summary = build_outputs(tmp_path)

    assert summary["rows"] >= 2
    assert (tmp_path / summary["response"]).exists()
    assert (tmp_path / summary["report"]).exists()
