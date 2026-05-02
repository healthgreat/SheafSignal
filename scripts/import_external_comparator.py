#!/usr/bin/env python
"""Import and align external CCC comparator results with SheafSignal edges."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd

import _bootstrap  # noqa: F401
from sheafsignal.comparators import (
    align_sheaf_edges_with_comparator,
    comparator_summary,
    standardize_cellchat_edges,
    standardize_cellphonedb_edges,
    standardize_external_comparator_edges,
)


def tool_slug(tool: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", tool.strip()).strip("_").lower()
    if not slug:
        raise ValueError("tool name must contain at least one alphanumeric character")
    return slug


def _read_table(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in {".tsv", ".txt"}:
        return pd.read_csv(path, sep="\t")
    return pd.read_csv(path)


def _update_tool_comparison(
    *,
    results_dir: Path,
    row: dict[str, object],
) -> Path:
    output = results_dir / "tool_comparison.csv"
    if output.exists():
        table = pd.read_csv(output)
    else:
        table = pd.DataFrame()

    keys = ["dataset_id", "tool"]
    for key in keys:
        if key not in table.columns:
            table[key] = pd.Series(dtype=object)

    keep = ~(
        (table["dataset_id"].astype(str) == str(row["dataset_id"]))
        & (table["tool"].astype(str) == str(row["tool"]))
    )
    table = table.loc[keep].copy()
    table = pd.concat([table, pd.DataFrame([row])], ignore_index=True, sort=False)
    table.to_csv(output, index=False)
    return output


def import_external_comparator(
    *,
    dataset_id: str,
    tool: str,
    input_path: Path,
    benchmark_dir: Path,
    results_dir: Path,
    sender_col: str,
    receiver_col: str,
    score_col: str,
    ligand_col: str | None,
    receptor_col: str | None,
    aggregate: str,
    score_ascending: bool,
    input_format: str = "generic",
) -> dict[str, Path]:
    sheaf_edge_path = benchmark_dir / "results" / "sheaf_energy_by_edge.csv"
    if not sheaf_edge_path.exists():
        raise FileNotFoundError(f"Missing SheafSignal edge table: {sheaf_edge_path}")

    external = _read_table(input_path)
    if input_format == "cellchat":
        standardized = standardize_cellchat_edges(external)
    elif input_format == "cellphonedb":
        standardized = standardize_cellphonedb_edges(external)
    else:
        standardized = standardize_external_comparator_edges(
            external,
            tool=tool,
            sender_col=sender_col,
            receiver_col=receiver_col,
            score_col=score_col,
            ligand_col=ligand_col,
            receptor_col=receptor_col,
            aggregate=aggregate,
            score_ascending=score_ascending,
        )

    sheaf_edges = pd.read_csv(sheaf_edge_path)
    aligned = align_sheaf_edges_with_comparator(sheaf_edges, standardized, tool=tool)
    summary = comparator_summary(aligned)

    comparator_dir = benchmark_dir / "comparators"
    comparator_dir.mkdir(parents=True, exist_ok=True)
    slug = tool_slug(tool)
    standardized_path = comparator_dir / f"{slug}_edges.csv"
    aligned_path = comparator_dir / f"sheafsignal_vs_{slug}.csv"

    standardized.insert(0, "dataset_id", dataset_id)
    aligned.insert(0, "dataset_id", dataset_id)
    standardized.to_csv(standardized_path, index=False)
    aligned.to_csv(aligned_path, index=False)

    tool_table_path = _update_tool_comparison(
        results_dir=results_dir,
        row={
            "dataset_id": dataset_id,
            "tool": tool,
            "status": "completed_external_import",
            "comparison_level": "cell_type_edge",
            "edge_score_table": str(standardized_path),
            "aligned_edge_table": str(aligned_path),
            "notes": (
                f"Imported external comparator from {input_path}; "
                f"format={input_format}, sender={sender_col}, receiver={receiver_col}, "
                f"score={score_col}, aggregate={aggregate}."
            ),
            **summary,
        },
    )

    return {
        "standardized": standardized_path,
        "aligned": aligned_path,
        "tool_comparison": tool_table_path,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--tool", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--benchmark-dir", default=None)
    parser.add_argument("--results-dir", default="benchmarks/results")
    parser.add_argument("--sender-col", default="sender")
    parser.add_argument("--receiver-col", default="receiver")
    parser.add_argument("--score-col", default="score")
    parser.add_argument("--ligand-col", default=None)
    parser.add_argument("--receptor-col", default=None)
    parser.add_argument("--aggregate", default="max", choices=["sum", "mean", "max"])
    parser.add_argument("--score-ascending", action="store_true")
    parser.add_argument(
        "--input-format",
        default="generic",
        choices=["generic", "cellchat", "cellphonedb"],
    )
    args = parser.parse_args(argv)

    dataset_id = args.dataset_id
    benchmark_dir = Path(args.benchmark_dir or f"benchmarks/results/{dataset_id}")
    paths = import_external_comparator(
        dataset_id=dataset_id,
        tool=args.tool,
        input_path=Path(args.input),
        benchmark_dir=benchmark_dir,
        results_dir=Path(args.results_dir),
        sender_col=args.sender_col,
        receiver_col=args.receiver_col,
        score_col=args.score_col,
        ligand_col=args.ligand_col,
        receptor_col=args.receptor_col,
        aggregate=args.aggregate,
        score_ascending=args.score_ascending,
        input_format=args.input_format,
    )
    for path in paths.values():
        print(f"wrote {path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
