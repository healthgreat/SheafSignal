#!/usr/bin/env python
"""Run a safe, one-command readiness check for post-unblock publication.

Author: SheafSignal contributors
Date: 2026-05-03
Purpose: refresh non-destructive external/authorship gates and summarize whether
the project can proceed to GitHub release, DOI insertion, and clean-clone
reproduction. This script never pushes, uploads, mints DOI records, or prints
secret tokens.
"""

from __future__ import annotations

import argparse
import csv
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


EXTERNAL_AUTH = Path("release/EXTERNAL_RELEASE_AUTHORIZATION_STATUS.tsv")
AUTHOR_PREFLIGHT = Path("manuscript/submission_metadata/AUTHOR_CONFIRMATION_PREFLIGHT_STATUS.tsv")
AUTHOR_CONTACTS = Path("manuscript/submission_metadata/AUTHOR_CONTACT_RECONCILIATION.tsv")
USER_ACTION_PACKET = Path("release/USER_ACTION_NOW_PACKET.tsv")
EXTERNAL_INPUT_INTAKE = Path("release/EXTERNAL_INPUT_INTAKE_STATUS.tsv")
AUTHOR_RESPONSE_FROM_INTAKE = Path(
    "manuscript/submission_metadata/AUTHOR_CONFIRMATION_RESPONSE_FROM_INTAKE.tsv"
)
LIVE_GANTT = Path("manuscript/SHEAFSIGNAL_LIVE_GANTT_STATUS.tsv")
OUTPUT_TSV = Path("release/UNBLOCK_READINESS_STATUS.tsv")
OUTPUT_REPORT = Path("release/UNBLOCK_READINESS_REPORT.md")


SAFE_REFRESH_COMMANDS = [
    ["python", "scripts/check_external_release_authorization.py"],
    ["python", "scripts/build_external_input_intake.py"],
    ["python", "scripts/apply_external_input_intake.py"],
    ["python", "scripts/reconcile_author_contacts.py"],
    ["python", "scripts/check_author_confirmation_preflight.py"],
    ["python", "scripts/build_release_unblocker_matrix.py"],
    ["python", "scripts/build_user_action_now_packet.py"],
    ["python", "scripts/build_live_gantt_status.py"],
]


@dataclass(frozen=True)
class GateRow:
    gate: str
    status: str
    blocking: str
    evidence: str
    next_action: str


def _read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _row_by(rows: list[dict[str, str]], key: str, value: str) -> dict[str, str]:
    for row in rows:
        if str(row.get(key, "")).strip() == value:
            return row
    return {}


def _count(rows: list[dict[str, str]], key: str, value: str) -> int:
    return sum(1 for row in rows if str(row.get(key, "")).strip() == value)


def _run_refresh(root: Path) -> list[str]:
    logs: list[str] = []
    for command in SAFE_REFRESH_COMMANDS:
        result = subprocess.run(
            command,
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        tail = ((result.stdout or "") + "\n" + (result.stderr or "")).strip()[-800:]
        logs.append(f"{' '.join(command)} -> returncode={result.returncode}; {tail}")
        if result.returncode != 0:
            break
    return logs


def build_gate_rows(root: Path) -> list[GateRow]:
    external = _read_tsv(root / EXTERNAL_AUTH)
    author = _read_tsv(root / AUTHOR_PREFLIGHT)
    contacts = _read_tsv(root / AUTHOR_CONTACTS)
    action = _read_tsv(root / USER_ACTION_PACKET)
    intake = _read_tsv(root / EXTERNAL_INPUT_INTAKE)
    response_from_intake = _read_tsv(root / AUTHOR_RESPONSE_FROM_INTAKE)
    gantt = _read_tsv(root / LIVE_GANTT)

    github_token = _row_by(external, "check_id", "github_token_api")
    github_cli = _row_by(external, "check_id", "github_cli_auth")
    zenodo_token = _row_by(external, "check_id", "zenodo_token_file")
    zenodo_doi = _row_by(external, "check_id", "zenodo_doi_placeholders")
    action_p0 = _count(action, "priority", "P0")
    intake_p0 = _count(intake, "blocking", "yes")
    response_pending = sum(
        1
        for row in response_from_intake
        if str(row.get("confirmed", "")).strip() == "fill_yes_no_or_skip"
        and str(row.get("item", "")).strip() != "ORCID IDs"
    )
    live_blocking = _count(gantt, "blocking", "yes")
    author_blocking = _count(author, "severity", "blocking")
    author_pending = _count(author, "severity", "pending")
    missing_author_email = _count(contacts, "action_needed", "blocking_missing_email")
    extra_contacts = _count(contacts, "action_needed", "confirm_not_author_or_update_author_line")

    github_status = github_token.get("status", "missing")
    github_ready = github_status in {"valid", "valid_with_required_scopes"}
    author_ready = author_blocking == 0 and author_pending == 0 and missing_author_email == 0
    zenodo_ready = zenodo_doi.get("status", "missing") in {"pass", "ready", "completed"} or zenodo_token.get(
        "status", ""
    ) in {"present", "valid"}
    github_next = (
        "No user action needed; Codex can use GH_TOKEN from the local token file."
        if github_ready
        else "Regenerate GitHub token with repo and workflow scopes, then save it to D:/secrets/github_token.txt."
    )
    author_next = (
        "No action needed; author-owned declarations are applied."
        if author_ready
        else "Confirm remaining author-owned declarations: CRediT, funding, COI, ethics/data-use, and public release approvals."
    )
    zenodo_next = (
        "No user action needed; Codex can mint DOI after the public release archive is final."
        if zenodo_ready
        else "Provide a real Zenodo DOI or save a Zenodo API token to D:/secrets/zenodo_token.txt."
    )
    intake_next = (
        "No action needed unless author-owned facts change."
        if intake_p0 == 0
        else "Fill the consolidated intake template, then rerun this check."
    )
    response_next = (
        "No action needed; canonical author response has been derived from intake."
        if response_pending == 0
        else "Fill intake fields until the derived author response has no required pending rows."
    )
    action_packet_next = (
        "No P0 user action remains; keep the packet as the short audit trail."
        if action_p0 == 0
        else "Clear the P0 rows in the action packet."
    )
    live_gantt_next = (
        "Resolve release-chain blockers shown in the live Gantt: GitHub branch/tag, "
        "DOI, metadata insertion, clean-clone, and submission-day journal check."
        if live_blocking
        else "No action needed; live Gantt has no blocking rows."
    )

    return [
        GateRow(
            "github_publication_auth",
            github_status,
            "no" if github_ready else "yes",
            f"gh={github_cli.get('status', 'missing')}",
            github_next,
        ),
        GateRow(
            "author_confirmation",
            f"blocking={author_blocking}; pending={author_pending}",
            "no" if author_ready else "yes",
            f"missing_author_email={missing_author_email}; extra_contacts={extra_contacts}",
            author_next,
        ),
        GateRow(
            "zenodo_identifier",
            f"token={zenodo_token.get('status', 'missing')}; doi={zenodo_doi.get('status', 'missing')}",
            "no" if zenodo_ready else "yes",
            "release archive exists; DOI placeholder still blocks final metadata unless real DOI is supplied",
            zenodo_next,
        ),
        GateRow(
            "external_input_intake",
            f"P0_missing={intake_p0}",
            "yes" if intake_p0 else "no",
            "release/EXTERNAL_INPUT_INTAKE_TEMPLATE.tsv",
            intake_next,
        ),
        GateRow(
            "author_response_from_intake",
            f"pending_rows={response_pending}",
            "yes" if response_pending else "no",
            "manuscript/submission_metadata/AUTHOR_CONFIRMATION_RESPONSE_FROM_INTAKE.tsv",
            response_next,
        ),
        GateRow(
            "short_user_action_packet",
            f"P0={action_p0}",
            "yes" if action_p0 else "no",
            "release/USER_ACTION_NOW_PACKET_ZH.md",
            action_packet_next,
        ),
        GateRow(
            "live_gantt_blockers",
            f"blocking_rows={live_blocking}",
            "yes" if live_blocking else "no",
            "manuscript/SHEAFSIGNAL_LIVE_GANTT_STATUS.md",
            live_gantt_next,
        ),
    ]


def classify_decision(rows: list[GateRow], refresh_logs: list[str]) -> str:
    if refresh_logs and any("returncode=0" not in log for log in refresh_logs):
        return "UNBLOCK_READINESS_REFRESH_FAILED"
    if any(row.blocking == "yes" for row in rows):
        return "UNBLOCK_READINESS_BLOCKED_EXTERNAL_INPUTS"
    return "UNBLOCK_READINESS_READY_FOR_POST_UNBLOCK_PIPELINE"


def _replace_with_retry(tmp_path: Path, final_path: Path, retries: int = 5) -> None:
    for attempt in range(retries):
        try:
            tmp_path.replace(final_path)
            return
        except PermissionError:
            if attempt == retries - 1:
                raise
            time.sleep(0.2 * (attempt + 1))


def _write_tsv_atomic(path: Path, rows: list[GateRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    fieldnames = list(GateRow.__dataclass_fields__.keys())
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


def build_report(rows: list[GateRow], refresh_logs: list[str]) -> str:
    decision = classify_decision(rows, refresh_logs)
    table = [
        "| Gate | Status | Blocking | Evidence | Next action |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        table.append(
            f"| `{row.gate}` | `{row.status}` | `{row.blocking}` | {row.evidence} | {row.next_action} |"
        )
    log_lines = [f"- `{log}`" for log in refresh_logs] or ["- refresh skipped"]
    return "\n".join(
        [
            "# SheafSignal Unblock Readiness Report",
            "",
            f"- Timestamp: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`",
            f"- Decision: `{decision}`",
            "",
            "## Gate Table",
            "",
            *table,
            "",
            "## Safe Refresh Log",
            "",
            *log_lines,
            "",
            "## If Ready",
            "",
            "When this report says `UNBLOCK_READINESS_READY_FOR_POST_UNBLOCK_PIPELINE`, run:",
            "",
            "```bash",
            "python scripts/build_post_unblock_release_pipeline.py --doi <REAL_ZENODO_DOI> --execute",
            "```",
            "",
            "## Boundary",
            "",
            "This report is a non-destructive publication readiness check. It does not",
            "push to GitHub, upload to Zenodo, mint a DOI, infer author-owned facts, or",
            "guarantee acceptance by any journal.",
            "",
        ]
    )


def build_outputs(root: Path, *, refresh: bool = True) -> dict[str, object]:
    root = root.resolve()
    refresh_logs = _run_refresh(root) if refresh else []
    rows = build_gate_rows(root)
    _write_tsv_atomic(root / OUTPUT_TSV, rows)
    _write_text_atomic(root / OUTPUT_REPORT, build_report(rows, refresh_logs))
    return {
        "decision": classify_decision(rows, refresh_logs),
        "rows": len(rows),
        "blocking_rows": sum(row.blocking == "yes" for row in rows),
        "report": OUTPUT_REPORT.as_posix(),
        "tsv": OUTPUT_TSV.as_posix(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--no-refresh", action="store_true")
    args = parser.parse_args(argv)
    summary = build_outputs(Path(args.root), refresh=not args.no_refresh)
    print("UNBLOCK_READINESS_CHECK_WRITTEN")
    for key, value in summary.items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
