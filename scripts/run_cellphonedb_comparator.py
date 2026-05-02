#!/usr/bin/env python
"""Prepare and optionally run CellPhoneDB v5 comparator inputs."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import traceback
from pathlib import Path

import pandas as pd

import _bootstrap  # noqa: F401


def _write_json_atomic(path: Path, payload: dict[str, object]) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    tmp_path.replace(path)


def prepare_cellphonedb_inputs(
    *,
    processed_dir: Path,
    output_dir: Path,
    cell_type_col: str = "cell_type",
    max_cells: int | None = None,
    iterations: int = 1000,
    threshold: float = 0.1,
    threads: int = 4,
    debug_seed: int = 42,
    cpdb_database: Path | None = None,
) -> dict[str, Path]:
    expression_path = processed_dir / "expression.csv"
    metadata_path = processed_dir / "metadata.csv"
    if not expression_path.exists():
        raise FileNotFoundError(f"CellPhoneDB requires cell-level expression.csv: {expression_path}")
    if not metadata_path.exists():
        raise FileNotFoundError(f"CellPhoneDB requires metadata.csv: {metadata_path}")
    output_dir.mkdir(parents=True, exist_ok=True)

    metadata = pd.read_csv(metadata_path)
    if cell_type_col not in metadata.columns:
        raise ValueError(f"metadata.csv must contain {cell_type_col!r}.")
    use_cells = metadata["cell_id"].astype(str).tolist()
    if max_cells is not None:
        use_cells = use_cells[:max_cells]
        metadata = metadata.loc[metadata["cell_id"].astype(str).isin(use_cells)].copy()

    expression = pd.read_csv(expression_path)
    expression["cell_id"] = expression["cell_id"].astype(str)
    expression = expression.loc[expression["cell_id"].isin(use_cells)].copy()
    expression = expression.set_index("cell_id").reindex(metadata["cell_id"].astype(str)).fillna(0.0)
    expression = expression.apply(pd.to_numeric, errors="coerce").fillna(0.0)

    meta_out = output_dir / "cellphonedb_meta.tsv"
    counts_out = output_dir / "cellphonedb_counts.tsv"
    command_out = output_dir / "cellphonedb_command.txt"
    metadata[["cell_id", cell_type_col]].rename(
        columns={"cell_id": "Cell", cell_type_col: "cell_type"}
    ).to_csv(meta_out, sep="\t", index=False)
    counts = expression.transpose()
    counts.index.name = "Gene"
    counts.to_csv(counts_out, sep="\t")
    database_arg = (
        f"--cpdb-file-path {cpdb_database.as_posix()} "
        if cpdb_database is not None
        else ""
    )
    command = (
        "cellphonedb method statistical_analysis "
        f"{meta_out.as_posix()} {counts_out.as_posix()} "
        f"--counts-data hgnc_symbol --iterations {iterations} "
        f"--threshold {threshold} --threads {threads} --debug-seed {debug_seed} "
        f"{database_arg}--score-interactions --output-path {output_dir.as_posix()}"
    )
    command_out.write_text(command + "\n", encoding="utf-8")
    return {"meta": meta_out, "counts": counts_out, "command": command_out}


def _full_run_completed_status(*, max_cells: int | None, iterations: int) -> str:
    """Keep smoke/subsample runs out of full comparator completion gates."""
    if max_cells is not None or iterations < 1000:
        return "smoke_completed_pending_full"
    return "completed_external_run_pending_import"


def _run_cellphonedb_api(
    *,
    cpdb_database: Path,
    meta_path: Path,
    counts_path: Path,
    output_dir: Path,
    iterations: int,
    threshold: float,
    threads: int,
    debug_seed: int,
    score_interactions: bool,
) -> dict[str, object]:
    """Run CellPhoneDB through its Python API when the CLI entrypoint is absent."""
    try:
        from cellphonedb.src.core.methods import cpdb_statistical_analysis_method
    except ImportError as exc:
        return {
            "status": "missing_cellphonedb_python_api",
            "error": repr(exc),
        }

    try:
        result = cpdb_statistical_analysis_method.call(
            cpdb_file_path=str(cpdb_database),
            meta_file_path=str(meta_path),
            counts_file_path=str(counts_path),
            counts_data="hgnc_symbol",
            output_path=str(output_dir),
            iterations=iterations,
            threshold=threshold,
            threads=threads,
            debug_seed=debug_seed,
            result_precision=3,
            pvalue=0.05,
            score_interactions=score_interactions,
            separator="|",
        )
    except Exception as exc:  # pragma: no cover - exercised in real optional envs
        return {
            "status": "failed",
            "error": repr(exc),
            "traceback_tail": traceback.format_exc()[-4000:],
        }

    return {
        "status": "completed",
        "api_result_keys": sorted(str(key) for key in result.keys())
        if isinstance(result, dict)
        else [],
    }


def run_cellphonedb(
    *,
    command_path: Path,
    meta_path: Path,
    counts_path: Path,
    output_dir: Path,
    run: bool,
    cpdb_database: Path | None = None,
    iterations: int = 1000,
    threshold: float = 0.1,
    threads: int = 4,
    debug_seed: int = 42,
    max_cells: int | None = None,
    api_fallback: bool = True,
    score_interactions: bool = True,
) -> dict[str, object]:
    executable = shutil.which("cellphonedb")
    metadata = {
        "tool": "CellPhoneDB",
        "status": "prepared_not_run",
        "cellphonedb_executable": executable or "",
        "execution_mode": "not_run",
        "command_path": str(command_path),
        "meta_path": str(meta_path),
        "counts_path": str(counts_path),
        "output_dir": str(output_dir),
        "cpdb_database": str(cpdb_database) if cpdb_database is not None else "",
        "iterations": iterations,
        "threshold": threshold,
        "threads": threads,
        "debug_seed": debug_seed,
        "max_cells": max_cells,
        "api_fallback": api_fallback,
        "score_interactions": score_interactions,
    }
    if not run:
        return metadata
    if executable is None:
        if api_fallback and cpdb_database is not None and cpdb_database.exists():
            api_metadata = _run_cellphonedb_api(
                cpdb_database=cpdb_database,
                meta_path=meta_path,
                counts_path=counts_path,
                output_dir=output_dir,
                iterations=iterations,
                threshold=threshold,
                threads=threads,
                debug_seed=debug_seed,
                score_interactions=score_interactions,
            )
            metadata.update(api_metadata)
            metadata["execution_mode"] = "python_api"
            if metadata["status"] == "completed":
                metadata["status"] = _full_run_completed_status(
                    max_cells=max_cells,
                    iterations=iterations,
                )
            return metadata
        metadata["status"] = "missing_cellphonedb_executable"
        metadata["execution_mode"] = "missing"
        return metadata
    command = command_path.read_text(encoding="utf-8").strip().split()
    completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=3600)
    metadata["execution_mode"] = "cli"
    metadata["status"] = (
        _full_run_completed_status(max_cells=max_cells, iterations=iterations)
        if completed.returncode == 0
        else "failed"
    )
    metadata["returncode"] = completed.returncode
    metadata["stdout_tail"] = completed.stdout[-4000:]
    metadata["stderr_tail"] = completed.stderr[-4000:]
    return metadata


def update_tool_comparison_status(
    *,
    results_dir: Path,
    dataset_id: str,
    metadata_path: Path,
    run_metadata: dict[str, object],
) -> Path:
    """Record CellPhoneDB run readiness in the shared comparator table."""
    output = results_dir / "tool_comparison.csv"
    if output.exists():
        table = pd.read_csv(output)
    else:
        table = pd.DataFrame()

    status = str(run_metadata.get("status", "unknown"))
    row = {
        "dataset_id": dataset_id,
        "tool": "CellPhoneDB",
        "status": status,
        "comparison_level": "cell_type_edge",
        "edge_score_table": "",
        "aligned_edge_table": "",
        "n_edges": pd.NA,
        "spearman_sheaf_energy_vs_tool_score": pd.NA,
        "sender_rank_spearman": pd.NA,
        "receiver_rank_spearman": pd.NA,
        "top_lr_jaccard": pd.NA,
        "high_sheaf_low_tool_edges": pd.NA,
        "high_tool_low_sheaf_edges": pd.NA,
        "concordant_high_edges": pd.NA,
        "unaligned_edges": pd.NA,
        "notes": f"CellPhoneDB run metadata recorded at {metadata_path.as_posix()}.",
    }
    if status == "missing_cellphonedb_executable":
        row["notes"] = (
            "CellPhoneDB input bundle was prepared, but the cellphonedb executable "
            f"was not found. Reproduce by rerunning {run_metadata.get('command_path', '')} "
            "after installing CellPhoneDB v5 in an isolated environment."
        )
    elif status == "prepared_not_run":
        row["notes"] = (
            "CellPhoneDB input bundle was prepared. Add --run after installing "
            "CellPhoneDB v5 to execute statistical_analysis."
        )
    elif status == "smoke_completed_pending_full":
        row["notes"] = (
            "CellPhoneDB statistical_analysis completed only for a smoke/subsample "
            "or <1000-iteration run. This is execution validation, not full "
            "reviewer-facing comparator evidence."
        )
    elif status == "completed_external_run_pending_import":
        row["notes"] = (
            "CellPhoneDB statistical_analysis completed; import significant_means "
            "with scripts/import_external_comparator.py --input-format cellphonedb."
        )

    if not table.empty and {"dataset_id", "tool", "status"}.issubset(table.columns):
        existing = table.loc[
            (table["dataset_id"].astype(str) == dataset_id)
            & (table["tool"].astype(str) == "CellPhoneDB")
        ]
        if not existing.empty and set(existing["status"]) == {"completed_external_import"}:
            return output
        table = table.loc[
            ~(
                (table["dataset_id"].astype(str) == dataset_id)
                & (table["tool"].astype(str) == "CellPhoneDB")
            )
        ].copy()

    columns = list(dict.fromkeys([*table.columns, *row.keys()]))
    frames = [
        table.reindex(columns=columns).dropna(axis=1, how="all"),
        pd.DataFrame([row]).reindex(columns=columns).dropna(axis=1, how="all"),
    ]
    updated = pd.concat(frames, ignore_index=True).reindex(columns=columns)
    updated.to_csv(output, index=False)
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--processed-dir", default=None)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--results-dir", default="benchmarks/results")
    parser.add_argument("--max-cells", type=int, default=None)
    parser.add_argument("--iterations", type=int, default=1000)
    parser.add_argument("--threshold", type=float, default=0.1)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--debug-seed", type=int, default=42)
    parser.add_argument(
        "--cpdb-database",
        default="data/external/cellphonedb_database/cellphonedb.zip",
    )
    parser.add_argument("--no-api-fallback", action="store_true")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args(argv)

    processed_dir = Path(args.processed_dir or f"data/processed/{args.dataset_id}")
    output_dir = Path(
        args.output_dir
        or f"benchmarks/results/{args.dataset_id}/comparators/cellphonedb_run"
    )
    paths = prepare_cellphonedb_inputs(
        processed_dir=processed_dir,
        output_dir=output_dir,
        max_cells=args.max_cells,
        iterations=args.iterations,
        threshold=args.threshold,
        threads=args.threads,
        debug_seed=args.debug_seed,
        cpdb_database=Path(args.cpdb_database) if args.cpdb_database else None,
    )
    metadata = run_cellphonedb(
        command_path=paths["command"],
        meta_path=paths["meta"],
        counts_path=paths["counts"],
        output_dir=output_dir,
        run=args.run,
        cpdb_database=Path(args.cpdb_database) if args.cpdb_database else None,
        iterations=args.iterations,
        threshold=args.threshold,
        threads=args.threads,
        debug_seed=args.debug_seed,
        max_cells=args.max_cells,
        api_fallback=not args.no_api_fallback,
    )
    metadata_path = output_dir / "cellphonedb_run_metadata.json"
    _write_json_atomic(metadata_path, metadata)
    tool_path = update_tool_comparison_status(
        results_dir=Path(args.results_dir),
        dataset_id=args.dataset_id,
        metadata_path=metadata_path,
        run_metadata=metadata,
    )
    for path in [*paths.values(), metadata_path, tool_path]:
        print(f"wrote {path.resolve()}")
    return 0 if metadata["status"] != "failed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
