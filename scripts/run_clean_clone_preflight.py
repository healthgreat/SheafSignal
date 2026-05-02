#!/usr/bin/env python
"""Run a clean-export reproduction preflight for SheafSignal.

Author: SheafSignal contributors
Date: 2026-05-02
Purpose: verify that the Git-tracked state at HEAD can run a lightweight
reproduction check from a clean exported copy. This is a local preflight, not a
substitute for a public GitHub clone after the final release URL exists.
"""

from __future__ import annotations

import argparse
import csv
import os
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path


DEFAULT_OUTPUT_DIR = Path("release/clean_clone_preflight")
DEFAULT_AUDIT_PATH = DEFAULT_OUTPUT_DIR / "CLEAN_CLONE_PREFLIGHT_AUDIT.tsv"
DEFAULT_REPORT_PATH = DEFAULT_OUTPUT_DIR / "CLEAN_CLONE_PREFLIGHT_REPORT.md"


@dataclass(frozen=True)
class CommandResult:
    step: str
    command: str
    cwd: str
    returncode: int
    elapsed_seconds: float
    stdout_tail: str
    stderr_tail: str


def _run(
    step: str,
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    timeout: int = 120,
) -> CommandResult:
    start = time.time()
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        timeout=timeout,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    elapsed = time.time() - start
    return CommandResult(
        step=step,
        command=" ".join(command),
        cwd=str(cwd),
        returncode=result.returncode,
        elapsed_seconds=round(elapsed, 3),
        stdout_tail=_tail(result.stdout),
        stderr_tail=_tail(result.stderr),
    )


def _tail(text: str, max_chars: int = 2000) -> str:
    if not text:
        return ""
    clean = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    return clean[-max_chars:]


def _write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def _write_tsv_atomic(path: Path, results: list[CommandResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    fieldnames = [
        "step",
        "command",
        "cwd",
        "returncode",
        "elapsed_seconds",
        "stdout_tail",
        "stderr_tail",
    ]
    with tmp_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for result in results:
            writer.writerow(result.__dict__)
    tmp_path.replace(path)


def _git(root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-c", f"safe.directory={root.as_posix()}", *args],
        cwd=root,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _export_head(root: Path, temp_root: Path) -> Path:
    archive_path = temp_root / "sheafsignal_head.zip"
    clean_dir = temp_root / "clean_export"
    result = _git(root, ["archive", "--format=zip", "--output", str(archive_path), "HEAD"])
    if result.returncode != 0:
        raise RuntimeError(f"git archive failed: {result.stderr.strip()}")
    clean_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path) as archive:
        archive.extractall(clean_dir)
    return clean_dir


def _python_env(clean_dir: Path) -> dict[str, str]:
    env = os.environ.copy()
    src_path = str(clean_dir / "src")
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = src_path if not existing else f"{src_path}{os.pathsep}{existing}"
    env["PYTHONUNBUFFERED"] = "1"
    return env


def _assert_demo_outputs(output_dir: Path) -> CommandResult:
    start = time.time()
    expected = [
        output_dir / "results" / "sheaf_energy_by_edge.csv",
        output_dir / "results" / "hodge_decomposition_scores.csv",
        output_dir / "results" / "cellular_sheaf_restrictions.csv",
        output_dir / "results" / "cellular_sheaf_laplacian.csv",
        output_dir / "results" / "provenance.json",
        output_dir / "results" / "sheaf_energy_permutation_pvalues.csv",
        output_dir / "results" / "frustration_permutation_pvalues.csv",
        output_dir / "results" / "global_permutation_pvalues.csv",
    ]
    missing = [str(path) for path in expected if not path.exists()]
    returncode = 1 if missing else 0
    stdout = "all expected demo outputs exist" if not missing else ""
    stderr = "missing: " + "; ".join(missing) if missing else ""
    return CommandResult(
        step="assert_demo_outputs",
        command="internal_output_check",
        cwd=str(output_dir),
        returncode=returncode,
        elapsed_seconds=round(time.time() - start, 3),
        stdout_tail=stdout,
        stderr_tail=stderr,
    )


def _classify(results: list[CommandResult]) -> str:
    if all(result.returncode == 0 for result in results):
        return "CLEAN_CLONE_PREFLIGHT_PASS_LOCAL_EXPORT"
    return "CLEAN_CLONE_PREFLIGHT_FAIL"


def _build_report(
    *,
    decision: str,
    root: Path,
    commit: str,
    branch: str,
    results: list[CommandResult],
) -> str:
    result_lines = []
    for result in results:
        status = "pass" if result.returncode == 0 else "fail"
        result_lines.append(
            f"- `{result.step}`: `{status}`, returncode `{result.returncode}`, "
            f"{result.elapsed_seconds}s"
        )
        if result.returncode != 0 and result.stderr_tail:
            result_lines.append(f"  - stderr tail: `{result.stderr_tail}`")

    return "\n".join(
        [
            "# Clean-Clone Reproduction Preflight Report",
            "",
            f"- Decision: `{decision}`",
            f"- Source root: `{root}`",
            f"- Git branch: `{branch}`",
            f"- Git commit: `{commit}`",
            f"- Python executable: `{sys.executable}`",
            f"- Commands run: `{len(results)}`",
            "",
            "## Command Results",
            "",
            *result_lines,
            "",
            "## Interpretation Boundary",
            "",
            "This preflight exports the current Git `HEAD` into a clean temporary "
            "directory and runs a lightweight reproduction check from tracked files "
            "only. It is stronger than testing the dirty working tree, but it is not "
            "a substitute for a final public-GitHub clean clone after the release URL "
            "and Zenodo DOI are inserted.",
            "",
        ]
    )


def run_preflight(root: Path, output_dir: Path, *, keep_workdir: bool = False) -> dict[str, object]:
    root = root.resolve()
    output_dir = (root / output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    commit = _git(root, ["rev-parse", "--short", "HEAD"]).stdout.strip() or "NA"
    branch = _git(root, ["branch", "--show-current"]).stdout.strip() or "NA"

    temp_context = tempfile.TemporaryDirectory(prefix="sheafsignal_clean_export_")
    temp_root = Path(temp_context.name)
    results: list[CommandResult] = []
    try:
        clean_dir = _export_head(root, temp_root)
        env = _python_env(clean_dir)
        demo_output = temp_root / "demo_output"
        results.append(
            _run(
                "pytest_core_clean_export",
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "tests/test_pipeline.py",
                    "tests/test_formal_sheaf.py",
                    "tests/test_simulate.py",
                    "tests/test_sheaf_ground_truth_simulation.py",
                    "-q",
                ],
                cwd=clean_dir,
                env=env,
                timeout=180,
            )
        )
        results.append(
            _run(
                "cli_demo_clean_export",
                [
                    sys.executable,
                    "-m",
                    "sheafsignal.cli",
                    "run",
                    "--expression",
                    "examples/demo_expression.csv",
                    "--metadata",
                    "examples/demo_metadata.csv",
                    "--lr-db",
                    "examples/demo_ligand_receptor.csv",
                    "--gene-set",
                    "examples/demo_pathway_genes.txt",
                    "--project-dir",
                    str(demo_output),
                    "--no-plot",
                    "--n-permutations",
                    "5",
                    "--random-seed",
                    "42",
                ],
                cwd=clean_dir,
                env=env,
                timeout=180,
            )
        )
        results.append(_assert_demo_outputs(demo_output))
        results.append(
            _run(
                "release_audit_clean_export",
                [sys.executable, "scripts/release_audit.py", "--root", "."],
                cwd=clean_dir,
                env=env,
                timeout=120,
            )
        )
        if keep_workdir:
            target = output_dir / "last_clean_export"
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(clean_dir, target)
    finally:
        if not keep_workdir:
            temp_context.cleanup()

    decision = _classify(results)
    _write_tsv_atomic(root / DEFAULT_AUDIT_PATH, results)
    _write_text_atomic(
        root / DEFAULT_REPORT_PATH,
        _build_report(
            decision=decision,
            root=root,
            commit=commit,
            branch=branch,
            results=results,
        ),
    )
    return {
        "decision": decision,
        "audit_path": DEFAULT_AUDIT_PATH.as_posix(),
        "report_path": DEFAULT_REPORT_PATH.as_posix(),
        "n_commands": len(results),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--keep-workdir", action="store_true")
    args = parser.parse_args(argv)

    summary = run_preflight(
        Path(args.root),
        Path(args.output_dir),
        keep_workdir=args.keep_workdir,
    )
    print(summary["decision"])
    print(f"Audit: {summary['audit_path']}")
    print(f"Report: {summary['report_path']}")
    return 0 if summary["decision"] == "CLEAN_CLONE_PREFLIGHT_PASS_LOCAL_EXPORT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
