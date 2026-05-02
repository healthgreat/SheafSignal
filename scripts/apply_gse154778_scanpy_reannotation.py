#!/usr/bin/env python
"""Freeze full Scanpy GSE154778 reannotation into SheafSignal prepared inputs."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

import _bootstrap  # noqa: F401
from sheafsignal.core import make_cell_type_profiles, normalize_expression
from sheafsignal.io import read_expression


def _write_csv_atomic(frame: pd.DataFrame, path: Path, *, index: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    frame.to_csv(tmp_path, index=index)
    tmp_path.replace(path)


def freeze_scanpy_reannotation(
    *,
    expression_path: Path,
    scanpy_annotations_path: Path,
    output_dir: Path,
) -> dict[str, Path]:
    expression = read_expression(expression_path)
    annotations = pd.read_csv(scanpy_annotations_path)
    if "cell_id" not in annotations.columns:
        raise ValueError("Scanpy annotations must contain cell_id.")
    if "scanpy_reannotated_cell_type" not in annotations.columns:
        raise ValueError("Scanpy annotations must contain scanpy_reannotated_cell_type.")

    annotations["cell_id"] = annotations["cell_id"].astype(str)
    annotations = annotations.drop_duplicates("cell_id").set_index("cell_id")
    common = expression.index.astype(str).intersection(annotations.index.astype(str))
    if len(common) == 0:
        raise ValueError("No overlapping cell IDs between expression and Scanpy annotations.")

    expression = expression.loc[common].copy()
    metadata = annotations.loc[common].copy()
    metadata.insert(0, "cell_id", common)
    metadata["cell_type"] = metadata["scanpy_reannotated_cell_type"].astype(str)
    if "annotation_version" not in metadata.columns:
        metadata["annotation_version"] = "scanpy_full_v1"
    score_cols = [column for column in metadata.columns if column.startswith("score_")]
    if score_cols:
        scores = metadata[score_cols].apply(pd.to_numeric, errors="coerce").fillna(0.0)
        ordered = scores.apply(lambda row: row.sort_values(ascending=False).to_numpy(), axis=1)
        metadata["marker_score"] = [float(values[0]) if len(values) else 0.0 for values in ordered]
        metadata["marker_score_margin"] = [
            float(values[0] - values[1]) if len(values) > 1 else float(values[0])
            for values in ordered
        ]
    elif {"coarse_marker_score", "coarse_marker_score_margin"}.issubset(metadata.columns):
        metadata["marker_score"] = metadata["coarse_marker_score"]
        metadata["marker_score_margin"] = metadata["coarse_marker_score_margin"]
    else:
        metadata["marker_score"] = 0.0
        metadata["marker_score_margin"] = 0.0

    front = [
        "cell_id",
        "cell_type",
        "sample_id",
        "lesion_type",
        "annotation_version",
        "marker_score",
        "marker_score_margin",
    ]
    columns = [column for column in front if column in metadata.columns]
    columns.extend(column for column in metadata.columns if column not in columns)
    metadata = metadata[columns]

    normalized = normalize_expression(expression, method="cpm_log1p")
    profile_result = make_cell_type_profiles(
        normalized,
        metadata.set_index("cell_id"),
        cell_type_col="cell_type",
    )
    summary = (
        metadata.groupby(["cell_type", "lesion_type"], dropna=False)
        .size()
        .reset_index(name="n_cells")
    )
    sample_support = (
        metadata.groupby("cell_type", dropna=False)["sample_id"]
        .nunique()
        .reset_index(name="n_samples")
    )
    summary = summary.merge(sample_support, on="cell_type", how="left")
    summary.insert(0, "annotation_version", metadata["annotation_version"].iloc[0])

    paths = {
        "expression": output_dir / "expression.csv",
        "metadata": output_dir / "metadata.csv",
        "profiles": output_dir / "profiles.csv",
        "annotation_summary": output_dir / "annotation_summary.csv",
    }
    _write_csv_atomic(expression.reset_index().rename(columns={"index": "cell_id"}), paths["expression"])
    _write_csv_atomic(metadata.reset_index(drop=True), paths["metadata"])
    _write_csv_atomic(profile_result.profiles, paths["profiles"], index=True)
    _write_csv_atomic(summary, paths["annotation_summary"])
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--expression-path",
        default="data/processed/gse154778_pdac_scrna/expression.csv",
    )
    parser.add_argument(
        "--scanpy-annotations-path",
        default="benchmarks/results/gse154778_pdac_scrna/reannotation/scanpy_cell_annotations.csv",
    )
    parser.add_argument(
        "--output-dir",
        default="data/processed/gse154778_pdac_scrna_scanpy_full_v1",
    )
    args = parser.parse_args(argv)
    paths = freeze_scanpy_reannotation(
        expression_path=Path(args.expression_path),
        scanpy_annotations_path=Path(args.scanpy_annotations_path),
        output_dir=Path(args.output_dir),
    )
    for path in paths.values():
        print(f"wrote {path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
