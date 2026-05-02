#!/usr/bin/env python
"""Build a Nature Methods presubmission inquiry and desk-reject risk package.

Author: SheafSignal contributors
Date: 2026-04-30
Purpose: prepare editor-facing materials that summarize novelty, evidence,
claim boundaries and residual risks before a high-impact submission.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


OUTPUT_FILES = {
    "one_page_summary": "00_one_page_editor_summary.md",
    "inquiry_letter": "01_presubmission_inquiry_letter.md",
    "triage_risk": "02_editorial_triage_risk_audit.tsv",
    "novelty_evidence": "03_novelty_evidence_matrix.tsv",
    "claim_boundary": "04_editor_claim_boundary_note.md",
}


def _read_table(path: Path, sep: str = ",") -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, sep=sep)


def _write_text_atomic(path: Path, text: str) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def _completed_public_dataset_text(public_summary: pd.DataFrame) -> str:
    if public_summary.empty:
        return "public benchmark summary pending"
    completed = public_summary.loc[
        (public_summary["status"] == "completed")
        & (public_summary["dataset_id"] != "demo_synthetic")
    ].copy()
    parts = []
    for row in completed.to_dict(orient="records"):
        parts.append(
            f"{row['dataset_id']} ({row['modality']}; top source "
            f"{row['top_frustration_cell_type']})"
        )
    return "; ".join(parts) if parts else "public benchmark summary pending"


def _comparator_text(tool_comparison: pd.DataFrame) -> str:
    if tool_comparison.empty:
        return "comparator summary pending"
    completed = tool_comparison.loc[
        tool_comparison["status"].astype(str).str.startswith("completed")
    ].copy()
    completed = completed.loc[completed["dataset_id"] != "demo_synthetic"]
    rows = []
    for tool, subset in completed.groupby("tool", sort=True):
        datasets = sorted(set(subset["dataset_id"].astype(str)))
        rows.append(f"{tool} ({len(datasets)} datasets)")
    return ", ".join(rows) if rows else "comparator summary pending"


def build_one_page_summary(public_summary: pd.DataFrame, tool_comparison: pd.DataFrame) -> str:
    return f"""# One-Page Editor Summary

## Proposed Title

SheafSignal maps frustration in cell communication networks

## Target Journal

Nature Methods, as a methods-focused article.

## Core Advance

SheafSignal reframes cell-cell communication from pairwise ligand-receptor
intensity to a sheaf-valued flow over a biological graph. This enables
edge-level communication inconsistency, local feedback/curl and global
circulation to be quantified with Hodge decomposition.

## Evidence Package

- Simulation recovery of gradient, curl, harmonic and mixed flow components.
- Public benchmarks: {_completed_public_dataset_text(public_summary)}.
- Comparator evidence: {_comparator_text(tool_comparison)}.
- Claim gating: GSE154778 Myeloid is the only main-text cell-type-level
  computational signal; sparse categories remain supplementary QC.
- Reproducibility: GitHub and Zenodo release manifests, checksums, deterministic
  archives and final go/no-go gates are generated locally.

## Editorial Boundary

The manuscript is not positioned as clinical utility, treatment prediction or a
claim of broad superiority over all cell-cell communication tools. It is a
methods manuscript about graph-level communication consistency.
"""


def build_inquiry_letter(public_summary: pd.DataFrame, tool_comparison: pd.DataFrame) -> str:
    return f"""# Presubmission Inquiry Letter Draft

Dear Nature Methods Editors,

We would like to ask whether the manuscript "SheafSignal maps frustration in
cell communication networks" may be suitable for consideration as a methods
article in Nature Methods.

Current cell-cell communication workflows primarily rank sender-receiver
ligand-receptor interactions. SheafSignal addresses a different mathematical
question: whether inferred communication is self-consistent across a biological
graph. The method represents communication as a sheaf-valued flow and applies
Hodge decomposition to quantify pathway inconsistency, local feedback/curl and
global circulation.

The evidence package includes controlled recovery of gradient, curl and
harmonic components; public tumor microenvironment benchmarks across
{_completed_public_dataset_text(public_summary)}; and comparator analyses using
{_comparator_text(tool_comparison)}. The manuscript also includes programmatic
claim gating. For example, in GSE154778 pancreatic cancer, Myeloid is retained
as the only main-text cell-type-level computational signal, while sparse
categories are restricted to supplementary quality-control context.

We position the study as a reproducible computational methods contribution. We
do not claim clinical utility, treatment prediction, or broad superiority over
all communication tools. Source code, small benchmark summaries and release
manifests are prepared for GitHub release, and frozen processed benchmark
objects are prepared for Zenodo deposition before submission.

We would appreciate your advice on whether this manuscript is within the scope
and interest of Nature Methods.

Sincerely,

TBD
"""


def build_triage_risk_table() -> pd.DataFrame:
    rows = [
        {
            "risk_id": "T1",
            "editorial_risk": "Perceived as another CCC scoring tool",
            "risk_level": "high",
            "current_mitigation": "Lead with sheaf-valued flow and Hodge decomposition rather than LR ranking.",
            "remaining_action": "Use Figure 1 and abstract to emphasize changed mathematical object.",
        },
        {
            "risk_id": "T2",
            "editorial_risk": "Public-data-only biological evidence",
            "risk_level": "medium",
            "current_mitigation": "Frame as methods benchmark, not clinical or therapeutic discovery.",
            "remaining_action": "Keep clinical language out of title, abstract and cover letter.",
        },
        {
            "risk_id": "T3",
            "editorial_risk": "Comparator coverage incomplete",
            "risk_level": "medium",
            "current_mitigation": "Full LIANA, LRProductBaseline, MechanisticTargetPrior and bounded nichenetr-engine outputs exist.",
            "remaining_action": "Do not claim broad superiority; state CellChat/CellPhoneDB/niche-DE pending.",
        },
        {
            "risk_id": "T4",
            "editorial_risk": "Sparse cell-type overinterpretation",
            "risk_level": "low",
            "current_mitigation": "Programmatic claim gating restricts GSE154778 main claim to Myeloid.",
            "remaining_action": "Keep sparse categories in supplement/QC only.",
        },
        {
            "risk_id": "T5",
            "editorial_risk": "Reproducibility package incomplete",
            "risk_level": "medium",
            "current_mitigation": "Release manifests, deterministic archives, checksum files and go/no-go gates exist.",
            "remaining_action": "Mint Zenodo DOI and create public GitHub release before submission.",
        },
        {
            "risk_id": "T6",
            "editorial_risk": "Format or submission metadata incomplete",
            "risk_level": "medium",
            "current_mitigation": "Nature Methods format audit is locally ready; metadata templates exist.",
            "remaining_action": "Authors must fill names, affiliations, CRediT, COI and ethics wording.",
        },
    ]
    return pd.DataFrame(rows)


def build_novelty_evidence_matrix() -> pd.DataFrame:
    rows = [
        {
            "novelty_axis": "mathematical_object",
            "claim": "CCC is represented as sheaf-valued flow, not only edge intensity.",
            "evidence_file": "src/sheafsignal; manuscript/nature_methods_package/09_full_manuscript_draft.md",
            "allowed_editor_message": "The contribution changes the object of analysis.",
            "boundary": "Do not describe as a universal replacement for all CCC tools.",
        },
        {
            "novelty_axis": "hodge_decomposition",
            "claim": "Gradient, curl and harmonic communication components are quantified.",
            "evidence_file": "benchmarks/results/component_recovery.csv",
            "allowed_editor_message": "Simulation validates component recovery.",
            "boundary": "Simulation is not biological validation.",
        },
        {
            "novelty_axis": "public_benchmark_breadth",
            "claim": "PDAC, melanoma, breast cancer scRNA-seq and Visium spatial cases are benchmarked.",
            "evidence_file": "benchmarks/results/public_tme_sheafsignal_summary.csv",
            "allowed_editor_message": "Public TME benchmarks support method generality.",
            "boundary": "Do not claim universal source-cell biology.",
        },
        {
            "novelty_axis": "claim_gating",
            "claim": "Sparse or unsupported categories are programmatically downgraded.",
            "evidence_file": "benchmarks/results/gse154778_pdac_scrna/qc/claim_gating_by_cell_type.csv",
            "allowed_editor_message": "Biological interpretation is pre-gated.",
            "boundary": "Do not rescue sparse categories in the narrative.",
        },
        {
            "novelty_axis": "external_comparators",
            "claim": "LIANA and bounded nichenetr-engine comparator outputs are aligned.",
            "evidence_file": "benchmarks/results/tool_comparison.csv",
            "allowed_editor_message": "The method is benchmarkable against external CCC evidence.",
            "boundary": "Do not claim broad superiority over all CCC tools.",
        },
    ]
    return pd.DataFrame(rows)


def build_claim_boundary_note() -> str:
    return """# Editor-Facing Claim Boundary Note

SheafSignal should be described as a methods contribution. The allowed central
claim is that it introduces a sheaf/Hodge formulation for graph-level
communication consistency and frustration.

The presubmission inquiry must not claim:

- guaranteed acceptance or guaranteed publication;
- clinical utility, treatment response prediction or therapeutic guidance;
- full pretrained NicheNet network benchmarking;
- broad superiority over all CCC tools;
- strong biological mechanisms from sparse cell types or marker-dominant
  Visium spot labels.

The strongest editor-facing message is:

> SheafSignal asks a graph-level consistency question that standard pairwise
> ligand-receptor scoring does not directly answer.
"""


def build_package(
    *,
    output_dir: Path,
    public_summary: pd.DataFrame,
    tool_comparison: pd.DataFrame,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {key: output_dir / name for key, name in OUTPUT_FILES.items()}
    _write_text_atomic(paths["one_page_summary"], build_one_page_summary(public_summary, tool_comparison))
    _write_text_atomic(paths["inquiry_letter"], build_inquiry_letter(public_summary, tool_comparison))
    build_triage_risk_table().to_csv(paths["triage_risk"], sep="\t", index=False)
    build_novelty_evidence_matrix().to_csv(paths["novelty_evidence"], sep="\t", index=False)
    _write_text_atomic(paths["claim_boundary"], build_claim_boundary_note())
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="manuscript/presubmission_inquiry")
    parser.add_argument("--public-summary", default="benchmarks/results/public_tme_sheafsignal_summary.csv")
    parser.add_argument("--tool-comparison", default="benchmarks/results/tool_comparison.csv")
    args = parser.parse_args(argv)

    paths = build_package(
        output_dir=Path(args.output_dir),
        public_summary=_read_table(Path(args.public_summary)),
        tool_comparison=_read_table(Path(args.tool_comparison)),
    )
    for path in paths.values():
        print(f"wrote {path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
