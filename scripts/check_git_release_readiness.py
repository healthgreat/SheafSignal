#!/usr/bin/env python
"""Audit local Git readiness before a public SheafSignal release.

Author: SheafSignal contributors
Date: 2026-05-02
Purpose: make the GitHub-release gate machine-readable without publishing or
minting a DOI. The audit is intentionally local-first: a clean local commit is
allowed to pass as a freeze candidate, while missing public remote/DOI remains
an explicit warning/blocker for formal submission.
"""

from __future__ import annotations

import argparse
import csv
import subprocess
from dataclasses import dataclass
from pathlib import Path


DEFAULT_AUDIT_PATH = Path("release/GIT_RELEASE_READINESS_AUDIT.tsv")
DEFAULT_REPORT_PATH = Path("release/GIT_RELEASE_READINESS_REPORT.md")


@dataclass(frozen=True)
class GitSnapshot:
    has_commit: bool
    branch: str
    remote_count: int
    exact_tag: str
    dirty_paths: tuple[str, ...]
    file_scope: tuple[tuple[str, int], ...]
    oversized_files: tuple[tuple[str, int], ...]


def _run_git(root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-c", f"safe.directory={root.as_posix()}", *args],
        cwd=root,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def _write_tsv_atomic(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    fieldnames = ["check_id", "area", "status", "evidence", "action"]
    with tmp_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    tmp_path.replace(path)


def _bytes_to_mb(size_bytes: int) -> float:
    return round(size_bytes / (1024 * 1024), 3)


def _split_lines(text: str) -> tuple[str, ...]:
    return tuple(line.strip() for line in text.splitlines() if line.strip())


def _list_nonignored_files(root: Path) -> tuple[tuple[str, int], ...]:
    result = _run_git(root, ["ls-files", "--cached", "--others", "--exclude-standard"])
    if result.returncode != 0:
        return tuple()
    rows: list[tuple[str, int]] = []
    for rel_text in _split_lines(result.stdout):
        path = root / rel_text
        if path.is_file():
            rows.append((rel_text.replace("\\", "/"), path.stat().st_size))
    return tuple(sorted(rows, key=lambda item: item[1], reverse=True))


def collect_snapshot(root: Path, max_mb: float) -> GitSnapshot:
    root = root.resolve()
    head = _run_git(root, ["rev-parse", "--verify", "HEAD"])
    has_commit = head.returncode == 0

    branch_result = _run_git(root, ["branch", "--show-current"])
    branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "NA"
    if not branch:
        branch = "detached_or_unborn"

    remote_result = _run_git(root, ["remote", "-v"])
    remotes = set()
    if remote_result.returncode == 0:
        for line in _split_lines(remote_result.stdout):
            remotes.add(line.split()[0])

    tag_result = _run_git(root, ["describe", "--tags", "--exact-match", "HEAD"])
    exact_tag = tag_result.stdout.strip() if tag_result.returncode == 0 else ""

    status_result = _run_git(root, ["status", "--porcelain", "--untracked-files=all"])
    dirty_paths = _split_lines(status_result.stdout) if status_result.returncode == 0 else tuple()

    file_scope = _list_nonignored_files(root)
    max_bytes = int(max_mb * 1024 * 1024)
    oversized_files = tuple((path, size) for path, size in file_scope if size > max_bytes)

    return GitSnapshot(
        has_commit=has_commit,
        branch=branch,
        remote_count=len(remotes),
        exact_tag=exact_tag,
        dirty_paths=dirty_paths,
        file_scope=file_scope,
        oversized_files=oversized_files,
    )


def classify_release_state(snapshot: GitSnapshot) -> tuple[str, str]:
    """Return decision and manuscript-facing gate status."""
    if not snapshot.has_commit:
        return "GIT_RELEASE_BLOCKED_NO_COMMIT", "red"
    if snapshot.oversized_files:
        return "GIT_RELEASE_BLOCKED_FILE_SCOPE", "red"
    if snapshot.dirty_paths:
        return "GIT_RELEASE_BLOCKED_DIRTY_WORKTREE", "red_yellow"
    if snapshot.remote_count == 0:
        return "GIT_RELEASE_LOCAL_FREEZE_PASS_PUBLIC_REMOTE_PENDING", "yellow"
    if not snapshot.exact_tag:
        return "GIT_RELEASE_REMOTE_PRESENT_TAG_PENDING", "yellow"
    return "GIT_RELEASE_READY_FOR_PUBLIC_PUSH_OR_ALREADY_PUSHED", "green_yellow"


def build_audit_rows(snapshot: GitSnapshot, max_mb: float) -> list[dict[str, str]]:
    decision, gate_status = classify_release_state(snapshot)
    largest = ", ".join(
        f"{path} ({_bytes_to_mb(size)} MB)" for path, size in snapshot.file_scope[:5]
    )
    if not largest:
        largest = "no non-ignored files detected"

    rows = [
        {
            "check_id": "git_commit_exists",
            "area": "local_git_freeze",
            "status": "pass" if snapshot.has_commit else "fail",
            "evidence": "HEAD exists" if snapshot.has_commit else "no commits in repository",
            "action": "Create a local freeze commit before public release.",
        },
        {
            "check_id": "git_branch",
            "area": "local_git_freeze",
            "status": "pass" if snapshot.branch != "detached_or_unborn" else "warn",
            "evidence": snapshot.branch,
            "action": "Use a named codex/ branch for auditable release work.",
        },
        {
            "check_id": "git_dirty_worktree",
            "area": "local_git_freeze",
            "status": "pass" if not snapshot.dirty_paths else "warn",
            "evidence": f"{len(snapshot.dirty_paths)} dirty/untracked paths",
            "action": "Commit or intentionally ignore generated files before tagging.",
        },
        {
            "check_id": "git_file_scope",
            "area": "large_file_guard",
            "status": "pass" if not snapshot.oversized_files else "fail",
            "evidence": f"{len(snapshot.file_scope)} non-ignored files; largest: {largest}",
            "action": f"Keep every Git-tracked file under {max_mb:g} MB; put larger data in Zenodo.",
        },
        {
            "check_id": "git_remote",
            "area": "public_release",
            "status": "pass" if snapshot.remote_count else "warn",
            "evidence": f"{snapshot.remote_count} configured remotes",
            "action": "Add a public GitHub remote before changing G11 to green.",
        },
        {
            "check_id": "git_exact_tag",
            "area": "public_release",
            "status": "pass" if snapshot.exact_tag else "warn",
            "evidence": snapshot.exact_tag or "no exact tag on HEAD",
            "action": "Create an immutable version tag after the final freeze commit.",
        },
        {
            "check_id": "g11_decision",
            "area": "status_gate",
            "status": gate_status,
            "evidence": decision,
            "action": "Do not mint Zenodo DOI until scientific gates and public release metadata are frozen.",
        },
    ]
    return rows


def build_report(snapshot: GitSnapshot, max_mb: float) -> str:
    decision, gate_status = classify_release_state(snapshot)
    largest_lines = [
        f"- `{path}`: {_bytes_to_mb(size)} MB" for path, size in snapshot.file_scope[:10]
    ]
    if not largest_lines:
        largest_lines = ["- no non-ignored files detected"]

    dirty_preview = [f"- `{item}`" for item in snapshot.dirty_paths[:20]]
    if not dirty_preview:
        dirty_preview = ["- clean"]

    return "\n".join(
        [
            "# Git Release Readiness Report",
            "",
            f"- Decision: `{decision}`",
            f"- G11 gate status: `{gate_status}`",
            f"- Branch: `{snapshot.branch}`",
            f"- Has local commit: `{snapshot.has_commit}`",
            f"- Configured remotes: `{snapshot.remote_count}`",
            f"- Exact tag on HEAD: `{snapshot.exact_tag or 'none'}`",
            f"- Non-ignored file count: `{len(snapshot.file_scope)}`",
            f"- Oversized file threshold: `{max_mb:g} MB`",
            f"- Oversized file count: `{len(snapshot.oversized_files)}`",
            "",
            "## Largest Non-Ignored Files",
            "",
            *largest_lines,
            "",
            "## Dirty Worktree Preview",
            "",
            *dirty_preview,
            "",
            "## Interpretation Boundary",
            "",
            "A local freeze commit is a reproducibility milestone, not a public release. "
            "G11 cannot become green until the repository has a public GitHub remote, "
            "an immutable release tag, and the release URL is written into manuscript "
            "and release metadata. Zenodo DOI minting remains intentionally held until "
            "the scientific and public-release gates are frozen.",
            "",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--max-mb", type=float, default=20.0)
    parser.add_argument("--audit-path", default=str(DEFAULT_AUDIT_PATH))
    parser.add_argument("--report-path", default=str(DEFAULT_REPORT_PATH))
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    snapshot = collect_snapshot(root, args.max_mb)
    rows = build_audit_rows(snapshot, args.max_mb)
    audit_path = root / args.audit_path
    report_path = root / args.report_path
    _write_tsv_atomic(audit_path, rows)
    _write_text_atomic(report_path, build_report(snapshot, args.max_mb))

    decision, _gate_status = classify_release_state(snapshot)
    print(decision)
    print(f"Audit: {audit_path.relative_to(root).as_posix()}")
    print(f"Report: {report_path.relative_to(root).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
