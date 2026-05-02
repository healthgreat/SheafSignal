#!/usr/bin/env python
"""Check external GitHub and Zenodo authorization gates without printing tokens.

Author: SheafSignal maintainers
Date: 2026-05-03
Purpose: provide a repeatable account-authorization health check before public
GitHub release, Zenodo DOI minting, and public clean-clone reproduction.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path


DEFAULT_GITHUB_TOKEN_PATH = Path(r"D:\secrets\github_token.txt")
DEFAULT_ZENODO_TOKEN_PATH = Path(r"D:\secrets\zenodo_token.txt")
DEFAULT_GH_EXE = Path(r"D:\BioSoft\GitHubCLI\gh_2.92.0\bin\gh.exe")
DEFAULT_STATUS_PATH = Path("release/EXTERNAL_RELEASE_AUTHORIZATION_STATUS.tsv")
DEFAULT_REPORT_PATH = Path("release/EXTERNAL_RELEASE_AUTHORIZATION_REPORT.md")


@dataclass(frozen=True)
class AuthCheckRow:
    check_id: str
    severity: str
    status: str
    evidence: str
    required_action: str
    validation_command: str


def _write_tsv_atomic(path: Path, rows: list[AuthCheckRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    fieldnames = [
        "check_id",
        "severity",
        "status",
        "evidence",
        "required_action",
        "validation_command",
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


def _run_command(args: list[str], cwd: Path, timeout: int = 30) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def resolve_gh_executable(default_path: Path = DEFAULT_GH_EXE) -> str:
    if default_path.exists():
        return str(default_path)
    found = shutil.which("gh")
    return found or ""


def classify_token_file(path: Path, service_name: str) -> AuthCheckRow:
    if not path.exists():
        return AuthCheckRow(
            check_id=f"{service_name}_token_file",
            severity="blocking" if service_name == "github" else "pending",
            status="missing",
            evidence=f"{path} does not exist.",
            required_action=f"Save a {service_name} token outside the repository if API upload/auth is preferred.",
            validation_command=f"Test-Path {path}",
        )
    size = path.stat().st_size
    if size == 0:
        return AuthCheckRow(
            check_id=f"{service_name}_token_file",
            severity="blocking",
            status="empty",
            evidence=f"{path} exists but is empty.",
            required_action=f"Overwrite {path} with a valid {service_name} token.",
            validation_command=f"(Get-Item {path}).Length",
        )
    return AuthCheckRow(
        check_id=f"{service_name}_token_file",
        severity="pass",
        status="present",
        evidence=f"{path} exists; size={size} bytes. Token content was not printed.",
        required_action="None if the API validation row also passes.",
        validation_command=f"(Get-Item {path}).Length",
    )


def _read_token(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def probe_github_token(path: Path, timeout: int = 20) -> AuthCheckRow:
    if not path.exists() or path.stat().st_size == 0:
        return AuthCheckRow(
            check_id="github_token_api",
            severity="blocking",
            status="not_tested_missing_token",
            evidence="GitHub token API validation was skipped because no non-empty token file was present.",
            required_action="Create a valid GitHub token or complete gh browser login.",
            validation_command="python scripts/check_external_release_authorization.py",
        )
    token = _read_token(path)
    request = urllib.request.Request(
        "https://api.github.com/user",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "SheafSignal-release-auth-check",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
            login = payload.get("login", "unknown")
            return AuthCheckRow(
                check_id="github_token_api",
                severity="pass",
                status="valid",
                evidence=f"GitHub API accepted the token for login={login}. Token content was not printed.",
                required_action="Codex can use this token to authenticate GitHub CLI or push release metadata.",
                validation_command="python scripts/check_external_release_authorization.py",
            )
    except urllib.error.HTTPError as exc:
        status = "invalid_or_unauthorized" if exc.code in {401, 403} else f"http_{exc.code}"
        action = (
            "Regenerate a GitHub personal access token with repository permissions "
            "or complete gh browser login."
        )
        return AuthCheckRow(
            check_id="github_token_api",
            severity="blocking",
            status=status,
            evidence=f"GitHub API returned HTTP {exc.code}. Token content was not printed.",
            required_action=action,
            validation_command="python scripts/check_external_release_authorization.py",
        )
    except (OSError, urllib.error.URLError) as exc:
        return AuthCheckRow(
            check_id="github_token_api",
            severity="pending",
            status="network_error",
            evidence=f"Could not reach GitHub API: {exc.__class__.__name__}.",
            required_action="Retry after network/VPN is stable.",
            validation_command="python scripts/check_external_release_authorization.py",
        )


def probe_zenodo_token(path: Path, timeout: int = 20) -> AuthCheckRow:
    if not path.exists() or path.stat().st_size == 0:
        return AuthCheckRow(
            check_id="zenodo_token_api",
            severity="pending",
            status="not_tested_missing_token",
            evidence="Zenodo token API validation was skipped because no non-empty token file was present.",
            required_action="Save a Zenodo token if Codex should upload/mint DOI via API.",
            validation_command="python scripts/check_external_release_authorization.py",
        )
    token = _read_token(path)
    request = urllib.request.Request(
        "https://zenodo.org/api/deposit/depositions?size=1",
        headers={"Authorization": f"Bearer {token}", "User-Agent": "SheafSignal-release-auth-check"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            _ = response.read()
            return AuthCheckRow(
                check_id="zenodo_token_api",
                severity="pass",
                status="valid",
                evidence="Zenodo API accepted the token. Token content was not printed.",
                required_action="Codex can use this token for Zenodo API upload when the release is frozen.",
                validation_command="python scripts/check_external_release_authorization.py",
            )
    except urllib.error.HTTPError as exc:
        return AuthCheckRow(
            check_id="zenodo_token_api",
            severity="blocking",
            status="invalid_or_unauthorized" if exc.code in {401, 403} else f"http_{exc.code}",
            evidence=f"Zenodo API returned HTTP {exc.code}. Token content was not printed.",
            required_action="Regenerate a Zenodo token with deposit permissions or use manual web upload.",
            validation_command="python scripts/check_external_release_authorization.py",
        )
    except (OSError, urllib.error.URLError) as exc:
        return AuthCheckRow(
            check_id="zenodo_token_api",
            severity="pending",
            status="network_error",
            evidence=f"Could not reach Zenodo API: {exc.__class__.__name__}.",
            required_action="Retry after network/VPN is stable.",
            validation_command="python scripts/check_external_release_authorization.py",
        )


def check_gh_cli(root: Path, gh_exe: str) -> list[AuthCheckRow]:
    if not gh_exe:
        return [
            AuthCheckRow(
                check_id="github_cli_binary",
                severity="blocking",
                status="missing",
                evidence="No GitHub CLI binary found in PATH or default portable location.",
                required_action="Install GitHub CLI or keep the portable gh.exe at the documented path.",
                validation_command="gh --version",
            ),
            AuthCheckRow(
                check_id="github_cli_auth",
                severity="blocking",
                status="not_tested_missing_cli",
                evidence="GitHub CLI auth was skipped because gh was not found.",
                required_action="Install GitHub CLI first.",
                validation_command="gh auth status --hostname github.com",
            ),
        ]
    version = _run_command([gh_exe, "--version"], cwd=root, timeout=15)
    version_line = (version.stdout or version.stderr).splitlines()[0] if (version.stdout or version.stderr) else "unknown"
    rows = [
        AuthCheckRow(
            check_id="github_cli_binary",
            severity="pass" if version.returncode == 0 else "blocking",
            status="present" if version.returncode == 0 else "error",
            evidence=f"{gh_exe}; {version_line}",
            required_action="None if auth also passes.",
            validation_command=f'"{gh_exe}" --version',
        )
    ]
    auth = _run_command([gh_exe, "auth", "status", "--hostname", "github.com"], cwd=root, timeout=20)
    output = " ".join((auth.stdout + " " + auth.stderr).split())
    rows.append(
        AuthCheckRow(
            check_id="github_cli_auth",
            severity="pass" if auth.returncode == 0 else "blocking",
            status="logged_in" if auth.returncode == 0 else "not_logged_in",
            evidence=output[:300] if output else "no auth output",
            required_action="None." if auth.returncode == 0 else "Run gh auth login or authenticate gh with a valid token.",
            validation_command=f'"{gh_exe}" auth status --hostname github.com',
        )
    )
    return rows


def check_git_remote(root: Path) -> AuthCheckRow:
    result = _run_command(["git", "remote", "get-url", "origin"], cwd=root, timeout=15)
    if result.returncode == 0:
        return AuthCheckRow(
            check_id="git_origin_remote",
            severity="pass",
            status="configured",
            evidence=result.stdout.strip(),
            required_action="Verify the remote is public before final submission.",
            validation_command="git remote -v",
        )
    return AuthCheckRow(
        check_id="git_origin_remote",
        severity="blocking",
        status="missing",
        evidence="No origin remote configured.",
        required_action="Create or connect the public GitHub repository after auth succeeds.",
        validation_command="git remote -v",
    )


def check_release_archive(root: Path) -> AuthCheckRow:
    archive = root / "release/archives/sheafsignal_zenodo_upload.zip"
    if archive.exists() and archive.stat().st_size > 0:
        return AuthCheckRow(
            check_id="zenodo_upload_archive",
            severity="pass",
            status="present",
            evidence=f"{archive}; size={archive.stat().st_size} bytes",
            required_action="Use only after the final release metadata is frozen.",
            validation_command="Test-Path release/archives/sheafsignal_zenodo_upload.zip",
        )
    return AuthCheckRow(
        check_id="zenodo_upload_archive",
        severity="blocking",
        status="missing",
        evidence=f"{archive} is missing or empty.",
        required_action="Regenerate release archives after final metadata is ready.",
        validation_command="python scripts/package_release_archives.py",
    )


def check_doi_placeholders(root: Path) -> AuthCheckRow:
    text_parts = []
    for rel in [
        "metadata/datasets.tsv",
        "release/DATA_AVAILABILITY_STATEMENT_DRAFT.md",
        "manuscript/NATURE_METHODS_GO_NO_GO_REPORT.md",
    ]:
        path = root / rel
        if path.exists():
            text_parts.append(path.read_text(encoding="utf-8", errors="replace"))
    has_pending = any("PENDING_ZENODO_RELEASE" in part for part in text_parts)
    return AuthCheckRow(
        check_id="zenodo_doi_placeholders",
        severity="blocking" if has_pending else "pass",
        status="pending" if has_pending else "cleared",
        evidence="PENDING_ZENODO_RELEASE is present." if has_pending else "No PENDING_ZENODO_RELEASE placeholder found in checked files.",
        required_action="Mint DOI and run scripts/finalize_zenodo_doi.py." if has_pending else "None.",
        validation_command="python scripts/check_release_metadata_placeholders.py",
    )


def build_authorization_rows(
    root: Path,
    github_token_path: Path = DEFAULT_GITHUB_TOKEN_PATH,
    zenodo_token_path: Path = DEFAULT_ZENODO_TOKEN_PATH,
    gh_exe: str | None = None,
    skip_network: bool = False,
) -> list[AuthCheckRow]:
    gh = gh_exe if gh_exe is not None else resolve_gh_executable()
    rows: list[AuthCheckRow] = []
    rows.extend(check_gh_cli(root, gh))
    rows.append(classify_token_file(github_token_path, "github"))
    rows.append(
        AuthCheckRow(
            check_id="github_token_api",
            severity="pending",
            status="skipped_by_flag",
            evidence="Network token validation skipped by --skip-network.",
            required_action="Run without --skip-network before release.",
            validation_command="python scripts/check_external_release_authorization.py",
        )
        if skip_network
        else probe_github_token(github_token_path)
    )
    rows.append(check_git_remote(root))
    rows.append(classify_token_file(zenodo_token_path, "zenodo"))
    rows.append(
        AuthCheckRow(
            check_id="zenodo_token_api",
            severity="pending",
            status="skipped_by_flag",
            evidence="Network token validation skipped by --skip-network.",
            required_action="Run without --skip-network before API upload, or use manual upload.",
            validation_command="python scripts/check_external_release_authorization.py",
        )
        if skip_network
        else probe_zenodo_token(zenodo_token_path)
    )
    rows.append(check_release_archive(root))
    rows.append(check_doi_placeholders(root))
    return harmonize_github_env_token(rows)


def harmonize_github_env_token(rows: list[AuthCheckRow]) -> list[AuthCheckRow]:
    """Downgrade persistent gh login if a file token is API-valid.

    GitHub CLI commands can use the `GH_TOKEN` environment variable even when
    `gh auth login --with-token` refuses to persist the token. The release gate
    should therefore distinguish a usable local token from a fully logged-in
    credential store.
    """

    github_token_valid = any(
        row.check_id == "github_token_api" and row.status == "valid" for row in rows
    )
    if not github_token_valid:
        return rows

    updated: list[AuthCheckRow] = []
    for row in rows:
        if row.check_id == "github_cli_auth" and row.status != "logged_in":
            updated.append(
                AuthCheckRow(
                    check_id=row.check_id,
                    severity="pending",
                    status="env_token_available_persistent_login_missing",
                    evidence=(
                        "GitHub CLI persistent login is missing, but the local token "
                        "passed GitHub API validation and can be used via GH_TOKEN."
                    ),
                    required_action=(
                        "Persistent gh login is optional; Codex can set GH_TOKEN from "
                        "the local token file for repo creation and push operations."
                    ),
                    validation_command="python scripts/check_external_release_authorization.py",
                )
            )
        else:
            updated.append(row)
    return updated


def classify_decision(rows: list[AuthCheckRow]) -> str:
    blocking = [row for row in rows if row.severity == "blocking"]
    if any(row.check_id == "github_token_api" and row.status == "valid" for row in rows):
        github_unblocked = True
    else:
        github_unblocked = any(row.check_id == "github_cli_auth" and row.status == "logged_in" for row in rows)
    zenodo_ready = any(row.check_id == "zenodo_token_api" and row.status == "valid" for row in rows)
    if not blocking:
        return "EXTERNAL_RELEASE_AUTHORIZATION_READY"
    if github_unblocked and zenodo_ready:
        return "EXTERNAL_RELEASE_AUTHORIZATION_PARTIAL_METADATA_BLOCKED"
    return "EXTERNAL_RELEASE_AUTHORIZATION_BLOCKED"


def build_report(rows: list[AuthCheckRow]) -> str:
    decision = classify_decision(rows)
    blocking_lines = [
        f"- `{row.check_id}`: `{row.status}`. Action: {row.required_action}"
        for row in rows
        if row.severity == "blocking"
    ]
    if not blocking_lines:
        blocking_lines = ["- none"]
    pass_count = sum(row.severity == "pass" for row in rows)
    pending_count = sum(row.severity == "pending" for row in rows)
    blocking_count = sum(row.severity == "blocking" for row in rows)
    return "\n".join(
        [
            "# External Release Authorization Report",
            "",
            f"- Decision: `{decision}`",
            f"- Passed checks: `{pass_count}`",
            f"- Pending checks: `{pending_count}`",
            f"- Blocking checks: `{blocking_count}`",
            "",
            "## Blocking Checks",
            "",
            *blocking_lines,
            "",
            "## Interpretation Boundary",
            "",
            "This report validates account and release-infrastructure readiness. It does not",
            "print token contents, does not change GitHub or Zenodo state, and does not",
            "guarantee journal acceptance.",
            "",
            "## Next Command",
            "",
            "```bash",
            "python scripts/check_external_release_authorization.py",
            "```",
            "",
        ]
    )


def write_authorization_outputs(
    root: Path,
    rows: list[AuthCheckRow],
    status_path: Path = DEFAULT_STATUS_PATH,
    report_path: Path = DEFAULT_REPORT_PATH,
) -> dict[str, Path]:
    status_out = root / status_path
    report_out = root / report_path
    _write_tsv_atomic(status_out, rows)
    _write_text_atomic(report_out, build_report(rows))
    return {"status": status_out, "report": report_out}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--github-token-path", default=str(DEFAULT_GITHUB_TOKEN_PATH))
    parser.add_argument("--zenodo-token-path", default=str(DEFAULT_ZENODO_TOKEN_PATH))
    parser.add_argument("--gh-exe", default=None)
    parser.add_argument("--skip-network", action="store_true")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    rows = build_authorization_rows(
        root=root,
        github_token_path=Path(args.github_token_path),
        zenodo_token_path=Path(args.zenodo_token_path),
        gh_exe=args.gh_exe,
        skip_network=args.skip_network,
    )
    outputs = write_authorization_outputs(root, rows)
    print(f"decision: {classify_decision(rows)}")
    for label, path in outputs.items():
        print(f"wrote {label}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
