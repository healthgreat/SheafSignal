#!/usr/bin/env python
"""Create or apply submission-day journal metric/CAS/warning checks.

Author: SheafSignal contributors
Date: 2026-05-03
Purpose: prevent stale journal-positioning claims by requiring a
machine-readable submission-day verification of JIF, CAS zone, and warning-list
status before final target selection.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path


DEFAULT_AUDIT = Path("manuscript/journal_metric_audit/JOURNAL_METRIC_AUDIT.tsv")
DEFAULT_RESPONSE = Path(
    "manuscript/journal_metric_audit/JOURNAL_SUBMISSION_DAY_CHECK_TEMPLATE.tsv"
)
DEFAULT_REPORT = Path(
    "manuscript/journal_metric_audit/JOURNAL_SUBMISSION_DAY_CHECK_REPORT.md"
)

CONFIRMED_VALUES = {"yes", "confirmed", "approved"}
BLOCKED_VALUES = {"no", "blocked", "not_verified"}


@dataclass(frozen=True)
class SubmissionDayRow:
    journal: str
    current_route_decision: str
    latest_jif: str
    latest_five_year_jif: str
    official_cas_zone: str
    official_warning_status: str
    verification_date: str
    verifier: str
    source_url_or_note: str
    selected_target: str
    confirmed_for_submission: str
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


def build_template_rows(audit_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = []
    for row in audit_rows:
        rows.append(
            {
                "journal": row.get("journal", ""),
                "current_route_decision": row.get("route_decision", ""),
                "latest_jif": row.get("jif_2024", ""),
                "latest_five_year_jif": row.get("five_year_jif_2024", ""),
                "official_cas_zone": "fill_official_cas_zone",
                "official_warning_status": "fill_official_warning_status",
                "verification_date": "YYYY-MM-DD",
                "verifier": "",
                "source_url_or_note": row.get("metric_source_url", ""),
                "selected_target": "yes_or_no",
                "confirmed_for_submission": "fill_yes_no",
                "notes": "",
            }
        )
    return rows


def _is_confirmed(row: dict[str, str]) -> bool:
    return str(row.get("confirmed_for_submission", "")).strip().lower() in CONFIRMED_VALUES


def _is_blocked(row: dict[str, str]) -> bool:
    return str(row.get("confirmed_for_submission", "")).strip().lower() in BLOCKED_VALUES


def _is_selected(row: dict[str, str]) -> bool:
    return str(row.get("selected_target", "")).strip().lower() in {"yes", "selected", "primary"}


def classify_decision(rows: list[dict[str, str]], *, applied: bool) -> str:
    if not rows:
        return "JOURNAL_SUBMISSION_DAY_CHECK_EMPTY"
    if not applied:
        return "JOURNAL_SUBMISSION_DAY_CHECK_TEMPLATE_READY"
    selected = [row for row in rows if _is_selected(row)]
    if not selected:
        return "JOURNAL_SUBMISSION_DAY_CHECK_APPLIED_NO_TARGET_SELECTED"
    if any(_is_blocked(row) for row in selected):
        return "JOURNAL_SUBMISSION_DAY_CHECK_TARGET_BLOCKED"
    if all(_is_confirmed(row) for row in selected):
        return "JOURNAL_SUBMISSION_DAY_CHECK_READY"
    return "JOURNAL_SUBMISSION_DAY_CHECK_TARGET_PENDING"


def build_report(rows: list[dict[str, str]], *, applied: bool) -> str:
    decision = classify_decision(rows, applied=applied)
    selected = [row for row in rows if _is_selected(row)]
    selected_lines = [
        f"- `{row.get('journal', '')}`: confirmed `{row.get('confirmed_for_submission', '')}`, "
        f"CAS `{row.get('official_cas_zone', '')}`, warning `{row.get('official_warning_status', '')}`"
        for row in selected
    ] or ["- none"]
    return "\n".join(
        [
            "# Journal Submission-Day Check Report",
            "",
            f"- Decision: `{decision}`",
            f"- Applied: `{applied}`",
            f"- Candidate journals checked: `{len(rows)}`",
            f"- Selected target rows: `{len(selected)}`",
            "",
            "## Selected Target Status",
            "",
            *selected_lines,
            "",
            "## Required Evidence",
            "",
            "- Latest JIF / 5-year JIF source.",
            "- Official or institutional CAS-zone lookup.",
            "- Official/current warning-list lookup.",
            "- Verifier and verification date.",
            "",
            "## Boundary",
            "",
            "This check is a submission-day routing gate. It does not guarantee",
            "acceptance, and it does not replace scientific, release, author, or",
            "clean-clone reproducibility gates.",
            "",
        ]
    )


def write_template(root: Path, audit_path: Path, response_path: Path, report_path: Path) -> dict[str, Path]:
    audit_rows = _read_tsv(root / audit_path)
    rows = build_template_rows(audit_rows)
    fieldnames = list(SubmissionDayRow.__dataclass_fields__.keys())
    _write_tsv_atomic(root / response_path, rows, fieldnames)
    _write_text_atomic(root / report_path, build_report(rows, applied=False))
    return {"response": root / response_path, "report": root / report_path}


def apply_response(root: Path, response_path: Path, report_path: Path) -> dict[str, Path]:
    rows = _read_tsv(root / response_path)
    _write_text_atomic(root / report_path, build_report(rows, applied=True))
    return {"response": root / response_path, "report": root / report_path}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--audit", default=str(DEFAULT_AUDIT))
    parser.add_argument("--response", default=str(DEFAULT_RESPONSE))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if args.apply:
        outputs = apply_response(root, Path(args.response), Path(args.report))
        print("JOURNAL_SUBMISSION_DAY_CHECK_APPLY_RUN")
    else:
        outputs = write_template(root, Path(args.audit), Path(args.response), Path(args.report))
        print("JOURNAL_SUBMISSION_DAY_CHECK_TEMPLATE_WRITTEN")
    for label, path in outputs.items():
        print(f"{label}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
