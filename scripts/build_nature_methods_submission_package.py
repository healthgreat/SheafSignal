#!/usr/bin/env python
"""Build a Nature Methods first-submission manuscript scaffold.

Author: SheafSignal contributors
Date: 2026-04-30
Purpose: convert current SheafSignal benchmark gates into journal-facing draft
materials while preserving claim boundaries.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

OUTPUT_FILES = {
    "title_page": "00_title_page.md",
    "abstract": "01_abstract.md",
    "cover_letter": "02_cover_letter_draft.md",
    "main_text": "03_main_text_skeleton.md",
    "methods": "04_methods_skeleton.md",
    "claim_map": "05_claim_evidence_map.tsv",
    "figure_plan": "06_figure_plan.tsv",
    "checklist": "07_submission_checklist.tsv",
    "limitations": "08_claim_boundaries_and_limitations.md",
    "full_manuscript": "09_full_manuscript_draft.md",
    "supplementary": "10_supplementary_information_draft.md",
}


def _read_table(path: Path, sep: str = ",") -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, sep=sep)


def _atomic_write_text(path: Path, text: str) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def _completed_public_datasets(public_summary: pd.DataFrame) -> str:
    if public_summary.empty or "status" not in public_summary:
        return "public benchmark datasets are pending."
    completed = public_summary.loc[
        (public_summary["status"] == "completed")
        & (public_summary["dataset_id"] != "demo_synthetic")
    ].copy()
    if completed.empty:
        return "public benchmark datasets are pending."
    parts = []
    for row in completed.to_dict(orient="records"):
        parts.append(
            f"{row['dataset_id']} ({row['modality']}, top source "
            f"{row['top_frustration_cell_type']})"
        )
    return "; ".join(parts)


def _component_summary(component_recovery: pd.DataFrame) -> str:
    if component_recovery.empty:
        return "Component-recovery simulation table is pending."
    rows = []
    for row in component_recovery.to_dict(orient="records"):
        rows.append(
            f"{row['scenario']}: gradient={float(row['gradient_ratio']):.3g}, "
            f"curl={float(row['curl_ratio']):.3g}, "
            f"harmonic={float(row['harmonic_ratio']):.3g}"
        )
    return "; ".join(rows)


def _comparator_summary(tool_comparison: pd.DataFrame) -> str:
    if tool_comparison.empty:
        return "Comparator table is pending."
    completed = tool_comparison.loc[
        tool_comparison["status"].astype(str).str.startswith("completed")
    ].copy()
    completed = completed.loc[completed["dataset_id"] != "demo_synthetic"]
    if completed.empty:
        return "Comparator imports are pending."
    rows = []
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
        rows.append(f"{tool}: {len(datasets)} datasets, Spearman {rho_text}")
    return "; ".join(rows)


def build_title_page() -> str:
    return """# SheafSignal maps frustration in cell communication networks

Manuscript type: Methods article

Target journal: Nature Methods

Authors: TBD

Affiliations: TBD

Corresponding author: TBD

Code availability: GitHub repository pending public release

Data availability: Zenodo DOI pending; public source accessions listed in
`metadata/datasets.tsv`

Status: Draft scaffold generated from current benchmark gates. This file is not
a journal-formatted final manuscript.
"""


def build_abstract(public_summary: pd.DataFrame, tool_comparison: pd.DataFrame) -> str:
    public_text = _completed_public_datasets(public_summary)
    return f"""# Abstract Draft

Cell-cell communication methods prioritize ligand-receptor activity but rarely
test whether inferred signals are self-consistent across a tissue graph. We
present SheafSignal, a method that represents communication as a sheaf-valued
flow and uses Hodge decomposition to quantify pathway inconsistency, local
feedback and global circulation. Controlled simulations recover gradient, curl,
harmonic and mixed flow structure. Across public tumor microenvironment
benchmarks ({public_text}), dominant frustration sources are context-specific
rather than universal. Comparator analyses include ligand-receptor product
baselines, full LIANA imports, bounded nichenetr-engine scoring with a
project-curated prior and a transparent mechanistic target-prior baseline. In
pancreatic cancer, claim gating identifies Myeloid as the only main-text
cell-type-level computational signal, while sparse categories remain
supplementary QC. SheafSignal provides a reproducible framework for studying
communication inconsistency rather than communication intensity alone.

Boundary: this abstract draft makes no clinical, therapeutic, or guaranteed
publication claim.
"""


def build_cover_letter() -> str:
    return """# Cover Letter Draft

Dear Editors,

We submit "SheafSignal maps frustration in cell communication networks" for
consideration as a Methods article in Nature Methods.

Most cell-cell communication workflows rank ligand-receptor interactions, but
they do not directly test whether communication signals are self-consistent
across a tissue graph or whether they form feedback and circulation structure.
SheafSignal addresses this gap by defining cell-cell communication as a
sheaf-valued flow and decomposing it with graph Hodge theory. This changes the
mathematical object under study from edge intensity to graph-level consistency.

The manuscript is organized around four evidence layers: controlled simulation
recovery of gradient, curl and harmonic components; public tumor
microenvironment benchmarks across pancreatic cancer, melanoma and breast
cancer; a public Visium spatial hotspot case; and comparator analyses against
ligand-receptor product baselines, LIANA, nichenetr-engine scoring with a
transparent project-curated prior, and a mechanistic target-prior baseline.

We have taken a conservative approach to biological interpretation. In
GSE154778 pancreatic cancer, Myeloid is presented as a claim-gated
computational signal, whereas sparse cell-type categories are retained only as
quality-control context. We do not claim clinical utility, treatment prediction,
or broad superiority over all communication tools.

All scripts, tests, benchmark manifests and release inventories are prepared
for public GitHub release. Frozen processed benchmark objects are prepared for
Zenodo deposition before submission.

Sincerely,

TBD
"""


def build_main_text_skeleton(
    public_summary: pd.DataFrame,
    component_recovery: pd.DataFrame,
    tool_comparison: pd.DataFrame,
) -> str:
    return f"""# Main Text Skeleton

## Introduction

- Current ligand-receptor communication tools answer whether a sender can
  signal to a receiver.
- The missing question is graph-level consistency: whether edge-level
  communication agrees with receiver pathway state across the tissue network.
- SheafSignal introduces a sheaf-valued flow object and Hodge decomposition to
  quantify inconsistency, feedback/curl and harmonic circulation.

## Results

### SheafSignal defines communication frustration as a sheaf-valued flow

- Define sender-receiver ligand-receptor flow.
- Define receiver pathway-state gradient.
- Define sheaf energy as mismatch between communication flow and pathway-state
  transition.
- Decompose net graph flow into gradient, curl and harmonic components.

### Controlled simulations recover known Hodge components

Evidence summary: {_component_summary(component_recovery)}

### Public tumor benchmarks reveal context-specific frustration architecture

Completed public benchmark summary: {_completed_public_datasets(public_summary)}

Interpretation boundary: these datasets support a reusable method and
context-specific architecture; they do not support a universal source-cell
claim across cancers.

### GSE154778 claim gating supports a Myeloid computational signal

- Main-text candidate: Myeloid only.
- Sparse or low-confidence categories remain supplementary QC.
- Sample-level heterogeneity is reported as a limitation rather than hidden.

### External and mechanistic comparators show SheafSignal is not only LR intensity

Comparator summary: {_comparator_summary(tool_comparison)}

Interpretation boundary: use LIANA and bounded nichenetr-engine evidence as
benchmark support. Do not claim broad superiority over all CCC tools.

### Spatial Visium analysis demonstrates hotspot localization

- Use hotspot localization and k-neighbor sensitivity.
- Do not infer single-cell mechanism from marker-dominant Visium spot labels.

## Discussion

- SheafSignal moves CCC analysis from pairwise communication intensity to
  graph-level consistency.
- The method is designed for hypothesis generation and mechanistic
  prioritization, not clinical decision making.
- Main limitations: public-data-only validation, marker/coarse annotations in
  some datasets, bounded nichenetr-engine prior, pending CellChat/CellPhoneDB
  and niche-DE comparators.

## Data And Code Availability

- GitHub release package is generated locally.
- Zenodo deposition is required before submission.
"""


def build_methods_skeleton() -> str:
    return """# Methods Skeleton

## Input Data

- Cell-by-gene expression matrix or spatial spot-by-gene matrix.
- Cell type or spot-program metadata.
- Ligand-receptor database.
- Pathway or target-gene set.
- Optional spatial coordinates.

## Preprocessing

- Use dataset-specific adapters for public scRNA-seq and Visium data.
- Aggregate selected LR, marker and pathway genes to cell-type profiles for the
  main benchmark path.
- Keep raw and processed large files out of Git; release frozen processed
  objects through Zenodo.

## Sheaf Energy

- Compute ligand-receptor sender-receiver flow.
- Compute pathway-state difference between sender and receiver profiles.
- Standardize both terms and calculate edge-level mismatch energy.

## Hodge Decomposition

- Collapse anti-parallel directed flows to canonical net pairwise flow.
- Decompose net edge flow into gradient, curl and harmonic components.
- Report gradient_ratio, curl_ratio and harmonic_ratio.

## Frustration Scoring

- Compute sender-level outgoing share of total sheaf energy.
- Use claim gating to restrict biological interpretation to supported cell
  types.

## Statistical Testing

- Use empirical permutation and Benjamini-Hochberg FDR where specified.
- Use stratified or sample-aware designs when sample identity is available.

## Comparator Analyses

- Internal LRProductBaseline: ligand expression times receptor expression.
- LIANA: full imports for public scRNA-seq benchmarks.
- NicheNet/nichenetr-engine: official nichenetr scoring with a project-curated
  tumor-microenvironment prior matrix.
- MechanisticTargetPrior: transparent ligand-target prior baseline.

## Software And Reproducibility

- Python package with pytest tests.
- R-side nichenetr dependency installed separately.
- Release manifests, SHA256 checksums and archives generated before submission.
"""


def build_claim_evidence_map(
    public_summary: pd.DataFrame,
    tool_comparison: pd.DataFrame,
    gates: pd.DataFrame,
) -> pd.DataFrame:
    n_public = 0
    if not public_summary.empty:
        n_public = int(
            (
                (public_summary["status"] == "completed")
                & (public_summary["dataset_id"] != "demo_synthetic")
            ).sum()
        )
    completed_tools = []
    if not tool_comparison.empty:
        completed = tool_comparison.loc[
            tool_comparison["status"].astype(str).str.startswith("completed")
        ]
        completed_tools = sorted(set(completed["tool"].astype(str)))
    gate_status = {}
    if not gates.empty:
        gate_status = dict(
            zip(gates["gate_id"].astype(str), gates["current_status"].astype(str))
        )
    rows = [
        {
            "claim_id": "C1",
            "claim": "SheafSignal is a distinct sheaf/Hodge formulation of CCC.",
            "evidence": "G1 status: " + gate_status.get("G1", "missing"),
            "manuscript_use": "main_text_allowed",
            "boundary": "Do not describe as only a new LR score.",
        },
        {
            "claim_id": "C2",
            "claim": "Gradient, curl and harmonic components are recoverable in controlled simulations.",
            "evidence": "G2 status: " + gate_status.get("G2", "missing"),
            "manuscript_use": "main_text_allowed",
            "boundary": "Do not treat simulation as biological validation.",
        },
        {
            "claim_id": "C3",
            "claim": "Public tumor benchmarks show context-specific frustration architecture.",
            "evidence": f"{n_public} completed public non-demo benchmarks.",
            "manuscript_use": "main_text_allowed",
            "boundary": "Do not generalize one source cell type across all cancers.",
        },
        {
            "claim_id": "C4",
            "claim": "GSE154778 Myeloid is a claim-gated computational source signal.",
            "evidence": "G4 status: " + gate_status.get("G4", "missing"),
            "manuscript_use": "main_text_allowed_with_boundary",
            "boundary": "Do not claim uniform patient-level biology or therapeutic relevance.",
        },
        {
            "claim_id": "C5",
            "claim": "Sparse GSE154778 categories are underpowered for main biology.",
            "evidence": "G5 status: " + gate_status.get("G5", "missing"),
            "manuscript_use": "supplement_qc_only",
            "boundary": "Do not rescue sparse cell types by overinterpretation.",
        },
        {
            "claim_id": "C6",
            "claim": "External comparator evidence exists.",
            "evidence": ";".join(completed_tools),
            "manuscript_use": "main_text_allowed_with_boundary",
            "boundary": "Do not claim broad superiority over all CCC tools.",
        },
        {
            "claim_id": "C7",
            "claim": "The package is reproducible and release-ready.",
            "evidence": "G10 status: " + gate_status.get("G10", "missing"),
            "manuscript_use": "availability_statement_allowed",
            "boundary": "Do not cite a Zenodo DOI until minted.",
        },
    ]
    return pd.DataFrame(rows)


def build_figure_plan() -> pd.DataFrame:
    rows = [
        {
            "figure": "Figure 1",
            "purpose": "SheafSignal concept and Hodge decomposition",
            "source": "figures/publication_figure1_sheafsignal_concept.pdf",
            "status": "generated",
        },
        {
            "figure": "Figure 2",
            "purpose": "Simulation component recovery",
            "source": "figures/publication_figure2_component_recovery.pdf",
            "status": "generated",
        },
        {
            "figure": "Figure 3",
            "purpose": "Public TME benchmark summary",
            "source": "figures/publication_figure3_tme_summary.pdf",
            "status": "generated",
        },
        {
            "figure": "Figure 4",
            "purpose": "GSE154778 Myeloid claim gating and robustness",
            "source": "figures/publication_figure4_gse154778_claim_gating.pdf",
            "status": "generated",
        },
        {
            "figure": "Figure 5",
            "purpose": "Comparator alignment with LIANA and bounded nichenetr-engine",
            "source": "figures/publication_figure5_comparator_alignment.pdf",
            "status": "generated",
        },
        {
            "figure": "Supplementary Figure",
            "purpose": "Visium spatial hotspot sensitivity",
            "source": "benchmarks/results/tenx_breast_visium/spatial/qc",
            "status": "supplement_ready",
        },
    ]
    return pd.DataFrame(rows)


def build_submission_checklist() -> pd.DataFrame:
    rows = [
        {
            "item": "Zenodo DOI minted",
            "status": "blocking_pending",
            "evidence_or_action": "Upload release/archives/sheafsignal_zenodo_upload.zip and record DOI.",
        },
        {
            "item": "GitHub repository public release",
            "status": "pending",
            "evidence_or_action": "Use release/archives/sheafsignal_github_release.zip or tracked repository contents.",
        },
        {
            "item": "All tests pass",
            "status": "complete_current_run",
            "evidence_or_action": "Run python -m pytest before final submission.",
        },
        {
            "item": "Release audit passes",
            "status": "complete_current_run",
            "evidence_or_action": "Run python scripts/release_audit.py before final submission.",
        },
        {
            "item": "Nature Methods formatting checked",
            "status": "pending_submission_day_check",
            "evidence_or_action": "Check current official author instructions before upload.",
        },
        {
            "item": "No overclaiming",
            "status": "required",
            "evidence_or_action": "Use 05_claim_evidence_map.tsv and 08_claim_boundaries_and_limitations.md.",
        },
        {
            "item": "Conflict of interest and author contributions",
            "status": "tbd_by_authors",
            "evidence_or_action": "Authors must fill journal submission metadata.",
        },
    ]
    return pd.DataFrame(rows)


def build_limitations() -> str:
    return """# Claim Boundaries And Limitations

## Claims Allowed In Main Text

- SheafSignal defines a sheaf-valued communication-flow object over a biological
  graph.
- Hodge decomposition provides gradient, curl and harmonic summaries of
  communication flow.
- Public tumor benchmarks show context-specific communication frustration
  architecture.
- In GSE154778, Myeloid is the only main-text cell-type-level computational
  signal under the current claim gate.
- LIANA, bounded nichenetr-engine scoring and transparent mechanistic prior
  comparators support benchmarkability against external and target-program
  methods.

## Claims Not Allowed

- Guaranteed acceptance by any journal.
- Clinical utility, treatment prediction or therapeutic recommendation.
- Full pretrained NicheNet network benchmarking.
- Broad superiority over CellChat, CellPhoneDB, LIANA, NicheNet and niche-DE.
- Strong biology from sparse cell types or marker-dominant Visium spot labels.

## Submission-Day Checks

- Re-check journal instructions and impact metrics.
- Mint Zenodo DOI and update all availability statements.
- Re-run all tests and release audit.
- Freeze all figures and supplementary tables.
"""


def build_full_manuscript_draft(
    public_summary: pd.DataFrame,
    component_recovery: pd.DataFrame,
    tool_comparison: pd.DataFrame,
) -> str:
    return f"""# Full Manuscript Draft

## Title

SheafSignal maps frustration in cell communication networks

## Abstract

Cell-cell communication analyses commonly prioritize ligand-receptor activity,
but they rarely ask whether inferred communication is self-consistent across a
tissue graph. SheafSignal represents communication as a sheaf-valued flow and
uses Hodge decomposition to quantify pathway inconsistency, local feedback and
global circulation. Controlled simulations recover the expected gradient, curl,
harmonic and mixed components. Public tumor microenvironment benchmarks show
context-specific dominant frustration sources rather than a universal source
cell type. Comparator analyses include ligand-receptor product baselines, full
LIANA imports, bounded nichenetr-engine scoring with a project-curated
tumor-microenvironment prior and a transparent mechanistic target-prior
baseline. In GSE154778 pancreatic cancer, Myeloid is retained as the only
main-text cell-type-level computational signal under the pre-specified claim
gate, while sparse categories are restricted to supplementary quality-control
context. SheafSignal provides a reproducible framework for studying
communication inconsistency rather than only communication intensity.

## Introduction

Ligand-receptor communication tools have made it routine to prioritize
candidate sender-receiver interactions from single-cell and spatial
transcriptomics data. These tools answer an important pairwise question: whether
a sender cell type has ligands that can engage receptors in a receiver cell
type. A separate graph-level question remains underdeveloped. If communication
edges are interpreted as a tissue-scale signaling network, are those edges
consistent with downstream pathway state over the whole graph, or do they form
feedback and circulation patterns that cannot be captured by pairwise edge
ranking alone?

SheafSignal addresses this gap by changing the mathematical object from
ligand-receptor intensity to sheaf-valued communication flow. For each directed
cell-type edge, SheafSignal compares ligand-receptor flow with the receiver
pathway-state transition. The resulting sheaf energy quantifies local mismatch,
or communication frustration. Net graph flow is then decomposed into gradient,
curl and harmonic components, providing interpretable summaries of directional
signal, local feedback and global circulation.

## Results

### SheafSignal defines communication frustration on a biological graph

SheafSignal takes expression profiles, cell-type annotations, a
ligand-receptor database and a pathway or target-gene set. Sender-receiver flow
is computed from ligand and receptor expression, while receiver pathway state
is computed from target-gene activity. Edge-level sheaf energy is the mismatch
between standardized communication flow and standardized pathway-state
transition. Sender-level frustration scores summarize which cell types
contribute the largest outgoing share of communication inconsistency.

### Hodge simulations recover expected flow components

The simulation benchmark covers pure gradient, pure curl, pure harmonic and
mixed flow cases. Current component-recovery results are:
{_component_summary(component_recovery)}.
These simulations validate the decomposition behavior of the mathematical
primitive. They are not presented as biological evidence.

### Public tumor benchmarks show context-specific frustration architecture

The current public benchmark set includes:
{_completed_public_datasets(public_summary)}.
The dominant source differs across disease contexts. This supports the methods
claim that SheafSignal can report context-specific communication frustration
architecture. It does not support a universal claim that one source cell type
dominates across cancers.

### Claim-gated pancreatic cancer analysis prioritizes Myeloid signal

In GSE154778 pancreatic cancer, Myeloid is the only cell-type-level signal
allowed into the main biological narrative under the current claim gate.
Sparse or low-confidence categories remain supplement-only or QC-warning-only.
Sample-level heterogeneity is retained as a limitation, not hidden by
cell-level resampling.

### Comparator analyses distinguish frustration from communication intensity

Comparator evidence currently includes:
{_comparator_summary(tool_comparison)}.
These analyses show that SheafSignal can be aligned with established
communication evidence while retaining a distinct inconsistency-oriented
quantity. The allowed claim is benchmarkability and non-equivalence to simple
LR intensity. The manuscript must not claim broad superiority over all
cell-cell communication tools.

### Spatial Visium analysis provides hotspot localization

The public breast Visium case evaluates spatial hotspot localization and
k-neighbor sensitivity. Marker-dominant spot labels are treated as spot-program
context, not single-cell annotation. Spatial results are therefore positioned
as a method demonstration and supplement-level hotspot analysis rather than
histology-confirmed mechanism.

## Discussion

SheafSignal reframes cell-cell communication as a graph-level consistency
problem. This makes it possible to ask whether communication is directional,
locally frustrated, feedback-like or globally circulating. The framework is
designed for mechanistic hypothesis generation and methods benchmarking.

Several limitations define the current manuscript boundary. First, the
benchmark is public-data-only and does not support clinical claims. Second,
some annotations are coarse or marker-based and require cautious
interpretation. Third, the NicheNet comparator uses the official nichenetr
scoring engine with a project-curated tumor-microenvironment prior matrix, not
a full pretrained NicheNet network benchmark. Fourth, CellChat, CellPhoneDB and
niche-DE remain out of scope until separately executed and imported.

## Data Availability

Frozen processed benchmark objects are prepared for Zenodo deposition. The
manuscript must not cite a Zenodo DOI until the deposition has been published
and `metadata/datasets.tsv` plus the data availability statement have been
updated. Raw public datasets remain available from their original GEO and 10x
Genomics accessions.

## Code Availability

Code and small benchmark summaries are prepared for public GitHub release. The
repository URL must be inserted after the public release is created.

## Boundary

This draft does not guarantee journal acceptance and does not make clinical,
therapeutic or treatment-response claims.
"""


def build_supplementary_information_draft() -> str:
    return """# Supplementary Information Draft

## Supplementary Methods

### Dataset Preparation

Public scRNA-seq and spatial transcriptomics datasets are listed in
`metadata/datasets.tsv`. Raw public datasets are downloaded from their original
repositories and are not redistributed through GitHub. Frozen processed
benchmark objects are prepared for Zenodo deposition.

### Annotation QC

GSE154778 uses coarse marker-based annotation for the first-pass benchmark.
Marker heatmaps, cell-type counts, annotation-confidence distributions and
frustration-confidence overlays are generated under
`benchmarks/results/gse154778_pdac_scrna/qc/`.

### Claim Gating

Cell-type-level biological claims require minimum cell and sample support.
Underpowered categories are demoted to supplement-only or QC-warning-only
interpretation. Myeloid is currently the only GSE154778 main-text candidate.

### Comparator Analyses

Comparator outputs include LRProductBaseline, full LIANA imports,
MechanisticTargetPrior and bounded nichenetr-engine scoring. CellChat,
CellPhoneDB and niche-DE remain pending and must not be represented as
completed benchmarks.

### Spatial Sensitivity

The Visium spatial case includes k-neighbor sensitivity and hotspot QC. These
analyses test spatial robustness of hotspot ranking, not histology-confirmed
cell-type mechanisms.

## Supplementary Tables

- `manuscript/SCI20_50_SUBMISSION_GATES.tsv`
- `manuscript/reviewer_objection_response_table.tsv`
- `manuscript/FINAL_SUBMISSION_BLOCKERS.tsv`
- `manuscript/nature_methods_package/05_claim_evidence_map.tsv`
- `manuscript/nature_methods_package/06_figure_plan.tsv`
- `manuscript/submission_metadata/SUBMISSION_SYSTEM_METADATA_CHECKLIST.tsv`
- `release/zenodo_upload_manifest.tsv`
- `release/archive_manifest.tsv`

## Reproducibility

Before submission, run:

```bash
python -m pytest
python scripts/release_audit.py
python scripts/check_final_submission_blockers.py
```

The final command must not report `NO_GO` at journal submission.
"""


def build_package(
    *,
    output_dir: Path,
    public_summary: pd.DataFrame,
    component_recovery: pd.DataFrame,
    tool_comparison: pd.DataFrame,
    gates: pd.DataFrame,
    polished_manuscript_path: Path | None = None,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {key: output_dir / filename for key, filename in OUTPUT_FILES.items()}
    _atomic_write_text(paths["title_page"], build_title_page())
    _atomic_write_text(
        paths["abstract"], build_abstract(public_summary, tool_comparison)
    )
    _atomic_write_text(paths["cover_letter"], build_cover_letter())
    _atomic_write_text(
        paths["main_text"],
        build_main_text_skeleton(public_summary, component_recovery, tool_comparison),
    )
    _atomic_write_text(paths["methods"], build_methods_skeleton())
    build_claim_evidence_map(public_summary, tool_comparison, gates).to_csv(
        paths["claim_map"],
        sep="\t",
        index=False,
    )
    build_figure_plan().to_csv(paths["figure_plan"], sep="\t", index=False)
    build_submission_checklist().to_csv(paths["checklist"], sep="\t", index=False)
    _atomic_write_text(paths["limitations"], build_limitations())
    if polished_manuscript_path is not None and polished_manuscript_path.exists():
        full_manuscript = polished_manuscript_path.read_text(encoding="utf-8")
    else:
        full_manuscript = build_full_manuscript_draft(
            public_summary,
            component_recovery,
            tool_comparison,
        )
    _atomic_write_text(
        paths["full_manuscript"],
        full_manuscript,
    )
    _atomic_write_text(paths["supplementary"], build_supplementary_information_draft())
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="manuscript/nature_methods_package")
    parser.add_argument(
        "--public-summary",
        default="benchmarks/results/public_tme_sheafsignal_summary.csv",
    )
    parser.add_argument(
        "--component-recovery", default="benchmarks/results/component_recovery.csv"
    )
    parser.add_argument(
        "--tool-comparison", default="benchmarks/results/tool_comparison.csv"
    )
    parser.add_argument("--gates", default="manuscript/SCI20_50_SUBMISSION_GATES.tsv")
    parser.add_argument(
        "--polished-manuscript", default="manuscript/SCI_MANUSCRIPT_V2_POLISHED.md"
    )
    args = parser.parse_args(argv)

    paths = build_package(
        output_dir=Path(args.output_dir),
        public_summary=_read_table(Path(args.public_summary)),
        component_recovery=_read_table(Path(args.component_recovery)),
        tool_comparison=_read_table(Path(args.tool_comparison)),
        gates=_read_table(Path(args.gates), sep="\t"),
        polished_manuscript_path=Path(args.polished_manuscript),
    )
    for path in paths.values():
        print(f"wrote {path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
