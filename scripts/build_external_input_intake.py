#!/usr/bin/env python
"""Build and validate a single external-input intake sheet.

Author: SheafSignal contributors
Date: 2026-05-03
Purpose: consolidate user-owned release credentials, author confirmations, DOI
information, and external-review returns into one auditable intake workflow
without storing secret token values in the repository.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


DEFAULT_TEMPLATE = Path("release/EXTERNAL_INPUT_INTAKE_TEMPLATE.tsv")
DEFAULT_STATUS = Path("release/EXTERNAL_INPUT_INTAKE_STATUS.tsv")
DEFAULT_REPORT = Path("release/EXTERNAL_INPUT_INTAKE_REPORT.md")
def _default_secret_path(env_name: str, filename: str) -> Path:
    override = os.environ.get(env_name)
    if override:
        return Path(override)
    secret_dir = os.environ.get("SHEAFSIGNAL_SECRET_DIR")
    if secret_dir:
        return Path(secret_dir) / filename
    return Path.home() / ".config" / "sheafsignal" / filename


GITHUB_TOKEN_PATH = _default_secret_path("SHEAFSIGNAL_GITHUB_TOKEN_PATH", "github_token.txt")
ZENODO_TOKEN_PATH = _default_secret_path("SHEAFSIGNAL_ZENODO_TOKEN_PATH", "zenodo_token.txt")

YES_VALUES = {"yes", "approved", "confirmed", "true"}
OPTIONAL_BLANK = {"external_beta_review_return_path"}


@dataclass(frozen=True)
class IntakeRow:
    field_id: str
    priority: str
    owner: str
    expected_input: str
    current_value: str
    user_value: str
    secret_path: str
    validation_rule: str
    notes: str


@dataclass(frozen=True)
class IntakeStatus:
    field_id: str
    priority: str
    status: str
    blocking: str
    evidence: str
    next_action: str


def default_rows() -> list[IntakeRow]:
    return [
        IntakeRow(
            "github_token_file",
            "P0",
            "user",
            "Save GitHub classic token with repo and workflow scopes to secret_path; do not paste token here.",
            "valid_missing_workflow_scope",
            "",
            str(GITHUB_TOKEN_PATH),
            "file_exists_nonempty",
            "The token must include repo and workflow scopes; scope validation is done by check_external_release_authorization.py.",
        ),
        IntakeRow(
            "github_token_rotation_confirmed",
            "P0",
            "user",
            "yes only after replacing any GitHub token that was pasted into chat or another non-secret channel.",
            "token_pasted_in_chat_requires_rotation",
            "",
            "",
            "yes",
            "Security gate: Codex must not push with a token that may have been exposed in chat.",
        ),
        IntakeRow(
            "zenodo_doi",
            "P0",
            "user_or_codex_after_zenodo",
            "Real DOI, for example 10.5281/zenodo.1234567, if minted manually.",
            "PENDING_ZENODO_RELEASE",
            "",
            "",
            "doi_or_zenodo_token",
            "Either fill this DOI or save a Zenodo token to D:/secrets/zenodo_token.txt.",
        ),
        IntakeRow(
            "han_yan_email",
            "P0",
            "authors",
            "Final email for corresponding author Han Yan.",
            "missing_email",
            "",
            "",
            "email",
            "Required before journal submission metadata can be finalized.",
        ),
        IntakeRow(
            "extra_contacts_decision",
            "P0",
            "authors",
            "Use not_authors, or expand_author_line with final order/affiliation/CRediT in notes.",
            "16 supplied contacts not in current author line",
            "",
            "",
            "one_of:not_authors|expand_author_line",
            "Do not silently ignore unmatched contact names.",
        ),
        IntakeRow(
            "equal_contribution_wording",
            "P0",
            "authors",
            "Exact wording, for example Han Yan and Yi Miao contributed equally.",
            "ambiguous YM/YH vs HY/YM",
            "",
            "",
            "nonempty",
            "Needed to remove the equal-contribution blocker.",
        ),
        IntakeRow(
            "author_order_approved",
            "P0",
            "authors",
            "yes if final author order and degrees are approved.",
            "pending",
            "",
            "",
            "yes",
            "If not approved, put corrections in notes.",
        ),
        IntakeRow(
            "credit_roles_approved",
            "P0",
            "authors",
            "yes if CRediT assignments are approved.",
            "pending",
            "",
            "",
            "yes",
            "If not approved, put corrected roles in notes.",
        ),
        IntakeRow(
            "funding_statement_approved",
            "P0",
            "authors",
            "yes if no funding statement is correct, or put grant details in user_value/notes.",
            "Not reported",
            "",
            "",
            "nonempty",
            "A real grant statement can be supplied instead of yes.",
        ),
        IntakeRow(
            "competing_interests_approved",
            "P0",
            "corresponding_authors",
            "yes if 'no competing interests' is correct, or put disclosure.",
            "pending",
            "",
            "",
            "nonempty",
            "Do not infer COI status from silence.",
        ),
        IntakeRow(
            "ethics_data_use_approved",
            "P0",
            "corresponding_authors",
            "yes if public-data ethics/data-use wording is approved, or put institutional wording.",
            "pending",
            "",
            "",
            "nonempty",
            "IRB/exemption wording is institution- and journal-dependent.",
        ),
        IntakeRow(
            "github_public_release_approved",
            "P0",
            "authors",
            "yes if public GitHub release is approved.",
            "pending",
            "",
            "",
            "yes",
            "Required before public release.",
        ),
        IntakeRow(
            "zenodo_deposition_approved",
            "P0",
            "authors",
            "yes if Zenodo deposition contents/restrictions are approved.",
            "pending",
            "",
            "",
            "yes",
            "Required before DOI release.",
        ),
        IntakeRow(
            "external_beta_review_return_path",
            "P1",
            "user_or_reviewers",
            "Optional path to returned external review comments or folder.",
            "not_returned",
            "",
            "",
            "optional_path_exists",
            "Useful for high-impact hardening, but not required for local infrastructure checks.",
        ),
    ]


def _read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _replace_with_retry(tmp_path: Path, final_path: Path, retries: int = 5) -> None:
    for attempt in range(retries):
        try:
            tmp_path.replace(final_path)
            return
        except PermissionError:
            if attempt == retries - 1:
                raise
            time.sleep(0.2 * (attempt + 1))


def _write_tsv_atomic(path: Path, rows: list[object], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow(row.__dict__)
    _replace_with_retry(tmp_path, path)


def _write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    _replace_with_retry(tmp_path, path)


def _is_email(value: str) -> bool:
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value.strip()))


def _is_doi(value: str) -> bool:
    normalized = value.strip().removeprefix("https://doi.org/")
    return bool(re.fullmatch(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", normalized))


def _validate_row(row: dict[str, str]) -> IntakeStatus:
    field_id = str(row.get("field_id", "")).strip()
    priority = str(row.get("priority", "")).strip()
    rule = str(row.get("validation_rule", "")).strip()
    value = str(row.get("user_value", "")).strip()
    secret_path = str(row.get("secret_path", "")).strip()
    passed = False
    evidence = "not_validated"
    next_action = "Fill the required user_value or secret_path."

    if rule == "file_exists_nonempty":
        path = Path(secret_path)
        passed = path.exists() and path.is_file() and path.stat().st_size > 0
        evidence = f"{secret_path} {'exists_nonempty' if passed else 'missing_or_empty'}"
        next_action = f"Save the required secret file to {secret_path}."
    elif rule == "doi_or_zenodo_token":
        doi_ok = _is_doi(value)
        token_ok = ZENODO_TOKEN_PATH.exists() and ZENODO_TOKEN_PATH.stat().st_size > 0
        passed = doi_ok or token_ok
        evidence = f"doi_valid={doi_ok}; zenodo_token_file_present={token_ok}"
        next_action = "Fill a real DOI or save a Zenodo token outside the repository."
    elif rule == "email":
        passed = _is_email(value)
        evidence = "email_valid" if passed else "email_missing_or_invalid"
        next_action = "Provide a valid email address."
    elif rule.startswith("one_of:"):
        choices = set(rule.split(":", 1)[1].split("|"))
        passed = value in choices
        evidence = f"value={value or 'blank'}; allowed={','.join(sorted(choices))}"
        next_action = "Choose one of the allowed values and put details in notes if needed."
    elif rule == "yes":
        passed = value.lower() in YES_VALUES
        evidence = f"value={value or 'blank'}"
        next_action = "Enter yes/approved/confirmed, or document corrections before approval."
    elif rule == "nonempty":
        passed = bool(value)
        evidence = "nonempty" if passed else "blank"
        next_action = "Provide an approval value or replacement wording in user_value."
    elif rule == "optional_path_exists":
        if not value and field_id in OPTIONAL_BLANK:
            passed = True
            evidence = "optional_blank"
        else:
            passed = Path(value).exists()
            evidence = f"path_exists={passed}"
        next_action = "Optionally provide a real path to returned reviews."
    else:
        evidence = f"unknown_rule={rule}"
        next_action = "Fix validation_rule in the intake template."

    return IntakeStatus(
        field_id=field_id,
        priority=priority,
        status="pass" if passed else "missing",
        blocking="yes" if priority == "P0" and not passed else "no",
        evidence=evidence,
        next_action=next_action,
    )


def build_status_rows(template_rows: list[dict[str, str]]) -> list[IntakeStatus]:
    return [_validate_row(row) for row in template_rows]


def classify_decision(rows: list[IntakeStatus]) -> str:
    if not rows:
        return "EXTERNAL_INPUT_INTAKE_TEMPLATE_MISSING"
    if any(row.blocking == "yes" for row in rows):
        return "EXTERNAL_INPUT_INTAKE_P0_MISSING"
    return "EXTERNAL_INPUT_INTAKE_READY"


def build_report(rows: list[IntakeStatus]) -> str:
    decision = classify_decision(rows)
    p0_missing = sum(row.blocking == "yes" for row in rows)
    table = [
        "| Field | Priority | Status | Blocking | Evidence | Next action |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        table.append(
            f"| `{row.field_id}` | `{row.priority}` | `{row.status}` | `{row.blocking}` | {row.evidence} | {row.next_action} |"
        )
    return "\n".join(
        [
            "# External Input Intake Report",
            "",
            f"- Timestamp: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`",
            f"- Decision: `{decision}`",
            f"- P0 missing/blocking fields: `{p0_missing}`",
            "",
            "## Intake Status",
            "",
            *table,
            "",
            "## How To Use",
            "",
            "Fill `release/EXTERNAL_INPUT_INTAKE_TEMPLATE.tsv`. Do not paste GitHub",
            "or Zenodo token values into the TSV. Save secret tokens only to the",
            "`secret_path` locations listed in the template.",
            "",
            "After filling the TSV or secret files, run:",
            "",
            "```bash",
            "python scripts/build_external_input_intake.py",
            "python scripts/run_unblock_readiness_check.py",
            "```",
            "",
            "## Boundary",
            "",
            "This intake validates whether required external inputs are present. It",
            "does not infer authorship, does not validate token scopes by itself,",
            "does not mint a DOI, and does not guarantee journal acceptance.",
            "",
        ]
    )


def build_outputs(root: Path, *, overwrite_template: bool = False) -> dict[str, object]:
    root = root.resolve()
    template_path = root / DEFAULT_TEMPLATE
    if overwrite_template or not template_path.exists():
        _write_tsv_atomic(
            template_path,
            default_rows(),
            list(IntakeRow.__dataclass_fields__.keys()),
        )
    status_rows = build_status_rows(_read_tsv(template_path))
    _write_tsv_atomic(
        root / DEFAULT_STATUS,
        status_rows,
        list(IntakeStatus.__dataclass_fields__.keys()),
    )
    _write_text_atomic(root / DEFAULT_REPORT, build_report(status_rows))
    return {
        "decision": classify_decision(status_rows),
        "rows": len(status_rows),
        "p0_missing": sum(row.blocking == "yes" for row in status_rows),
        "template": DEFAULT_TEMPLATE.as_posix(),
        "status": DEFAULT_STATUS.as_posix(),
        "report": DEFAULT_REPORT.as_posix(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--overwrite-template", action="store_true")
    args = parser.parse_args(argv)
    summary = build_outputs(Path(args.root), overwrite_template=args.overwrite_template)
    print("EXTERNAL_INPUT_INTAKE_WRITTEN")
    for key, value in summary.items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
