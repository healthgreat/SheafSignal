#!/usr/bin/env python
"""Prepare public benchmark datasets into the SheafSignal CSV schema.

The script is intentionally conservative. It creates the CI/demo prepared
dataset automatically and records clear statuses for large public datasets.
Dataset-specific converters should be added after each raw file is downloaded
and inspected.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import pandas as pd

import _bootstrap  # noqa: F401
from sheafsignal.adapters import (
    prepare_gse154778_pdac,
    prepare_gse154778_pdac_profiles,
    prepare_gse103322_hnsc_profiles,
    prepare_gse176078_brca_profiles,
    prepare_gse72056_melanoma_profiles,
    prepare_tenx_breast_visium,
)
from sheafsignal.manifest import load_dataset_manifest, validate_dataset_manifest


def _copy_demo_dataset(root: Path, output_dir: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    expression = output_dir / "expression.csv"
    metadata = output_dir / "metadata.csv"
    shutil.copyfile(root / "examples" / "demo_expression.csv", expression)
    shutil.copyfile(root / "examples" / "demo_metadata.csv", metadata)
    return {
        "status": "prepared",
        "prepared_expression": str(expression),
        "prepared_metadata": str(metadata),
        "message": "Copied synthetic CI demo into processed schema.",
    }


def _split_optional_list(value: object) -> list[str]:
    text = str(value).strip()
    if text.upper() in {"", "NA", "N/A", "NAN", "NONE", "NULL"}:
        return []
    return [item.strip() for item in text.split(";") if item.strip()]


def _status_for_public_row(
    row: dict[str, object],
    max_cells: int | None = None,
    marker_margin: float = 0.05,
    force: bool = False,
    profile_only: bool = False,
    chunksize: int = 2000,
    write_selected_expression: bool = False,
) -> dict[str, object]:
    expression = Path(str(row["prepared_expression"]))
    metadata = Path(str(row["prepared_metadata"]))
    profile = expression.parent / "profiles.csv"
    summary = expression.parent / "annotation_summary.csv"
    raw_path = Path(str(row["local_path"]))
    aux_paths = [Path(path) for path in _split_optional_list(row.get("aux_local_paths", ""))]

    needs_selected_expression = write_selected_expression and not expression.exists()
    if profile_only and profile.exists() and metadata.exists() and not force and not needs_selected_expression:
        return {
            "status": "profile_prepared_exists",
            "prepared_expression": str(expression),
            "prepared_profile": str(profile),
            "prepared_metadata": str(metadata),
            "annotation_summary": str(summary),
            "message": "Prepared profile files already exist.",
        }

    if expression.exists() and metadata.exists() and not force:
        return {
            "status": "prepared_exists",
            "prepared_expression": str(expression),
            "prepared_profile": str(profile) if profile.exists() else "",
            "prepared_metadata": str(metadata),
            "message": "Prepared CSV files already exist.",
        }

    if not raw_path.exists():
        return {
            "status": "missing_raw_download",
            "prepared_expression": str(expression),
            "prepared_profile": str(profile),
            "prepared_metadata": str(metadata),
            "annotation_summary": str(summary),
            "n_cells": pd.NA,
            "n_genes": pd.NA,
            "n_cell_types": pd.NA,
            "message": f"Run scripts/download_public_datasets.py before preparing {row['dataset_id']}.",
        }

    if str(row["dataset_id"]) == "tenx_breast_visium":
        if not aux_paths or not aux_paths[0].exists():
            return {
                "status": "missing_raw_download",
                "prepared_expression": str(expression),
                "prepared_profile": str(profile),
                "prepared_metadata": str(metadata),
                "annotation_summary": str(summary),
                "n_cells": pd.NA,
                "n_genes": pd.NA,
                "n_cell_types": pd.NA,
                "message": "Run scripts/download_public_datasets.py before preparing Visium spatial bundle.",
            }
        return prepare_tenx_breast_visium(
            h5_path=raw_path,
            spatial_tar_path=aux_paths[0],
            expression_out=expression,
            metadata_out=metadata,
            profile_out=profile,
            summary_out=summary,
            lr_db_path="metadata/tme_ligand_receptor.csv",
            gene_set_path="metadata/tme_pathway_genes.txt",
            marker_margin=marker_margin,
        )

    if str(row["dataset_id"]) == "gse154778_pdac_scrna":
        if profile_only:
            result = prepare_gse154778_pdac_profiles(
                raw_path=raw_path,
                profile_out=profile,
                metadata_out=metadata,
                summary_out=summary,
                lr_db_path="metadata/tme_ligand_receptor.csv",
                gene_set_path="metadata/tme_pathway_genes.txt",
                expression_out=expression if write_selected_expression else None,
                max_cells=max_cells,
                marker_margin=marker_margin,
                chunksize=chunksize,
            )
            result["prepared_expression"] = str(expression)
            return result
        return prepare_gse154778_pdac(
            raw_path=raw_path,
            expression_out=expression,
            metadata_out=metadata,
            max_cells=max_cells,
            marker_margin=marker_margin,
        )

    if str(row["dataset_id"]) == "gse72056_melanoma_scrna":
        result = prepare_gse72056_melanoma_profiles(
            raw_path=raw_path,
            profile_out=profile,
            metadata_out=metadata,
            summary_out=summary,
            lr_db_path="metadata/tme_ligand_receptor.csv",
            gene_set_path="metadata/tme_pathway_genes.txt",
            expression_out=expression if write_selected_expression else None,
            max_cells=max_cells,
            chunksize=chunksize,
        )
        result["prepared_expression"] = str(expression)
        return result

    if str(row["dataset_id"]) == "gse176078_brca_scrna":
        result = prepare_gse176078_brca_profiles(
            raw_path=raw_path,
            profile_out=profile,
            metadata_out=metadata,
            summary_out=summary,
            lr_db_path="metadata/tme_ligand_receptor.csv",
            gene_set_path="metadata/tme_pathway_genes.txt",
            expression_out=expression if write_selected_expression else None,
            max_cells=max_cells,
        )
        result["prepared_expression"] = str(expression)
        return result

    if str(row["dataset_id"]) == "gse103322_hnsc_scrna":
        result = prepare_gse103322_hnsc_profiles(
            raw_path=raw_path,
            profile_out=profile,
            metadata_out=metadata,
            summary_out=summary,
            lr_db_path="metadata/tme_ligand_receptor.csv",
            gene_set_path="metadata/tme_pathway_genes.txt",
            expression_out=expression if write_selected_expression else None,
            max_cells=max_cells,
            chunksize=chunksize,
        )
        result["prepared_expression"] = str(expression)
        return result

    return {
        "status": "raw_found_adapter_pending",
        "prepared_expression": str(expression),
        "prepared_profile": str(profile),
        "prepared_metadata": str(metadata),
        "annotation_summary": str(summary),
        "n_cells": pd.NA,
        "n_genes": pd.NA,
        "n_cell_types": pd.NA,
        "message": (
            "Raw file exists, but this dataset needs a dataset-specific adapter "
            "before publication-scale benchmarking."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="metadata/datasets.tsv")
    parser.add_argument("--results-dir", default="benchmarks/results")
    parser.add_argument("--dataset-id", action="append", default=[])
    parser.add_argument("--include-demo", action="store_true")
    parser.add_argument("--max-cells", type=int, default=None)
    parser.add_argument("--marker-margin", type=float, default=0.05)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--profile-only", action="store_true")
    parser.add_argument("--chunksize", type=int, default=2000)
    parser.add_argument(
        "--write-selected-expression",
        action="store_true",
        help=(
            "For profile-first adapters such as GSE72056/GSE176078, also write "
            "selected-gene cell-level expression.csv for external tools such as LIANA."
        ),
    )
    args = parser.parse_args(argv)

    root = Path.cwd()
    validate_dataset_manifest(args.manifest, require_public_downloads=False)
    manifest = load_dataset_manifest(args.manifest)
    selected = set(args.dataset_id)

    rows = []
    for row in manifest.to_dict(orient="records"):
        dataset_id = str(row["dataset_id"])
        role = str(row.get("benchmark_role", ""))
        if selected and dataset_id not in selected:
            continue
        if dataset_id == "demo_synthetic" and not args.include_demo and not selected:
            continue

        if dataset_id == "demo_synthetic":
            status = _copy_demo_dataset(root, Path("data/processed/demo_synthetic"))
        elif role.startswith("public_"):
            status = _status_for_public_row(
                row,
                max_cells=args.max_cells,
                marker_margin=args.marker_margin,
                force=args.force,
                profile_only=args.profile_only,
                chunksize=args.chunksize,
                write_selected_expression=args.write_selected_expression,
            )
        else:
            status = {
                "status": "skipped",
                "prepared_expression": str(row.get("prepared_expression", "")),
                "prepared_metadata": str(row.get("prepared_metadata", "")),
                "message": "Dataset role is not part of the public benchmark.",
            }

        rows.append(
            {
                "dataset_id": dataset_id,
                "benchmark_role": role,
                "modality": row.get("modality", ""),
                "disease": row.get("disease", ""),
                **status,
            }
        )

    results_dir = Path(args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    output = results_dir / "public_dataset_preparation_plan.csv"
    pd.DataFrame(rows).to_csv(output, index=False)
    print(f"wrote {output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
