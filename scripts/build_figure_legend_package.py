#!/usr/bin/env python
"""Build figure legends and source maps for the SheafSignal manuscript.

Author: SheafSignal contributors
Date: 2026-04-30
Purpose: generate evidence-linked main and supplementary figure legends for a
20-50 IF methods-manuscript route without inventing unsupported claims.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

OUTPUT_FILES = {
    "inventory": "00_figure_legend_inventory.tsv",
    "main_legends": "01_main_figure_legends.md",
    "supplementary_legends": "02_supplementary_figure_legends.md",
    "source_map": "03_figure_source_map.tsv",
    "claim_checklist": "04_figure_claim_boundary_checklist.tsv",
}


def _read_table(path: Path, sep: str = ",") -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, sep=sep)


def _write_text_atomic(path: Path, text: str) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def _write_table_atomic(path: Path, table: pd.DataFrame) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    table.to_csv(tmp_path, sep="\t", index=False)
    tmp_path.replace(path)


def _format_ratio(value: object) -> str:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(numeric):
        return "NA"
    return f"{float(numeric):.3f}"


def _component_sentence(component_recovery: pd.DataFrame) -> str:
    if component_recovery.empty:
        return "Component-recovery values are pending."
    parts = []
    for row in component_recovery.to_dict(orient="records"):
        scenario = str(row.get("scenario", "unknown"))
        parts.append(
            f"{scenario}: gradient {_format_ratio(row.get('gradient_ratio'))}, "
            f"curl {_format_ratio(row.get('curl_ratio'))}, "
            f"harmonic {_format_ratio(row.get('harmonic_ratio'))}"
        )
    return "; ".join(parts) + "."


def _public_dataset_sentence(public_summary: pd.DataFrame) -> str:
    if public_summary.empty:
        return "Public benchmark summary is pending."
    completed = public_summary.loc[
        (public_summary.get("status", pd.Series(dtype=str)).astype(str) == "completed")
        & (
            public_summary.get("dataset_id", pd.Series(dtype=str)).astype(str)
            != "demo_synthetic"
        )
    ].copy()
    if completed.empty:
        return "Public benchmark summary is pending."
    parts = []
    for row in completed.to_dict(orient="records"):
        parts.append(
            f"{row.get('dataset_id')} with {int(row.get('n_cell_types', 0))} "
            f"cell-type states, {int(row.get('n_edges', 0))} edges, "
            f"top source {row.get('top_frustration_cell_type')}"
        )
    return "; ".join(parts) + "."


def _myeloid_sentence(myeloid_summary: pd.DataFrame) -> str:
    if myeloid_summary.empty:
        return "GSE154778 Myeloid claim-readiness summary is pending."
    row = myeloid_summary.iloc[0].to_dict()
    return (
        "Myeloid passed the GSE154778 claim gate with "
        f"min lesion support of {int(row.get('min_lesion_n_cells', 0))} cells "
        f"and {int(row.get('min_lesion_n_samples', 0))} samples, "
        f"bootstrap top frequency {_format_ratio(row.get('bootstrap_top_frequency'))}, "
        f"primary frustration score {_format_ratio(row.get('primary_frustration_score'))}, "
        f"and metastatic frustration score {_format_ratio(row.get('metastatic_frustration_score'))}."
    )


def _comparator_sentence(tool_comparison: pd.DataFrame) -> str:
    if tool_comparison.empty:
        return "Comparator summary is pending."
    completed = tool_comparison.loc[
        tool_comparison.get("status", pd.Series(dtype=str))
        .astype(str)
        .str.startswith("completed")
    ].copy()
    completed = completed.loc[
        completed.get("dataset_id", pd.Series(dtype=str)).astype(str)
        != "demo_synthetic"
    ]
    if completed.empty:
        return "Comparator summary is pending."
    parts = []
    for tool, subset in completed.groupby("tool", sort=True):
        datasets = sorted(set(subset["dataset_id"].astype(str)))
        rho = pd.to_numeric(
            subset.get("spearman_sheaf_energy_vs_tool_score", pd.Series(dtype=float)),
            errors="coerce",
        ).dropna()
        if rho.empty:
            rho_text = "NA"
        else:
            rho_text = f"{float(rho.min()):.3f}-{float(rho.max()):.3f}"
        parts.append(f"{tool}: {len(datasets)} datasets, Spearman {rho_text}")
    return "; ".join(parts) + "."


def build_figure_inventory(
    figure_plan: pd.DataFrame, figure_manifest: pd.DataFrame
) -> pd.DataFrame:
    rows = []
    for row in figure_plan.to_dict(orient="records"):
        figure = str(row.get("figure", "unknown"))
        rows.append(
            {
                "display_item": figure,
                "item_type": "main" if figure.startswith("Figure") else "supplementary",
                "purpose": row.get("purpose", ""),
                "planned_source": row.get("source", ""),
                "plan_status": row.get("status", ""),
                "manifest_entries": "",
            }
        )
    if not figure_manifest.empty:
        main_entries = figure_manifest.loc[
            figure_manifest["figure_id"].astype(str).str.startswith("fig")
        ]
        supp_entries = figure_manifest.loc[
            figure_manifest["figure_id"].astype(str).str.startswith("supp")
        ]
        rows.append(
            {
                "display_item": "Generated main figure files",
                "item_type": "manifest",
                "purpose": "Main generated PDF files",
                "planned_source": "manuscript/figure_manifest.tsv",
                "plan_status": "generated_or_manifested",
                "manifest_entries": ";".join(
                    main_entries["figure_id"].astype(str).tolist()
                ),
            }
        )
        rows.append(
            {
                "display_item": "Supplementary figure and table files",
                "item_type": "manifest",
                "purpose": "Supplementary source files and generated QC figures",
                "planned_source": "manuscript/figure_manifest.tsv",
                "plan_status": "generated_or_manifested",
                "manifest_entries": ";".join(
                    supp_entries["figure_id"].astype(str).tolist()
                ),
            }
        )
    return pd.DataFrame(rows)


def build_main_legends(
    *,
    component_recovery: pd.DataFrame,
    public_summary: pd.DataFrame,
    myeloid_summary: pd.DataFrame,
    tool_comparison: pd.DataFrame,
) -> str:
    return f"""# Main Figure Legends Draft

## Figure 1. SheafSignal formulation of communication frustration.

Schematic of the SheafSignal workflow. Ligand-receptor evidence is represented
as a directed sender-receiver communication flow, receiver pathway state is
represented on graph nodes, and sheaf energy quantifies mismatch between the
edge signal and node-state transition. Hodge decomposition separates the flow
into gradient, curl and harmonic components. This figure supports the
mathematical-object claim only; it does not claim clinical utility or broad
superiority over existing communication tools.

Source evidence: `src/sheafsignal`, `manuscript/nature_methods_package/05_claim_evidence_map.tsv`,
`figures/publication_figure1_sheafsignal_concept.pdf`.

## Figure 2. Controlled recovery of Hodge communication components.

Simulation benchmark showing recovery of pre-specified gradient, curl,
harmonic and mixed flow structure. {_component_sentence(component_recovery)}
These simulations validate component separation under controlled settings and
should not be interpreted as biological validation.

Source evidence: `benchmarks/results/component_recovery.csv`,
`figures/publication_figure2_component_recovery.pdf`.

## Figure 3. Public tumor microenvironment benchmarks.

Summary of completed public tumor microenvironment benchmarks analyzed with
the same SheafSignal workflow. {_public_dataset_sentence(public_summary)}
The figure supports context-specific communication-frustration architecture
across public datasets, not a universal source-cell mechanism across all
cancers.

Source evidence: `benchmarks/results/public_tme_sheafsignal_summary.csv`,
`figures/publication_figure3_tme_summary.pdf`.

## Figure 4. GSE154778 Myeloid claim gating and robustness.

GSE154778 pancreatic cancer analysis with evidence-tier gating, lesion
stratification, annotation QC and sample-level robustness checks. {_myeloid_sentence(myeloid_summary)}
Sparse stromal and lymphoid categories remain supplementary/QC context and are
not used for main mechanistic claims.

Source evidence: `benchmarks/results/gse154778_pdac_scrna/qc/`,
`benchmarks/results/gse154778_pdac_scrna/stability/`,
`benchmarks/results/gse154778_pdac_scrna/stratified/`.

## Figure 5. Comparator alignment and complementarity.

Edge-level SheafSignal results are aligned against ligand-receptor product
baseline, LIANA, bounded nichenetr-engine scoring with a project-curated TME
prior, and MechanisticTargetPrior outputs. {_comparator_sentence(tool_comparison)}
This figure supports benchmarkability and complementarity; it must not be captioned as broad superiority over all cell-cell communication tools.

Source evidence: `benchmarks/results/tool_comparison.csv`,
`benchmarks/results/*/comparators/sheafsignal_vs_*.csv`.
"""


def build_supplementary_legends(figure_manifest: pd.DataFrame) -> str:
    lines = [
        "# Supplementary Figure And Table Legends Draft",
        "",
        "The following supplementary legends are generated from the current",
        "`manuscript/figure_manifest.tsv`. They are source-linked placeholders",
        "that should be edited only after final panel layout is frozen.",
        "",
    ]
    if figure_manifest.empty:
        lines.append("No supplementary manifest entries were found.")
        return "\n".join(lines) + "\n"

    for row in figure_manifest.to_dict(orient="records"):
        figure_id = str(row.get("figure_id", ""))
        if not figure_id.startswith("supp"):
            continue
        path = str(row.get("path", ""))
        source = str(row.get("source_results_dir", ""))
        title = figure_id.replace("supp_", "").replace("_", " ").title()
        lines.extend(
            [
                f"## {figure_id}",
                "",
                f"{title}. Source file: `{path}`. Source directory: `{source}`.",
                "Interpretation is restricted to the quality-control, benchmark,",
                "release, or manuscript-support role indicated by the file name;",
                "this supplementary item does not add a new clinical or",
                "therapeutic claim.",
                "",
            ]
        )
    return "\n".join(lines)


def build_source_map() -> pd.DataFrame:
    rows = [
        {
            "display_item": "Figure 1",
            "claim_ids": "C1",
            "source_files": "src/sheafsignal;manuscript/nature_methods_package/05_claim_evidence_map.tsv;figures/publication_figure1_sheafsignal_concept.pdf",
            "allowed_claim": "SheafSignal is a distinct sheaf/Hodge formulation of CCC.",
            "boundary": "Do not describe as only a new LR score or as clinical utility.",
            "main_text_allowed": True,
        },
        {
            "display_item": "Figure 2",
            "claim_ids": "C2",
            "source_files": "benchmarks/results/component_recovery.csv;figures/publication_figure2_component_recovery.pdf",
            "allowed_claim": "Gradient, curl and harmonic components are recoverable in controlled simulations.",
            "boundary": "Do not treat simulation as biological validation.",
            "main_text_allowed": True,
        },
        {
            "display_item": "Figure 3",
            "claim_ids": "C3",
            "source_files": "benchmarks/results/public_tme_sheafsignal_summary.csv;figures/publication_figure3_tme_summary.pdf",
            "allowed_claim": "Public tumor benchmarks show context-specific frustration architecture.",
            "boundary": "Do not generalize one source cell type across all cancers.",
            "main_text_allowed": True,
        },
        {
            "display_item": "Figure 4",
            "claim_ids": "C4;C5",
            "source_files": "benchmarks/results/gse154778_pdac_scrna/qc;benchmarks/results/gse154778_pdac_scrna/stability;benchmarks/results/gse154778_pdac_scrna/stratified;figures/publication_figure4_gse154778_claim_gating.pdf",
            "allowed_claim": "GSE154778 Myeloid is a claim-gated computational source signal.",
            "boundary": "Sparse categories remain supplement/QC and cannot be main mechanisms.",
            "main_text_allowed": True,
        },
        {
            "display_item": "Figure 5",
            "claim_ids": "C6",
            "source_files": "benchmarks/results/tool_comparison.csv;benchmarks/results/*/comparators/sheafsignal_vs_*.csv;figures/publication_figure5_comparator_alignment.pdf",
            "allowed_claim": "External comparator evidence exists and can be aligned.",
            "boundary": "Do not claim broad superiority over all CCC tools or full pretrained NicheNet benchmarking.",
            "main_text_allowed": True,
        },
        {
            "display_item": "Supplementary figures and tables",
            "claim_ids": "C5;C7",
            "source_files": "manuscript/figure_manifest.tsv;release/*;benchmarks/results/*/qc",
            "allowed_claim": "Supplementary material documents QC, release readiness and claim boundaries.",
            "boundary": "Supplementary QC items cannot create stronger biology claims than the main claim gate allows.",
            "main_text_allowed": False,
        },
    ]
    return pd.DataFrame(rows)


def build_claim_boundary_checklist(source_map: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in source_map.to_dict(orient="records"):
        rows.append(
            {
                "display_item": row["display_item"],
                "must_have_source": row["source_files"],
                "allowed_claim": row["allowed_claim"],
                "forbidden_or_limited_claim": row["boundary"],
                "requires_author_review_before_submission": True,
                "status": "draft_legend_source_linked",
            }
        )
    rows.extend(
        [
            {
                "display_item": "All figures",
                "must_have_source": "manuscript/figure_manifest.tsv",
                "allowed_claim": "Every visual item must map to a source table, script or generated figure.",
                "forbidden_or_limited_claim": "Do not add untracked panels or unsupported claims during manual figure assembly.",
                "requires_author_review_before_submission": True,
                "status": "global_rule",
            },
            {
                "display_item": "All captions",
                "must_have_source": "manuscript/nature_methods_package/05_claim_evidence_map.tsv",
                "allowed_claim": "Captions may restate only claims listed in the claim-evidence map.",
                "forbidden_or_limited_claim": "No clinical utility, treatment guidance, guaranteed acceptance, or broad CCC-tool superiority.",
                "requires_author_review_before_submission": True,
                "status": "global_rule",
            },
        ]
    )
    return pd.DataFrame(rows)


def build_package(
    *,
    output_dir: Path,
    figure_plan: pd.DataFrame,
    figure_manifest: pd.DataFrame,
    component_recovery: pd.DataFrame,
    public_summary: pd.DataFrame,
    myeloid_summary: pd.DataFrame,
    tool_comparison: pd.DataFrame,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {key: output_dir / name for key, name in OUTPUT_FILES.items()}
    inventory = build_figure_inventory(figure_plan, figure_manifest)
    source_map = build_source_map()
    claim_checklist = build_claim_boundary_checklist(source_map)
    _write_table_atomic(paths["inventory"], inventory)
    _write_text_atomic(
        paths["main_legends"],
        build_main_legends(
            component_recovery=component_recovery,
            public_summary=public_summary,
            myeloid_summary=myeloid_summary,
            tool_comparison=tool_comparison,
        ),
    )
    _write_text_atomic(
        paths["supplementary_legends"], build_supplementary_legends(figure_manifest)
    )
    _write_table_atomic(paths["source_map"], source_map)
    _write_table_atomic(paths["claim_checklist"], claim_checklist)
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="manuscript/figure_legends")
    parser.add_argument(
        "--figure-plan", default="manuscript/nature_methods_package/06_figure_plan.tsv"
    )
    parser.add_argument("--figure-manifest", default="manuscript/figure_manifest.tsv")
    parser.add_argument(
        "--component-recovery", default="benchmarks/results/component_recovery.csv"
    )
    parser.add_argument(
        "--public-summary",
        default="benchmarks/results/public_tme_sheafsignal_summary.csv",
    )
    parser.add_argument(
        "--myeloid-summary",
        default="benchmarks/results/gse154778_pdac_scrna/qc/myeloid_claim_readiness_summary.csv",
    )
    parser.add_argument(
        "--tool-comparison", default="benchmarks/results/tool_comparison.csv"
    )
    args = parser.parse_args(argv)

    paths = build_package(
        output_dir=Path(args.output_dir),
        figure_plan=_read_table(Path(args.figure_plan), sep="\t"),
        figure_manifest=_read_table(Path(args.figure_manifest), sep="\t"),
        component_recovery=_read_table(Path(args.component_recovery)),
        public_summary=_read_table(Path(args.public_summary)),
        myeloid_summary=_read_table(Path(args.myeloid_summary)),
        tool_comparison=_read_table(Path(args.tool_comparison)),
    )
    for path in paths.values():
        print(f"wrote {path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
