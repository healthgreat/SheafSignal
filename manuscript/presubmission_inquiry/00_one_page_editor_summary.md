# One-Page Editor Summary

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
- Public benchmarks: gse72056_melanoma_scrna, gse154778_pdac_scrna and gse176078_brca_scrna as scRNA-seq sheaf-energy ranking cases; tenx_breast_visium as a spot-level spatial hotspot workflow demonstration with k-neighbor sensitivity.
- Comparator evidence: LIANA (3 datasets), LRProductBaseline (4 datasets), MechanisticTargetPrior (3 datasets), NicheNet (3 datasets).
- Claim gating: GSE154778 Myeloid remains a supplement-level computational
  hypothesis; sparse categories remain supplementary QC.
- Reproducibility: GitHub and Zenodo release manifests, checksums, deterministic
  archives and final go/no-go gates are generated locally.

## Editorial Boundary

The manuscript is not positioned as clinical utility, treatment prediction or a
claim of broad superiority over all cell-cell communication tools. It is a
methods manuscript about graph-level communication consistency.
