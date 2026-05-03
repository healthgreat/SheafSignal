import pandas as pd

from scripts.reconcile_author_contacts import build_outputs, reconcile_contacts


def test_reconcile_contacts_detects_missing_current_author_email():
    author_rows = [
        {"given_names": "Han", "family_names": "Yan", "email": "missing_email"},
        {"given_names": "Yi", "family_names": "Miao", "email": "miaoyi@njmu.edu.cn"},
    ]
    contact_rows = [{"name": "Yi Miao", "email": "miaoyi@njmu.edu.cn"}]

    rows = reconcile_contacts(author_rows, contact_rows)
    row_map = {row.name: row for row in rows}

    assert row_map["Han Yan"].action_needed == "blocking_missing_email"
    assert row_map["Yi Miao"].action_needed == "no_contact_mismatch_detected"


def test_reconcile_contacts_detects_extra_supplied_contacts():
    author_rows = [{"given_names": "Chongfa", "family_names": "Chen", "email": "a@example.org"}]
    contact_rows = [
        {"name": "Chongfa Chen", "email": "a@example.org"},
        {"name": "Extra Person", "email": "extra@example.org"},
    ]

    rows = reconcile_contacts(author_rows, contact_rows)
    row_map = {row.name: row for row in rows}

    assert row_map["Extra Person"].manuscript_status == "not_in_current_author_line"
    assert row_map["Extra Person"].action_needed == "confirm_not_author_or_update_author_line"


def test_reconcile_contacts_honors_not_authors_decision():
    author_rows = [{"given_names": "Chongfa", "family_names": "Chen", "email": "a@example.org"}]
    contact_rows = [
        {"name": "Chongfa Chen", "email": "a@example.org"},
        {"name": "Extra Person", "email": "extra@example.org"},
    ]
    intake_rows = [{"field_id": "extra_contacts_decision", "user_value": "not_authors"}]

    rows = reconcile_contacts(author_rows, contact_rows, intake_rows)
    row_map = {row.name: row for row in rows}

    assert row_map["Extra Person"].action_needed == "documented_non_author_contact"


def test_build_outputs_writes_contact_reconciliation(tmp_path):
    metadata = tmp_path / "manuscript" / "submission_metadata" / "AUTHOR_METADATA_TEMPLATE.tsv"
    contacts = (
        tmp_path
        / "manuscript"
        / "submission_metadata"
        / "USER_PROVIDED_AUTHOR_EMAILS_2026-05-03.tsv"
    )
    metadata.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {"given_names": "Han", "family_names": "Yan", "email": "missing_email"},
            {"given_names": "Yi", "family_names": "Miao", "email": "miaoyi@njmu.edu.cn"},
        ]
    ).to_csv(metadata, sep="\t", index=False)
    pd.DataFrame([{"name": "Yi Miao", "email": "miaoyi@njmu.edu.cn"}]).to_csv(
        contacts, sep="\t", index=False
    )

    summary = build_outputs(tmp_path)

    assert summary["decision"] == "AUTHOR_CONTACT_RECONCILIATION_BLOCKED_MISSING_EMAIL"
    assert summary["blocking_missing_email"] == 1
    assert (tmp_path / summary["tsv"]).exists()
    assert (tmp_path / summary["report"]).exists()
