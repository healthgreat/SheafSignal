#!/usr/bin/env python
"""Build a live Gantt/status dashboard for SheafSignal.

Author: SheafSignal contributors
Date: 2026-05-03
Purpose: summarize current 20-50 IF readiness, release blockers, author gates,
external review status, and next actions in one reproducible Markdown report.
"""

from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


IF_REPORT = Path("manuscript/IF20_50_DISTANCE_REPORT.md")
RELEASE_UNBLOCKER = Path("release/RELEASE_UNBLOCKER_MATRIX.tsv")
AUTHOR_STATUS = Path("manuscript/submission_metadata/AUTHOR_CONFIRMATION_PREFLIGHT_STATUS.tsv")
EXTERNAL_REVIEW_TRIAGE = Path("external_ai_review_packet/EXTERNAL_BETA_REVIEW_TRIAGE_REPORT.md")
SHAREABLE_REVIEW_BUNDLE = Path(
    "external_ai_review_packet/shareable_review_bundle/SHAREABLE_REVIEW_BUNDLE_REPORT.md"
)
JOURNAL_SUBMISSION_DAY = Path(
    "manuscript/journal_metric_audit/JOURNAL_SUBMISSION_DAY_CHECK_REPORT.md"
)
OUTPUT_REPORT = Path("manuscript/SHEAFSIGNAL_LIVE_GANTT_STATUS.md")
OUTPUT_TSV = Path("manuscript/SHEAFSIGNAL_LIVE_GANTT_STATUS.tsv")


@dataclass(frozen=True)
class StatusRow:
    item: str
    status: str
    owner: str
    blocking: str
    next_action: str


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _metric(text: str, label: str) -> str:
    pattern = re.compile(rf"- {re.escape(label)}: `([^`]+)`")
    match = pattern.search(text)
    return match.group(1) if match else "unknown"


def _decision(text: str) -> str:
    return _metric(text, "Decision")


def _author_counts(rows: list[dict[str, str]]) -> dict[str, int]:
    counts = {"blocking": 0, "pending": 0, "optional": 0, "pass": 0}
    for row in rows:
        severity = str(row.get("severity", "")).strip()
        if severity in counts:
            counts[severity] += 1
    return counts


def _active_release_blockers(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    inactive = {"pass", "ready", "completed", "public_remote_branch_available"}
    return [
        row
        for row in rows
        if row.get("priority") == "blocking" and row.get("current_status") not in inactive
    ]


def build_status_rows(root: Path) -> list[StatusRow]:
    if_text = _read_text(root / IF_REPORT)
    release_rows = _read_tsv(root / RELEASE_UNBLOCKER)
    author_rows = _read_tsv(root / AUTHOR_STATUS)
    review_text = _read_text(root / EXTERNAL_REVIEW_TRIAGE)
    bundle_text = _read_text(root / SHAREABLE_REVIEW_BUNDLE)
    journal_text = _read_text(root / JOURNAL_SUBMISSION_DAY)

    author_counts = _author_counts(author_rows)
    active_release = _active_release_blockers(release_rows)
    rows = [
        StatusRow(
            "scientific_method_hardening",
            _metric(if_text, "Scientific/method hardening index"),
            "codex",
            "no",
            "Keep claims bounded; do not promote computational signals to mechanisms.",
        ),
        StatusRow(
            "submission_infrastructure",
            _metric(if_text, "Submission infrastructure index"),
            "user_then_codex",
            "yes" if active_release else "no",
            "Clear GitHub token, Zenodo DOI, author facts, and public clean-clone gates.",
        ),
        StatusRow(
            "release_blockers",
            f"{len(active_release)} active",
            "user_then_codex",
            "yes" if active_release else "no",
            "Regenerate GitHub token with workflow scope; mint Zenodo DOI; rerun release pipeline.",
        ),
        StatusRow(
            "author_confirmation",
            f"blocking={author_counts['blocking']}; pending={author_counts['pending']}",
            "authors",
            "yes" if author_counts["blocking"] or author_counts["pending"] else "no",
            "Fill AUTHOR_CONFIRMATION_RESPONSE_TEMPLATE.tsv and apply it.",
        ),
        StatusRow(
            "external_beta_reviews",
            _decision(review_text) or "not_run",
            "user_or_external_reviewers",
            "no",
            "Send shareable bundle, collect returned reviews, and triage them.",
        ),
        StatusRow(
            "shareable_review_bundle",
            _decision(bundle_text) or "not_run",
            "codex",
            "no",
            "Use bundle zip for external AI or human review.",
        ),
        StatusRow(
            "journal_submission_day_check",
            _decision(journal_text) or "not_run",
            "codex_on_submission_day",
            "yes",
            "Fill latest JIF, CAS zone, warning-list status, verifier, and date before submission.",
        ),
    ]
    return rows


def classify_decision(rows: list[StatusRow], if_text: str) -> str:
    if any(row.blocking == "yes" for row in rows if row.item != "journal_submission_day_check"):
        return "LIVE_STATUS_EXTERNAL_AND_AUTHOR_GATES_BLOCK_SUBMISSION"
    if _metric(if_text, "Submission infrastructure index") != "100.0%":
        return "LIVE_STATUS_RELEASE_AUDIT_REQUIRED"
    return "LIVE_STATUS_READY_FOR_FINAL_GO_NO_GO"


def _write_tsv_atomic(path: Path, rows: list[StatusRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    fieldnames = list(StatusRow.__dataclass_fields__.keys())
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


def _gantt() -> str:
    return """```mermaid
gantt
    title SheafSignal Live 20-50 IF Route
    dateFormat  YYYY-MM-DD

    section Completed
    Formal sheaf / Hodge core                 :done, 2026-05-02, 1d
    Full GSE154778 reannotation               :done, 2026-05-02, 1d
    Comparator and statistics hardening       :done, 2026-05-02, 1d
    External review bundle and triage         :done, 2026-05-03, 1d
    Author response workflow                  :done, 2026-05-03, 1d
    Journal submission-day check template     :done, 2026-05-03, 1d

    section Current Blocking Work
    GitHub token workflow scope               :crit, active, 2026-05-03, 1d
    Author facts filled and applied           :crit, active, 2026-05-03, 1d
    Zenodo DOI minted                         :crit, active, 2026-05-04, 1d
    Returned external beta reviews            :active, 2026-05-04, 5d

    section After Unblock
    Public GitHub release                     :2026-05-04, 1d
    DOI metadata insertion                    :2026-05-04, 1d
    Public clean-clone reproduction           :2026-05-05, 1d
    Final GO/NO-GO refresh                    :2026-05-06, 1d
```"""


def build_report(root: Path, rows: list[StatusRow]) -> str:
    if_text = _read_text(root / IF_REPORT)
    decision = classify_decision(rows, if_text)
    table_lines = [
        "| Item | Status | Owner | Blocking | Next action |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        table_lines.append(
            f"| `{row.item}` | `{row.status}` | `{row.owner}` | `{row.blocking}` | {row.next_action} |"
        )
    return "\n".join(
        [
            "# SheafSignal Live Gantt Status",
            "",
            f"- Timestamp: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`",
            f"- Decision: `{decision}`",
            f"- IF20-50 decision: `{_metric(if_text, 'Decision')}`",
            f"- Overall readiness: `{_metric(if_text, 'Overall readiness index')}`",
            f"- Scientific/method readiness: `{_metric(if_text, 'Scientific/method hardening index')}`",
            f"- Submission infrastructure readiness: `{_metric(if_text, 'Submission infrastructure index')}`",
            "",
            "## Gantt",
            "",
            _gantt(),
            "",
            "## Live Status Table",
            "",
            *table_lines,
            "",
            "## Short Interpretation",
            "",
            "The scientific and software side is near complete, but submission is still blocked by external release and author-owned facts. The project should not be submitted until GitHub, Zenodo DOI, author confirmation, returned review triage, and public clean-clone checks are complete.",
            "",
            "## Boundary",
            "",
            "This dashboard is a live internal readiness artifact. It does not guarantee acceptance by any journal.",
            "",
        ]
    )


def build_outputs(root: Path) -> dict[str, object]:
    root = root.resolve()
    rows = build_status_rows(root)
    _write_tsv_atomic(root / OUTPUT_TSV, rows)
    _write_text_atomic(root / OUTPUT_REPORT, build_report(root, rows))
    return {
        "report": OUTPUT_REPORT.as_posix(),
        "tsv": OUTPUT_TSV.as_posix(),
        "rows": len(rows),
        "blocking_rows": sum(row.blocking == "yes" for row in rows),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args(argv)

    summary = build_outputs(Path(args.root))
    print("LIVE_GANTT_STATUS_WRITTEN")
    print(f"Report: {summary['report']}")
    print(f"Rows: {summary['rows']}")
    print(f"Blocking rows: {summary['blocking_rows']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
