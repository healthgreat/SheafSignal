#!/usr/bin/env python
"""Publish SheafSignal to GitHub after token scopes are release-ready.

Author: SheafSignal maintainers
Date: 2026-05-03
Purpose: safely push the frozen branch, create a release tag, and optionally
create a GitHub release only after the local token has both repo and workflow
scopes.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path


def _default_secret_path(env_name: str, filename: str) -> Path:
    override = os.environ.get(env_name)
    if override:
        return Path(override)
    secret_dir = os.environ.get("SHEAFSIGNAL_SECRET_DIR")
    if secret_dir:
        return Path(secret_dir) / filename
    return Path.home() / ".config" / "sheafsignal" / filename


DEFAULT_GITHUB_TOKEN_PATH = _default_secret_path(
    "SHEAFSIGNAL_GITHUB_TOKEN_PATH", "github_token.txt"
)
DEFAULT_GH_EXE = Path(os.environ.get("SHEAFSIGNAL_GH_EXE", "gh"))
DEFAULT_TAG = "v0.1.0"
DEFAULT_BRANCH = "codex/sheafsignal-hardening-release"
DEFAULT_REPO = "healthgreat/SheafSignal"
DEFAULT_ARCHIVE = Path("release/archives/sheafsignal_github_release.zip")
DEFAULT_REPORT = Path("release/GITHUB_RELEASE_PUBLICATION_REPORT.md")


@dataclass(frozen=True)
class CommandStep:
    step_id: str
    command: list[str]
    purpose: str


def parse_scope_header(scope_header: str) -> set[str]:
    return {scope.strip() for scope in scope_header.split(",") if scope.strip()}


def missing_required_scopes(scope_header: str, required: tuple[str, ...] = ("repo", "workflow")) -> set[str]:
    scopes = parse_scope_header(scope_header)
    return {scope for scope in required if scope not in scopes}


def _read_token(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def get_github_token_identity(token_path: Path) -> tuple[str, str]:
    token = _read_token(token_path)
    request = urllib.request.Request(
        "https://api.github.com/user",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "SheafSignal-github-release-publisher",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))
        return payload.get("login", "unknown"), response.headers.get("X-OAuth-Scopes", "")


def current_branch(root: Path) -> str:
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def ensure_clean_worktree(root: Path) -> None:
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git status failed")
    if result.stdout.strip():
        raise RuntimeError(
            "Working tree is dirty. Commit or stash changes before publishing."
        )


def build_release_steps(
    repo: str,
    branch: str,
    tag: str,
    archive: Path,
    create_release: bool,
    draft: bool,
) -> list[CommandStep]:
    steps = [
        CommandStep(
            step_id="repo_view",
            command=["gh", "repo", "view", repo, "--json", "nameWithOwner,visibility,url"],
            purpose="Verify the public GitHub repository exists.",
        ),
        CommandStep(
            step_id="push_branch",
            command=["git", "push", "-u", "origin", f"HEAD:{branch}"],
            purpose="Push the frozen branch to the public repository.",
        ),
        CommandStep(
            step_id="create_or_update_tag",
            command=["git", "tag", "-f", tag],
            purpose="Create or update the local release tag at the current commit.",
        ),
        CommandStep(
            step_id="push_tag",
            command=["git", "push", "-f", "origin", tag],
            purpose="Push the release tag to GitHub.",
        ),
    ]
    if create_release:
        command = [
            "gh",
            "release",
            "create",
            tag,
            str(archive),
            "--repo",
            repo,
            "--title",
            f"SheafSignal {tag}",
            "--notes",
            "Initial reproducible SheafSignal methods package release. Zenodo DOI remains the authoritative data archive identifier after minting.",
        ]
        if draft:
            command.append("--draft")
        steps.append(
            CommandStep(
                step_id="create_github_release",
                command=command,
                purpose="Create a GitHub release with the source archive attached.",
            )
        )
    return steps


def run_step(step: CommandStep, root: Path, env: dict[str, str], dry_run: bool) -> str:
    printable = " ".join(step.command)
    if dry_run:
        return f"DRY_RUN {step.step_id}: {printable}"
    command = [str(DEFAULT_GH_EXE) if part == "gh" and DEFAULT_GH_EXE.exists() else part for part in step.command]
    result = subprocess.run(
        command,
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"{step.step_id} failed with exit code {result.returncode}: "
            f"{(result.stderr or result.stdout).strip()}"
        )
    return f"OK {step.step_id}: {printable}"


def _write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def build_report(
    decision: str,
    login: str,
    scopes: str,
    branch: str,
    tag: str,
    repo: str,
    logs: list[str],
    dry_run: bool,
) -> str:
    log_lines = [f"- {line}" for line in logs] or ["- none"]
    return "\n".join(
        [
            "# GitHub Release Publication Report",
            "",
            f"- Decision: `{decision}`",
            f"- GitHub login: `{login}`",
            f"- Token scopes: `{scopes}`",
            f"- Repository: `https://github.com/{repo}`",
            f"- Branch: `{branch}`",
            f"- Tag: `{tag}`",
            f"- Dry run: `{dry_run}`",
            "",
            "## Step Log",
            "",
            *log_lines,
            "",
            "## Boundary",
            "",
            "This report documents GitHub publication mechanics. It does not mint a",
            "Zenodo DOI, does not replace author confirmation, and does not guarantee",
            "journal acceptance.",
            "",
        ]
    )


def build_blocked_report(reason: str) -> str:
    return "\n".join(
        [
            "# GitHub Release Publication Report",
            "",
            "- Decision: `GITHUB_RELEASE_BLOCKED`",
            f"- Blocking reason: {reason}",
            "",
            "## Required Action",
            "",
            "Regenerate the GitHub token with both `repo` and `workflow` scopes,",
            "then rerun this script after committing local changes.",
            "",
            "## Boundary",
            "",
            "This report documents why GitHub publication did not run. It does not",
            "print token contents, does not mint a Zenodo DOI, and does not guarantee",
            "journal acceptance.",
            "",
        ]
    )


def publish_github_release(
    root: Path,
    token_path: Path,
    repo: str,
    branch: str,
    tag: str,
    archive: Path,
    create_release: bool,
    draft: bool,
    dry_run: bool,
) -> str:
    if not token_path.exists():
        raise RuntimeError(f"GitHub token file is missing: {token_path}")
    if not archive.exists():
        raise RuntimeError(f"GitHub release archive is missing: {archive}")

    login, scopes = get_github_token_identity(token_path)
    missing = missing_required_scopes(scopes)
    if missing:
        raise RuntimeError(
            "GitHub token is valid but missing required scope(s): "
            + ", ".join(sorted(missing))
        )

    ensure_clean_worktree(root)
    actual_branch = current_branch(root)
    if actual_branch != branch:
        raise RuntimeError(f"Current branch is {actual_branch!r}, expected {branch!r}.")

    env = os.environ.copy()
    env["GH_TOKEN"] = _read_token(token_path)
    steps = build_release_steps(
        repo=repo,
        branch=branch,
        tag=tag,
        archive=archive,
        create_release=create_release,
        draft=draft,
    )
    logs = [run_step(step, root, env, dry_run=dry_run) for step in steps]
    decision = "GITHUB_RELEASE_DRY_RUN_READY" if dry_run else "GITHUB_RELEASE_PUBLISHED"
    report = build_report(
        decision=decision,
        login=login,
        scopes=scopes,
        branch=branch,
        tag=tag,
        repo=repo,
        logs=logs,
        dry_run=dry_run,
    )
    _write_text_atomic(root / DEFAULT_REPORT, report)
    return decision


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--token-path", default=str(DEFAULT_GITHUB_TOKEN_PATH))
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--branch", default=DEFAULT_BRANCH)
    parser.add_argument("--tag", default=DEFAULT_TAG)
    parser.add_argument("--archive", default=str(DEFAULT_ARCHIVE))
    parser.add_argument("--create-release", action="store_true")
    parser.add_argument("--publish-release", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    try:
        decision = publish_github_release(
            root=root,
            token_path=Path(args.token_path),
            repo=args.repo,
            branch=args.branch,
            tag=args.tag,
            archive=Path(args.archive),
            create_release=args.create_release,
            draft=not args.publish_release,
            dry_run=args.dry_run,
        )
    except RuntimeError as exc:
        _write_text_atomic(root / DEFAULT_REPORT, build_blocked_report(str(exc)))
        print(f"GITHUB_RELEASE_BLOCKED: {exc}", file=sys.stderr)
        print(f"wrote {DEFAULT_REPORT}", file=sys.stderr)
        return 1
    print(decision)
    print(f"wrote {DEFAULT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
