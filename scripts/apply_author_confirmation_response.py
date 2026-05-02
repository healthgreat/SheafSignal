#!/usr/bin/env python
"""Create or apply machine-readable author confirmation responses.

Author: SheafSignal contributors
Date: 2026-05-03
Purpose: turn author-owned submission facts into a TSV workflow that can update
the author confirmation checklist without inferring or fabricating metadata.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path


DEFAULT_CHECKLIST = Path("manuscript/submission_metadata/AUTHOR_CONFIRMATION_CHECKLIST.tsv")
DEFAULT_RESPONSE = Path("manuscript/submission_metadata/AUTHOR_CONFIRMATION_RESPONSE_TEMPLATE.tsv")
DEFAULT_REPORT = Path("manuscript/submission_metadata/AUTHOR_CONFIRMATION_RESPONSE_APPLY_REPORT.md")

CONFIRMED_STATUSES = {"yes", "approved", "confirmed"}
BLOCKING_RESPONSES = {"no", "rejected", "blocked"}
SKIP_RESPONSES = {"skip", "not_applicable", "na", "n/a"}


@dataclass(frozen=True)
class ResponseRow:
    item: str
    current_value: str
    required_confirmation: str
    owner: str
    confirmed: str
    final_value: str
    notes: str


def _read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _write_tsv_atomic(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    tmp_path.replace(path)


def _write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def build_response_template(checklist_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = []
    for row in checklist_rows:
        rows.append(
            {
                "item": row.get("item", ""),
                "current_value": row.get("current_value", ""),
                "required_confirmation": row.get("required_confirmation", ""),
                "owner": row.get("owner", ""),
                "confirmed": "fill_yes_no_or_skip",
                "final_value": "",
                "notes": "",
            }
        )
    return rows


def _response_map(response_rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {str(row.get("item", "")).strip(): row for row in response_rows}


def _status_after_response(original_status: str, confirmed: str) -> str:
    normalized = confirmed.strip().lower()
    if normalized in CONFIRMED_STATUSES:
        return "confirmed"
    if normalized in BLOCKING_RESPONSES:
        return "blocked_by_author_response"
    if normalized in SKIP_RESPONSES:
        return "optional_author_metadata" if original_status == "optional_author_metadata" else original_status
    return original_status


def apply_responses(
    checklist_rows: list[dict[str, str]],
    response_rows: list[dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    responses = _response_map(response_rows)
    updated_rows = []
    audit_rows = []
    for row in checklist_rows:
        item = str(row.get("item", "")).strip()
        response = responses.get(item, {})
        confirmed = str(response.get("confirmed", "")).strip()
        final_value = str(response.get("final_value", "")).strip()
        old_status = str(row.get("status", "")).strip()
        old_value = str(row.get("current_value", "")).strip()
        new_status = _status_after_response(old_status, confirmed)
        new_value = final_value if new_status == "confirmed" and final_value else old_value
        updated = dict(row)
        updated["current_value"] = new_value
        updated["status"] = new_status
        updated_rows.append(updated)
        audit_rows.append(
            {
                "item": item,
                "old_status": old_status,
                "new_status": new_status,
                "old_value": old_value,
                "new_value": new_value,
                "confirmed": confirmed or "blank",
                "notes": str(response.get("notes", "")).strip(),
            }
        )
    return updated_rows, audit_rows


def classify_decision(audit_rows: list[dict[str, str]], *, applied: bool) -> str:
    if not applied:
        return "AUTHOR_CONFIRMATION_RESPONSE_TEMPLATE_READY"
    if any(row["new_status"] == "blocked_by_author_response" for row in audit_rows):
        return "AUTHOR_CONFIRMATION_RESPONSE_APPLIED_AUTHOR_BLOCKED"
    if any(row["confirmed"] == "blank" for row in audit_rows):
        return "AUTHOR_CONFIRMATION_RESPONSE_PARTIAL_APPLIED"
    return "AUTHOR_CONFIRMATION_RESPONSE_APPLIED"


def build_report(audit_rows: list[dict[str, str]], *, applied: bool) -> str:
    decision = classify_decision(audit_rows, applied=applied)
    confirmed_count = sum(row["new_status"] == "confirmed" for row in audit_rows)
    blank_count = sum(row["confirmed"] == "blank" for row in audit_rows)
    blocked_count = sum(row["new_status"] == "blocked_by_author_response" for row in audit_rows)
    lines = [
        "# Author Confirmation Response Apply Report",
        "",
        f"- Decision: `{decision}`",
        f"- Applied to checklist: `{applied}`",
        f"- Confirmed rows: `{confirmed_count}`",
        f"- Blank response rows: `{blank_count}`",
        f"- Author-blocked rows: `{blocked_count}`",
        "",
        "## Changed Rows",
        "",
    ]
    changed = [
        row
        for row in audit_rows
        if row["old_status"] != row["new_status"] or row["old_value"] != row["new_value"]
    ]
    if not changed:
        lines.append("- none")
    else:
        for row in changed:
            lines.append(
                f"- `{row['item']}`: `{row['old_status']}` -> `{row['new_status']}`"
            )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This script applies author-provided TSV responses only. It does not infer",
            "missing author facts, does not validate email ownership, and does not",
            "guarantee journal acceptance.",
            "",
        ]
    )
    return "\n".join(lines)


def write_template(root: Path, checklist_path: Path, response_path: Path, report_path: Path) -> dict[str, Path]:
    checklist_rows = _read_tsv(root / checklist_path)
    template_rows = build_response_template(checklist_rows)
    fieldnames = list(ResponseRow.__dataclass_fields__.keys())
    _write_tsv_atomic(root / response_path, template_rows, fieldnames)
    _, audit_rows = apply_responses(checklist_rows, template_rows)
    _write_text_atomic(root / report_path, build_report(audit_rows, applied=False))
    return {"response": root / response_path, "report": root / report_path}


def apply_response_file(root: Path, checklist_path: Path, response_path: Path, report_path: Path) -> dict[str, Path]:
    checklist_rows = _read_tsv(root / checklist_path)
    response_rows = _read_tsv(root / response_path)
    updated_rows, audit_rows = apply_responses(checklist_rows, response_rows)
    if checklist_rows:
        fieldnames = list(checklist_rows[0].keys())
    else:
        fieldnames = ["item", "current_value", "required_confirmation", "status", "owner"]
    _write_tsv_atomic(root / checklist_path, updated_rows, fieldnames)
    _write_text_atomic(root / report_path, build_report(audit_rows, applied=True))
    return {"checklist": root / checklist_path, "report": root / report_path}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--checklist", default=str(DEFAULT_CHECKLIST))
    parser.add_argument("--response", default=str(DEFAULT_RESPONSE))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    checklist = Path(args.checklist)
    response = Path(args.response)
    report = Path(args.report)
    if args.apply:
        outputs = apply_response_file(root, checklist, response, report)
        print("AUTHOR_CONFIRMATION_RESPONSE_APPLY_RUN")
    else:
        outputs = write_template(root, checklist, response, report)
        print("AUTHOR_CONFIRMATION_RESPONSE_TEMPLATE_WRITTEN")
    for label, path in outputs.items():
        print(f"{label}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
