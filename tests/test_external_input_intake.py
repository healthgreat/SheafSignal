from pathlib import Path

from scripts.build_external_input_intake import (
    build_outputs,
    build_status_rows,
    classify_decision,
    default_rows,
)


def _row(field_id, value="", notes="", rule="nonempty", priority="P0", secret_path=""):
    return {
        "field_id": field_id,
        "priority": priority,
        "owner": "authors",
        "expected_input": "test",
        "current_value": "pending",
        "user_value": value,
        "secret_path": secret_path,
        "validation_rule": rule,
        "notes": notes,
    }


def test_default_intake_rows_include_required_release_and_author_fields():
    rows = default_rows()
    field_ids = {row.field_id for row in rows}

    assert "github_token_file" in field_ids
    assert "zenodo_doi" in field_ids
    assert "han_yan_email" in field_ids
    assert "github_public_release_approved" in field_ids


def test_status_rows_validate_email_doi_and_yes_fields(tmp_path):
    secret = tmp_path / "token.txt"
    secret.write_text("x", encoding="utf-8")
    rows = build_status_rows(
        [
            _row("email", "han.yan@example.org", rule="email"),
            _row("doi", "10.5281/zenodo.1234567", rule="doi_or_zenodo_token"),
            _row("approval", "yes", rule="yes"),
            _row("secret", rule="file_exists_nonempty", secret_path=str(secret)),
        ]
    )

    assert all(row.status == "pass" for row in rows)
    assert classify_decision(rows) == "EXTERNAL_INPUT_INTAKE_READY"


def test_status_rows_block_missing_p0_fields():
    rows = build_status_rows(
        [
            _row("email", "", rule="email"),
            _row("approval", "", rule="yes"),
            _row("wording", "", notes="instruction text is not user input", rule="nonempty"),
        ]
    )

    assert classify_decision(rows) == "EXTERNAL_INPUT_INTAKE_P0_MISSING"
    assert sum(row.blocking == "yes" for row in rows) == 3


def test_build_outputs_writes_template_status_and_report(tmp_path):
    summary = build_outputs(tmp_path)

    assert summary["decision"] == "EXTERNAL_INPUT_INTAKE_P0_MISSING"
    assert summary["p0_missing"] >= 1
    assert (tmp_path / Path(summary["template"])).exists()
    assert (tmp_path / Path(summary["status"])).exists()
    assert (tmp_path / Path(summary["report"])).exists()
