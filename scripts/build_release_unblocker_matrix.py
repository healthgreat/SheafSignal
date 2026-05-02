#!/usr/bin/env python
"""Build a release unblocker matrix for the SheafSignal submission package.

Author: SheafSignal maintainers
Date: 2026-05-03
Purpose: summarize external GitHub, Zenodo, author-confirmation, and
submission-day gates before a public 20-50 IF submission package is frozen.
"""

from __future__ import annotations

import csv
import subprocess
from pathlib import Path


MATRIX_PATH = Path("release/RELEASE_UNBLOCKER_MATRIX.tsv")
RUNBOOK_PATH = Path("release/RELEASE_UNBLOCKER_RUNBOOK_ZH.md")


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _write_tsv_atomic(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else []
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


def _git_remote_url(root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def _git_has_tag(root: Path, tag: str = "v0.1.0") -> bool:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "-q", "--verify", f"refs/tags/{tag}"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return False
    return result.returncode == 0


def _current_branch(root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def _remote_has_branch(root: Path) -> bool:
    branch = _current_branch(root)
    if not branch:
        return False
    try:
        result = subprocess.run(
            ["git", "ls-remote", "--heads", "origin", branch],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return False
    return result.returncode == 0 and bool(result.stdout.strip())


def _authorization_status(root: Path, check_id: str) -> str:
    rows = _read_tsv(root / "release/EXTERNAL_RELEASE_AUTHORIZATION_STATUS.tsv")
    for row in rows:
        if row.get("check_id") == check_id:
            return row.get("status", "")
    return ""


def _has_pending_zenodo(root: Path) -> bool:
    manifest = _read_text(root / "metadata/datasets.tsv")
    availability = _read_text(root / "release/DATA_AVAILABILITY_STATEMENT_DRAFT.md")
    return "PENDING_ZENODO_RELEASE" in manifest or "PENDING_ZENODO_RELEASE" in availability


def _final_blocker_status(root: Path, blocker_id: str) -> str:
    rows = _read_tsv(root / "manuscript/FINAL_SUBMISSION_BLOCKERS.tsv")
    for row in rows:
        if row.get("blocker_id") == blocker_id:
            return row.get("status", "")
    return ""


def _row(
    gate_id: str,
    priority: str,
    owner: str,
    current_status: str,
    evidence: str,
    required_action: str,
    validation_command: str,
    unlocks: str,
    claim_boundary: str,
) -> dict[str, str]:
    return {
        "gate_id": gate_id,
        "priority": priority,
        "owner": owner,
        "current_status": current_status,
        "evidence": evidence,
        "required_action": required_action,
        "validation_command": validation_command,
        "unlocks": unlocks,
        "claim_boundary": claim_boundary,
    }


def build_unblocker_rows(root: Path) -> list[dict[str, str]]:
    remote_url = _git_remote_url(root)
    remote_has_branch = _remote_has_branch(root) if remote_url else False
    has_release_tag = _git_has_tag(root)
    pending_zenodo = _has_pending_zenodo(root)
    zenodo_status = _final_blocker_status(root, "checklist::Zenodo DOI minted")
    github_token_status = _authorization_status(root, "github_token_api")

    if remote_url and remote_has_branch:
        github_repo_status = "public_remote_branch_available"
    elif remote_url:
        github_repo_status = "origin_configured_push_pending"
    else:
        github_repo_status = "pending_no_origin_remote"
    tag_status = "local_tag_exists_needs_public_release" if has_release_tag else "pending"
    zenodo_gate_status = "blocking_pending" if pending_zenodo else "complete_or_needs_audit"

    return [
        _row(
            "G01_github_auth",
            "blocking",
            "user_then_codex",
            github_token_status or "blocked_external_auth",
            "GitHub CLI auth status must show logged in; token content must never be printed.",
            "Regenerate a GitHub token with repo and workflow scopes or finish browser login, then let Codex validate auth.",
            "python scripts/check_external_release_authorization.py",
            "Allows Codex to create or push the public repository.",
            "This is an account authorization gate, not a scientific evidence gate.",
        ),
        _row(
            "G02_public_github_repo",
            "blocking",
            "codex_after_auth",
            github_repo_status,
            remote_url
            or "no origin remote configured; if a push fails on workflows, token likely lacks workflow scope",
            "Create or connect a public GitHub repository and push the frozen branch.",
            "git remote -v; git ls-remote origin HEAD",
            "Creates the public code URL required by Data and Code Availability.",
            "A public repository improves reproducibility but does not guarantee acceptance.",
        ),
        _row(
            "G03_release_tag",
            "blocking",
            "codex_after_github",
            tag_status,
            "target release tag: v0.1.0",
            "Create an immutable release tag after final audits pass.",
            "git tag --list v0.1.0",
            "Provides a frozen citable code state for Zenodo and reviewers.",
            "Do not tag before GitHub URL, author metadata, and DOI plan are aligned.",
        ),
        _row(
            "G04_zenodo_doi",
            "blocking",
            "user_then_codex",
            zenodo_gate_status,
            zenodo_status or "PENDING_ZENODO_RELEASE present in release metadata",
            "Upload the frozen archive or provide a Zenodo token, then mint a real DOI.",
            "python scripts/check_release_metadata_placeholders.py",
            "Removes DOI blockers in dataset manifest and Data Availability.",
            "Mint DOI only after the release archive is final; do not mint an incomplete release.",
        ),
        _row(
            "G05_metadata_insertion",
            "blocking",
            "codex_after_doi",
            "pending_real_github_url_and_doi",
            "CITATION, pyproject, .zenodo metadata, datasets.tsv, and Data Availability still need real identifiers.",
            "Insert public GitHub URL and Zenodo DOI into all release and manuscript metadata.",
            "python scripts/check_release_metadata_placeholders.py",
            "Converts release metadata from placeholder state to submission-ready state.",
            "Identifier insertion is administrative; scientific claims remain bounded by claim gates.",
        ),
        _row(
            "G06_public_clean_clone",
            "blocking",
            "codex_after_public_release",
            "pending",
            "Local clean-export preflight is not a substitute for a public clean-clone run.",
            "Clone the public repository into a fresh directory and rerun demo plus audits.",
            "python -m pytest; python scripts/release_audit.py",
            "Provides reviewer-grade reproducibility evidence.",
            "Clean-clone success supports reproducibility, not biological causality.",
        ),
        _row(
            "G07_author_confirmation",
            "blocking",
            "authors",
            "packet_ready_author_confirmation_pending",
            "manuscript/submission_metadata/AUTHOR_CONFIRMATION_PACKET.md",
            "Confirm corresponding author email, CRediT, funding, COI, ethics/data-use, and release approval.",
            "manual author confirmation; then rerun python scripts/check_final_submission_blockers.py --report-only",
            "Allows final journal upload metadata to be filled honestly.",
            "Author metadata cannot be inferred or fabricated by code.",
        ),
        _row(
            "S01_external_beta_review",
            "strengthening",
            "user_or_codex_packet",
            "recommended_not_required_for_local_go",
            "external_ai_review_packet and reviewer quickstart are prepared.",
            "Send the package to 2-3 independent computational biology readers and triage responses.",
            "manual review return; update reviewer response matrix",
            "Reduces high-impact reviewer risk around novelty and reproducibility.",
            "External review improves defensibility but does not guarantee acceptance.",
        ),
        _row(
            "S02_submission_day_metric_check",
            "strengthening",
            "codex",
            "pending_submission_day",
            "IF, CAS zone, and warning-list status can change.",
            "Recheck journal metrics, CAS zone, and warning status on the submission day.",
            "rerun journal metric audit immediately before submission",
            "Prevents stale journal-positioning statements.",
            "Metric checks guide routing; they are not scientific evidence.",
        ),
    ]


def build_runbook(rows: list[dict[str, str]]) -> str:
    blocking_count = sum(1 for row in rows if row["priority"] == "blocking")
    complete_like = sum(
        1
        for row in rows
        if row["current_status"].startswith("complete")
        or row["current_status"].startswith("configured")
        or row["current_status"].startswith("origin_configured")
        or row["current_status"].startswith("local_tag")
    )
    row_lines = "\n".join(
        "- `{gate_id}`: `{current_status}` -> {required_action}".format(**row)
        for row in rows
    )
    return f"""# SheafSignal Release Unblocker Runbook

Timestamp: 2026-05-03 02:00:00 +08:00

## Direct Status

- Blocking or mandatory release gates tracked: `{blocking_count}`.
- Gates already partly configured: `{complete_like}`.
- Current decision: `RELEASE_NOT_READY_UNTIL_GITHUB_ZENODO_AUTHOR_CONFIRMATION`.

This runbook is for release execution. It does not guarantee acceptance in any
journal and does not change the evidence boundary of the manuscript.

## Gate Matrix Summary

{row_lines}

## Execution Order

1. Complete `G01_github_auth`.
2. Let Codex execute `G02_public_github_repo` and `G03_release_tag` with:
   `python scripts/publish_github_release_after_auth.py --create-release`.
3. Complete `G04_zenodo_doi`.
4. Let Codex execute `G05_metadata_insertion`.
5. Let Codex execute `G06_public_clean_clone`.
6. Authors complete `G07_author_confirmation`.
7. Optional but high-value: complete `S01_external_beta_review`.
8. On the exact submission day, complete `S02_submission_day_metric_check`.

## Mermaid Gantt

```mermaid
gantt
    title SheafSignal Release Unblocker Path
    dateFormat  YYYY-MM-DD

    section Current Blockers
    GitHub token workflow scope     :crit, active, 2026-05-03, 1d
    Push public GitHub branch/tag   :crit, 2026-05-03, 1d
    Zenodo DOI                      :crit, 2026-05-04, 1d
    Metadata insertion              :crit, 2026-05-04, 1d
    Public clean-clone reproduction :crit, 2026-05-05, 1d
    Author confirmation             :crit, 2026-05-05, 2d

    section Strengthening
    External beta reviews           :2026-05-06, 7d
    Submission-day metric check     :2026-05-08, 1d
```

## User Boundary

The user only needs to authorize accounts and confirm author-owned facts.
Codex can perform repository creation, release tagging, DOI metadata insertion,
audits, and clean-clone verification after those external gates are unlocked.
"""


def build_release_unblocker_outputs(root: Path) -> dict[str, Path]:
    rows = build_unblocker_rows(root)
    matrix_path = root / MATRIX_PATH
    runbook_path = root / RUNBOOK_PATH
    _write_tsv_atomic(matrix_path, rows)
    _write_text_atomic(runbook_path, build_runbook(rows))
    return {"matrix": matrix_path, "runbook": runbook_path}


def main() -> int:
    root = Path.cwd()
    outputs = build_release_unblocker_outputs(root)
    for label, path in outputs.items():
        print(f"wrote {label}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
