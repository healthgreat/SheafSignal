#!/usr/bin/env python
"""Export compact inputs for external CCC comparator tools."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import pandas as pd

import _bootstrap  # noqa: F401
from sheafsignal.manifest import load_dataset_manifest, validate_dataset_manifest


def _require(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"Required comparator input source is missing: {path}")
    return path


def _write_readme(output_dir: Path, dataset_id: str) -> Path:
    readme = output_dir / "README.md"
    readme.write_text(
        "\n".join(
            [
                f"# External Comparator Inputs: {dataset_id}",
                "",
                "These files are compact, profile-level inputs for external",
                "cell-cell communication comparator tools. They are not raw",
                "single-cell matrices.",
                "",
                "## Files",
                "",
                "- `cell_type_profiles.csv`: cell type x selected genes mean expression.",
                "- `ligand_receptor_pairs.csv`: ligand-receptor pairs used by SheafSignal.",
                "- `cell_type_counts.csv`: cell type counts, including lesion strata when available.",
                "- `sheafsignal_edge_template.csv`: SheafSignal edge-level metrics for alignment.",
                "- `external_comparator_template.csv`: expected schema for imported external results.",
                "",
                "## External Result Schema",
                "",
                "Fill or export a table with at least these columns:",
                "",
                "```text",
                "sender,receiver,score",
                "```",
                "",
                "Optional ligand-receptor-level columns:",
                "",
                "```text",
                "ligand,receptor",
                "```",
                "",
                "Then align it with:",
                "",
                "```bash",
                "python scripts/import_external_comparator.py \\",
                f"  --dataset-id {dataset_id} \\",
                "  --tool LIANA \\",
                "  --input path/to/external_edges.csv \\",
                "  --sender-col sender \\",
                "  --receiver-col receiver \\",
                "  --score-col score",
                "```",
                "",
                "Interpretation boundary: external comparator scores represent",
                "communication intensity or tool-specific confidence, whereas",
                "SheafSignal `sheaf_energy` represents inconsistency between",
                "communication flow and pathway-state gradients.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return readme


def export_comparator_inputs(
    *,
    dataset_id: str,
    processed_dir: Path,
    benchmark_dir: Path,
    lr_db_path: Path,
    output_dir: Path,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    profiles_path = _require(processed_dir / "profiles.csv")
    lr_path = _require(lr_db_path)
    sheaf_edges_path = _require(benchmark_dir / "results" / "sheaf_energy_by_edge.csv")

    profiles_out = output_dir / "cell_type_profiles.csv"
    lr_out = output_dir / "ligand_receptor_pairs.csv"
    counts_out = output_dir / "cell_type_counts.csv"
    sheaf_template_out = output_dir / "sheafsignal_edge_template.csv"
    external_template_out = output_dir / "external_comparator_template.csv"

    shutil.copyfile(profiles_path, profiles_out)
    shutil.copyfile(lr_path, lr_out)

    if (processed_dir / "annotation_summary.csv").exists():
        counts = pd.read_csv(processed_dir / "annotation_summary.csv")
    elif (processed_dir / "metadata.csv").exists():
        metadata = pd.read_csv(processed_dir / "metadata.csv")
        group_cols = ["cell_type"]
        if "lesion_type" in metadata.columns:
            group_cols.append("lesion_type")
        counts = metadata.groupby(group_cols, dropna=False).size().reset_index(name="n_cells")
    else:
        profiles = pd.read_csv(profiles_path)
        counts = profiles[["cell_type"]].copy()
        counts["n_cells"] = pd.NA
    counts.to_csv(counts_out, index=False)

    sheaf_edges = pd.read_csv(sheaf_edges_path)
    sheaf_columns = [
        "sender",
        "receiver",
        "communication_flow",
        "sheaf_energy",
        "sheaf_mismatch",
        "flow_z",
        "pathway_gradient_z",
        "directional_agreement",
        "curl_component",
        "harmonic_component",
        "top_lr_pairs",
    ]
    present = [column for column in sheaf_columns if column in sheaf_edges.columns]
    sheaf_edges[present].to_csv(sheaf_template_out, index=False)

    pd.DataFrame(
        columns=[
            "tool",
            "sender",
            "receiver",
            "score",
            "ligand",
            "receptor",
            "source_file",
            "notes",
        ]
    ).to_csv(external_template_out, index=False)

    readme = _write_readme(output_dir, dataset_id)
    manifest = output_dir / "manifest.tsv"
    pd.DataFrame(
        [
            {
                "dataset_id": dataset_id,
                "file": path.name,
                "path": str(path),
                "purpose": purpose,
            }
            for path, purpose in [
                (profiles_out, "cell-type profile expression for external CCC tools"),
                (lr_out, "ligand-receptor database"),
                (counts_out, "cell-type count context"),
                (sheaf_template_out, "SheafSignal edge metrics for alignment"),
                (external_template_out, "expected external comparator schema"),
                (readme, "usage notes"),
            ]
        ]
    ).to_csv(manifest, sep="\t", index=False)

    return {
        "profiles": profiles_out,
        "ligand_receptor": lr_out,
        "counts": counts_out,
        "sheaf_template": sheaf_template_out,
        "external_template": external_template_out,
        "readme": readme,
        "manifest": manifest,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-id", default="gse154778_pdac_scrna")
    parser.add_argument("--all-completed-public", action="store_true")
    parser.add_argument("--manifest", default="metadata/datasets.tsv")
    parser.add_argument("--results-dir", default="benchmarks/results")
    parser.add_argument("--processed-dir", default=None)
    parser.add_argument("--benchmark-dir", default=None)
    parser.add_argument("--lr-db", default="metadata/tme_ligand_receptor.csv")
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args(argv)

    if args.all_completed_public:
        validate_dataset_manifest(args.manifest, require_public_downloads=False)
        manifest = load_dataset_manifest(args.manifest)
        exported = []
        for row in manifest.to_dict(orient="records"):
            dataset_id = str(row["dataset_id"])
            role = str(row.get("benchmark_role", ""))
            if not role.startswith("public_"):
                continue
            processed_dir = Path(str(row["prepared_expression"])).parent
            benchmark_dir = Path(args.results_dir) / dataset_id
            profile = processed_dir / "profiles.csv"
            sheaf_edges = benchmark_dir / "results" / "sheaf_energy_by_edge.csv"
            if not profile.exists() or not sheaf_edges.exists():
                continue
            output_dir = benchmark_dir / "comparator_inputs"
            paths = export_comparator_inputs(
                dataset_id=dataset_id,
                processed_dir=processed_dir,
                benchmark_dir=benchmark_dir,
                lr_db_path=Path(args.lr_db),
                output_dir=output_dir,
            )
            exported.append({"dataset_id": dataset_id, **{key: str(path) for key, path in paths.items()}})
            for path in paths.values():
                print(f"wrote {path.resolve()}")

        summary_path = Path(args.results_dir) / "comparator_input_exports.csv"
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(exported).to_csv(summary_path, index=False)
        print(f"wrote {summary_path.resolve()}")
        return 0

    dataset_id = args.dataset_id
    processed_dir = Path(args.processed_dir or f"data/processed/{dataset_id}")
    benchmark_dir = Path(args.benchmark_dir or f"benchmarks/results/{dataset_id}")
    output_dir = Path(args.output_dir or f"benchmarks/results/{dataset_id}/comparator_inputs")

    paths = export_comparator_inputs(
        dataset_id=dataset_id,
        processed_dir=processed_dir,
        benchmark_dir=benchmark_dir,
        lr_db_path=Path(args.lr_db),
        output_dir=output_dir,
    )
    for path in paths.values():
        print(f"wrote {path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
