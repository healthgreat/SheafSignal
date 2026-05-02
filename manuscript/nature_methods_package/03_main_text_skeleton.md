# Main Text Skeleton

## Introduction

- Current ligand-receptor communication tools answer whether a sender can
  signal to a receiver.
- The missing question is graph-level consistency: whether edge-level
  communication agrees with receiver pathway state across the tissue network.
- SheafSignal introduces a sheaf-valued flow object and Hodge decomposition to
  quantify inconsistency, curl-like local structure and harmonic graph-flow
  components.

## Results

### SheafSignal defines communication frustration as a sheaf-valued flow

- Define sender-receiver ligand-receptor flow.
- Define receiver pathway-state gradient.
- Define sheaf energy as mismatch between communication flow and pathway-state
  transition.
- Decompose net graph flow into gradient, curl and harmonic components.

### Controlled simulations recover known Hodge components

Evidence summary: gradient_chain: gradient=1, curl=0, harmonic=1.82e-31; triangle_curl: gradient=0, curl=1, harmonic=0; harmonic_ring: gradient=0, curl=0, harmonic=1; mixed: gradient=0.446, curl=0.286, harmonic=0.268

### Public tumor benchmarks report context-specific computational sheaf-energy rankings

Completed public benchmark summary: gse72056_melanoma_scrna (scRNA-seq, highest computational source CAF/Fibroblast); gse154778_pdac_scrna (scRNA-seq, highest computational source CAF/Fibroblast after expression-mode permutation/FDR hardening); gse176078_brca_scrna (scRNA-seq, highest computational source Endothelial); gse103322_hnsc_scrna (scRNA-seq, highest computational source Endothelial); tenx_breast_visium (Visium spatial transcriptomics, spot-level hotspot demonstration with k-neighbor sensitivity and marker-program QC)

Interpretation boundary: these datasets support a reusable method and
dataset-dependent computational rankings; they do not support a universal
source-cell claim or validated tumor mechanism across cancers.

### GSE154778 claim gating exposes analysis-mode dependence

- Main-text source mechanism candidate: none under the current hardening gate.
- Myeloid remains a hypothesis-generating QC observation, not a validated source claim.
- CAF/Fibroblast is expression-mode top but remains underpowered for lesion-specific interpretation.
- Sample-level heterogeneity is reported as a limitation rather than hidden.

### External and mechanistic comparators show SheafSignal is not only LR intensity

Comparator summary: LIANA: 3 datasets, Spearman 0.0743-0.699; LRProductBaseline: 4 datasets, Spearman -0.0496-0.72; MechanisticTargetPrior: 3 datasets, Spearman 0.176-0.643; NicheNet: 3 datasets, Spearman 0.184-0.75

Interpretation boundary: use LIANA and bounded nichenetr-engine evidence as
benchmark support. Do not claim broad superiority over all CCC tools.

### Spatial Visium analysis demonstrates hotspot localization

- Use hotspot localization and k-neighbor sensitivity.
- Do not infer single-cell mechanism from marker-dominant Visium spot labels.

## Discussion

- SheafSignal moves CCC analysis from pairwise communication intensity to
  graph-level consistency.
- The method is designed for hypothesis generation and computational
  prioritization, not clinical decision making.
- Main limitations: public-data-only validation, marker/coarse annotations in
  some datasets, bounded nichenetr-engine prior, and comparator claims limited
  to the completed primary scRNA-seq scope. Pending demo/Visium/GSE103322 and
  niche-DE rows remain outside the main comparator claim.

## Data And Code Availability

- GitHub release package is generated locally.
- Zenodo deposition is required before submission.
