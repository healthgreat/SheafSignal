#!/usr/bin/env python
"""Reconcile current manuscript author metadata with a supplied email list.

Author: SheafSignal contributors
Date: 2026-05-03
Purpose: expose author-contact mismatches before public release or journal
submission without inferring authorship, contribution, or email ownership.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


DEFAULT_AUTHOR_METADATA = Path("manuscript/submission_metadata/AUTHOR_METADATA_TEMPLATE.tsv")
DEFAULT_CONTACTS = Path("manuscript/submission_metadata/USER_PROVIDED_AUTHOR_EMAILS_2026-05-03.tsv")
DEFAULT_OUT_TSV = Path("manuscript/submission_metadata/AUTHOR_CONTACT_RECONCILIATION.tsv")
DEFAULT_OUT_REPORT = Path("manuscript/submission_metadata/AUTHOR_CONTACT_RECONCILIATION_REPORT.md")


@dataclass(frozen=True)
class ContactRow:
    name: str
    manuscript_status: str
    manuscript_email: str
    supplied_email: str
    action_needed: str


def _read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _write_tsv_atomic(path: Path, rows: list[ContactRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    fieldnames = list(ContactRow.__dataclass_fields__.keys())
    with tmp_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow(row.__dict__)
    tmp_path.replace(path)


def _write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def _author_name(row: dict[str, str]) -> str:
    given = str(row.get("given_names", "")).strip()
    family = str(row.get("family_names", "")).strip()
    return f"{given} {family}".strip()


def _contact_map(contact_rows: list[dict[str, str]]) -> dict[str, str]:
    return {
        str(row.get("name", "")).strip(): str(row.get("email", "")).strip()
        for row in contact_rows
        if str(row.get("name", "")).strip()
    }


def reconcile_contacts(
    author_rows: list[dict[str, str]], contact_rows: list[dict[str, str]]
) -> list[ContactRow]:
    contacts = _contact_map(contact_rows)
    current_names = {_author_name(row) for row in author_rows}
    rows: list[ContactRow] = []
    for author in author_rows:
        name = _author_name(author)
        manuscript_email = str(author.get("email", "")).strip()
        supplied_email = contacts.get(name, "")
        if not supplied_email and manuscript_email in {"", "missing_email", "not_provided"}:
            action = "blocking_missing_email"
        elif supplied_email and manuscript_email in {"", "missing_email", "not_provided"}:
            action = "update_manuscript_email_after_author_confirmation"
        elif supplied_email and supplied_email != manuscript_email:
            action = "review_email_mismatch"
        else:
            action = "no_contact_mismatch_detected"
        rows.append(
            ContactRow(
                name=name,
                manuscript_status="in_current_author_line",
                manuscript_email=manuscript_email,
                supplied_email=supplied_email or "not_supplied",
                action_needed=action,
            )
        )

    for name, email in sorted(contacts.items()):
        if name not in current_names:
            rows.append(
                ContactRow(
                    name=name,
                    manuscript_status="not_in_current_author_line",
                    manuscript_email="not_applicable",
                    supplied_email=email,
                    action_needed="confirm_not_author_or_update_author_line",
                )
            )
    return rows


def classify_decision(rows: list[ContactRow]) -> str:
    if not rows:
        return "AUTHOR_CONTACT_RECONCILIATION_INPUT_MISSING"
    if any(row.action_needed == "blocking_missing_email" for row in rows):
        return "AUTHOR_CONTACT_RECONCILIATION_BLOCKED_MISSING_EMAIL"
    if any(
        row.action_needed
        in {
            "update_manuscript_email_after_author_confirmation",
            "review_email_mismatch",
            "confirm_not_author_or_update_author_line",
        }
        for row in rows
    ):
        return "AUTHOR_CONTACT_RECONCILIATION_REVIEW_NEEDED"
    return "AUTHOR_CONTACT_RECONCILIATION_READY"


def build_report(rows: list[ContactRow]) -> str:
    decision = classify_decision(rows)
    missing = [row for row in rows if row.action_needed == "blocking_missing_email"]
    extras = [row for row in rows if row.manuscript_status == "not_in_current_author_line"]
    mismatches = [row for row in rows if row.action_needed == "review_email_mismatch"]
    matched = [row for row in rows if row.action_needed == "no_contact_mismatch_detected"]
    lines = [
        "# Author Contact Reconciliation Report",
        "",
        f"- Timestamp: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`",
        f"- Decision: `{decision}`",
        f"- Current manuscript authors with matched or unchanged contact: `{len(matched)}`",
        f"- Current manuscript authors missing supplied email: `{len(missing)}`",
        f"- Email mismatches requiring review: `{len(mismatches)}`",
        f"- Supplied contacts not in current author line: `{len(extras)}`",
        "",
        "## Blocking Missing Emails",
        "",
    ]
    if missing:
        lines.extend(
            f"- `{row.name}`: manuscript email `{row.manuscript_email}`, supplied email `{row.supplied_email}`"
            for row in missing
        )
    else:
        lines.append("- none")
    lines.extend(["", "## Supplied Contacts Not In Current Author Line", ""])
    if extras:
        lines.extend(f"- `{row.name}`: `{row.supplied_email}`" for row in extras)
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This reconciliation table does not decide authorship order, contribution,",
            "email ownership, corresponding-author status, or journal eligibility. It",
            "only compares the current author metadata with the user-supplied contact",
            "list so that submission blockers can be resolved explicitly.",
            "",
        ]
    )
    return "\n".join(lines)


def build_outputs(
    root: Path,
    author_metadata: Path = DEFAULT_AUTHOR_METADATA,
    contacts: Path = DEFAULT_CONTACTS,
    out_tsv: Path = DEFAULT_OUT_TSV,
    out_report: Path = DEFAULT_OUT_REPORT,
) -> dict[str, object]:
    root = root.resolve()
    rows = reconcile_contacts(_read_tsv(root / author_metadata), _read_tsv(root / contacts))
    _write_tsv_atomic(root / out_tsv, rows)
    _write_text_atomic(root / out_report, build_report(rows))
    return {
        "decision": classify_decision(rows),
        "rows": len(rows),
        "blocking_missing_email": sum(row.action_needed == "blocking_missing_email" for row in rows),
        "extra_contacts": sum(row.manuscript_status == "not_in_current_author_line" for row in rows),
        "tsv": out_tsv.as_posix(),
        "report": out_report.as_posix(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--author-metadata", default=str(DEFAULT_AUTHOR_METADATA))
    parser.add_argument("--contacts", default=str(DEFAULT_CONTACTS))
    parser.add_argument("--out-tsv", default=str(DEFAULT_OUT_TSV))
    parser.add_argument("--out-report", default=str(DEFAULT_OUT_REPORT))
    args = parser.parse_args(argv)

    summary = build_outputs(
        Path(args.root),
        Path(args.author_metadata),
        Path(args.contacts),
        Path(args.out_tsv),
        Path(args.out_report),
    )
    print("AUTHOR_CONTACT_RECONCILIATION_WRITTEN")
    for key, value in summary.items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
