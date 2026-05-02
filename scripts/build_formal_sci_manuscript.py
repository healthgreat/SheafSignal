#!/usr/bin/env python
"""Build formal SCI manuscript v1 from SheafSignal evidence tables.

Author: SheafSignal contributors
Date: 2026-05-01
Purpose: convert the current benchmark, claim-gating and release evidence into
a formal manuscript draft with claim-tracked companion files.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


OUTPUT_FILES = {
    "title_abstract": "SCI_TITLE_ABSTRACT_KEYWORDS.md",
    "manuscript": "SCI_MANUSCRIPT_V1.md",
    "claim_tracked": "SCI_MANUSCRIPT_V1_claim_tracked.md",
    "cover_letter": "SCI_COVER_LETTER_NatureMethods.md",
    "author_todo": "SCI_AUTHOR_TODO.md",
}


def _read_table(path: Path, sep: str = ",") -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, sep=sep)


def _write_text_atomic(path: Path, text: str) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def _fmt(value: object, digits: int = 3) -> str:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(numeric):
        return "NA"
    return f"{float(numeric):.{digits}g}"


def component_recovery_text(component_recovery: pd.DataFrame) -> str:
    if component_recovery.empty:
        return "Component recovery results are pending."
    parts = []
    for row in component_recovery.to_dict(orient="records"):
        parts.append(
            f"{row['scenario']} "
            f"(gradient {_fmt(row['gradient_ratio'])}, "
            f"curl {_fmt(row['curl_ratio'])}, "
            f"harmonic {_fmt(row['harmonic_ratio'])})"
        )
    return "; ".join(parts)


def public_benchmark_text(public_summary: pd.DataFrame) -> str:
    if public_summary.empty:
        return "Public benchmark results are pending."
    completed = public_summary.loc[
        (public_summary["status"].astype(str) == "completed")
        & (public_summary["dataset_id"].astype(str) != "demo_synthetic")
    ].copy()
    if completed.empty:
        return "Public benchmark results are pending."
    parts = []
    for row in completed.to_dict(orient="records"):
        parts.append(
            f"{row['dataset_id']} ({row['modality']}, {int(row['n_cell_types'])} "
            f"cell-type states, {int(row['n_edges'])} edges, top source "
            f"{row['top_frustration_cell_type']}, total sheaf energy "
            f"{_fmt(row['total_sheaf_energy'])})"
        )
    return "; ".join(parts)


def myeloid_text(myeloid_summary: pd.DataFrame) -> str:
    if myeloid_summary.empty:
        return "GSE154778 Myeloid readiness results are pending."
    row = myeloid_summary.iloc[0]
    return (
        f"Myeloid passed the main-claim gate with minimum lesion support of "
        f"{int(row['min_lesion_n_cells'])} cells and "
        f"{int(row['min_lesion_n_samples'])} samples, bootstrap top frequency "
        f"{_fmt(row['bootstrap_top_frequency'])}, primary frustration score "
        f"{_fmt(row['primary_frustration_score'])}, metastatic frustration "
        f"score {_fmt(row['metastatic_frustration_score'])}, and median marker "
        f"score margin {_fmt(row['median_marker_score_margin'])}."
    )


def comparator_text(tool_comparison: pd.DataFrame) -> str:
    if tool_comparison.empty:
        return "Comparator results are pending."
    completed = tool_comparison.loc[
        tool_comparison["status"].astype(str).str.startswith("completed")
    ].copy()
    completed = completed.loc[completed["dataset_id"].astype(str) != "demo_synthetic"]
    if completed.empty:
        return "Comparator results are pending."
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
            rho_text = f"{float(rho.min()):.3g}-{float(rho.max()):.3g}"
        parts.append(f"{tool}: {len(datasets)} datasets, Spearman {rho_text}")
    return "; ".join(parts)


def build_title_abstract_keywords(public_summary: pd.DataFrame) -> str:
    return """# Title, Abstract And Keywords

## Title

SheafSignal maps frustration in cell communication networks

## Short Title

Sheaf-valued communication frustration

## Abstract

Cell-cell communication analyses prioritize ligand-receptor activity but rarely
test whether inferred signals are self-consistent across a tissue graph. We
present SheafSignal, a method that represents communication as a sheaf-valued
flow and uses Hodge decomposition to quantify pathway inconsistency, local
feedback and global circulation. Controlled simulations recovered expected
gradient, curl, harmonic and mixed components. Across public melanoma,
pancreatic cancer, breast cancer and breast Visium benchmarks, dominant
frustration sources were context-specific rather than universal. Comparator
analyses included ligand-receptor product baselines, LIANA, bounded
nichenetr-engine scoring with a project-curated tumor-microenvironment prior,
and a mechanistic target-prior baseline. In pancreatic cancer, pre-specified
claim gating retained Myeloid as the main cell-type-level computational signal
and kept sparse categories in supplementary quality-control context.
SheafSignal provides a reproducible framework for studying communication
inconsistency rather than communication intensity alone.

## Keywords

cell-cell communication; sheaf theory; Hodge decomposition; single-cell
RNA-seq; spatial transcriptomics; tumor microenvironment; ligand-receptor
analysis; reproducible bioinformatics
"""


def build_manuscript(
    *,
    component_recovery: pd.DataFrame,
    public_summary: pd.DataFrame,
    myeloid_summary: pd.DataFrame,
    tool_comparison: pd.DataFrame,
) -> str:
    return f"""# SheafSignal maps frustration in cell communication networks

Article type: Methods article

Authors: TBD

Affiliations: TBD

Correspondence: TBD

## Abstract

Cell-cell communication analyses prioritize ligand-receptor activity but rarely
test whether inferred signals are self-consistent across a tissue graph. We
present SheafSignal, a method that represents communication as a sheaf-valued
flow and uses Hodge decomposition to quantify pathway inconsistency, local
feedback and global circulation. Controlled simulations recovered expected
gradient, curl, harmonic and mixed components. Across public tumor
microenvironment benchmarks, dominant frustration sources were
context-specific rather than universal. Comparator analyses included
ligand-receptor product baselines, LIANA, bounded nichenetr-engine scoring with
a project-curated tumor-microenvironment prior, and a mechanistic target-prior
baseline. In pancreatic cancer, pre-specified claim gating retained Myeloid as
the main cell-type-level computational signal and kept sparse categories in
supplementary quality-control context. SheafSignal provides a reproducible
framework for studying communication inconsistency rather than communication
intensity alone.

## Introduction

Cell-cell communication workflows have become central to single-cell and
spatial transcriptomics analysis because they translate expression profiles
into candidate signaling relationships between cell populations
[REF: CellChat], [REF: CellPhoneDB], [REF: NicheNet], [REF: LIANA]. Most
widely used approaches ask a pairwise question: whether a sender population
expresses ligands that can engage receptors in a receiver population. This
question is necessary, but it is not the same as asking whether the resulting
communication network is self-consistent across a tissue.

The difference matters when communication is interpreted as a network-level
biological process. A collection of strong ligand-receptor edges can still be
inconsistent with downstream pathway-state changes, can form local feedback
loops, or can participate in circulation-like structure that is not reducible
to pairwise edge intensity. Existing workflows provide rich ligand-receptor
ranking and prioritization, but they do not directly decompose communication
into gradient, feedback-like and global circulation components. This leaves a
gap between cell-cell communication scoring and graph-level interpretation.

SheafSignal addresses this gap by changing the mathematical object under
analysis. Instead of treating communication only as edge intensity, SheafSignal
represents communication as a sheaf-valued flow over a biological graph. For a
directed sender-receiver edge, ligand-receptor evidence is compared with the
receiver pathway-state transition. The mismatch defines sheaf energy, which we
interpret as communication frustration. Graph Hodge decomposition then
separates the resulting flow into gradient, curl and harmonic components,
corresponding to directional signal, local feedback-like structure and global
circulation-like structure [REF: graph Hodge decomposition], [REF: cellular
sheaves].

Here we present SheafSignal as a reproducible computational method and evaluate
it using controlled simulations, public tumor microenvironment single-cell
benchmarks, a public breast spatial transcriptomics case, and external
communication comparators. The central claim is methodological: SheafSignal
asks a graph-level consistency question that standard pairwise
ligand-receptor scoring does not directly answer.

## Results

### SheafSignal defines communication frustration as sheaf energy

SheafSignal takes an expression matrix, cell-type annotations, a
ligand-receptor database and a pathway or target-gene set. For each directed
sender-receiver pair, it summarizes ligand-receptor communication flow and
receiver pathway-state transition on a shared graph. Edge-level sheaf energy
is calculated as a standardized mismatch between these quantities. Sender-level
frustration scores then summarize which cell populations contribute the
largest outgoing share of inconsistency. This formulation makes the unit of
analysis a graph-valued communication object rather than a single
ligand-receptor score.

The method returns edge-level sheaf energy, global gradient/curl/harmonic
ratios and node-level frustration scores. These outputs are designed to support
three questions: which communication edges are inconsistent with pathway-state
change; whether the communication flow is dominated by directional,
feedback-like or circulation-like structure; and which cell populations are
the main sources of communication frustration.

### Controlled simulations recover gradient, curl and harmonic components

We first evaluated whether the Hodge component outputs recover known
ground-truth structure. The simulation benchmark included pure gradient, pure
curl, pure harmonic and mixed-flow graphs. The current component-recovery
table is: {component_recovery_text(component_recovery)}. These results support
the mathematical implementation of the decomposition and the expected behavior
of the SheafSignal flow object (Figure 2).

This simulation layer is intentionally limited to method validation. It does
not establish biological mechanisms and is not used as evidence for any
disease-specific claim.

### Public tumor benchmarks reveal context-specific frustration architecture

We next applied the same workflow to public tumor microenvironment datasets.
The completed non-demo benchmark set is: {public_benchmark_text(public_summary)}.
The leading frustration source differed across datasets, supporting the
interpretation that communication frustration is context-specific rather than
dominated by a single universal source population (Figure 3).

This result is a method-level observation. It shows that SheafSignal can
summarize graph-level communication inconsistency across multiple public
contexts. It does not support a universal biological claim that any one cell
type is the dominant frustration source across all tumors.

### Claim-gated pancreatic cancer analysis identifies a Myeloid computational signal

GSE154778 pancreatic cancer was used as the first detailed claim-gated
single-cell case. Because the processed matrix did not provide a complete
paper-ready author annotation for all downstream requirements, we used
coarse marker-based annotation with explicit quality control. We then applied
pre-specified evidence-tier filters based on cell counts, sample support,
lesion support, marker confidence and sample-level robustness.

Under this gate, {myeloid_text(myeloid_summary)} Sparse stromal and lymphoid
categories were retained only for supplementary quality-control interpretation.
In particular, sparse lesion-specific categories are not used for main
mechanistic claims (Figure 4).

The GSE154778 result should therefore be read as a claim-gated computational
signal. It supports prioritizing Myeloid communication frustration for
hypothesis generation, while preserving sample-level heterogeneity and
annotation uncertainty.

### Comparator analyses show alignment and complementarity

We compared SheafSignal outputs with conventional and external communication
evidence. The current aligned comparator set is: {comparator_text(tool_comparison)}.
These analyses show that SheafSignal can be benchmarked against existing
communication evidence while retaining an inconsistency-focused output
(Figure 5).

The comparator evidence supports alignment, complementarity and
non-equivalence to simple ligand-receptor product intensity. It does not
support a broad superiority claim over all cell-cell communication tools. The
current nichenetr-engine analysis uses official nichenetr scoring with a
project-curated tumor-microenvironment prior matrix, not a full pretrained
NicheNet network benchmark.

### Spatial analysis demonstrates hotspot localization with explicit spot-level boundaries

The public breast Visium case was used to evaluate whether SheafSignal can be
applied in spatial transcriptomics. Spatial hotspot outputs were assessed with
k-neighbor sensitivity and spot-level quality control. Because Visium spots are
not single cells and marker-dominant labels can reflect mixed programs, the
spatial analysis is positioned as a hotspot-localization demonstration rather
than histology-validated cell-type mechanism.

## Discussion

SheafSignal reframes cell-cell communication analysis as a graph-level
consistency problem. By representing communication as a sheaf-valued flow and
applying Hodge decomposition, the method reports edge-level inconsistency,
directional flow, local feedback-like structure and global circulation-like
structure. This complements ligand-receptor prioritization by asking whether
the inferred communication network is internally consistent with pathway-state
transitions.

The public tumor microenvironment benchmarks show that frustration sources can
vary across cancer contexts. The detailed pancreatic cancer case illustrates
why claim gating is necessary: Myeloid passes the current evidence gate,
whereas sparse categories remain underpowered for main-text biological
interpretation. The spatial case extends the workflow to Visium data while
retaining spot-level interpretation boundaries.

Several limitations define the current manuscript. First, the evidence is
derived from public data and should be interpreted as computational and
hypothesis-generating. Second, some annotations are coarse or marker-based, so
cell-type-level conclusions require explicit confidence checks. Third, the
current comparator panel includes LIANA, ligand-receptor product baselines,
MechanisticTargetPrior and bounded nichenetr-engine scoring, but it does not
claim exhaustive benchmarking of all communication tools. Fourth, the current
NicheNet-related analysis is not a full pretrained NicheNet network benchmark.

Future work can extend SheafSignal in three directions: larger simulation
stress tests across graph density and noise regimes, broader comparator
execution including additional external tools, and experimental validation of
specific frustration sources. The current manuscript establishes the
mathematical object, software workflow and public-data benchmark foundation.

## Methods

### Input data and graph construction

SheafSignal accepts cell-by-gene expression data, cell-type annotations,
ligand-receptor pairs and pathway or target-gene sets. For single-cell
datasets, expression is aggregated to cell-type profiles for graph-level
analysis. For spatial data, spot-program labels and spatial neighborhoods are
used with explicit spot-level interpretation boundaries.

### Communication flow and pathway state

For each sender-receiver pair, ligand expression in the sender and receptor
expression in the receiver define a communication flow score. Receiver pathway
state is summarized from target-gene activity. Both quantities are standardized
before edge-level mismatch is calculated so that sheaf energy reflects
relative inconsistency rather than raw expression scale.

### Sheaf energy and Hodge decomposition

The edge-level mismatch between communication flow and pathway-state transition
is reported as sheaf energy. The net graph flow is decomposed into gradient,
curl and harmonic components using graph Hodge decomposition. The corresponding
ratios summarize the fraction of flow energy attributable to directional,
local feedback-like and global circulation-like structure.

### Claim gating and sparse-category handling

GSE154778 pancreatic cancer analyses use an evidence-tier filter before any
cell-type-level signal is allowed into the main narrative. Categories with
insufficient cell support, sample support or marker confidence are downgraded
to supplementary quality-control interpretation. This rule is applied before
biological interpretation and is documented in the claim-gating tables.

### Comparator analyses

Comparator analyses include ligand-receptor product baselines, LIANA imports,
MechanisticTargetPrior and bounded nichenetr-engine scoring with a
project-curated tumor-microenvironment prior matrix. Comparator tables are
aligned at the sender-receiver edge level. The primary comparison is alignment
and complementarity, not broad superiority.

### Reproducibility

All scripts, tests, benchmark manifests, release manifests, figure source maps
and claim-safety audits are generated within the project repository. Large
processed objects are prepared for Zenodo deposition, while source code and
small result tables are prepared for GitHub release.

## Data Availability

Raw public datasets remain available from the original GEO and 10x Genomics
accessions listed in `metadata/datasets.tsv`. Frozen processed benchmark
objects are prepared for Zenodo deposition. A Zenodo DOI must be inserted after
the deposition is published.

## Code Availability

Source code, tests, benchmark scripts and small result tables are prepared for
public GitHub release. The final repository URL must be inserted after the
public release is created.

## Acknowledgements

TBD.

## Author Contributions

TBD.

## Competing Interests

TBD.

## Boundary Statement

This manuscript is a computational methods study. It does not claim clinical
utility, treatment guidance, treatment-response prediction, guaranteed journal
acceptance or broad superiority over all cell-cell communication tools.
"""


def build_claim_tracked(manuscript: str) -> str:
    evidence = """# Claim-Tracked Companion

## Claim Map

- C1: SheafSignal is a distinct sheaf/Hodge formulation of CCC. Evidence:
  `src/sheafsignal`, `manuscript/nature_methods_package/05_claim_evidence_map.tsv`.
- C2: Gradient, curl and harmonic components are recoverable in controlled
  simulations. Evidence: `benchmarks/results/component_recovery.csv`.
- C3: Public tumor benchmarks show context-specific frustration architecture.
  Evidence: `benchmarks/results/public_tme_sheafsignal_summary.csv`.
- C4: GSE154778 Myeloid is a claim-gated computational source signal.
  Evidence: `benchmarks/results/gse154778_pdac_scrna/qc/myeloid_claim_readiness_summary.csv`.
- C5: Sparse GSE154778 categories are underpowered for main biology. Evidence:
  `benchmarks/results/gse154778_pdac_scrna/qc/claim_gating_by_cell_type.csv`.
- C6: External comparator evidence exists. Evidence:
  `benchmarks/results/tool_comparison.csv`.
- C7: The package is reproducible and release-ready pending DOI. Evidence:
  `release/archive_manifest.tsv`, `manuscript/NATURE_METHODS_GO_NO_GO_REPORT.md`.

## Draft With Evidence Boundary

"""
    return evidence + manuscript


def build_cover_letter() -> str:
    return """# Nature Methods Cover Letter Draft

Dear Editors,

We submit "SheafSignal maps frustration in cell communication networks" for
consideration as a Methods article.

Current cell-cell communication analyses primarily prioritize ligand-receptor
activity between sender and receiver populations. SheafSignal asks a different
network-level question: whether inferred communication is self-consistent
across a biological graph. The method represents communication as a
sheaf-valued flow and uses Hodge decomposition to quantify edge-level
frustration, local feedback-like structure and global circulation-like
structure.

The manuscript is supported by controlled Hodge-component simulations, public
tumor microenvironment benchmarks, a spatial transcriptomics demonstration,
and comparator analyses against ligand-receptor product baselines, LIANA,
MechanisticTargetPrior and bounded nichenetr-engine scoring with a transparent
project-curated prior. Biological interpretation is deliberately gated; for
example, in GSE154778 pancreatic cancer, Myeloid is retained as the main
claim-gated computational signal, while sparse categories remain supplementary
quality-control context.

The study is positioned as a reproducible computational methods contribution.
It does not claim clinical utility, treatment guidance, treatment-response
prediction, guaranteed publication or broad superiority over all communication
tools. Source code, tests, benchmark scripts and release manifests are prepared
for public GitHub release, and processed benchmark objects are prepared for
Zenodo deposition before submission.

Sincerely,

TBD
"""


def build_author_todo() -> str:
    return """# SCI Manuscript V1 Author Todo

## Blocking Before Submission

1. Fill author list, affiliations, ORCID identifiers and corresponding author
   information.
2. Fill CRediT author contributions.
3. Confirm competing interests.
4. Confirm institutional wording for ethics and public-data use.
5. Create the public GitHub release.
6. Upload the Zenodo archive and insert the DOI into `metadata/datasets.tsv`,
   Data Availability and release files.
7. Freeze final figures and update figure panel labels.
8. Run:

```bash
python scripts/check_claim_safety.py --report-only
python scripts/check_final_submission_blockers.py --report-only
python -m pytest
python scripts/release_audit.py
```

## Writing Tasks

1. Replace `[REF: ...]` placeholders with verified references.
2. Convert Markdown to journal-formatted DOCX or submission-system text.
3. Review whether Figure 1 needs a professionally drawn conceptual panel.
4. Review all figure legends against `manuscript/figure_legends/03_figure_source_map.tsv`.
5. Keep all clinical and therapeutic wording inside boundary statements only.
"""


def build_package(
    *,
    output_dir: Path,
    component_recovery: pd.DataFrame,
    public_summary: pd.DataFrame,
    myeloid_summary: pd.DataFrame,
    tool_comparison: pd.DataFrame,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {key: output_dir / name for key, name in OUTPUT_FILES.items()}
    title = build_title_abstract_keywords(public_summary)
    manuscript = build_manuscript(
        component_recovery=component_recovery,
        public_summary=public_summary,
        myeloid_summary=myeloid_summary,
        tool_comparison=tool_comparison,
    )
    _write_text_atomic(paths["title_abstract"], title)
    _write_text_atomic(paths["manuscript"], manuscript)
    _write_text_atomic(paths["claim_tracked"], build_claim_tracked(manuscript))
    _write_text_atomic(paths["cover_letter"], build_cover_letter())
    _write_text_atomic(paths["author_todo"], build_author_todo())
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="manuscript")
    parser.add_argument("--component-recovery", default="benchmarks/results/component_recovery.csv")
    parser.add_argument("--public-summary", default="benchmarks/results/public_tme_sheafsignal_summary.csv")
    parser.add_argument(
        "--myeloid-summary",
        default="benchmarks/results/gse154778_pdac_scrna/qc/myeloid_claim_readiness_summary.csv",
    )
    parser.add_argument("--tool-comparison", default="benchmarks/results/tool_comparison.csv")
    args = parser.parse_args(argv)

    paths = build_package(
        output_dir=Path(args.output_dir),
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
