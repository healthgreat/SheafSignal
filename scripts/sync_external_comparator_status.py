#!/usr/bin/env python
"""Sync sidecar comparator run statuses into benchmarks/results/tool_comparison.csv."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


BASE_COLUMNS = [
    "dataset_id",
    "tool",
    "status",
    "comparison_level",
    "edge_score_table",
    "aligned_edge_table",
    "n_edges",
    "spearman_sheaf_energy_vs_tool_score",
    "sender_rank_spearman",
    "receiver_rank_spearman",
    "top_lr_jaccard",
    "high_sheaf_low_tool_edges",
    "high_tool_low_sheaf_edges",
    "concordant_high_edges",
    "unaligned_edges",
    "notes",
]


def _read_key_value_tsv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or "\t" not in line:
            continue
        key, value = line.split("\t", 1)
        values[key] = value
    return values


def _base_row(dataset_id: str, tool: str, status: str, notes: str) -> dict[str, object]:
    row: dict[str, object] = {column: pd.NA for column in BASE_COLUMNS}
    row.update(
        {
            "dataset_id": dataset_id,
            "tool": tool,
            "status": status,
            "comparison_level": "cell_type_edge",
            "edge_score_table": "",
            "aligned_edge_table": "",
            "notes": notes,
        }
    )
    return row


def cellchat_status_row(dataset_id: str, status_path: Path) -> dict[str, object]:
    status = _read_key_value_tsv(status_path)
    raw_status = status.get("status", "unknown")
    if raw_status == "missing_dependency":
        normalized = "missing_cellchat_dependency"
        notes = (
            "CellChat sidecar workflow was invoked, but R package CellChat was "
            f"not installed. Status file: {status_path.as_posix()}."
        )
    elif raw_status == "completed":
        normalized = "completed_external_run_pending_import"
        notes = (
            "CellChat workflow completed; import cellchat_communication.csv "
            "with scripts/import_external_comparator.py --input-format cellchat."
        )
    else:
        normalized = f"cellchat_{raw_status}"
        notes = f"CellChat sidecar status file: {status_path.as_posix()}."
    return _base_row(dataset_id, "CellChat", normalized, notes)


def cellphonedb_status_row(dataset_id: str, metadata_path: Path) -> dict[str, object]:
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    raw_status = str(metadata.get("status", "unknown"))
    if raw_status == "completed":
        normalized = "completed_external_run_pending_import"
        notes = (
            "CellPhoneDB statistical_analysis completed; import significant_means "
            "with scripts/import_external_comparator.py --input-format cellphonedb."
        )
    elif raw_status == "missing_cellphonedb_executable":
        normalized = raw_status
        notes = (
            "CellPhoneDB input bundle was prepared, but the cellphonedb executable "
            f"was not found. Metadata file: {metadata_path.as_posix()}."
        )
    else:
        normalized = raw_status
        notes = f"CellPhoneDB sidecar metadata file: {metadata_path.as_posix()}."
    return _base_row(dataset_id, "CellPhoneDB", normalized, notes)


def _upsert_rows(table: pd.DataFrame, rows: list[dict[str, object]]) -> pd.DataFrame:
    if table.empty:
        table = pd.DataFrame(columns=BASE_COLUMNS)
    columns = list(dict.fromkeys([*table.columns, *BASE_COLUMNS]))
    table = table.reindex(columns=columns)
    for row in rows:
        dataset_id = str(row["dataset_id"])
        tool = str(row["tool"])
        mask = (table["dataset_id"].astype(str) == dataset_id) & (table["tool"].astype(str) == tool)
        existing = table.loc[mask]
        if not existing.empty and set(existing["status"].astype(str)) == {"completed_external_import"}:
            continue
        table = table.loc[~mask].copy()
        row_frame = pd.DataFrame([row]).reindex(columns=columns)
        frames = [table.dropna(axis=1, how="all"), row_frame.dropna(axis=1, how="all")]
        table = pd.concat(frames, ignore_index=True).reindex(columns=columns)
    return table


def sync_external_comparator_statuses(results_dir: Path, dataset_ids: list[str] | None = None) -> Path:
    summary_path = results_dir / "public_tme_sheafsignal_summary.csv"
    if dataset_ids is None:
        summary = pd.read_csv(summary_path)
        dataset_ids = [
            str(value)
            for value in summary["dataset_id"].tolist()
            if str(value) != "demo_synthetic"
        ]

    rows = []
    for dataset_id in dataset_ids:
        comparator_dir = results_dir / dataset_id / "comparators"
        cellchat_status = comparator_dir / "cellchat_run" / "cellchat_run_status.tsv"
        if cellchat_status.exists():
            rows.append(cellchat_status_row(dataset_id, cellchat_status))
        cpdb_metadata = comparator_dir / "cellphonedb_run" / "cellphonedb_run_metadata.json"
        if cpdb_metadata.exists():
            rows.append(cellphonedb_status_row(dataset_id, cpdb_metadata))

    output = results_dir / "tool_comparison.csv"
    table = pd.read_csv(output) if output.exists() else pd.DataFrame()
    table = _upsert_rows(table, rows)
    table.to_csv(output, index=False)
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", default="benchmarks/results")
    parser.add_argument("--dataset-id", action="append", default=[])
    args = parser.parse_args(argv)

    output = sync_external_comparator_statuses(
        Path(args.results_dir),
        dataset_ids=args.dataset_id or None,
    )
    print(f"wrote {output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

