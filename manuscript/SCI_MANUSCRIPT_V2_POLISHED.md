# SheafSignal maps communication frustration in tissue signaling networks

Article type: Methods article

Authors: TBD

Affiliations: TBD

Correspondence: TBD

## Abstract

Cell-cell communication methods transform transcriptomes into candidate
ligand-receptor links, but they usually evaluate those links pairwise rather
than asking whether the resulting tissue-level communication network is
self-consistent. We present SheafSignal, a computational framework that models
cell-cell communication as a sheaf-valued flow over a biological graph and
uses Hodge decomposition to quantify edge-level frustration, directional
signal, local curl-like structure and global circulation-like graph components.
Controlled simulations recovered gradient, curl, harmonic and mixed-flow
components. In public tumor-microenvironment benchmarks spanning melanoma,
pancreatic cancer, breast cancer single-cell RNA-seq, head and neck cancer
single-cell RNA-seq and breast Visium data, SheafSignal identified
context-specific computational rankings rather than a universal source cell
type. In pancreatic cancer, expression-mode permutation/FDR hardening showed
that earlier profile-level Myeloid prioritization is annotation- and
analysis-mode-dependent rather than a standalone biological claim.
Comparisons with ligand-
receptor product scoring, LIANA, bounded nichenetr-engine scoring and a
mechanistic target-prior baseline showed alignment with existing communication
evidence while preserving a distinct inconsistency-focused readout.
SheafSignal provides a reproducible route for studying when inferred
communication is discordant with pathway-state structure, complementing
existing intensity-focused cell-cell communication tools.

## Introduction

Single-cell and spatial transcriptomics have made cell-cell communication
analysis a routine part of tissue profiling. Widely used methods including
CellChat, CellPhoneDB, NicheNet and LIANA prioritize candidate interactions by
combining ligand, receptor and, in some settings, downstream target evidence
[@cellchat_jin_2021; @cellphonedb_efremova_2020; @cellphonedb_troule_2025;
@nichenet_browaeys_2020; @nichenet_protocol_sangaram_2025;
@liana_plus_dimitrov_2024]. These approaches answer an essential question:
which sender-receiver pairs have plausible communication evidence? They do
not, by design, fully answer a different graph-level question: whether the
collection of inferred communication edges is self-consistent with tissue-wide
pathway-state change.

This distinction becomes important when communication is interpreted as a
network process rather than as an ordered list of ligand-receptor scores. A
high-scoring edge can be locally inconsistent with the receiver-state
transition, and a set of individually plausible edges can form curl-like or
circulation-like graph components that are not reducible to pairwise intensity.
Existing benchmarks have clarified how communication tools differ in their
resources and scoring assumptions [@ccc_comparison_dimitrov_2022], but a
method is still needed for quantifying inconsistency, curl-like components and
circulation-like components directly on the inferred communication graph.

SheafSignal addresses this gap by changing the mathematical object under
analysis. For each directed sender-receiver edge, the method compares
ligand-receptor communication evidence with a receiver pathway-state
transition and treats the mismatch as sheaf energy, or communication
frustration. The resulting edge flow is then decomposed using graph Hodge
theory into gradient, curl and harmonic components [@hodge_rank_jiang_2011;
@hodge_laplacians_lim_2020], with cellular sheaves providing the language for
local-to-global consistency constraints [@cellular_sheaves_hansen_2019].
SheafSignal therefore asks not only where communication is strong, but where
it is inconsistent with the state changes it is expected to explain.

Here we evaluate SheafSignal as a reproducible methods framework. The study
uses controlled mathematical simulations, public tumor microenvironment
single-cell benchmarks, a public spatial transcriptomics demonstration,
external comparator alignments and explicit claim gates for sparse or
uncertain annotations. The central claim is methodological: SheafSignal
provides a graph-consistency view of cell-cell communication that complements,
but does not replace, established ligand-receptor prioritization.

## Results

### A sheaf-valued flow defines communication frustration

SheafSignal takes a cell-by-gene or profile-by-gene expression table,
cell-type annotations, ligand-receptor pairs and a pathway or target-gene set.
It builds a directed cell-type graph in which each sender-receiver edge carries
two quantities: communication evidence derived from sender ligand and receiver
receptor expression, and a pathway-state transition estimated in the receiver
context. Edge-level sheaf energy is the standardized mismatch between these
quantities. Node-level frustration scores summarize the share of outgoing
inconsistency contributed by each sender population, while global
gradient/curl/harmonic ratios summarize the structure of the resulting flow.

This design separates three outputs that are conflated in ordinary edge
ranking. A gradient-dominated flow is largely explainable by node potentials;
curl captures local feedback-like inconsistency around triangular motifs; and
harmonic energy represents residual circulation-like structure that is neither
node-potential nor local-triangle flow. The output therefore complements
ligand-receptor intensity by making network self-consistency measurable.

### Simulations validate the Hodge component implementation

We first tested whether the implementation recovers known graph-flow
structure. The simulation panel included pure gradient, pure curl, pure
harmonic and mixed-flow scenarios. The pure-flow controls recovered their expected dominant component (gradient_chain: gradient 1, curl 0, harmonic 1.82e-31; triangle_curl: gradient 0, curl 1, harmonic 0; harmonic_ring: gradient 0, curl 0, harmonic 1), and the mixed graph distributed energy across components (mixed: gradient 0.446, curl 0.286, harmonic 0.268).
These controls validate the decomposition layer and define the interpretation
of the reported ratios. They are mathematical checks, not biological evidence.

### Public tumor benchmarks show context-specific computational sheaf-energy rankings

We next ran the same workflow across public tumor microenvironment datasets.
The completed public benchmark set comprised gse72056_melanoma_scrna (scRNA-seq; 7 cell-type states; highest computational source CAF/Fibroblast; total sheaf energy 47.7); gse154778_pdac_scrna (scRNA-seq; 7 cell-type states; highest computational source CAF/Fibroblast; total sheaf energy 38.1); gse176078_brca_scrna (scRNA-seq; 8 cell-type states; highest computational source Endothelial; total sheaf energy 45.4); gse103322_hnsc_scrna (scRNA-seq; 8 cell-type states; highest computational source Endothelial; total sheaf energy 56.9); and tenx_breast_visium (Visium spatial transcriptomics; 3,798 in-tissue spots and 22,788 directed spot-neighbor edges for hotspot localization at k=6). The highest sender contributing
frustration differed across scRNA-seq datasets and analysis modes: CAF/Fibroblast in
melanoma and pancreatic cancer, and Endothelial in breast cancer single-cell data
and head and neck cancer. The Visium case is used only as a spot-level spatial
hotspot workflow demonstration. This pattern supports the method-level
claim that computational sheaf-energy rankings are dataset-dependent, not the
biological claim that a single cell type universally dominates tumor
communication inconsistency.

### Pancreatic cancer claim gating exposes mode-dependent cell-type rankings

GSE154778 pancreatic cancer was used as the detailed claim-gated case because
it includes primary and metastatic lesions and a complete public processed
matrix. The first-pass annotation is deliberately described as coarse
marker-based annotation. We therefore required minimum lesion-level cell
support, sample support, marker confidence and robustness evidence before any
cell-type-level result could enter the main narrative.

The earlier profile-level and lesion-stratified QC workflow prioritized
Myeloid under annotation-aware support criteria, but the pooled expression-mode
confirmatory run ranked CAF/Fibroblast highest by raw node frustration score
(frustration score 0.431; empirical p=0.0118; BH-FDR=0.0157 with 10,000
sample-stratified permutations), while Myeloid had a lower raw score but a
stronger deviation from its sample-stratified null distribution (frustration
score 0.185; empirical p=9.999e-05; BH-FDR=0.0002). Because CAF/Fibroblast has
sparse metastatic support in the lesion-stratified gate and Myeloid is not the
pooled top-ranked source, neither cell type is promoted here as a validated
pancreatic-cancer mechanism. The GSE154778 case is retained as an explicit
example of why annotation validation, permutation/FDR hardening and
sample-level support must precede biological source claims.

### Comparator alignment shows complementarity rather than broad superiority

SheafSignal was compared with conventional and external communication evidence
after aligning outputs at the sender-receiver edge level. Aligned comparator evidence included LRProductBaseline across 4 datasets, Spearman -0.0496-0.72; LIANA across 3 datasets, Spearman 0.0743-0.699; MechanisticTargetPrior across 3 datasets, Spearman 0.176-0.643; NicheNet across 3 datasets, Spearman 0.184-0.75.
The comparator panel shows that SheafSignal is not merely a relabelled
ligand-receptor product score, while also showing that it remains connected to
recognized communication evidence. The intended conclusion is complementarity:
existing tools prioritize communication evidence, whereas SheafSignal asks
whether those graph-level flows are consistent with pathway-state structure.

The NicheNet-related comparator is intentionally bounded. It uses the official
nichenetr scoring engine with a project-curated tumor-microenvironment prior
matrix, not a full pretrained NicheNet network benchmark. For this reason, the
manuscript does not claim broad superiority over NicheNet, CellChat,
CellPhoneDB, LIANA or niche-DE.

### Spatial analysis localizes hotspots with spot-level boundaries

The breast Visium case demonstrates how the framework extends to spatial
profiles. SheafSignal was run on spot-level profiles and spatial neighborhoods,
with k-neighbor sensitivity checks and spot-level QC. Because Visium spots can
contain mixed cell states and the current labels are marker-dominant rather
than histology-validated single-cell identities, these results are positioned
as hotspot localization and workflow demonstration. They are not presented as
histology-confirmed cell-type mechanisms.

## Discussion

SheafSignal reframes cell-cell communication analysis around consistency
rather than intensity alone. By representing communication as a sheaf-valued
flow and decomposing that flow with Hodge theory, the method reports where
communication edges are discordant with pathway-state transitions and whether
the fitted graph-flow structure is dominated by directional, local curl-like or
global circulation-like components. This provides an
interpretive layer that is absent from pairwise ligand-receptor ranking.

The public benchmarks illustrate the practical value of this reframing.
Different tumor datasets showed different computational frustration rankings,
arguing against a universal cell-type explanation and in favor of dataset- and
context-specific analysis. The pancreatic cancer case also illustrates why
claim gating is necessary for high-impact computational biology: a Myeloid
signal observed in profile-level and lesion-stratified QC did not remain a
standalone main claim after expression-mode permutation/FDR hardening, while
the CAF/Fibroblast ranking is underpowered for lesion-specific interpretation.
The result is therefore a cautionary computational finding for follow-up, not
a clinical or mechanistic proof.

The comparator analyses support the same boundary. Alignment with LIANA,
ligand-receptor product scoring, a mechanistic target-prior baseline and
bounded nichenetr-engine scoring indicates that SheafSignal remains connected
to established communication evidence. Discordance is also expected, because
SheafSignal measures inconsistency relative to pathway-state structure rather
than communication strength alone. The manuscript therefore avoids broad
superiority language and treats comparator evidence as a test of alignment,
non-equivalence and interpretability.

Several limitations are central to the current study. First, all disease
examples are based on public data and should be interpreted as computational
and hypothesis-generating. Second, some annotations are coarse, especially in
GSE154778 and the Visium case, so cell-type claims require explicit QC and
should not be overextended. Third, the current comparator set does not exhaust
all CCC tools or all possible NicheNet resources. Fourth, SheafSignal itself
does not provide evidence for clinical utility, treatment guidance or
therapeutic recommendations.

Future work should extend the framework to larger simulation stress tests,
additional public and private validation cohorts, fuller external tool
execution, and experimental perturbation of prioritized frustration sources.
The present study establishes the mathematical formulation, open software,
public-data benchmark suite and claim-safety framework needed for that next
stage.

## Methods

### Inputs and preprocessing

SheafSignal accepts expression data, cell annotations, ligand-receptor pairs
and pathway or target-gene sets. Single-cell data are summarized to cell-type
or sample-by-cell-type profiles for graph-level analysis after dataset-specific
preparation. Spatial data are analyzed at spot-profile level with explicit
spot-level interpretation boundaries. Public dataset accession, download,
checksum and preparation metadata are tracked in the dataset manifest.

### Communication flow and sheaf energy

For each directed sender-receiver pair, sender ligand expression and receiver
receptor expression define communication evidence. Receiver pathway state is
summarized from target-gene activity. Both quantities are standardized before
their mismatch is calculated. This mismatch is reported as edge-level sheaf
energy, with sender-level frustration scores computed from outgoing sheaf
energy.

### Hodge decomposition

The edge flow is decomposed into gradient, curl and harmonic components using
graph Hodge decomposition. Gradient energy captures the portion explainable by
node potentials, curl captures local feedback-like triangular structure, and
harmonic energy captures residual global circulation-like structure. Component
ratios are reported as fractions of total flow energy.

### Claim gating

The GSE154778 pancreatic cancer analysis used a pre-specified evidence-tier
gate. A category was eligible for main-text interpretation only when it had
adequate cell support and sample support within lesion strata, acceptable
marker confidence and robustness evidence. Sparse or low-confidence categories
were downgraded to supplementary QC interpretation before biological
discussion.

### Comparator analyses

Comparator outputs were aligned at the sender-receiver edge level. The current
panel includes a ligand-receptor product baseline, LIANA imports,
MechanisticTargetPrior scoring and bounded nichenetr-engine scoring with a
project-curated tumor-microenvironment prior matrix. The comparison tests
alignment and complementarity, not broad tool superiority.

### Reproducibility and availability

All source code, tests, dataset manifests, figure manifests, release manifests,
claim-safety audits and manuscript-supporting tables are generated within the
repository. Large processed objects are prepared for Zenodo deposition, while
code and small result tables are prepared for GitHub release.

## Data Availability

Raw public data remain available from the original GEO and 10x Genomics
sources listed in `metadata/datasets.tsv`. Frozen processed objects are
prepared for Zenodo deposition. The Zenodo DOI must be inserted after the
deposition is published.

## Code Availability

Source code, tests, benchmark scripts and small result tables are prepared for
public GitHub release. The final repository URL must be inserted after public
release.

## Acknowledgements

TBD.

## Author Contributions

TBD.

## Competing Interests

TBD.

## Boundary Statement

This is a computational methods manuscript. It does not claim clinical
utility, treatment guidance, treatment-response prediction, guaranteed journal
acceptance or broad superiority over established cell-cell communication
tools.
