#!/usr/bin/env python
"""Check author-owned submission confirmations before journal upload.

Author: SheafSignal maintainers
Date: 2026-05-03
Purpose: separate author-owned metadata blockers from code, statistics, and
release-infrastructure blockers for the SheafSignal submission package.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
import tomllib


DEFAULT_CHECKLIST = Path("manuscript/submission_metadata/AUTHOR_CONFIRMATION_CHECKLIST.tsv")
DEFAULT_STATUS = Path("manuscript/submission_metadata/AUTHOR_CONFIRMATION_PREFLIGHT_STATUS.tsv")
DEFAULT_REPORT = Path("manuscript/submission_metadata/AUTHOR_CONFIRMATION_PREFLIGHT_REPORT.md")
DEFAULT_PYPROJECT = Path("pyproject.toml")

BLOCKING_STATUSES = {"blocking_author_confirmation"}
PENDING_STATUSES = {
    "draft_pending_author_confirmation",
    "needs_author_confirmation",
    "external_release_confirmation",
}
OPTIONAL_STATUSES = {"optional_author_metadata"}


@dataclass(frozen=True)
class AuthorConfirmationRow:
    item: str
    severity: str
    status: str
    current_value: str
    required_confirmation: str
    owner: str


def _read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _write_tsv_atomic(path: Path, rows: list[AuthorConfirmationRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    fieldnames = [
        "item",
        "severity",
        "status",
        "current_value",
        "required_confirmation",
        "owner",
    ]
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


def classify_status(status: str) -> str:
    normalized = status.strip()
    if normalized in BLOCKING_STATUSES:
        return "blocking"
    if normalized in PENDING_STATUSES:
        return "pending"
    if normalized in OPTIONAL_STATUSES:
        return "optional"
    if normalized in {"confirmed", "complete", "approved"}:
        return "pass"
    return "review"


def _pyproject_author_email_rows(pyproject_path: Path | None) -> list[AuthorConfirmationRow]:
    if pyproject_path is None or not pyproject_path.exists():
        return []
    with pyproject_path.open("rb") as handle:
        data = tomllib.load(handle)
    rows: list[AuthorConfirmationRow] = []
    for author in data.get("project", {}).get("authors", []):
        if not isinstance(author, dict):
            continue
        name = str(author.get("name", "")).strip()
        email = str(author.get("email", "")).strip()
        if name and not email:
            rows.append(
                AuthorConfirmationRow(
                    item=f"pyproject author email: {name}",
                    severity="blocking",
                    status="blocking_author_confirmation",
                    current_value="missing_email_in_pyproject.toml",
                    required_confirmation=(
                        "Add a non-empty email field for every pyproject.toml "
                        "project author before submission."
                    ),
                    owner="authors",
                )
            )
    return rows


def build_author_confirmation_rows(
    checklist_path: Path,
    pyproject_path: Path | None = None,
) -> list[AuthorConfirmationRow]:
    raw_rows = _read_tsv(checklist_path)
    rows: list[AuthorConfirmationRow] = []
    for raw in raw_rows:
        status = str(raw.get("status", "")).strip()
        rows.append(
            AuthorConfirmationRow(
                item=str(raw.get("item", "")).strip(),
                severity=classify_status(status),
                status=status,
                current_value=str(raw.get("current_value", "")).strip(),
                required_confirmation=str(raw.get("required_confirmation", "")).strip(),
                owner=str(raw.get("owner", "")).strip(),
            )
        )
    rows.extend(_pyproject_author_email_rows(pyproject_path))
    return rows


def classify_decision(rows: list[AuthorConfirmationRow]) -> str:
    if not rows:
        return "AUTHOR_CONFIRMATION_CHECKLIST_MISSING"
    if any(row.severity == "blocking" for row in rows):
        return "AUTHOR_CONFIRMATION_BLOCKED"
    if any(row.severity in {"pending", "review"} for row in rows):
        return "AUTHOR_CONFIRMATION_PENDING"
    return "AUTHOR_CONFIRMATION_READY"


def build_report(rows: list[AuthorConfirmationRow]) -> str:
    decision = classify_decision(rows)
    counts = {
        "blocking": sum(row.severity == "blocking" for row in rows),
        "pending": sum(row.severity == "pending" for row in rows),
        "optional": sum(row.severity == "optional" for row in rows),
        "pass": sum(row.severity == "pass" for row in rows),
        "review": sum(row.severity == "review" for row in rows),
    }
    blocking_lines = [
        f"- `{row.item}`: `{row.current_value}` -> {row.required_confirmation}"
        for row in rows
        if row.severity == "blocking"
    ] or ["- none"]
    pending_lines = [
        f"- `{row.item}`: `{row.status}` -> {row.required_confirmation}"
        for row in rows
        if row.severity == "pending"
    ] or ["- none"]
    optional_lines = [
        f"- `{row.item}`: {row.required_confirmation}"
        for row in rows
        if row.severity == "optional"
    ] or ["- none"]
    return "\n".join(
        [
            "# Author Confirmation Preflight Report",
            "",
            f"- Decision: `{decision}`",
            f"- Blocking author confirmations: `{counts['blocking']}`",
            f"- Pending author confirmations: `{counts['pending']}`",
            f"- Optional author metadata items: `{counts['optional']}`",
            f"- Passed confirmations: `{counts['pass']}`",
            f"- Review-needed rows: `{counts['review']}`",
            "",
            "## Blocking Author Confirmations",
            "",
            *blocking_lines,
            "",
            "## Pending Author Confirmations",
            "",
            *pending_lines,
            "",
            "## Optional Metadata",
            "",
            *optional_lines,
            "",
            "## Minimal Author Reply Needed",
            "",
            "```text",
            "Han Yan email:",
            "Equal contribution wording:",
            "CRediT roles approved: yes/no",
            "Funding statement approved or grant details:",
            "Competing interests approved: yes/no",
            "Ethics/data-use wording approved: yes/no",
            "Public GitHub and Zenodo release approved: yes/no",
            "```",
            "",
            "## Boundary",
            "",
            "This report checks author-owned submission facts. It does not infer or",
            "fabricate author confirmations, does not change scientific claims, and",
            "does not guarantee journal acceptance.",
            "",
        ]
    )


def write_outputs(
    root: Path,
    rows: list[AuthorConfirmationRow],
    status_path: Path = DEFAULT_STATUS,
    report_path: Path = DEFAULT_REPORT,
) -> dict[str, Path]:
    status_out = root / status_path
    report_out = root / report_path
    _write_tsv_atomic(status_out, rows)
    _write_text_atomic(report_out, build_report(rows))
    return {"status": status_out, "report": report_out}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--checklist", default=str(DEFAULT_CHECKLIST))
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    checklist = Path(args.checklist)
    if not checklist.is_absolute():
        checklist = root / checklist
    rows = build_author_confirmation_rows(checklist, root / DEFAULT_PYPROJECT)
    outputs = write_outputs(root, rows)
    print(f"decision: {classify_decision(rows)}")
    for label, path in outputs.items():
        print(f"wrote {label}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
