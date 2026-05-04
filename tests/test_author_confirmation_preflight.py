from pathlib import Path
import importlib.util
import sys


def _load_script(name: str):
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_author_confirmation_blocks_missing_email(tmp_path):
    script = _load_script("check_author_confirmation_preflight")
    checklist = tmp_path / "AUTHOR_CONFIRMATION_CHECKLIST.tsv"
    checklist.write_text(
        "item\tcurrent_value\trequired_confirmation\tstatus\towner\n"
        "Han Yan email\tmissing_email\tProvide final email\tblocking_author_confirmation\tauthors\n"
        "ORCID IDs\tnot_provided\tOptional\toptional_author_metadata\tauthors\n",
        encoding="utf-8",
    )

    rows = script.build_author_confirmation_rows(checklist)

    assert script.classify_decision(rows) == "AUTHOR_CONFIRMATION_BLOCKED"
    assert rows[0].severity == "blocking"
    assert rows[1].severity == "optional"


def test_author_confirmation_pending_when_no_blocking(tmp_path):
    script = _load_script("check_author_confirmation_preflight")
    checklist = tmp_path / "AUTHOR_CONFIRMATION_CHECKLIST.tsv"
    checklist.write_text(
        "item\tcurrent_value\trequired_confirmation\tstatus\towner\n"
        "CRediT roles\tSee template\tApprove roles\tdraft_pending_author_confirmation\tauthors\n",
        encoding="utf-8",
    )

    rows = script.build_author_confirmation_rows(checklist)

    assert script.classify_decision(rows) == "AUTHOR_CONFIRMATION_PENDING"


def test_author_confirmation_blocks_pyproject_author_missing_email(tmp_path):
    script = _load_script("check_author_confirmation_preflight")
    checklist = tmp_path / "AUTHOR_CONFIRMATION_CHECKLIST.tsv"
    checklist.write_text(
        "item\tcurrent_value\trequired_confirmation\tstatus\towner\n"
        "Competing interests\tapproved\tApprove wording\tconfirmed\tauthors\n",
        encoding="utf-8",
    )
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        "[project]\n"
        "authors = [\n"
        '  {name = "Chongfa Chen", email = "chen@example.org"},\n'
        '  {name = "Han Yan"},\n'
        "]\n",
        encoding="utf-8",
    )

    rows = script.build_author_confirmation_rows(checklist, pyproject)

    assert script.classify_decision(rows) == "AUTHOR_CONFIRMATION_BLOCKED"
    assert any(row.item == "pyproject author email: Han Yan" for row in rows)


def test_author_confirmation_report_contains_minimal_reply():
    script = _load_script("check_author_confirmation_preflight")
    rows = [
        script.AuthorConfirmationRow(
            item="Han Yan email",
            severity="blocking",
            status="blocking_author_confirmation",
            current_value="missing_email",
            required_confirmation="Provide final email",
            owner="authors",
        )
    ]

    report = script.build_report(rows)

    assert "AUTHOR_CONFIRMATION_BLOCKED" in report
    assert "Han Yan email:" in report
    assert "does not guarantee journal acceptance" in report


def test_author_confirmation_outputs_are_written(tmp_path):
    script = _load_script("check_author_confirmation_preflight")
    rows = [
        script.AuthorConfirmationRow(
            item="ethics data-use",
            severity="pending",
            status="draft_pending_author_confirmation",
            current_value="draft",
            required_confirmation="Confirm wording",
            owner="corresponding_authors",
        )
    ]

    outputs = script.write_outputs(tmp_path, rows)

    assert outputs["status"].exists()
    assert outputs["report"].exists()
    assert "ethics data-use" in outputs["status"].read_text(encoding="utf-8")
