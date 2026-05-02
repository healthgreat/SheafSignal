#!/usr/bin/env python
"""Build or execute the post-unblock release pipeline for SheafSignal.

Author: SheafSignal contributors
Date: 2026-05-03
Purpose: define the exact GitHub, Zenodo, DOI-finalization, clean-clone, and
final-audit command chain that can run only after external and author-owned
submission gates are cleared.
"""

from __future__ import annotations

import argparse
import csv
import subprocess
from dataclasses import dataclass
from pathlib import Path


DEFAULT_PLAN = Path("release/POST_UNBLOCK_RELEASE_PIPELINE_PLAN.tsv")
DEFAULT_REPORT = Path("release/POST_UNBLOCK_RELEASE_PIPELINE_REPORT.md")
RELEASE_UNBLOCKER = Path("release/RELEASE_UNBLOCKER_MATRIX.tsv")
EXTERNAL_AUTH = Path("release/EXTERNAL_RELEASE_AUTHORIZATION_STATUS.tsv")
AUTHOR_PREFLIGHT = Path("manuscript/submission_metadata/AUTHOR_CONFIRMATION_PREFLIGHT_STATUS.tsv")
ZENODO_PREFLIGHT = Path("release/ZENODO_UPLOAD_PREFLIGHT_STATUS.tsv")


@dataclass(frozen=True)
class PipelineStep:
    step_id: str
    phase: str
    command: str
    run_by_default: str
    stop_on_failure: str
    purpose: str


@dataclass(frozen=True)
class PipelineRunResult:
    step_id: str
    command: str
    returncode: int
    stdout_tail: str
    stderr_tail: str


def _read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _tail(text: str, max_chars: int = 1200) -> str:
    clean = (text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    return clean[-max_chars:]


def _status(rows: list[dict[str, str]], key: str, value: str, status_col: str = "status") -> str:
    for row in rows:
        if str(row.get(key, "")) == value:
            return str(row.get(status_col, "")).strip()
    return "not_found"


def _severity_count(rows: list[dict[str, str]], severity: str) -> int:
    return sum(1 for row in rows if str(row.get("severity", "")) == severity)


def build_gate_snapshot(root: Path) -> dict[str, object]:
    release_rows = _read_tsv(root / RELEASE_UNBLOCKER)
    auth_rows = _read_tsv(root / EXTERNAL_AUTH)
    author_rows = _read_tsv(root / AUTHOR_PREFLIGHT)
    zenodo_rows = _read_tsv(root / ZENODO_PREFLIGHT)
    active_release_blockers = [
        row
        for row in release_rows
        if row.get("priority") == "blocking"
        and row.get("current_status") not in {"pass", "ready", "completed"}
    ]
    return {
        "active_release_blockers": len(active_release_blockers),
        "github_token_api": _status(auth_rows, "check_id", "github_token_api"),
        "github_cli_auth": _status(auth_rows, "check_id", "github_cli_auth"),
        "zenodo_token_file": _status(zenodo_rows, "check_id", "zenodo_token_file"),
        "zenodo_archive_sha256": _status(zenodo_rows, "check_id", "zenodo_archive_sha256"),
        "author_blocking": _severity_count(author_rows, "blocking"),
        "author_pending": _severity_count(author_rows, "pending"),
    }


def classify_decision(snapshot: dict[str, object], doi: str | None, require_author_ready: bool) -> str:
    if snapshot["github_token_api"] not in {"valid", "valid_with_required_scopes"}:
        return "POST_UNBLOCK_PIPELINE_BLOCKED_GITHUB_TOKEN"
    if require_author_ready and (
        int(snapshot["author_blocking"]) > 0 or int(snapshot["author_pending"]) > 0
    ):
        return "POST_UNBLOCK_PIPELINE_BLOCKED_AUTHOR_CONFIRMATION"
    if snapshot["zenodo_archive_sha256"] != "pass":
        return "POST_UNBLOCK_PIPELINE_BLOCKED_ZENODO_PREFLIGHT"
    if not doi:
        return "POST_UNBLOCK_PIPELINE_READY_DOI_REQUIRED_FOR_FINALIZE"
    return "POST_UNBLOCK_PIPELINE_READY_TO_EXECUTE"


def build_pipeline_steps(doi: str | None, publish_release: bool) -> list[PipelineStep]:
    publish_flag = "--publish-release" if publish_release else ""
    finalize_command = (
        f"python scripts/finalize_zenodo_doi.py --doi {doi}"
        if doi
        else "python scripts/finalize_zenodo_doi.py --doi <REAL_ZENODO_DOI>"
    )
    return [
        PipelineStep(
            "preflight_external_auth",
            "preflight",
            "python scripts/check_external_release_authorization.py",
            "yes",
            "yes",
            "Verify GitHub token, Zenodo token/archive, and DOI placeholders.",
        ),
        PipelineStep(
            "preflight_author_confirmation",
            "preflight",
            "python scripts/check_author_confirmation_preflight.py",
            "yes",
            "yes",
            "Verify author-owned submission facts are no longer blocking.",
        ),
        PipelineStep(
            "preflight_zenodo_upload",
            "preflight",
            "python scripts/check_zenodo_upload_preflight.py",
            "yes",
            "yes",
            "Verify Zenodo upload archive and metadata match.",
        ),
        PipelineStep(
            "publish_github_release",
            "external_release",
            (
                "python scripts/publish_github_release_after_auth.py --create-release "
                f"{publish_flag}"
            ).strip(),
            "yes",
            "yes",
            "Push branch/tag and create a GitHub release after workflow scope is present.",
        ),
        PipelineStep(
            "finalize_zenodo_doi",
            "metadata",
            finalize_command,
            "yes_if_doi_provided",
            "yes",
            "Write real Zenodo DOI into dataset manifest and Data Availability.",
        ),
        PipelineStep(
            "rebuild_release_files",
            "metadata",
            "python scripts/build_reproducibility_release.py && python scripts/package_release_archives.py",
            "yes",
            "yes",
            "Rebuild release manifests and archives after DOI insertion.",
        ),
        PipelineStep(
            "final_blocker_report",
            "audit",
            "python scripts/check_release_metadata_placeholders.py && python scripts/check_final_submission_blockers.py --report-only",
            "yes",
            "yes",
            "Confirm DOI/GitHub placeholders and final submission blockers are cleared.",
        ),
        PipelineStep(
            "clean_export_preflight",
            "audit",
            "python scripts/run_clean_clone_preflight.py",
            "yes",
            "yes",
            "Run tracked-HEAD clean-export reproduction check.",
        ),
        PipelineStep(
            "full_test_and_release_audit",
            "audit",
            "python -m pytest -q && python scripts/release_audit.py",
            "yes",
            "yes",
            "Run full local tests and sensitive/large-file release audit.",
        ),
        PipelineStep(
            "refresh_distance_report",
            "reporting",
            "python scripts/build_if20_50_gap_report.py && python scripts/build_submission_unblocker_handoff.py",
            "yes",
            "yes",
            "Refresh final IF20-50 distance and handoff reports.",
        ),
    ]


def _write_tsv_atomic(path: Path, rows: list[PipelineStep]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    fieldnames = list(PipelineStep.__dataclass_fields__.keys())
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


def build_report(
    *,
    decision: str,
    snapshot: dict[str, object],
    steps: list[PipelineStep],
    results: list[PipelineRunResult],
    execute: bool,
) -> str:
    snapshot_lines = [f"- `{key}`: `{value}`" for key, value in snapshot.items()]
    step_lines = [
        f"| `{step.step_id}` | `{step.phase}` | `{step.run_by_default}` | `{step.command}` |"
        for step in steps
    ]
    result_lines = [
        f"- `{result.step_id}` returncode `{result.returncode}`"
        for result in results
    ] or ["- none"]
    return "\n".join(
        [
            "# Post-Unblock Release Pipeline Report",
            "",
            f"- Decision: `{decision}`",
            f"- Execute mode: `{execute}`",
            "",
            "## Gate Snapshot",
            "",
            *snapshot_lines,
            "",
            "## Pipeline Plan",
            "",
            "| Step | Phase | Run by default | Command |",
            "|---|---|---|---|",
            *step_lines,
            "",
            "## Execution Results",
            "",
            *result_lines,
            "",
            "## Boundary",
            "",
            "This pipeline only handles release mechanics and reproducibility audits. "
            "It does not infer author-owned facts, does not print secrets, and does "
            "not guarantee acceptance by any journal.",
            "",
        ]
    )


def _run_command(root: Path, step: PipelineStep) -> PipelineRunResult:
    result = subprocess.run(
        step.command,
        cwd=root,
        shell=True,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return PipelineRunResult(
        step_id=step.step_id,
        command=step.command,
        returncode=result.returncode,
        stdout_tail=_tail(result.stdout),
        stderr_tail=_tail(result.stderr),
    )


def write_outputs(
    root: Path,
    steps: list[PipelineStep],
    decision: str,
    snapshot: dict[str, object],
    results: list[PipelineRunResult],
    execute: bool,
) -> dict[str, Path]:
    plan_path = root / DEFAULT_PLAN
    report_path = root / DEFAULT_REPORT
    _write_tsv_atomic(plan_path, steps)
    _write_text_atomic(
        report_path,
        build_report(
            decision=decision,
            snapshot=snapshot,
            steps=steps,
            results=results,
            execute=execute,
        ),
    )
    return {"plan": plan_path, "report": report_path}


def run_orchestrator(
    root: Path,
    *,
    doi: str | None,
    execute: bool,
    publish_release: bool,
    require_author_ready: bool,
) -> tuple[str, list[PipelineRunResult]]:
    snapshot = build_gate_snapshot(root)
    steps = build_pipeline_steps(doi, publish_release=publish_release)
    decision = classify_decision(snapshot, doi, require_author_ready)
    results: list[PipelineRunResult] = []
    if execute and decision == "POST_UNBLOCK_PIPELINE_READY_TO_EXECUTE":
        for step in steps:
            if step.step_id == "finalize_zenodo_doi" and not doi:
                continue
            result = _run_command(root, step)
            results.append(result)
            if result.returncode != 0 and step.stop_on_failure == "yes":
                decision = f"POST_UNBLOCK_PIPELINE_FAILED_AT_{step.step_id}"
                break
        else:
            decision = "POST_UNBLOCK_PIPELINE_COMPLETED"
    return decision, results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--doi", default="")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--publish-release", action="store_true")
    parser.add_argument("--skip-author-ready-check", action="store_true")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    doi = args.doi.strip() or None
    steps = build_pipeline_steps(doi, publish_release=args.publish_release)
    decision, results = run_orchestrator(
        root,
        doi=doi,
        execute=args.execute,
        publish_release=args.publish_release,
        require_author_ready=not args.skip_author_ready_check,
    )
    snapshot = build_gate_snapshot(root)
    outputs = write_outputs(
        root,
        steps,
        decision,
        snapshot,
        results,
        execute=args.execute,
    )
    print(decision)
    for label, path in outputs.items():
        print(f"{label}: {path}")
    if not args.execute:
        return 0
    if decision != "POST_UNBLOCK_PIPELINE_COMPLETED":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
