# Claim-Tracked Companion

## Claim Map

- C1: SheafSignal is a distinct sheaf/Hodge formulation of CCC. Evidence:
  `src/sheafsignal`, `manuscript/nature_methods_package/05_claim_evidence_map.tsv`.
- C2: Gradient, curl and harmonic components are recoverable in controlled
  simulations. Evidence: `benchmarks/results/component_recovery.csv`.
- C3: Public tumor benchmarks show dataset-dependent computational sheaf-energy rankings.
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

# SheafSignal maps frustration in cell communication networks

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
table is: gradient_chain (gradient 1, curl 0, harmonic 1.82e-31); triangle_curl (gradient 0, curl 1, harmonic 0); harmonic_ring (gradient 0, curl 0, harmonic 1); mixed (gradient 0.446, curl 0.286, harmonic 0.268). These results support
the mathematical implementation of the decomposition and the expected behavior
of the SheafSignal flow object (Figure 2).

This simulation layer is intentionally limited to method validation. It does
not establish biological mechanisms and is not used as evidence for any
disease-specific claim.

### Public tumor benchmarks reveal dataset-dependent computational sheaf-energy rankings

We next applied the same workflow to public tumor microenvironment datasets.
The completed non-demo benchmark set is: gse72056_melanoma_scrna (scRNA-seq, 7 cell-type states, 42 edges, top source CAF/Fibroblast, total sheaf energy 36); gse154778_pdac_scrna (scRNA-seq, 7 cell-type states, 42 edges, top source Myeloid, total sheaf energy 36.1); gse176078_brca_scrna (scRNA-seq, 8 cell-type states, 56 edges, top source Tumor/Malignant, total sheaf energy 3.31); and tenx_breast_visium (Visium spatial transcriptomics, spot-level hotspot demonstration with k-neighbor sensitivity and marker-program QC).
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

Under this gate, Myeloid passed the main-claim gate with minimum lesion support of 497 cells and 6 samples, bootstrap top frequency 1, primary frustration score 0.378, metastatic frustration score 0.811, and median marker score margin 0.355. Sparse stromal and lymphoid
categories were retained only for supplementary quality-control interpretation.
In particular, sparse lesion-specific categories are not used for main
mechanistic claims (Figure 4).

The GSE154778 result should therefore be read as a claim-gated computational
signal. It supports prioritizing Myeloid communication frustration for
hypothesis generation, while preserving sample-level heterogeneity and
annotation uncertainty.

### Comparator analyses show alignment and complementarity

We compared SheafSignal outputs with conventional and external communication
evidence. The current aligned comparator set is: LIANA: 3 datasets, Spearman 0.0743-0.699; LRProductBaseline: 4 datasets, Spearman -0.0496-0.72; MechanisticTargetPrior: 3 datasets, Spearman 0.176-0.643; NicheNet: 3 datasets, Spearman 0.184-0.75.
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
