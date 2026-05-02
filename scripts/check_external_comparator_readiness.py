#!/usr/bin/env python
"""Build an auditable execution plan for external CCC comparators.

Author: SheafSignal contributors
Date: 2026-04-29
Method reference: external CCC comparator benchmarking gate for LIANA,
CellChat, CellPhoneDB, NicheNet, and niche-DE.
Purpose: keep Nature Methods-facing comparator status explicit instead of
silently treating placeholders as completed evidence.
"""

from __future__ import annotations

import argparse
import json
import importlib.metadata
import importlib.util
import shutil
import subprocess
from pathlib import Path

import pandas as pd

import _bootstrap  # noqa: F401
from sheafsignal.manifest import load_dataset_manifest, validate_dataset_manifest


LIANA_TARGET_DATASETS = (
    "gse154778_pdac_scrna",
    "gse72056_melanoma_scrna",
    "gse176078_brca_scrna",
)
LIANA_CONDA_ENV = "sheafsignal-liana"
SMOKE_MAX_CELLS = 5000
FULL_MAX_CELLS = ""


def _package_status(package: str) -> dict[str, object]:
    present = importlib.util.find_spec(package) is not None
    version = ""
    if present:
        try:
            version = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            version = "installed_version_unknown"
    return {
        "check_type": "python_package",
        "name": package,
        "present": bool(present),
        "version_or_path": version,
        "required_for": "LIANA" if package in {"liana", "scanpy", "anndata"} else "",
    }


def _conda_env_status(conda_path: str, env_name: str) -> dict[str, object]:
    if not conda_path:
        return {
            "check_type": "conda_env",
            "name": env_name,
            "present": False,
            "version_or_path": "",
            "required_for": "LIANA isolated execution",
        }
    try:
        completed = subprocess.run(
            [conda_path, "env", "list", "--json"],
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
        payload = json.loads(completed.stdout) if completed.returncode == 0 else {}
    except (OSError, json.JSONDecodeError, subprocess.SubprocessError):
        payload = {}
    envs = [Path(path) for path in payload.get("envs", [])]
    match = [path for path in envs if path.name == env_name]
    return {
        "check_type": "conda_env",
        "name": env_name,
        "present": bool(match),
        "version_or_path": str(match[0]) if match else "",
        "required_for": "LIANA isolated execution",
    }


def _conda_env_package_status(
    conda_path: str,
    env_name: str,
    package: str,
) -> dict[str, object]:
    if not conda_path:
        return {
            "check_type": "conda_env_package",
            "name": f"{env_name}:{package}",
            "present": False,
            "version_or_path": "",
            "required_for": "LIANA isolated execution",
        }
    code = (
        "import importlib.util, importlib.metadata; "
        f"pkg={package!r}; "
        "present=importlib.util.find_spec(pkg) is not None; "
        "version=''; "
        "\nif present:\n"
        "    try:\n"
        "        version=importlib.metadata.version(pkg)\n"
        "    except importlib.metadata.PackageNotFoundError:\n"
        "        version='installed_version_unknown'\n"
        "print(str(present) + '\\t' + version)"
    )
    try:
        completed = subprocess.run(
            [conda_path, "run", "-n", env_name, "python", "-c", code],
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except (OSError, subprocess.SubprocessError):
        completed = None
    present = False
    version = ""
    if completed is not None and completed.returncode == 0:
        line = completed.stdout.strip().splitlines()[-1] if completed.stdout.strip() else ""
        parts = line.split("\t", 1)
        present = parts[0] == "True"
        version = parts[1] if len(parts) > 1 else ""
    return {
        "check_type": "conda_env_package",
        "name": f"{env_name}:{package}",
        "present": bool(present),
        "version_or_path": version,
        "required_for": "LIANA isolated execution",
    }


def detect_environment_status() -> pd.DataFrame:
    """Detect optional external-comparator environment dependencies."""
    rows = []
    conda_path = shutil.which("conda") or shutil.which("conda.bat") or ""
    rows.append(
        {
            "check_type": "executable",
            "name": "conda",
            "present": bool(conda_path),
            "version_or_path": conda_path,
            "required_for": "isolated LIANA environment",
        }
    )
    for package in ["liana", "scanpy", "anndata"]:
        rows.append(_package_status(package))
    rows.append(_conda_env_status(conda_path, LIANA_CONDA_ENV))
    for package in ["liana", "scanpy", "anndata", "sheafsignal"]:
        rows.append(_conda_env_package_status(conda_path, LIANA_CONDA_ENV, package))
    return pd.DataFrame(rows)


def _status_for_dataset(
    *,
    dataset_id: str,
    manifest_row: pd.Series,
    results_dir: Path,
) -> tuple[str, list[str]]:
    missing: list[str] = []
    expression = Path(str(manifest_row.get("prepared_expression", "")))
    metadata = Path(str(manifest_row.get("prepared_metadata", "")))
    sheaf_edges = results_dir / dataset_id / "results" / "sheaf_energy_by_edge.csv"
    if not expression.exists():
        missing.append(f"missing_prepared_expression:{expression}")
    if not metadata.exists():
        missing.append(f"missing_prepared_metadata:{metadata}")
    if not sheaf_edges.exists():
        missing.append(f"missing_sheaf_edges:{sheaf_edges}")
    return ("ready" if not missing else "blocked_missing_inputs", missing)


def _current_tool_status(
    *,
    dataset_id: str,
    tool: str,
    tool_comparison: pd.DataFrame,
) -> str:
    if tool_comparison.empty:
        return "missing_tool_comparison"
    required = {"dataset_id", "tool", "status"}
    if not required.issubset(tool_comparison.columns):
        return "malformed_tool_comparison"
    match = tool_comparison.loc[
        (tool_comparison["dataset_id"].astype(str) == dataset_id)
        & (tool_comparison["tool"].astype(str).str.lower() == tool.lower())
    ]
    if match.empty:
        return "not_listed"
    return str(match.iloc[-1]["status"])


def _liana_metadata_path(results_dir: Path, dataset_id: str) -> Path:
    return (
        results_dir
        / dataset_id
        / "comparators"
        / "liana_run"
        / "liana_run_metadata.json"
    )


def _read_liana_run_metadata(results_dir: Path, dataset_id: str) -> dict[str, object]:
    """Read LIANA run metadata used to distinguish smoke from full imports."""
    path = _liana_metadata_path(results_dir, dataset_id)
    if not path.exists():
        return {"metadata_present": False, "metadata_path": str(path)}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {
            "metadata_present": False,
            "metadata_path": str(path),
            "metadata_error": "json_decode_error",
        }
    if not isinstance(payload, dict):
        return {
            "metadata_present": False,
            "metadata_path": str(path),
            "metadata_error": "not_a_json_object",
        }
    payload["metadata_present"] = True
    payload["metadata_path"] = str(path)
    return payload


def _liana_phase_from_metadata(metadata: dict[str, object]) -> str:
    if not bool(metadata.get("metadata_present")):
        return "unknown"
    max_cells = metadata.get("max_cells")
    if pd.isna(max_cells) or max_cells in {"", "None", "none", "null"}:
        return "full"
    return "smoke"


def _count_csv_data_rows(path: Path) -> int | None:
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as handle:
        return max(0, sum(1 for _ in handle) - 1)


def _resolve_processed_dir(
    *,
    metadata: dict[str, object],
    dataset_id: str,
    results_dir: Path,
) -> Path:
    project_root = results_dir.parent.parent
    processed_value = str(metadata.get("processed_dir", "")).strip()
    processed_dir = Path(processed_value) if processed_value else Path()
    if processed_value and processed_dir.is_absolute() and processed_dir.exists():
        return processed_dir
    if processed_value:
        candidate = project_root / processed_dir
        if candidate.exists():
            return candidate
    return project_root / "data" / "processed" / dataset_id


def _prepared_subset_status(
    *,
    metadata: dict[str, object],
    dataset_id: str,
    results_dir: Path,
    min_coverage: float = 0.95,
) -> tuple[bool, int | None, int | None]:
    expression_cells = metadata.get("n_expression_cells_read")
    metadata_cells = metadata.get("n_metadata_cells_read")
    try:
        expression_n = int(expression_cells) if expression_cells is not None else None
        metadata_n = int(metadata_cells) if metadata_cells is not None else None
    except (TypeError, ValueError):
        expression_n = None
        metadata_n = None

    if expression_n is None or metadata_n is None:
        processed_dir = _resolve_processed_dir(
            metadata=metadata,
            dataset_id=dataset_id,
            results_dir=results_dir,
        )
        expression_n = _count_csv_data_rows(processed_dir / "expression.csv")
        metadata_n = _count_csv_data_rows(processed_dir / "metadata.csv")

    if expression_n is None or metadata_n is None or metadata_n == 0:
        return False, expression_n, metadata_n
    return (expression_n / metadata_n) < min_coverage, expression_n, metadata_n


def _phase_specific_liana_status(
    *,
    dataset_id: str,
    run_phase: str,
    current_status: str,
    results_dir: Path,
) -> str:
    """Map a tool_comparison import row onto the planned smoke/full run phase."""
    if "completed_external_import" not in str(current_status):
        return current_status

    metadata = _read_liana_run_metadata(results_dir, dataset_id)
    recorded_phase = _liana_phase_from_metadata(metadata)
    if recorded_phase == "unknown":
        return "completed_import_metadata_missing"
    is_prepared_subset, _, _ = _prepared_subset_status(
        metadata=metadata,
        dataset_id=dataset_id,
        results_dir=results_dir,
    )
    if recorded_phase == "full" and is_prepared_subset:
        if run_phase == "full":
            return "completed_prepared_subset_import"
        if run_phase == "smoke":
            return "superseded_by_prepared_subset_import"
    if run_phase == recorded_phase:
        return f"completed_{recorded_phase}_import"
    if run_phase == "full" and recorded_phase == "smoke":
        return "not_run_full_after_smoke"
    if run_phase == "smoke" and recorded_phase == "full":
        return "superseded_by_full_import"
    return f"completed_external_import_{recorded_phase}_only"


def _claim_gate_effect_for_liana_status(status: str, ready: bool) -> str:
    if status == "completed_full_import":
        return "full_external_liana_evidence_available"
    if status == "completed_prepared_subset_import":
        return "partial_external_prepared_subset_evidence"
    if status == "completed_smoke_import":
        return "partial_external_smoke_evidence"
    if status == "not_run_full_after_smoke":
        return "full_external_liana_evidence_still_pending"
    if status == "superseded_by_full_import":
        return "full_external_liana_evidence_available"
    if status == "superseded_by_prepared_subset_import":
        return "partial_external_prepared_subset_evidence"
    if ready:
        return "can_update_external_gate_after_import"
    return "external_comparator_remains_pending"


def _liana_command(dataset_id: str, run_phase: str, use_conda_run: bool = False) -> str:
    base = [
        "conda run -n sheafsignal-liana python" if use_conda_run else "python",
        "scripts/run_liana_comparator.py",
        f"--dataset-id {dataset_id}",
        "--min-cells 20",
        "--n-perms 1000",
        "--n-jobs 4",
    ]
    if run_phase == "smoke":
        base.append(f"--max-cells {SMOKE_MAX_CELLS}")
    return " ".join(base)


def build_liana_execution_plan(
    *,
    manifest: pd.DataFrame,
    tool_comparison: pd.DataFrame,
    environment: pd.DataFrame,
    results_dir: Path,
    target_datasets: tuple[str, ...] = LIANA_TARGET_DATASETS,
) -> pd.DataFrame:
    """Build smoke/full LIANA run rows for public scRNA-seq benchmarks."""
    active_liana_present = bool(
        environment.loc[
            (environment["check_type"] == "python_package")
            & (environment["name"] == "liana"),
            "present",
        ].any()
    )
    conda_liana_present = bool(
        environment.loc[
            (environment["check_type"] == "conda_env_package")
            & (environment["name"] == f"{LIANA_CONDA_ENV}:liana"),
            "present",
        ].any()
    )
    liana_present = active_liana_present or conda_liana_present
    use_conda_run = conda_liana_present
    rows: list[dict[str, object]] = []
    manifest_by_id = manifest.set_index("dataset_id", drop=False)
    for dataset_id in target_datasets:
        if dataset_id not in manifest_by_id.index:
            for run_phase in ["smoke", "full"]:
                rows.append(
                    {
                        "dataset_id": dataset_id,
                        "tool": "LIANA",
                        "run_phase": run_phase,
                        "ready_to_run": False,
                        "environment_status": "manifest_missing_dataset",
                        "data_status": "manifest_missing_dataset",
                        "current_import_status": "not_listed",
                        "command": _liana_command(
                            dataset_id,
                            run_phase,
                            use_conda_run=use_conda_run,
                        ),
                        "expected_output_dir": (
                            f"benchmarks/results/{dataset_id}/comparators/liana_run"
                        ),
                        "blockers": "manifest_missing_dataset",
                        "claim_gate_effect": "external_comparator_remains_pending",
                    }
                )
            continue

        row = manifest_by_id.loc[dataset_id]
        data_status, data_blockers = _status_for_dataset(
            dataset_id=dataset_id,
            manifest_row=row,
            results_dir=results_dir,
        )
        current_status = _current_tool_status(
            dataset_id=dataset_id,
            tool="LIANA",
            tool_comparison=tool_comparison,
        )
        env_status = (
            f"ready_conda_env:{LIANA_CONDA_ENV}"
            if conda_liana_present
            else "ready_active_python"
            if active_liana_present
            else "missing_python_package_liana"
        )
        for run_phase in ["smoke", "full"]:
            ready = bool(liana_present and data_status == "ready")
            blockers = list(data_blockers)
            if not liana_present:
                blockers.append(
                    "missing_python_package_liana:create envs/liana_environment.yml first"
                )
            phase_status = _phase_specific_liana_status(
                dataset_id=dataset_id,
                run_phase=run_phase,
                current_status=current_status,
                results_dir=results_dir,
            )
            rows.append(
                {
                    "dataset_id": dataset_id,
                    "tool": "LIANA",
                    "run_phase": run_phase,
                    "ready_to_run": ready,
                    "environment_status": env_status,
                    "data_status": data_status,
                    "current_import_status": phase_status,
                    "command": _liana_command(
                        dataset_id,
                        run_phase,
                        use_conda_run=use_conda_run,
                    ),
                    "expected_output_dir": f"benchmarks/results/{dataset_id}/comparators/liana_run",
                    "blockers": ";".join(blockers),
                    "claim_gate_effect": _claim_gate_effect_for_liana_status(
                        phase_status,
                        ready,
                    ),
                }
            )
    return pd.DataFrame(rows)


def build_gate_summary(
    *,
    execution_plan: pd.DataFrame,
    environment: pd.DataFrame,
) -> pd.DataFrame:
    liana_rows = execution_plan.loc[execution_plan["tool"] == "LIANA"].copy()
    statuses = liana_rows["current_import_status"].astype(str)
    smoke_completed = statuses.isin(["completed_smoke_import", "superseded_by_full_import"])
    full_completed = statuses.isin(["completed_full_import", "superseded_by_full_import"])
    prepared_subset_completed = statuses.isin(
        [
            "completed_prepared_subset_import",
            "superseded_by_prepared_subset_import",
        ]
    )
    import_metadata_missing = statuses.eq("completed_import_metadata_missing")
    ready_rows = liana_rows["ready_to_run"].astype(bool)
    active_liana_present = bool(
        environment.loc[
            (environment["check_type"] == "python_package")
            & (environment["name"] == "liana"),
            "present",
        ].any()
    )
    conda_liana_present = bool(
        environment.loc[
            (environment["check_type"] == "conda_env_package")
            & (environment["name"] == f"{LIANA_CONDA_ENV}:liana"),
            "present",
        ].any()
    )
    liana_present = active_liana_present or conda_liana_present
    n_target_datasets = int(liana_rows["dataset_id"].astype(str).nunique())
    n_smoke_completed_datasets = int(
        liana_rows.loc[smoke_completed, "dataset_id"].astype(str).nunique()
    )
    n_full_completed_datasets = int(
        liana_rows.loc[full_completed, "dataset_id"].astype(str).nunique()
    )
    n_prepared_subset_completed_datasets = int(
        liana_rows.loc[prepared_subset_completed, "dataset_id"].astype(str).nunique()
    )
    n_metadata_missing_rows = int(import_metadata_missing.sum())

    if n_full_completed_datasets == n_target_datasets and n_target_datasets > 0:
        gate_status = "satisfied_liana_full"
    elif n_prepared_subset_completed_datasets == n_target_datasets and n_target_datasets > 0:
        gate_status = "partially_satisfied_prepared_subset_only"
    elif n_full_completed_datasets > 0 or n_prepared_subset_completed_datasets > 0:
        gate_status = "partially_satisfied_mixed"
    elif n_smoke_completed_datasets == n_target_datasets and n_target_datasets > 0:
        gate_status = "partially_satisfied_smoke_only"
    elif n_smoke_completed_datasets > 0 or n_full_completed_datasets > 0:
        gate_status = "partially_satisfied"
    elif n_metadata_missing_rows > 0:
        gate_status = "partial_import_phase_uncertain"
    elif ready_rows.any():
        gate_status = "ready_to_execute"
    else:
        gate_status = "blocked_environment_or_inputs"

    if gate_status == "satisfied_liana_full":
        manuscript_boundary = (
            "Full LIANA benchmarking is complete for the public scRNA-seq datasets. "
            "Do not claim broad CCC-tool superiority until at least one mechanistic "
            "comparator such as NicheNet is also complete."
        )
        next_action = (
            "Add at least one mechanistic comparator such as NicheNet and regenerate "
            "reviewer gates."
        )
    else:
        manuscript_boundary = (
            "Smoke and prepared-subset LIANA imports are partial external comparator "
            "evidence only. Do not claim full LIANA benchmarking until "
            "completed_full_import appears for the public scRNA-seq datasets."
        )
        next_action = (
            "For any prepared-subset dataset, build a true full-cell input or a "
            "pre-specified downsampling benchmark; then rebuild reviewer gates "
            "and add at least one mechanistic comparator such as NicheNet."
        )

    return pd.DataFrame(
        [
            {
                "gate_id": "external_liana_comparator",
                "gate_status": gate_status,
                "liana_package_present": liana_present,
                "n_execution_rows": int(len(liana_rows)),
                "n_ready_rows": int(ready_rows.sum()),
                "n_smoke_completed_datasets": n_smoke_completed_datasets,
                "n_full_completed_datasets": n_full_completed_datasets,
                "n_prepared_subset_completed_datasets": n_prepared_subset_completed_datasets,
                "n_phase_uncertain_rows": n_metadata_missing_rows,
                "manuscript_boundary": manuscript_boundary,
                "next_action": next_action,
            }
        ]
    )


def write_readiness_outputs(
    *,
    manifest_path: Path,
    results_dir: Path,
    manuscript_dir: Path,
    output_dir: Path,
) -> dict[str, Path]:
    validate_dataset_manifest(manifest_path, require_public_downloads=False)
    manifest = load_dataset_manifest(manifest_path)
    tool_comparison_path = results_dir / "tool_comparison.csv"
    if tool_comparison_path.exists():
        tool_comparison = pd.read_csv(tool_comparison_path)
    else:
        tool_comparison = pd.DataFrame()
    environment = detect_environment_status()
    execution_plan = build_liana_execution_plan(
        manifest=manifest,
        tool_comparison=tool_comparison,
        environment=environment,
        results_dir=results_dir,
    )
    gate_summary = build_gate_summary(
        execution_plan=execution_plan,
        environment=environment,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    manuscript_dir.mkdir(parents=True, exist_ok=True)
    environment_path = output_dir / "external_comparator_environment_status.csv"
    execution_path = output_dir / "external_comparator_execution_plan.csv"
    gate_csv_path = output_dir / "external_comparator_gate_summary.csv"
    gate_tsv_path = manuscript_dir / "external_comparator_gate_summary.tsv"

    environment.to_csv(environment_path, index=False)
    execution_plan.to_csv(execution_path, index=False)
    gate_summary.to_csv(gate_csv_path, index=False)
    gate_summary.to_csv(gate_tsv_path, sep="\t", index=False)
    return {
        "environment": environment_path,
        "execution_plan": execution_path,
        "gate_summary_csv": gate_csv_path,
        "gate_summary_tsv": gate_tsv_path,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="metadata/datasets.tsv")
    parser.add_argument("--results-dir", default="benchmarks/results")
    parser.add_argument("--manuscript-dir", default="manuscript")
    parser.add_argument("--output-dir", default="benchmarks/results")
    args = parser.parse_args(argv)

    paths = write_readiness_outputs(
        manifest_path=Path(args.manifest),
        results_dir=Path(args.results_dir),
        manuscript_dir=Path(args.manuscript_dir),
        output_dir=Path(args.output_dir),
    )
    for path in paths.values():
        print(f"wrote {path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
