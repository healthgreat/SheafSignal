#!/usr/bin/env python
"""Run LIANA rank_aggregate and import it as an external CCC comparator.

Author: SheafSignal contributors
Date: 2026-04-29
Method reference: LIANA rank_aggregate, liana-py documentation.
Purpose: execute an external CCC comparator on processed public datasets and
align its cell-type edge scores with SheafSignal sheaf_energy.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

import _bootstrap  # noqa: F401
from import_external_comparator import import_external_comparator


def _atomic_write_csv(table: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    table.to_csv(tmp, index=False)
    tmp.replace(path)


def _atomic_write_json(payload: dict[str, object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def _read_expression(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing expression matrix: {path}")
    expression = pd.read_csv(path)
    if "cell_id" in expression.columns:
        expression = expression.set_index("cell_id")
    elif expression.columns[0].startswith("Unnamed"):
        expression = expression.set_index(expression.columns[0])
    expression.index = expression.index.astype(str)
    return expression


def _read_metadata(path: Path, cell_type_col: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing metadata table: {path}")
    metadata = pd.read_csv(path)
    if "cell_id" not in metadata.columns:
        raise ValueError("metadata.csv must contain a cell_id column for LIANA alignment")
    if cell_type_col not in metadata.columns:
        raise ValueError(f"metadata.csv is missing cell type column: {cell_type_col}")
    metadata = metadata.copy()
    metadata["cell_id"] = metadata["cell_id"].astype(str)
    metadata[cell_type_col] = metadata[cell_type_col].astype(str)
    return metadata


def load_liana_anndata(
    *,
    processed_dir: Path,
    cell_type_col: str,
    max_cells: int | None = None,
    seed: int = 42,
):
    """Load SheafSignal processed CSV files into AnnData for LIANA."""
    try:
        import anndata as ad
    except ImportError as exc:  # pragma: no cover - depends on optional environment
        raise RuntimeError(
            "AnnData is required for LIANA comparator runs. Install the external "
            "comparator environment with: conda env create -f envs/liana_environment.yml"
        ) from exc

    expression = _read_expression(processed_dir / "expression.csv")
    metadata = _read_metadata(processed_dir / "metadata.csv", cell_type_col=cell_type_col)
    input_summary: dict[str, int | float | bool] = {
        "n_expression_cells_read": int(expression.shape[0]),
        "n_metadata_cells_read": int(metadata.shape[0]),
        "n_expression_genes_read": int(expression.shape[1]),
        "max_cells_applied": max_cells is not None,
    }

    common = metadata.loc[metadata["cell_id"].isin(expression.index), "cell_id"].tolist()
    if not common:
        raise ValueError("No overlapping cell_id values between expression.csv and metadata.csv")
    metadata = metadata.set_index("cell_id").loc[common].copy()
    expression = expression.loc[common].copy()
    input_summary["n_common_cells_before_sampling"] = int(len(common))

    if max_cells is not None and len(metadata) > max_cells:
        rng = np.random.default_rng(seed)
        selected: list[str] = []
        grouped = metadata.groupby(cell_type_col, sort=True)
        per_group = max(1, max_cells // max(1, grouped.ngroups))
        for _, group in grouped:
            cells = group.index.to_numpy()
            n_take = min(len(cells), per_group)
            selected.extend(rng.choice(cells, size=n_take, replace=False).tolist())
        if len(selected) < max_cells:
            remaining = metadata.index.difference(selected).to_numpy()
            n_extra = min(max_cells - len(selected), len(remaining))
            if n_extra > 0:
                selected.extend(rng.choice(remaining, size=n_extra, replace=False).tolist())
        selected = selected[:max_cells]
        metadata = metadata.loc[selected].copy()
        expression = expression.loc[selected].copy()
    input_summary["n_cells_after_sampling"] = int(len(metadata))

    numeric = expression.apply(pd.to_numeric, errors="coerce").fillna(0.0)
    adata = ad.AnnData(
        X=numeric.to_numpy(dtype=np.float32),
        obs=metadata,
        var=pd.DataFrame(index=numeric.columns.astype(str)),
    )
    adata.obs_names = metadata.index.astype(str)
    adata.var_names = numeric.columns.astype(str)
    adata.obs_names_make_unique()
    adata.var_names_make_unique()
    adata.uns["sheafsignal_liana_input_summary"] = input_summary
    return adata


def run_liana_rank_aggregate(
    adata,
    *,
    groupby: str,
    resource_name: str,
    expr_prop: float,
    min_cells: int,
    n_perms: int | None,
    seed: int,
    n_jobs: int,
) -> pd.DataFrame:
    """Execute LIANA rank_aggregate and return adata.uns['liana_res']."""
    try:
        import liana as li
    except ImportError as exc:  # pragma: no cover - depends on optional environment
        raise RuntimeError(
            "LIANA is not installed. Create the reproducible comparator environment with: "
            "conda env create -f envs/liana_environment.yml"
        ) from exc

    rank_aggregate = getattr(getattr(li, "mt", None), "rank_aggregate", None)
    if rank_aggregate is None:
        rank_aggregate = getattr(getattr(li, "method", None), "rank_aggregate", None)
    if rank_aggregate is None:
        raise RuntimeError("Installed liana package does not expose rank_aggregate")

    rank_aggregate(
        adata,
        groupby=groupby,
        resource_name=resource_name,
        expr_prop=expr_prop,
        min_cells=min_cells,
        use_raw=False,
        n_perms=n_perms,
        seed=seed,
        n_jobs=n_jobs,
        inplace=True,
        verbose=True,
    )
    if "liana_res" not in adata.uns:
        raise RuntimeError("LIANA completed without writing adata.uns['liana_res']")
    return adata.uns["liana_res"].copy()


def standardize_liana_edges(liana_res: pd.DataFrame) -> pd.DataFrame:
    """Convert LIANA output to SheafSignal's external comparator schema.

    LIANA rank fields are lower-is-better. For edge-level alignment with
    SheafSignal, this exports a higher-is-stronger score as 1 - rank.
    """
    if liana_res.empty:
        raise ValueError("LIANA result table is empty")
    required = {"source", "target"}
    missing = required.difference(liana_res.columns)
    if missing:
        raise ValueError(f"LIANA result is missing columns: {sorted(missing)}")

    score_col = None
    for candidate in ["magnitude_rank", "aggregate_rank", "specificity_rank"]:
        if candidate in liana_res.columns:
            score_col = candidate
            break
    if score_col is None:
        raise ValueError(
            "LIANA result must contain one of magnitude_rank, aggregate_rank, "
            "or specificity_rank"
        )

    ligand_col = "ligand_complex" if "ligand_complex" in liana_res.columns else "ligand"
    receptor_col = (
        "receptor_complex" if "receptor_complex" in liana_res.columns else "receptor"
    )
    out = pd.DataFrame(
        {
            "tool": "LIANA",
            "sender": liana_res["source"].astype(str),
            "receiver": liana_res["target"].astype(str),
            "score": 1.0 - pd.to_numeric(liana_res[score_col], errors="coerce"),
            "ligand": (
                liana_res[ligand_col].astype(str) if ligand_col in liana_res.columns else ""
            ),
            "receptor": (
                liana_res[receptor_col].astype(str)
                if receptor_col in liana_res.columns
                else ""
            ),
            "source_file": "liana_raw_results.csv",
            "notes": f"score=1-{score_col}; LIANA lower ranks indicate stronger interactions",
        }
    )
    return out.dropna(subset=["sender", "receiver", "score"]).reset_index(drop=True)


def run_liana_comparator(
    *,
    dataset_id: str,
    processed_dir: Path,
    benchmark_dir: Path,
    results_dir: Path,
    output_dir: Path,
    cell_type_col: str,
    resource_name: str,
    expr_prop: float,
    min_cells: int,
    n_perms: int | None,
    seed: int,
    n_jobs: int,
    max_cells: int | None,
) -> dict[str, Path]:
    adata = load_liana_anndata(
        processed_dir=processed_dir,
        cell_type_col=cell_type_col,
        max_cells=max_cells,
        seed=seed,
    )
    raw = run_liana_rank_aggregate(
        adata,
        groupby=cell_type_col,
        resource_name=resource_name,
        expr_prop=expr_prop,
        min_cells=min_cells,
        n_perms=n_perms,
        seed=seed,
        n_jobs=n_jobs,
    )
    liana_edges = standardize_liana_edges(raw)

    raw_path = output_dir / "liana_raw_results.csv"
    external_path = output_dir / "liana_external_edges.csv"
    metadata_path = output_dir / "liana_run_metadata.json"
    _atomic_write_csv(raw, raw_path)
    _atomic_write_csv(liana_edges, external_path)
    _atomic_write_json(
        {
            "dataset_id": dataset_id,
            "processed_dir": str(processed_dir),
            "cell_type_col": cell_type_col,
            "resource_name": resource_name,
            "expr_prop": expr_prop,
            "min_cells": min_cells,
            "n_perms": n_perms,
            "seed": seed,
            "n_jobs": n_jobs,
            "max_cells": max_cells,
            "n_cells_used": int(adata.n_obs),
            "n_genes_used": int(adata.n_vars),
            **adata.uns.get("sheafsignal_liana_input_summary", {}),
        },
        metadata_path,
    )

    imported = import_external_comparator(
        dataset_id=dataset_id,
        tool="LIANA",
        input_path=external_path,
        benchmark_dir=benchmark_dir,
        results_dir=results_dir,
        sender_col="sender",
        receiver_col="receiver",
        score_col="score",
        ligand_col="ligand",
        receptor_col="receptor",
        aggregate="max",
        score_ascending=False,
    )
    return {
        "liana_raw": raw_path,
        "liana_external_edges": external_path,
        "liana_metadata": metadata_path,
        **imported,
    }


def _optional_int(value: str) -> int | None:
    if value.lower() in {"none", "null", "na"}:
        return None
    return int(value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--processed-dir", default=None)
    parser.add_argument("--benchmark-dir", default=None)
    parser.add_argument("--results-dir", default="benchmarks/results")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--cell-type-col", default="cell_type")
    parser.add_argument("--resource-name", default="consensus")
    parser.add_argument("--expr-prop", type=float, default=0.1)
    parser.add_argument("--min-cells", type=int, default=5)
    parser.add_argument("--n-perms", type=_optional_int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--n-jobs", type=int, default=1)
    parser.add_argument("--max-cells", type=_optional_int, default=None)
    args = parser.parse_args(argv)

    dataset_id = args.dataset_id
    processed_dir = Path(args.processed_dir or f"data/processed/{dataset_id}")
    benchmark_dir = Path(args.benchmark_dir or f"benchmarks/results/{dataset_id}")
    output_dir = Path(args.output_dir or benchmark_dir / "comparators" / "liana_run")

    paths = run_liana_comparator(
        dataset_id=dataset_id,
        processed_dir=processed_dir,
        benchmark_dir=benchmark_dir,
        results_dir=Path(args.results_dir),
        output_dir=output_dir,
        cell_type_col=args.cell_type_col,
        resource_name=args.resource_name,
        expr_prop=args.expr_prop,
        min_cells=args.min_cells,
        n_perms=args.n_perms,
        seed=args.seed,
        n_jobs=args.n_jobs,
        max_cells=args.max_cells,
    )
    for path in paths.values():
        print(f"wrote {path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
