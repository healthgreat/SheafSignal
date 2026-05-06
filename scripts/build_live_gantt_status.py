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
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


IF_REPORT = Path("manuscript/IF20_50_DISTANCE_REPORT.md")
RELEASE_UNBLOCKER = Path("release/RELEASE_UNBLOCKER_MATRIX.tsv")
AUTHOR_STATUS = Path("manuscript/submission_metadata/AUTHOR_CONFIRMATION_PREFLIGHT_STATUS.tsv")
AUTHOR_CONTACT_RECONCILIATION = Path(
    "manuscript/submission_metadata/AUTHOR_CONTACT_RECONCILIATION_REPORT.md"
)
EXTERNAL_REVIEW_TRIAGE = Path("external_ai_review_packet/EXTERNAL_BETA_REVIEW_TRIAGE_REPORT.md")
SHAREABLE_REVIEW_BUNDLE = Path(
    "external_ai_review_packet/shareable_review_bundle/SHAREABLE_REVIEW_BUNDLE_REPORT.md"
)
JOURNAL_SUBMISSION_DAY = Path(
    "manuscript/journal_metric_audit/JOURNAL_SUBMISSION_DAY_CHECK_REPORT.md"
)
USER_ACTION_PACKET = Path("release/USER_ACTION_NOW_PACKET_ZH.md")
EXTERNAL_INPUT_INTAKE = Path("release/EXTERNAL_INPUT_INTAKE_REPORT.md")
AUTHOR_RESPONSE_FROM_INTAKE = Path(
    "manuscript/submission_metadata/AUTHOR_CONFIRMATION_FROM_INTAKE_REPORT.md"
)
UNBLOCK_READINESS = Path("release/UNBLOCK_READINESS_REPORT.md")
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
    inactive = {"pass", "ready", "completed", "valid", "public_remote_branch_available"}
    return [
        row
        for row in rows
        if row.get("priority") == "blocking"
        and row.get("current_status") not in inactive
        and not str(row.get("current_status", "")).endswith("_READY")
    ]


def _gate_done(status: str) -> bool:
    inactive = {"pass", "ready", "completed", "valid", "public_remote_branch_available"}
    return status in inactive or status.endswith("_READY")


def build_status_rows(root: Path) -> list[StatusRow]:
    if_text = _read_text(root / IF_REPORT)
    release_rows = _read_tsv(root / RELEASE_UNBLOCKER)
    author_rows = _read_tsv(root / AUTHOR_STATUS)
    contact_text = _read_text(root / AUTHOR_CONTACT_RECONCILIATION)
    review_text = _read_text(root / EXTERNAL_REVIEW_TRIAGE)
    bundle_text = _read_text(root / SHAREABLE_REVIEW_BUNDLE)
    journal_text = _read_text(root / JOURNAL_SUBMISSION_DAY)
    action_packet_text = _read_text(root / USER_ACTION_PACKET)
    intake_text = _read_text(root / EXTERNAL_INPUT_INTAKE)
    response_from_intake_text = _read_text(root / AUTHOR_RESPONSE_FROM_INTAKE)
    unblock_readiness_text = _read_text(root / UNBLOCK_READINESS)
    contact_decision = _decision(contact_text) or "not_run"
    action_packet_decision = _decision(action_packet_text) or "not_run"
    intake_decision = _decision(intake_text) or "not_run"

    author_counts = _author_counts(author_rows)
    active_release = _active_release_blockers(release_rows)
    release_next = (
        "No release-chain blocker remains; proceed with final audits and public clean-clone evidence."
        if not active_release
        else "Finish active release-chain blockers shown in release/RELEASE_UNBLOCKER_MATRIX.tsv."
    )
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
            release_next,
        ),
        StatusRow(
            "release_blockers",
            f"{len(active_release)} active",
            "user_then_codex",
            "yes" if active_release else "no",
            release_next,
        ),
        StatusRow(
            "author_confirmation",
            f"blocking={author_counts['blocking']}; pending={author_counts['pending']}",
            "authors",
            "yes" if author_counts["blocking"] or author_counts["pending"] else "no",
            (
                "No action needed."
                if not author_counts["blocking"] and not author_counts["pending"]
                else "Fill AUTHOR_CONFIRMATION_RESPONSE_TEMPLATE.tsv and apply it."
            ),
        ),
        StatusRow(
            "author_contact_reconciliation",
            contact_decision,
            "authors",
            "yes" if "BLOCKED" in contact_decision else "no",
            (
                "No action needed."
                if contact_decision == "AUTHOR_CONTACT_RECONCILIATION_READY"
                else "Provide Han Yan email and confirm whether extra supplied contacts are authors."
            ),
        ),
        StatusRow(
            "external_beta_reviews",
            _decision(review_text) or "not_run",
            "user_or_external_reviewers",
            "no",
            "Send shareable bundle, collect returned reviews, and triage them.",
        ),
        StatusRow(
            "round3_external_rereview",
            "pending_external_rereview_after_higher_rank_sheaf_fix",
            "user_or_external_reviewers",
            "yes",
            (
                "Send the refreshed shareable and source-code bundles to 2-3 reviewers "
                "and ask whether rank-one/trivial-sheaf and circular-benchmark fatal objections are gone."
            ),
        ),
        StatusRow(
            "shareable_review_bundle",
            _decision(bundle_text) or "not_run",
            "codex",
            "no",
            "Use bundle zip for external AI or human review.",
        ),
        StatusRow(
            "user_action_now_packet",
            action_packet_decision,
            "user_then_codex",
            "yes" if "P0_BLOCKERS_REMAIN" in action_packet_decision else "no",
            (
                "Clear the P0 rows in release/USER_ACTION_NOW_PACKET.tsv."
                if "P0_BLOCKERS_REMAIN" in action_packet_decision
                else "No P0 user action remains; keep the packet as the short audit trail."
            ),
        ),
        StatusRow(
            "external_input_intake",
            intake_decision,
            "user_then_codex",
            "yes" if "P0_MISSING" in intake_decision else "no",
            (
                "Fill missing P0 rows in release/EXTERNAL_INPUT_INTAKE_TEMPLATE.tsv."
                if "P0_MISSING" in intake_decision
                else "No action needed unless author-owned facts change."
            ),
        ),
        StatusRow(
            "author_response_from_intake",
            _decision(response_from_intake_text) or "not_run",
            "codex",
            "no",
            "No action needed; canonical author response has been derived from intake.",
        ),
        StatusRow(
            "unblock_readiness_runner",
            _decision(unblock_readiness_text) or "not_run",
            "codex",
            "no",
            "Run python scripts/run_unblock_readiness_check.py after external inputs are updated.",
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
    _replace_with_retry(tmp_path, path)


def _write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    _replace_with_retry(tmp_path, path)


def _replace_with_retry(tmp_path: Path, final_path: Path, retries: int = 5) -> None:
    """Replace output atomically, tolerating short Windows reader locks."""
    for attempt in range(retries):
        try:
            tmp_path.replace(final_path)
            return
        except PermissionError:
            if attempt == retries - 1:
                raise
            time.sleep(0.2 * (attempt + 1))


def _gantt(release_rows: list[dict[str, str]]) -> str:
    by_gate = {row.get("gate_id", ""): row.get("current_status", "") for row in release_rows}

    def line(label: str, gate_id: str, start: str) -> str:
        state = "done" if _gate_done(by_gate.get(gate_id, "")) else "crit, active"
        return f"    {label:<43}:{state}, {start}, 1d"

    return """```mermaid
gantt
    title SheafSignal Live 20-50 IF Route
    dateFormat  YYYY-MM-DD

    section Completed
    Rank-one legacy sheaf / Hodge core        :done, 2026-05-02, 1d
    Full GSE154778 reannotation               :done, 2026-05-02, 1d
    Comparator and statistics hardening       :done, 2026-05-02, 1d
    External review bundle and triage         :done, 2026-05-03, 1d
    Author response workflow                  :done, 2026-05-03, 1d
    Journal submission-day check template     :done, 2026-05-03, 1d
    GitHub and Zenodo token validation        :done, 2026-05-03, 1d
    Author facts filled and applied           :done, 2026-05-04, 1d
    Author contact reconciliation             :done, 2026-05-04, 1d
    Higher-rank LR-channel sheaf              :done, 2026-05-06, 1d
    Task-based comparator evaluation          :done, 2026-05-06, 1d

    section Release Chain
{github_auth}
{public_repo}
{release_tag}
{zenodo_doi}
{metadata}
{clean_clone}
{author_confirmation}
    Submission-day journal metric check       :crit, active, 2026-05-06, 1d
    Returned external beta reviews            :active, 2026-05-04, 5d
    Round 3 external rereview                 :crit, active, 2026-05-06, 5d

    section After Unblock
    Final GO/NO-GO refresh                    :2026-05-06, 1d
```""".format(
        github_auth=line("GitHub token rotation / auth", "G01_github_auth", "2026-05-04"),
        public_repo=line("Public GitHub branch", "G02_public_github_repo", "2026-05-04"),
        release_tag=line("GitHub release tag", "G03_release_tag", "2026-05-04"),
        zenodo_doi=line("Zenodo DOI minted", "G04_zenodo_doi", "2026-05-04"),
        metadata=line("Release metadata identifiers", "G05_metadata_insertion", "2026-05-04"),
        clean_clone=line("Public clean-clone reproduction", "G06_public_clean_clone", "2026-05-05"),
        author_confirmation=line("Author confirmation", "G07_author_confirmation", "2026-05-04"),
    )


def build_report(root: Path, rows: list[StatusRow]) -> str:
    if_text = _read_text(root / IF_REPORT)
    release_rows = _read_tsv(root / RELEASE_UNBLOCKER)
    active_release = _active_release_blockers(release_rows)
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
            _gantt(release_rows),
            "",
            "## Live Status Table",
            "",
            *table_lines,
            "",
            "## Short Interpretation",
            "",
            (
                "The scientific and software side is near complete, author-owned declarations are applied, and the real DOI/GitHub identifiers are recorded. Current blocking release-chain rows are: "
                + ", ".join(f"`{row.get('gate_id')}`" for row in active_release)
                + "."
                if active_release
                else "The release-chain blockers are cleared in the live matrix. Remaining checks are final audit refresh, public clean-clone evidence if newly generated outputs changed, returned beta reviews if available, and submission-day journal metrics."
            ),
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
