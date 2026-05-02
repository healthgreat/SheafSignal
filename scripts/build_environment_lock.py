#!/usr/bin/env python
"""Build pinned Python environment lock artifacts for release hardening."""

from __future__ import annotations

import argparse
from datetime import datetime
import platform
from pathlib import Path
import re
import subprocess
import sys

import pandas as pd


CORE_PACKAGES = [
    "numpy",
    "pandas",
    "matplotlib",
    "scipy",
    "h5py",
    "pytest",
    "ruff",
    "PyMuPDF",
    "python-docx",
    "scanpy",
    "anndata",
    "liana",
    "cellphonedb",
    "scrublet",
]

PINNED_REQUIREMENT = re.compile(r"^[A-Za-z0-9_.-]+==[^=<>~!]+$")
PINNED_VCS_REQUIREMENT = re.compile(
    r"^[A-Za-z0-9_.-]+\s+@\s+git\+https?://.+@[0-9a-f]{7,40}",
    re.IGNORECASE,
)
LOCAL_REFERENCE = re.compile(r"(@\s*file:|file:///|\\\\|^[A-Za-z]:\\)", re.IGNORECASE)


def _write_text_atomic(path: Path, text: str) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def _write_table_atomic(path: Path, table: pd.DataFrame) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    table.to_csv(tmp_path, sep="\t", index=False)
    tmp_path.replace(path)


def collect_pip_freeze() -> list[str]:
    result = subprocess.run(
        [sys.executable, "-m", "pip", "freeze", "--exclude-editable"],
        check=True,
        capture_output=True,
        text=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _package_name(requirement_line: str) -> str:
    return re.split(r"==|~=|>=|<=|>|<|@", requirement_line, maxsplit=1)[0].strip().lower()


def build_core_lock_lines(freeze_lines: list[str]) -> list[str]:
    wanted = {name.lower(): name for name in CORE_PACKAGES}
    found = {}
    for line in freeze_lines:
        name = _package_name(line)
        if name in wanted:
            found[name] = line
    return [found[name.lower()] for name in CORE_PACKAGES if name.lower() in found]


def audit_lock_lines(freeze_lines: list[str]) -> pd.DataFrame:
    rows = []
    for line in freeze_lines:
        if line.startswith("#"):
            continue
        pinned = bool(PINNED_REQUIREMENT.match(line) or PINNED_VCS_REQUIREMENT.match(line))
        local_reference = bool(LOCAL_REFERENCE.search(line))
        rows.append(
            {
                "requirement": line,
                "pinned_exact_version": pinned,
                "has_local_reference": local_reference,
                "status": "pass" if pinned and not local_reference else "warn",
            }
        )
    return pd.DataFrame(
        rows,
        columns=["requirement", "pinned_exact_version", "has_local_reference", "status"],
    )


def build_environment_lock(root: Path, freeze_lines: list[str] | None = None) -> dict[str, Path]:
    env_dir = root / "envs"
    env_dir.mkdir(parents=True, exist_ok=True)
    if freeze_lines is None:
        freeze_lines = collect_pip_freeze()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_lock = env_dir / "requirements-py311-lock.txt"
    core_lock = env_dir / "requirements-core-lock.txt"
    audit_path = env_dir / "environment_lock_audit.tsv"
    summary_path = env_dir / "environment_lock_summary.tsv"
    report_path = env_dir / "ENVIRONMENT_LOCK_REPORT.md"

    header = [
        "# SheafSignal Python environment lock",
        f"# Generated: {timestamp}",
        f"# Python: {platform.python_version()}",
        f"# Executable: {sys.executable}",
        "# Install project code after dependencies with: python -m pip install -e .",
        "",
    ]
    _write_text_atomic(full_lock, "\n".join(header + sorted(freeze_lines)) + "\n")

    core_lines = build_core_lock_lines(freeze_lines)
    _write_text_atomic(
        core_lock,
        "\n".join(
            [
                "# SheafSignal core package lock",
                f"# Generated: {timestamp}",
                "# Exact versions for primary runtime/dev/comparator packages detected locally.",
                "",
                *core_lines,
                "",
            ]
        ),
    )

    audit = audit_lock_lines(freeze_lines)
    _write_table_atomic(audit_path, audit)
    n_warn = int((audit["status"] == "warn").sum()) if not audit.empty else 0
    summary = pd.DataFrame(
        [
            {
                "generated": timestamp,
                "python_version": platform.python_version(),
                "python_executable": sys.executable,
                "platform": platform.platform(),
                "n_locked_requirements": len(freeze_lines),
                "n_core_locked_requirements": len(core_lines),
                "n_lock_warnings": n_warn,
                "decision": "ENVIRONMENT_LOCK_PASS" if n_warn == 0 else "ENVIRONMENT_LOCK_PASS_WITH_WARNINGS",
            }
        ]
    )
    _write_table_atomic(summary_path, summary)
    decision = str(summary.iloc[0]["decision"])
    lines = [
        "# Environment Lock Report",
        "",
        f"Decision: `{decision}`",
        "",
        f"- Python version: {platform.python_version()}",
        f"- Python executable: `{sys.executable}`",
        f"- Locked requirements: {len(freeze_lines)}",
        f"- Core locked requirements: {len(core_lines)}",
        f"- Lock warnings: {n_warn}",
        "",
        "## Artifacts",
        "",
        "- `envs/requirements-py311-lock.txt`",
        "- `envs/requirements-core-lock.txt`",
        "- `envs/environment_lock_audit.tsv`",
        "- `envs/environment_lock_summary.tsv`",
        "",
        "## Boundary",
        "",
        "This lock records the local Python environment used for the hardening run.",
        "It complements the broader conda YAML files, which remain convenience",
        "environment definitions. Final public release should use this lock or a",
        "container built from it for clean-clone reproduction.",
        "",
    ]
    _write_text_atomic(report_path, "\n".join(lines))
    return {
        "full_lock": full_lock,
        "core_lock": core_lock,
        "audit": audit_path,
        "summary": summary_path,
        "report": report_path,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    paths = build_environment_lock(root)
    for path in paths.values():
        print(f"wrote {path}")
    summary = pd.read_csv(paths["summary"], sep="\t")
    decision = str(summary.iloc[0]["decision"])
    return 0 if decision.startswith("ENVIRONMENT_LOCK_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
